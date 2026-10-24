"""Replay and chronology of the versioned pulse CSV result metadata."""

import bz2
import csv
from dataclasses import asdict
import hashlib
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from run_experiment import Config, MODEL, RESULT_SCHEMA_VERSION, SCENARIOS, run_mode
from science_contract import load_contract


ROOT = Path(__file__).resolve().parents[1]


class TestPulseMetadata(unittest.TestCase):
    def cli(self, directory, name, *arguments):
        output = Path(directory) / f'{name}.csv'
        result = subprocess.run([
            sys.executable, str(ROOT / 'run_experiment.py'), '--N', '80',
            '--reps', '2', '--seed', '17', '--output', str(output), *arguments,
        ], cwd=directory, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with output.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        return rows, json.loads(output.with_suffix('.json').read_text())

    def assert_chronology(self, row, meta, horizon):
        contract = load_contract()
        parameters = {entry['id']: entry['value'] for entry in contract['reference_parameters']}
        mixture = parameters['mixture_generations_ago']
        years = parameters['years_per_generation']
        expected = dict(result_schema_version=RESULT_SCHEMA_VERSION, model=MODEL,
                        science_contract_version=contract['contract_version'],
                        target_generation=horizon, mixture_generations_ago=mixture,
                        years_per_generation=years, target_generations_ago=mixture-horizon,
                        target_age_ka=(mixture-horizon)*years/1000)
        for key, value in expected.items():
            self.assertEqual(row[key], str(value), key)
            self.assertEqual(meta[key], value, key)
        self.assertEqual(int(row['gens_requested']), horizon)
        self.assertIn(f'generation {horizon} after pulse', meta['definition'])
        self.assertNotIn('50 ka', meta['definition'])

    def assert_replay(self, row):
        stored = json.loads(row['config_realized'])
        config = Config(**stored)
        self.assertEqual(stored, asdict(config))
        self.assertEqual(set(stored), set(asdict(Config())))
        self.assertEqual(config.seed, int(row['seed']))
        self.assertEqual(config.s_mt, float(row['s_mt_realized']))
        replayed = run_mode(config, row['mode'])
        for key, value in replayed.items():
            self.assertEqual(row[key], str(value), key)

    def test_cli_replay_all_modes_with_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            for mode in ('full', 'quick', 'adaptive'):
                with self.subTest(mode=mode):
                    rows, document = self.cli(
                        directory, mode, '--scenario', 'reich_point', '--mode', mode,
                        '--gens', '3', '--f', '.5', '--male-frac', '.6',
                        '--mt-arch-nuc-mod', '.003', '--y-mod-nuc-arch', '.002')
                    self.assertEqual(len(rows), 2)
                    for index, row in enumerate(rows):
                        self.assert_chronology(row, document['meta'], 3)
                        expected = Config(N=80, gens=3, f=.5, male_frac=.6, seed=17+index,
                                          stop_when_absorbed=mode != 'full',
                                          mt_arch_nuc_mod=.003, y_mod_nuc_arch=.002,
                                          **SCENARIOS['reich_point'])
                        self.assertEqual(json.loads(row['config_realized']), asdict(expected))
                        self.assertEqual(row['mt_selection_source'], 'fixed')
                        self.assertEqual(row['mt_posterior_sha256'], '')
                        self.assertEqual(row['mt_posterior_draw_seed'], '')
                        self.assert_replay(row)

    def test_cli_default_horizon_has_model_age_near_50ka(self):
        with tempfile.TemporaryDirectory() as directory:
            # Absorbed markers keep this default-horizon metadata check inexpensive.
            rows, document = self.cli(directory, 'default', '--scenario', 'neutral',
                                      '--mode', 'quick', '--f', '0')
            for row in rows:
                self.assert_chronology(row, document['meta'], 6993)
                self.assertAlmostEqual(float(row['target_age_ka']), 49.9928)
                self.assertEqual(row['auto_generations_completed'], '')
                self.assertLess(int(row['generations_completed']), 6993)
                self.assert_replay(row)

    def test_posterior_provenance_and_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            for shape in ('single_column', 'two_columns', 'gzip', 'bzip2'):
                # Synthetic test values, not the supplied SI1 distribution.
                content = (b'# synthetic posterior fixture\n0.001\n0.002\n0.004\n'
                           if shape == 'single_column' else
                           b'# synthetic posterior fixture\n0.001 1\n0.002 2\n0.004 3\n')
                suffix = '.txt'
                if shape == 'gzip':
                    content = gzip.compress(content, mtime=0)
                    suffix = '.txt.gz'
                elif shape == 'bzip2':
                    content = bz2.compress(content)
                    suffix = '.txt.bz2'
                posterior = Path(directory) / f'{shape}{suffix}'
                posterior.write_bytes(content)
                for scenario in ('reich_point', 'neutral'):
                    with self.subTest(shape=shape, scenario=scenario):
                        rows, _ = self.cli(
                            directory, shape+scenario, '--scenario', scenario, '--mode', 'full',
                            '--gens', '3', '--mt-posterior', str(posterior), '--f', '.5')
                        for index, row in enumerate(rows):
                            self.assertEqual(row['mt_posterior_sha256'], hashlib.sha256(content).hexdigest())
                            if scenario == 'neutral':
                                self.assertEqual(row['mt_selection_source'], 'posterior_not_applied')
                                self.assertEqual(row['mt_posterior_draw_seed'], '')
                                self.assertEqual(float(row['s_mt_realized']), 0.)
                            else:
                                draw_seed = 17+index+27383
                                expected = float(np.random.default_rng(draw_seed).choice([.001, .002, .004]))
                                self.assertEqual(row['mt_selection_source'], 'posterior_draw')
                                self.assertEqual(int(row['mt_posterior_draw_seed']), draw_seed)
                                self.assertEqual(float(row['s_mt_realized']), expected)
                            self.assert_replay(row)

    def test_final_measurement_generation_is_not_first_pass(self):
        for mode in ('quick', 'adaptive', 'full'):
            for frequency in (0., 1.):
                with self.subTest(mode=mode, f=frequency):
                    config = Config(N=80, gens=80, f=frequency, seed=17)
                    result = run_mode(config, mode)
                    if mode != 'full':
                        self.assertLess(result['generations_completed'], config.gens)
                    if mode == 'full' or (mode == 'adaptive' and frequency == 1.):
                        self.assertEqual(result['auto_generations_completed'], config.gens)
                    else:
                        self.assertEqual(result['auto_generations_completed'], '')
        # Inspect the serialization of the continuation generation as well.
        with tempfile.TemporaryDirectory() as directory:
            rows, _ = self.cli(directory, 'continued', '--scenario', 'reich_point',
                               '--mode', 'adaptive', '--f', '1', '--gens', '80')
            for row in rows:
                self.assertEqual(row['auto_generations_completed'], '80')
                self.assertLess(int(row['generations_completed']), 80)
                self.assert_replay(row)


if __name__ == '__main__':
    unittest.main()
