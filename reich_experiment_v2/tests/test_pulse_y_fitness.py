"""Sex-specific Y viability, independently of the female Y sentinel."""

from dataclasses import asdict
from itertools import product
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from epi_pulse import Config, _epistasis_loss


# Independent genotype tables, indexed by modern diploid copy count 0, 1, 2.
MODERN_EXPOSURE = {'additive': (0., .5, 1.), 'dominant': (0., 1., 1.),
                   'recessive': (0., 0., 1.)}
ARCHAIC_EXPOSURE = {'additive': (1., .5, 0.), 'dominant': (1., 1., 0.),
                    'recessive': (1., 0., 0.)}


class TestPulseYFitness(unittest.TestCase):
    def test_each_y_direction_requires_male_sex_independently_of_sentinel(self):
        # Female Y=0/1 are adversarial function inputs, not biological genotypes.
        cases = list(product((0, 1), (-1, 0, 1), (0, 1, 2)))
        sex = np.array([case[0] for case in cases])
        y = np.array([case[1] for case in cases])
        mt = np.zeros(len(cases), dtype=int)
        for dominance in MODERN_EXPOSURE:
            for locus in (1, 5):
                for field, marker, coefficient, table in (
                    ('y_mod_nuc_arch', 1, .3, ARCHAIC_EXPOSURE),
                    ('y_arch_nuc_mod', 0, .4, MODERN_EXPOSURE),
                ):
                    with self.subTest(dominance=dominance, locus=locus, field=field):
                        auto = np.zeros((len(cases), 8), dtype=int)
                        auto[:, locus] = [case[2] for case in cases]
                        config = Config(y_partner_locus=locus, mismatch_dominance=dominance,
                                        **{field: coefficient})
                        before = asdict(config)
                        inputs = [array.copy() for array in (sex, mt, y, auto)]
                        expected = [coefficient * table[dominance][copies]
                                    if sx == 1 and allele == marker else 0.
                                    for sx, allele, copies in cases]
                        actual = _epistasis_loss(config, sex, mt, y, auto)
                        np.testing.assert_allclose(actual, expected, atol=1e-15, rtol=0)
                        np.testing.assert_array_equal(actual[sex == 0], 0.)
                        self.assertGreater(float(actual[sex == 1].max()), 0.)
                        self.assertEqual(asdict(config), before)
                        for old, new in zip(inputs, (sex, mt, y, auto)):
                            np.testing.assert_array_equal(old, new)

    def test_y_survival_composes_with_mt_without_changing_female_fitness(self):
        cases = list(product((0, 1), (0, 1), (-1, 0, 1), (0, 1, 2), (0, 1, 2)))
        sex = np.array([case[0] for case in cases])
        mt = np.array([case[1] for case in cases])
        y = np.array([case[2] for case in cases])
        auto = np.zeros((len(cases), 8), dtype=int)
        auto[:, 0] = [case[3] for case in cases]
        auto[:, 1] = [case[4] for case in cases]
        for dominance in MODERN_EXPOSURE:
            with self.subTest(dominance=dominance):
                base = Config(mt_mod_nuc_arch=.2, mt_arch_nuc_mod=.25,
                              mismatch_dominance=dominance)
                config = Config(**{**asdict(base), 'y_mod_nuc_arch': .3, 'y_arch_nuc_mod': .4})
                expected = []
                for sx, maternal, paternal, mt_copies, y_copies in cases:
                    mt_cost = (.2 * ARCHAIC_EXPOSURE[dominance][mt_copies] if maternal == 1
                               else .25 * MODERN_EXPOSURE[dominance][mt_copies])
                    y_cost = 0.
                    if sx == 1 and paternal == 1:
                        y_cost = .3 * ARCHAIC_EXPOSURE[dominance][y_copies]
                    elif sx == 1 and paternal == 0:
                        y_cost = .4 * MODERN_EXPOSURE[dominance][y_copies]
                    expected.append(1. - (1. - mt_cost) * (1. - y_cost))
                actual = _epistasis_loss(config, sex, mt, y, auto)
                baseline = _epistasis_loss(base, sex, mt, y, auto)
                np.testing.assert_allclose(actual, expected, atol=1e-15, rtol=0)
                np.testing.assert_array_equal(actual[sex == 0], baseline[sex == 0])
                self.assertTrue(np.any(actual[sex == 1] > baseline[sex == 1]))


if __name__ == '__main__':
    unittest.main()
