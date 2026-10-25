"""I12: analytical invariants and preregistered synthetic transmission tests."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
from math import log, sqrt
import unittest

import numpy as np

from paleogen_rl.genetics.ancestry import BlockPanel, measure_ancestry
from paleogen_rl.genetics.inheritance import (
    INHERITANCE_VERSION, RecombinationMap, copy_counts, inherit_diploid,
)


SEEDS = (104729, 130363, 155921)
DESCENDANTS = 20000
ALPHA = .001


def panel(blocks):
    return BlockPanel(f'synthetic-{blocks}', tuple(f'b{i}' for i in range(blocks)))


class TestAutosomalInheritance(unittest.TestCase):
    def test_parental_origins_project_into_i11_measurement(self):
        parents = np.array([[[0]*4, [0]*4], [[1]*4, [1]*4]], dtype=np.uint8)
        mapping = RecombinationMap(panel(4), (0., .2, .5))
        mothers, fathers = [0, 1, 0], [1, 0, 1]
        children = inherit_diploid(parents, mothers=mothers, fathers=fathers,
                                   recombination_map=mapping, rng=np.random.default_rng(17))
        np.testing.assert_array_equal(children[:, 0, :], [[0]*4, [1]*4, [0]*4])
        np.testing.assert_array_equal(children[:, 1, :], [[1]*4, [0]*4, [1]*4])
        counts = copy_counts(children)
        self.assertEqual(counts.dtype, np.uint8)
        np.testing.assert_array_equal(counts, np.ones((3, 4), dtype=np.uint8))
        result = measure_ancestry(counts, mapping.panel, generation=1, target_generation=1,
                                  mode='full', partner_block_ids=('b0',))
        self.assertEqual(result['value'], .5)
        self.assertEqual(result['allele_copy_denominator'], 24)
        reversed_children = inherit_diploid(parents, mothers=fathers, fathers=mothers,
                                            recombination_map=mapping, rng=np.random.default_rng(17))
        np.testing.assert_array_equal(reversed_children, children[:, ::-1, :])

    def test_zero_recombination_transmits_whole_parental_homologues(self):
        parents = np.array([
            [[0, 1, 0, 1, 0, 1], [1, 0, 1, 0, 1, 0]],
            [[0, 0, 1, 1, 0, 0], [1, 1, 0, 0, 1, 1]],
        ])
        mapping = RecombinationMap(panel(6), (0.,)*5)
        mothers = np.arange(500) % 2
        fathers = 1-mothers
        children = inherit_diploid(parents, mothers=mothers, fathers=fathers,
                                   recombination_map=mapping, rng=np.random.default_rng(17))
        for slot, indices in enumerate((mothers, fathers)):
            allowed = np.any(np.all(children[:, slot, None, :] == parents[indices], axis=2), axis=1)
            self.assertTrue(allowed.all())

    def test_active_recombination_never_creates_an_allele_or_changes_parent_origin(self):
        parents = np.array([
            [[0, 1, 0, 1, 0], [0, 0, 1, 1, 1]],
            [[1, 0, 1, 0, 1], [1, 1, 1, 0, 0]],
            [[0, 1, 1, 0, 1], [1, 1, 0, 0, 1]],
        ])
        mapping = RecombinationMap(panel(5), (.5, .3, 0., .5))
        mothers = np.tile([0, 1, 2], 100)
        fathers = np.tile([2, 0, 1], 100)
        children = inherit_diploid(parents, mothers=mothers, fathers=fathers,
                                   recombination_map=mapping, rng=np.random.default_rng(42))
        self.assertEqual(children.shape, (300, 2, 5))
        for slot, indices in enumerate((mothers, fathers)):
            allowed = np.any(children[:, slot, None, :] == parents[indices], axis=1)
            self.assertTrue(allowed.all())

    def test_absorbing_ancestries_survive_five_generations_at_zero_and_active_recombination(self):
        for modern in (0, 1):
            for switches in ((0.,)*4, (.2, .5, 0., .3)):
                with self.subTest(modern=modern, switches=switches):
                    mapping = RecombinationMap(panel(5), switches)
                    population = np.full((40, 2, 5), modern, dtype=np.uint8)
                    rng = np.random.default_rng(17)
                    for generation in range(1, 6):
                        # Caller-defined female/male index pools; no selection.
                        population = inherit_diploid(
                            population, mothers=rng.integers(0, 20, 40),
                            fathers=rng.integers(20, 40, 40), recombination_map=mapping, rng=rng)
                        np.testing.assert_array_equal(population, modern)
                    result = measure_ancestry(copy_counts(population), mapping.panel,
                                              generation=5, target_generation=5, mode='full')
                    self.assertEqual(result['value'], float(modern))

    def test_mendelian_segregation_preregistered_tolerances(self):
        parents = np.array([[[0], [1]], [[0], [1]]], dtype=np.uint8)
        mapping = RecombinationMap(panel(1), ())
        epsilon = sqrt(log(2*15/ALPHA)/(2*DESCENDANTS))
        for seed in SEEDS:
            with self.subTest(seed=seed):
                children = inherit_diploid(
                    parents, mothers=np.zeros(DESCENDANTS, dtype=int),
                    fathers=np.ones(DESCENDANTS, dtype=int), recombination_map=mapping,
                    rng=np.random.default_rng(seed))
                observed = np.bincount(copy_counts(children)[:, 0], minlength=3)/DESCENDANTS
                for actual, expected in zip(observed, (.25, .5, .25)):
                    self.assertLessEqual(abs(actual-expected), epsilon)
                for slot in (0, 1):
                    self.assertLessEqual(abs(float(children[:, slot, 0].mean())-.5), epsilon)

    def test_boundary_switch_frequencies_preregistered_tolerances(self):
        parents = np.zeros((2, 2, 4), dtype=np.uint8)
        parents[:, 1, :] = 1
        mapping = RecombinationMap(panel(4), (0., .2, .5))
        epsilon = sqrt(log(2*18/ALPHA)/(2*DESCENDANTS))
        for seed in SEEDS:
            with self.subTest(seed=seed):
                children = inherit_diploid(
                    parents, mothers=np.zeros(DESCENDANTS, dtype=int),
                    fathers=np.ones(DESCENDANTS, dtype=int), recombination_map=mapping,
                    rng=np.random.default_rng(seed))
                for slot in (0, 1):
                    observed = (children[:, slot, 1:] != children[:, slot, :-1]).mean(axis=0)
                    self.assertEqual(observed[0], 0.)
                    for actual, expected in zip(observed, (0., .2, .5)):
                        self.assertLessEqual(abs(actual-expected), epsilon)

    def test_repeatability_and_input_rng_isolation(self):
        parents = np.array([[[0, 0, 1], [1, 1, 0]], [[1, 1, 0], [0, 0, 1]]])
        mothers = np.array([0, 1]*30)
        fathers = 1-mothers
        before = [array.copy() for array in (parents, mothers, fathers)]
        mapping = RecombinationMap(panel(3), (.2, .5))
        global_before = np.random.get_state()
        a, b = np.random.default_rng(42), np.random.default_rng(42)
        first = inherit_diploid(parents, mothers=mothers, fathers=fathers, recombination_map=mapping, rng=a)
        second = inherit_diploid(parents, mothers=mothers, fathers=fathers, recombination_map=mapping, rng=b)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(a.bit_generator.state, b.bit_generator.state)
        for old, new in zip(before, (parents, mothers, fathers)):
            np.testing.assert_array_equal(old, new)
        self.assertFalse(np.shares_memory(first, parents))
        global_after = np.random.get_state()
        for old, new in zip(global_before, global_after):
            np.testing.assert_equal(old, new)

    def test_map_is_immutable_validated_and_json_serializable(self):
        probabilities = [0., .2]
        mapping = RecombinationMap(panel(3), probabilities)
        probabilities[1] = .5
        self.assertEqual(mapping.switch_probabilities, (0., .2))
        with self.assertRaises(FrozenInstanceError):
            mapping.switch_probabilities = (.5, .5)
        document = json.loads(json.dumps(mapping.to_dict(), allow_nan=False))
        self.assertEqual(document['inheritance_version'], INHERITANCE_VERSION)
        self.assertEqual(document['offspring_homologue_order'], ['maternal', 'paternal'])
        self.assertFalse(document['within_block_recombination'])
        restored = RecombinationMap(BlockPanel(**document['panel']), document['switch_probabilities'])
        self.assertEqual(restored, mapping)
        for probabilities in ((0.,), (0., .1, .2), (-.1, .2), (.51, .2),
                              (float('nan'), .2), (float('inf'), .2), (True, .2), ('0', .2), '00'):
            with self.subTest(probabilities=probabilities), self.assertRaises(ValueError):
                RecombinationMap(panel(3), probabilities)
        with self.assertRaises(ValueError):
            RecombinationMap(None, ())

    def test_invalid_inputs_are_rejected_without_consuming_rng(self):
        valid = dict(haplotypes=np.zeros((2, 2, 3), dtype=np.uint8),
                     mothers=[0, 0], fathers=[1, 1], recombination_map=RecombinationMap(panel(3), (.2, .5)))
        invalid_states = (
            np.zeros((2, 3), dtype=int), np.zeros((2, 1, 3), dtype=int),
            np.zeros((0, 2, 3), dtype=int), np.zeros((2, 2, 0), dtype=int),
            np.full((2, 2, 3), 2), np.full((2, 2, 3), -1),
            np.zeros((2, 2, 3), dtype=float), np.full((2, 2, 3), float('nan')),
            np.ma.array(np.zeros((2, 2, 3), dtype=int), mask=True),
        )
        invalid = [dict(haplotypes=state) for state in invalid_states]
        for name in ('mothers', 'fathers'):
            for indices in ([], [0], [-1, 0], [0, 2], [True, False], [0., 1.], [[0, 1]],
                            np.ma.array([0, 1], mask=[False, True])):
                invalid.append({name: indices})
        invalid.extend([dict(recombination_map=None),
                        dict(recombination_map=RecombinationMap(panel(2), (.2,)))])
        for overrides in invalid:
            with self.subTest(overrides=repr(overrides)):
                rng = np.random.default_rng(17)
                before = deepcopy(rng.bit_generator.state)
                with self.assertRaises(ValueError):
                    inherit_diploid(**{**valid, **overrides}, rng=rng)
                self.assertEqual(rng.bit_generator.state, before)
        for state in invalid_states:
            with self.assertRaises(ValueError):
                copy_counts(state)
        with self.assertRaises(ValueError):
            inherit_diploid(**valid, rng=None)


if __name__ == '__main__':
    unittest.main()
