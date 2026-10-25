"""Analytical weighted measurements; no simulation or target optimization."""

from dataclasses import FrozenInstanceError
import json
import unittest

import numpy as np

from paleogen_rl.genetics.ancestry import BlockPanel, measure_ancestry
from paleogen_rl.genetics.weighted_ancestry import (
    MEASUREMENT_VERSION, WeightedBlockPanel, measure_weighted_ancestry,
)


class TestWeightedAutosomalAncestry(unittest.TestCase):
    def panel(self, weights):
        return WeightedBlockPanel(BlockPanel('synthetic', tuple(f'b{i}' for i in range(len(weights)))),
                                  weights, 'synthetic analytical fixture; no empirical calibration')

    def measure(self, counts, panel, **changes):
        arguments = dict(generation=7, target_generation=7, mode='full')
        arguments.update(changes)
        return measure_weighted_ancestry(counts, panel, **arguments)

    def test_analytical_values_units_and_input_preservation(self):
        panel = self.panel((1, 2, 1))
        for population in (1, 3, 20):
            for copies in (0, 1, 2):
                result = self.measure(np.full((population, 3), copies, dtype=int), panel)
                self.assertEqual(result['value'], copies/2)
                self.assertEqual(result['modern_ancestry_weight'], copies/2)
                self.assertEqual(result['weight_denominator'], 1.)
                self.assertEqual(result['unweighted_modern_allele_copies'], copies*population*3)
                self.assertEqual(result['unweighted_allele_copy_denominator'], 2*population*3)
        counts = np.array([[2, 0, 1], [0, 1, 0]])
        before = counts.copy()
        result = self.measure(counts, panel)
        self.assertEqual(result['value'], .3125)
        self.assertEqual(result['modern_ancestry_weight']/result['weight_denominator'], result['value'])
        self.assertEqual(result['unweighted_modern_allele_copies'], 4)
        self.assertEqual(result['diploid_individuals'], 2)
        np.testing.assert_array_equal(counts, before)

    def test_equal_weights_match_i11_without_relabeling_it(self):
        for population in (1, 3, 20):
            for blocks in (1, 8, 32):
                panel = self.panel((7,)*blocks)
                counts = np.arange(population*blocks).reshape(population, blocks) % 3
                legacy = measure_ancestry(counts, panel.panel, generation=7, target_generation=7, mode='full')
                result = self.measure(counts, panel)
                self.assertAlmostEqual(result['value'], legacy['value'], places=14)
                self.assertNotEqual(result['measurement_version'], legacy['measurement_version'])
                self.assertNotEqual(result['observable'], legacy['observable'])
                self.assertNotIn('allele_copy_denominator', result)

    def test_three_refinements_conserve_measurement_and_partner_weights(self):
        for neutral_counts, expected in (((0, 0), .375), ((1, 0), .5), ((1, 2), .75)):
            values, legacy_values = [], []
            for weights in ((2, 4, 2), (2, 2, 2, 2), (2, 1, 1, 1, 1, 2)):
                panel = self.panel(weights)
                counts = np.zeros((2, len(weights)), dtype=int)
                counts[:, 1:-1] = np.array(neutral_counts)[:, None]
                counts[0, [0, -1]] = 2
                counts[1, [0, -1]] = 1
                partners = (panel.panel.block_ids[0], panel.panel.block_ids[-1])
                result = self.measure(counts, panel, partner_block_ids=partners)
                values.append(result['value'])
                for partner in result['partner_diagnostics']:
                    self.assertEqual(partner['relative_panel_weight'], .25)
                    self.assertEqual(partner['value'], .75)
                    self.assertEqual(partner['weighted_ancestry_contribution'], .1875)
                legacy = measure_ancestry(counts, panel.panel, generation=7, target_generation=7, mode='full')
                legacy_values.append(legacy['value'])
            self.assertEqual(values, [expected]*3)
            if neutral_counts == (0, 0):
                self.assertEqual(legacy_values, [.5, .375, .25])

    def test_scale_invariance_and_large_finite_weights(self):
        counts = [[2, 0, 1], [0, 1, 0]]
        for scale in (1e-200, 1., 32., 1e200, 8e307):
            panel = self.panel((scale, 2*scale, scale))
            result = self.measure(counts, panel)
            self.assertEqual(result['value'], .3125)
            self.assertEqual(result['panel']['normalized_weights'], [.25, .5, .25])
            self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)

    def test_partner_annotations_never_change_measurement_or_weights(self):
        panel = self.panel((1, 2, 1))
        baseline = self.measure([[2, 0, 1]], panel)
        for partners in ((), ('b0',), ('b2', 'b0'), panel.panel.block_ids):
            result = self.measure([[2, 0, 1]], panel, partner_block_ids=partners)
            for field in ('value', 'modern_ancestry_weight', 'weight_denominator', 'panel',
                          'unweighted_modern_allele_copies', 'unweighted_allele_copy_denominator'):
                self.assertEqual(result[field], baseline[field])
        reversed_partners = self.measure([[2, 0, 1]], panel, partner_block_ids=('b2', 'b0'))
        self.assertEqual(reversed_partners['partner_block_ids'], ['b0', 'b2'])

    def test_owned_immutable_weights_and_json_reconstruction(self):
        weights = [1, 3]
        panel = self.panel(weights)
        weights.append(5)
        self.assertEqual(panel.block_weights, (1., 3.))
        for field, value in (('block_weights', (1., 1.)), ('normalized_weights', (.5, .5)), ('weight_basis', 'changed')):
            with self.assertRaises(FrozenInstanceError):
                setattr(panel, field, value)
        declaration = panel.to_dict()
        reconstructed = WeightedBlockPanel(BlockPanel(declaration['panel_id'], declaration['block_ids']),
                                            declaration['block_weights'], declaration['weight_basis'])
        self.assertEqual(panel, reconstructed)
        declaration['normalized_weights'].append(0.)
        self.assertEqual(panel.normalized_weights, (.25, .75))
        result = self.measure([[1, 2]], panel)
        self.assertEqual(result['measurement_version'], MEASUREMENT_VERSION)
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)

    def test_quick_availability_and_final_horizon_constraints(self):
        panel = self.panel((1, 2))
        for generation in (0, 3, 7):
            result = self.measure([[2, 1]], panel, mode='quick', generation=generation, partner_block_ids=('b0',))
            for field in ('value', 'modern_ancestry_weight', 'unweighted_modern_allele_copies', 'partner_diagnostics'):
                self.assertIsNone(result[field])
            self.assertEqual(result['status'], 'not_evaluated_quick')
            self.assertEqual(result['generation'], generation)
            self.assertEqual(result['unweighted_allele_copy_denominator'], 4)
        full = self.measure([[2, 1]], panel)
        self.assertEqual(self.measure([[2, 1]], panel, mode='adaptive'), {**full, 'mode': 'adaptive'})
        for mode in ('full', 'adaptive'):
            for generation in (0, 6, 8, True, 7.):
                with self.subTest(mode=mode, generation=generation), self.assertRaises(ValueError):
                    self.measure([[2, 1]], panel, mode=mode, generation=generation)

    def test_invalid_weights_counts_and_declarations_are_rejected(self):
        base = BlockPanel('invalid-weights', ('a', 'b'))
        for weights in (None, [], (1,), (1, 2, 3), (0, 1), (-1, 1), (True, 1), (np.bool_(True), 1),
                        (float('nan'), 1), (float('inf'), 1), ('1', 1), (None, 1),
                        (10**1000, 1), (5e-324, 1e308)):
            with self.subTest(weights=repr(weights)), self.assertRaises(ValueError):
                WeightedBlockPanel(base, weights, 'synthetic invalid fixture')
        for basis in ('', ' ', ' padded ', None):
            with self.assertRaises(ValueError):
                WeightedBlockPanel(base, (1, 1), basis)
        with self.assertRaises(ValueError):
            WeightedBlockPanel(None, (1, 1), 'synthetic')
        panel = self.panel((1, 2))
        for counts in ([], [[0]], [[0, 3]], [[-1, 0]], [[0., 1.]], [[True, False]],
                       np.ma.array([[0, 1]], mask=[[True, False]])):
            with self.subTest(counts=repr(counts)), self.assertRaises(ValueError):
                self.measure(counts, panel)
        for partners in (('missing',), ('b0', 'b0')):
            with self.assertRaises(ValueError):
                self.measure([[1, 2]], panel, partner_block_ids=partners)
        with self.assertRaises(ValueError):
            self.measure([[1, 2]], base)


if __name__ == '__main__':
    unittest.main()
