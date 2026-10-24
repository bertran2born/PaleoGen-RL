"""Seeded, pathwise parity of the local SI3 pulse reference and its extension."""

from copy import deepcopy
from dataclasses import asdict, replace
import json
from math import comb
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENT_ROOT / 'src'))
import reich_panmictic_original as original
from epi_pulse import Config, run
from run_experiment import SCENARIOS


SEEDS = (0, 17, 42)
FREQUENCIES = (0.0, 0.05, 1.0)
SCENARIO_NAMES = ('neutral', 'reich_point')
DOMINANCES = ('additive', 'dominant', 'recessive')


def capture_run(runner, config):
    """Observe copies of actual states, without drawing from the RNG or replacing laws."""
    trace = []
    initialize, step = original._init, original._step

    def record(population, rng, generation):
        trace.append({
            'generation': generation,
            'population': None if population is None else
            {key: value.copy() for key, value in population.items()},
            'rng_state': deepcopy(rng.bit_generator.state),
        })
        return population

    def observe_init(cfg, rng):
        return record(initialize(cfg, rng), rng, 0)

    def observe_step(population, cfg, rng, generation=1):
        return record(step(population, cfg, rng, generation), rng, generation + 1)

    with patch.object(original, '_init', observe_init), patch.object(original, '_step', observe_step):
        result = runner(config)
    return result, trace


class TestPulseReference(unittest.TestCase):
    def assert_traces_equal(self, expected, actual):
        self.assertEqual(len(expected), len(actual))
        for reference, extension in zip(expected, actual):
            generation = reference['generation']
            self.assertEqual(generation, extension['generation'])
            self.assertEqual(reference['rng_state'], extension['rng_state'])
            self.assertIsNotNone(reference['population'], f'failed reproduction at {generation}')
            self.assertIsNotNone(extension['population'], f'failed reproduction at {generation}')
            self.assertEqual(set(reference['population']), set(extension['population']))
            for key, array in reference['population'].items():
                other = extension['population'][key]
                self.assertEqual(array.dtype, other.dtype)
                np.testing.assert_array_equal(array, other, err_msg=f'generation={generation}, {key}')

    def assert_added_statistics(self, result, trace):
        population = trace[-1]['population']
        males = population['sex'] == 1
        count = int(males.sum())
        both = int(((population['mt'][males] == 1) & (population['Y'][males] == 1)).sum())
        probability = comb(both, 10) / comb(count, 10) if both >= 10 and count >= 10 else 0.0
        self.assertEqual(result['male_n'], count)
        self.assertEqual(result['both_modern_men'], both)
        self.assertAlmostEqual(result['p10_joint'], probability, places=14)
        self.assertEqual(result['joint_fixed'], bool(
            np.all(population['mt'] == 1) and count > 0 and np.all(population['Y'][males] == 1)))
        self.assertEqual(result['generations_completed'], trace[-1]['generation'])
        self.assertEqual(result['target_auto'], 0.03 <= result['auto_mod'] <= 0.07)

    def test_zero_penalty_pathwise_parity_matrix(self):
        for seed in SEEDS:
            for frequency in FREQUENCIES:
                for scenario in SCENARIO_NAMES:
                    for dominance in DOMINANCES:
                        for early_stop in (False, True):
                            with self.subTest(seed=seed, f=frequency, scenario=scenario,
                                              dominance=dominance, early_stop=early_stop):
                                shared = dict(N=80, gens=32, seed=seed, f=frequency,
                                              stop_when_absorbed=early_stop, **SCENARIOS[scenario])
                                expected, reference_trace = capture_run(original.run, original.Config(**shared))
                                config = Config(**shared, mismatch_dominance=dominance,
                                                mt_mod_nuc_arch=0.0, mt_arch_nuc_mod=0.0,
                                                y_mod_nuc_arch=0.0, y_arch_nuc_mod=0.0)
                                before = asdict(config)
                                actual, extended_trace = capture_run(run, config)
                                self.assert_traces_equal(reference_trace, extended_trace)
                                self.assertEqual(expected, {key: actual[key] for key in expected})
                                self.assert_added_statistics(actual, extended_trace)
                                self.assertEqual(asdict(config), before)
                                if not early_stop:
                                    self.assertEqual(len(extended_trace), config.gens + 1)
                                elif frequency in (0.0, 1.0):
                                    self.assertLess(actual['generations_completed'], config.gens)
                                if scenario == 'neutral':
                                    initial = extended_trace[0]['population']
                                    self.assertEqual(float(initial['mt'].mean()), frequency)
                                    if frequency in (0.0, 1.0):
                                        self.assertEqual(actual['mt_mod'], frequency)
                                        self.assertEqual(actual['Y_mod'], frequency)
                                        self.assertEqual(actual['auto_mod'], frequency)

    def test_ten_males_possible_without_population_fixation(self):
        result, trace = capture_run(run, Config(N=200, gens=1, seed=0, f=0.5,
                                                stop_when_absorbed=False))
        self.assert_added_statistics(result, trace)
        self.assertGreater(result['p10_joint'], 0)
        self.assertLess(result['p10_joint'], 1)
        self.assertFalse(result['joint_fixed'])
        # A replacement approximation is detectably different in this polymorphic case.
        with_replacement = (result['both_modern_men'] / result['male_n']) ** 10
        self.assertLess(result['p10_joint'], with_replacement)

    def test_repeatability_after_active_epistasis_and_error(self):
        for scenario in SCENARIO_NAMES:
            for seed in SEEDS:
                with self.subTest(scenario=scenario, seed=seed):
                    config = Config(N=80, gens=32, seed=seed, stop_when_absorbed=False,
                                    **SCENARIOS[scenario])
                    expected, expected_trace = capture_run(run, config)
                    repeated, repeated_trace = capture_run(run, config)
                    self.assertEqual(repeated, expected)
                    self.assert_traces_equal(expected_trace, repeated_trace)
                    original_penetrance = original._dm_penetrance
                    # Exercise the real temporary epistasis hook, not a stand-in engine.
                    run(replace(config, mt_arch_nuc_mod=0.003, y_mod_nuc_arch=0.003))
                    self.assertIs(original._dm_penetrance, original_penetrance)
                    after_active, trace = capture_run(run, config)
                    self.assertEqual(after_active, expected)
                    self.assert_traces_equal(expected_trace, trace)
                    # This error occurs inside breeding, after the hook is installed.
                    with self.assertRaisesRegex(ValueError, 'dominance'):
                        run(replace(config, mt_arch_nuc_mod=0.003,
                                    mismatch_dominance='invalid'))
                    self.assertIs(original._dm_penetrance, original_penetrance)
                    after_error, trace = capture_run(run, config)
                    self.assertEqual(after_error, expected)
                    self.assert_traces_equal(expected_trace, trace)

    def test_cli_repeated_seeded_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            for scenario in SCENARIO_NAMES:
                with self.subTest(scenario=scenario):
                    outputs = []
                    for repetition in (1, 2):
                        output = Path(directory) / f'{scenario}-{repetition}.csv'
                        result = subprocess.run([
                            sys.executable, str(EXPERIMENT_ROOT / 'run_experiment.py'),
                            '--scenario', scenario, '--mode', 'full', '--reps', '3',
                            '--N', '80', '--gens', '32', '--seed', '0',
                            '--output', str(output),
                        ], cwd=directory, capture_output=True, text=True, check=False)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        document = json.loads(output.with_suffix('.json').read_text(encoding='utf-8'))
                        self.assertEqual(document['meta'].pop('output'), str(output))
                        for summary in document['summary']:
                            self.assertGreaterEqual(summary.pop('time_seconds'), 0)
                        outputs.append((output.read_bytes(), document))
                    self.assertEqual(outputs[0], outputs[1])


if __name__ == '__main__':
    unittest.main()
