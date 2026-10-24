"""Scientific interpretation of pulse outputs, separate from numerical results."""

import csv
from dataclasses import asdict
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from run_experiment import Config, main, run_mode, scientific_context


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_FIELDS = {'scientific_status', 'published_result_reproduction',
                  'uncertainty_scope', 'approximation_notes'}


class TestPulseScientificContext(unittest.TestCase):
    def cli(self, directory, name, *arguments):
        output = Path(directory) / f'{name}.csv'
        result = subprocess.run([
            sys.executable, str(ROOT / 'run_experiment.py'), '--N', '80',
            '--gens', '3', '--reps', '2', '--f', '.5', '--seed', '17',
            '--output', str(output), *arguments,
        ], cwd=directory, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return self.read_outputs(output)

    def read_outputs(self, output):
        with output.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        return rows, json.loads(output.with_suffix('.json').read_text())

    def assert_context(self, context, *, active, selected, drawn):
        self.assertEqual(context['scientific_status'], 'exploratory_simulation')
        self.assertEqual(context['published_result_reproduction'], 'not_demonstrated')
        self.assertEqual(context['uncertainty_scope'], 'monte_carlo_only')
        notes = context['approximation_notes']
        for key in ('published_comparison', 'population_size', 'demography',
                    'autosomal_proxy', 'sampling', 'mt_selection'):
            self.assertIsInstance(notes[key], str)
            self.assertTrue(notes[key].strip())
        self.assertIn('Ne', notes['population_size'])
        self.assertIn('sans expansion', notes['demography'])
        self.assertIn('discrétisation', notes['autosomal_proxy'])
        self.assertEqual('epistasis' in notes, active)
        self.assertEqual('y_selection' in notes, selected)
        if drawn:
            self.assertIn('n’est pas authentifiée', notes['mt_selection'])
            self.assertIn('tiré par réplicat', notes['mt_selection'])
        else:
            self.assertIn('sans intégration', notes['mt_selection'])

    def row_context(self, row):
        return {**{key: row[key] for key in CONTEXT_FIELDS if key != 'approximation_notes'},
                'approximation_notes': json.loads(row['approximation_notes'])}

    def test_cli_context_in_all_modes_and_reference_scenarios(self):
        with tempfile.TemporaryDirectory() as directory:
            for mode in ('full', 'quick', 'adaptive'):
                for scenario in ('neutral', 'reich_point', 'reich_plus_symmetric_1pct'):
                    with self.subTest(mode=mode, scenario=scenario):
                        rows, document = self.cli(directory, mode+scenario,
                                                  '--mode', mode, '--scenario', scenario)
                        summary = document['summary'][0]
                        active = scenario == 'reich_plus_symmetric_1pct'
                        selected = scenario != 'neutral'
                        self.assert_context(summary['scientific_context'], active=active,
                                            selected=selected, drawn=False)
                        for row in rows:
                            context = self.row_context(row)
                            self.assertEqual(context, summary['scientific_context'])
                            self.assertEqual('neutral_control' in context['approximation_notes'],
                                             scenario == 'neutral')
                            stored = json.loads(row['config_realized'])
                            cfg = Config(**stored)
                            for key, value in run_mode(cfg, mode).items():
                                self.assertEqual(row[key], str(value), key)
                            self.assertEqual(asdict(cfg), stored)

    def test_overrides_determine_epistasis_instead_of_scenario_name(self):
        with tempfile.TemporaryDirectory() as directory:
            cases = [
                ('neutral', ['--y-arch-nuc-mod', '.01'], True),
                ('symmetric_1pct', ['--mt-mod-nuc-arch', '0', '--mt-arch-nuc-mod', '0',
                                    '--y-mod-nuc-arch', '0', '--y-arch-nuc-mod', '0'], False),
            ]
            for scenario, overrides, active in cases:
                with self.subTest(scenario=scenario):
                    rows, document = self.cli(directory, scenario, '--mode', 'full',
                                              '--scenario', scenario, *overrides)
                    context = document['summary'][0]['scientific_context']
                    self.assert_context(context, active=active, selected=False, drawn=False)
                    self.assertEqual('neutral_control' in context['approximation_notes'], not active)
                    for row in rows:
                        self.assertEqual(self.row_context(row), context)

    def test_posterior_is_not_implicitly_authenticated(self):
        with tempfile.TemporaryDirectory() as directory:
            posterior = Path(directory) / 'synthetic.txt'
            posterior.write_text('0.001\n0.003\n0.004\n')
            for scenario in ('neutral', 'reich_point'):
                rows, document = self.cli(directory, scenario, '--mode', 'full',
                                          '--scenario', scenario, '--mt-posterior', str(posterior))
                drawn = scenario == 'reich_point'
                context = document['summary'][0]['scientific_context']
                self.assert_context(context, active=False, selected=drawn, drawn=drawn)
                for row in rows:
                    self.assertEqual(self.row_context(row), context)
                    self.assertEqual(row['mt_selection_source'],
                                     'posterior_draw' if drawn else 'posterior_not_applied')

    def test_context_is_descriptive_and_does_not_change_results(self):
        cfg = Config(y_mod_nuc_arch=.01, seed=42)
        before = asdict(cfg)
        scientific_context(cfg, 'fixed')
        self.assertEqual(asdict(cfg), before)
        with tempfile.TemporaryDirectory() as directory:
            results = []
            for enabled in (False, True):
                output = Path(directory) / f'{enabled}.csv'
                argv = ['run_experiment.py', '--scenario', 'all', '--mode', 'full',
                        '--N', '80', '--gens', '3', '--f', '.5', '--reps', '2',
                        '--seed', '17', '--output', str(output)]
                # Compare actual reporting with an inert context provider; the
                # simulation and aggregation are executed in both cases.
                provider = scientific_context if enabled else lambda *args: {
                    'scientific_status': '', 'published_result_reproduction': '',
                    'uncertainty_scope': '', 'approximation_notes': {}}
                with patch.object(sys, 'argv', argv), patch('run_experiment.scientific_context', provider), \
                        patch('sys.stdout', new_callable=io.StringIO):
                    main()
                rows, document = self.read_outputs(output)
                for row in rows:
                    for key in CONTEXT_FIELDS:
                        row.pop(key)
                document['meta'].pop('output')
                for summary in document['summary']:
                    summary.pop('scientific_context')
                    summary.pop('time_seconds')
                results.append((rows, document))
            self.assertEqual(results[0], results[1])


if __name__ == '__main__':
    unittest.main()
