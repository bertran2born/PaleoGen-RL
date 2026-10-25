"""Population drift checks with the I13 protocol fixed before execution."""

import hashlib
import json
from math import log, sqrt
import unittest
from unittest.mock import patch

import numpy as np

from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap, copy_counts, inherit_diploid
from paleogen_rl.genetics.neutral import SIMULATION_VERSION, run_neutral


REPLICATE_SEEDS = range(310000, 311024)
REPLICATES = 1024
EXPECTED_ANCESTRY = .05
ALPHA = .01


def pulse_fixture():
    """Synthetic balanced pulse: one modern male and female among 40 diploids."""
    population = np.zeros((40, 2, 8), dtype=np.uint8)
    population[[0, 20], :, :] = 1
    sex = np.concatenate((np.ones(20, dtype=np.uint8), np.zeros(20, dtype=np.uint8)))
    return population, sex


def mapping(blocks, fraction):
    return RecombinationMap(BlockPanel(f'synthetic-{blocks}', tuple(f'b{i}' for i in range(blocks))),
                            (fraction,)*(blocks-1))


class TestAutosomalNeutral(unittest.TestCase):
    def test_parent_choices_respect_sexes_and_quotas_every_generation(self):
        for size in (5, 6):
            with self.subTest(N=size):
                parents = np.zeros((size, 2, 3), dtype=np.uint8)
                sex = np.arange(size, dtype=np.uint8) % 2
                expected_sex = sex.copy()
                child_sex = np.array([1]*(size//2)+[0]*(size-size//2), dtype=np.uint8)
                calls = 0
                def observe(population, **kwargs):
                    nonlocal calls, expected_sex
                    self.assertEqual(population.shape, (size, 2, 3))
                    self.assertEqual(len(kwargs['mothers']), size)
                    self.assertEqual(len(kwargs['fathers']), size)
                    self.assertTrue(np.all(expected_sex[kwargs['mothers']] == 0))
                    self.assertTrue(np.all(expected_sex[kwargs['fathers']] == 1))
                    offspring = inherit_diploid(population, **kwargs)
                    calls += 1
                    expected_sex = child_sex
                    return offspring
                with patch('paleogen_rl.genetics.neutral.inherit_diploid', side_effect=observe):
                    result = run_neutral(parents, sex, recombination_map=mapping(3, .25),
                                         generations=3, seed=17)
                self.assertEqual(calls, 3)
                np.testing.assert_array_equal(result.sex, child_sex)
                self.assertEqual(result.report['male_n'], size//2)
                self.assertEqual(result.report['female_n'], size-size//2)

    def test_zero_horizon_returns_owned_initial_state(self):
        parents, sex = pulse_fixture()
        result = run_neutral(parents, sex, recombination_map=mapping(8, .25), generations=0, seed=17)
        np.testing.assert_array_equal(result.haplotypes, parents)
        np.testing.assert_array_equal(result.sex, sex)
        self.assertFalse(np.shares_memory(result.haplotypes, parents))
        self.assertFalse(np.shares_memory(result.sex, sex))
        self.assertEqual(result.report['initial_measurement'], result.report['final_measurement'])
        self.assertEqual(result.report['generations_completed'], 0)
        self.assertEqual(result.report['work_units']['offspring_generated'], 0)

    def test_repeatability_and_annotations_do_not_change_reproduction(self):
        parents, sex = pulse_fixture()
        before_parents, before_sex = parents.copy(), sex.copy()
        global_before = np.random.get_state()
        kwargs = dict(recombination_map=mapping(8, .25), generations=5, seed=17)
        first = run_neutral(parents, sex, **kwargs)
        second = run_neutral(parents, sex, **kwargs)
        annotated = run_neutral(parents, sex, **kwargs, partner_block_ids=('b7', 'b0'))
        np.testing.assert_array_equal(first.haplotypes, second.haplotypes)
        np.testing.assert_array_equal(first.sex, second.sex)
        self.assertEqual(first.report, second.report)
        np.testing.assert_array_equal(first.haplotypes, annotated.haplotypes)
        for field in ('initial_measurement', 'final_measurement'):
            self.assertEqual(first.report[field]['value'], annotated.report[field]['value'])
            self.assertEqual(first.report[field]['panel'], annotated.report[field]['panel'])
            self.assertEqual(first.report[field]['allele_copy_denominator'],
                             annotated.report[field]['allele_copy_denominator'])
            self.assertEqual(annotated.report[field]['partner_block_ids'], ['b0', 'b7'])
        np.testing.assert_array_equal(parents, before_parents)
        np.testing.assert_array_equal(sex, before_sex)
        for old, new in zip(global_before, np.random.get_state()):
            np.testing.assert_equal(old, new)

    def test_absorbing_states_complete_the_full_clock(self):
        sex = np.array([1, 1, 1, 0, 0, 0], dtype=np.uint8)
        for modern in (0, 1):
            for fraction in (0., .25):
                with self.subTest(modern=modern, fraction=fraction):
                    result = run_neutral(np.full((6, 2, 3), modern, dtype=np.uint8), sex,
                                         recombination_map=mapping(3, fraction), generations=7, seed=17)
                    np.testing.assert_array_equal(result.haplotypes, modern)
                    self.assertEqual(result.report['generations_completed'], 7)
                    measurement = result.report['final_measurement']
                    self.assertEqual(measurement['generation'], 7)
                    self.assertEqual(measurement['target_generation'], 7)
                    self.assertEqual(measurement['status'], 'evaluated_at_target')
                    self.assertEqual(measurement['value'], float(modern))
                    self.assertEqual(result.report['work_units']['offspring_generated'], 42)

    def test_neutral_mean_in_preregistered_bernstein_intervals(self):
        parents, sex = pulse_fixture()
        self.assertEqual(float(copy_counts(parents).mean()/2), EXPECTED_ANCESTRY)
        for category in (0, 1):
            self.assertEqual(float(copy_counts(parents[sex == category]).mean()/2), EXPECTED_ANCESTRY)
        self.assertEqual(len(REPLICATE_SEEDS), REPLICATES)
        threshold = log(2*2/ALPHA)
        epsilon = (sqrt(2*EXPECTED_ANCESTRY*(1-EXPECTED_ANCESTRY)*threshold/REPLICATES)
                   + 2*threshold/(3*REPLICATES))
        self.assertLess(epsilon, EXPECTED_ANCESTRY)
        for fraction in (0., .25):
            with self.subTest(fraction=fraction):
                recombination = mapping(8, fraction)
                values = []
                for seed in REPLICATE_SEEDS:
                    result = run_neutral(parents, sex, recombination_map=recombination,
                                         generations=20, seed=seed)
                    self.assertEqual(result.report['generations_completed'], 20)
                    values.append(result.report['final_measurement']['value'])
                mean = float(np.mean(values))
                interval = (max(0., mean-epsilon), min(1., mean+epsilon))
                message = f'switch={fraction}, mean={mean}, interval={interval}'
                self.assertLessEqual(interval[0], EXPECTED_ANCESTRY, message)
                self.assertGreaterEqual(interval[1], EXPECTED_ANCESTRY, message)

    def test_report_traces_map_phase_and_work_and_replays(self):
        parents = np.zeros((4, 2, 3), dtype=np.uint8)
        parents[0, 0, :] = 1
        sex = np.array([1, 1, 0, 0], dtype=np.uint8)
        result = run_neutral(parents, sex, recombination_map=mapping(3, .25), generations=3, seed=73)
        report = json.loads(json.dumps(result.report, allow_nan=False))
        self.assertEqual(report, result.report)
        self.assertEqual(report['simulation_version'], SIMULATION_VERSION)
        self.assertEqual(report['mode'], 'full')
        self.assertEqual(report['initial_haplotypes_sha256'], hashlib.sha256(parents.tobytes()).hexdigest())
        self.assertEqual(report['initial_sex_sha256'], hashlib.sha256(sex.tobytes()).hexdigest())
        self.assertEqual(report['work_units'], dict(offspring_generated=12,
                                                  block_copy_transmissions=72, state_allele_entries=24))
        declaration = report['recombination_map']
        restored = RecombinationMap(BlockPanel(**declaration['panel']), declaration['switch_probabilities'])
        replayed = run_neutral(parents, sex, recombination_map=restored,
                               generations=report['generations_requested'], seed=report['seed'])
        np.testing.assert_array_equal(result.haplotypes, replayed.haplotypes)
        self.assertEqual(replayed.report, report)
        swapped = run_neutral(parents[:, ::-1, :], sex, recombination_map=restored,
                              generations=0, seed=73)
        self.assertEqual(swapped.report['initial_measurement']['value'], report['initial_measurement']['value'])
        self.assertNotEqual(swapped.report['initial_haplotypes_sha256'], report['initial_haplotypes_sha256'])

    def test_invalid_inputs_are_rejected_before_rng_construction(self):
        parents, sex = pulse_fixture()
        valid = dict(haplotypes=parents, sex=sex, recombination_map=mapping(8, .25),
                     generations=2, seed=17)
        invalid = [
            dict(seed=True), dict(seed=-1), dict(generations=-1), dict(generations=2.),
            dict(generations=True), dict(recombination_map=None), dict(recombination_map=mapping(3, .25)),
            dict(sex=sex[:-1]), dict(sex=np.zeros(40, dtype=int)), dict(sex=sex.astype(float)),
            dict(sex=np.full(40, 2)), dict(sex=np.ma.array(sex, mask=True)),
            dict(haplotypes=np.zeros((40, 8), dtype=int)), dict(haplotypes=np.full((40, 2, 8), 2)),
            dict(haplotypes=np.zeros((1, 2, 8), dtype=int), sex=[0]),
            dict(partner_block_ids=('missing',)),
        ]
        original_rng = np.random.default_rng
        for overrides in invalid:
            with self.subTest(overrides=repr(overrides)):
                with patch('paleogen_rl.genetics.neutral.np.random.default_rng', wraps=original_rng) as generator:
                    with self.assertRaises(ValueError):
                        run_neutral(**{**valid, **overrides})
                    generator.assert_not_called()
        np.testing.assert_array_equal(parents, pulse_fixture()[0])
        np.testing.assert_array_equal(sex, pulse_fixture()[1])

    def test_zero_recombination_keeps_whole_ancestral_haplotypes(self):
        parents = np.array([
            [[0, 1, 0], [1, 0, 1]], [[0, 0, 1], [1, 1, 0]],
            [[1, 0, 0], [0, 1, 1]], [[1, 1, 1], [0, 0, 0]],
        ], dtype=np.uint8)
        result = run_neutral(parents, [1, 1, 0, 0], recombination_map=mapping(3, 0.),
                             generations=6, seed=17)
        ancestors = {tuple(haplotype) for haplotype in parents.reshape(-1, 3)}
        for haplotype in result.haplotypes.reshape(-1, 3):
            self.assertIn(tuple(haplotype), ancestors)


if __name__ == '__main__':
    unittest.main()
