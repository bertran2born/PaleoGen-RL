"""Evaluation policies: real seeded markers and controlled autosomal branches."""

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

from run_experiment import Config, SCENARIOS, main, run_mode


ROOT = Path(__file__).resolve().parents[1]


def raw_result(probability, ancestry=0.05, generation=11):
    return dict(p10_joint=probability, auto_mod=ancestry,
                target_auto=0.03 <= ancestry <= 0.07,
                generations_completed=generation, mt_mod=probability,
                termination_reason='horizon_reached' if generation == 80 else 'markers_absorbed',
                Y_mod=probability, joint_fixed=probability == 1)


class TestPulseModes(unittest.TestCase):
    def test_real_seeded_mode_matrix(self):
        # Long cases exercise absorption; short f=.5 cases retain polymorphism.
        positive_without_fixation = False
        absorbed = set()
        for scenario in ('neutral', 'reich_point', 'reich_plus_symmetric_1pct'):
            for seed in (0, 17, 42):
                for frequency, horizon in ((0., 80), (.05, 80), (1., 80), (.5, 1)):
                    with self.subTest(scenario=scenario, seed=seed, f=frequency, gens=horizon):
                        cfg = Config(N=80, gens=horizon, seed=seed, f=frequency,
                                     **SCENARIOS[scenario])
                        before = asdict(cfg)
                        full = run_mode(cfg, 'full')
                        adaptive = run_mode(cfg, 'adaptive')
                        quick = run_mode(cfg, 'quick')
                        self.assertEqual(asdict(cfg), before)
                        self.assertEqual(full['generations_completed'], horizon)
                        for key in ('p10_joint', 'mt_mod', 'Y_mod', 'joint_fixed'):
                            self.assertEqual(adaptive[key], full[key], key)
                            self.assertEqual(quick[key], full[key], key)
                        self.assertEqual(set(full), set(adaptive))
                        self.assertEqual(set(full), set(quick))
                        self.assertEqual(quick['target_auto'], '')
                        self.assertEqual(quick['joint_and_target'], '')
                        self.assertEqual(quick['auto_evaluation_status'], 'not_evaluated_quick')
                        self.assertEqual(full['auto_mod_at_50ka'], full['auto_mod'])
                        if adaptive['p10_joint'] == 0:
                            self.assertEqual(adaptive['target_auto'], '')
                            self.assertEqual(adaptive['joint_and_target'], 0.)
                        else:
                            self.assertEqual(adaptive['auto_evaluation_status'], 'evaluated_at_target')
                            self.assertEqual(adaptive['joint_and_target'],
                                             adaptive['p10_joint'] * int(adaptive['target_auto']))
                            if horizon == 1:
                                self.assertEqual(adaptive['auto_mod_at_50ka'], full['auto_mod'])
                            positive_without_fixation |= not adaptive['joint_fixed']
                        if frequency in (0., 1.):
                            self.assertLess(quick['generations_completed'], horizon)
                            absorbed.add(frequency)
        self.assertTrue(positive_without_fixation)
        self.assertEqual(absorbed, {0., 1.})

    def test_controlled_early_ancestry_and_continuation(self):
        cfg = Config(seed=42, gens=80)
        for mode in ('quick', 'adaptive'):
            with self.subTest(mode=mode), patch('run_experiment.run', return_value=raw_result(0.)) as engine:
                result = run_mode(cfg, mode)
                self.assertEqual(result['auto_mod'], .05)
                self.assertEqual(result['target_auto'], '')
                self.assertEqual(result['joint_and_target'], '' if mode == 'quick' else 0.)
                engine.assert_called_once()
        # The final filter must replace an apparently successful early diagnostic.
        with patch('run_experiment.run', side_effect=[raw_result(.25), raw_result(.25, .2, 80)]) as engine:
            result = run_mode(cfg, 'adaptive')
            self.assertEqual(result['auto_mod'], .05)
            self.assertEqual(result['auto_mod_at_50ka'], .2)
            self.assertFalse(result['target_auto'])
            self.assertEqual(result['joint_and_target'], 0.)
            first, second = engine.call_args_list
            self.assertEqual(asdict(first.args[0]), {**asdict(cfg), 'stop_when_absorbed': True})
            self.assertEqual(asdict(second.args[0]), {**asdict(cfg), 'stop_when_absorbed': False})
            self.assertEqual(second.kwargs, {'accelerate_after_absorption': True})
        with patch('run_experiment.run', side_effect=[raw_result(.25), raw_result(.5, generation=80)]):
            with self.assertRaisesRegex(RuntimeError, 'marker results changed'):
                run_mode(cfg, 'adaptive')

    def test_mixed_adaptive_csv_in_both_orders(self):
        with tempfile.TemporaryDirectory() as directory:
            for first_positive in (False, True):
                output = Path(directory) / f'{first_positive}.csv'
                positive = [raw_result(.25), raw_result(.25, .06, 80)]
                impossible = [raw_result(0.)]
                results = positive + impossible if first_positive else impossible + positive
                argv = ['run_experiment.py', '--scenario', 'neutral', '--mode', 'adaptive',
                        '--reps', '2', '--gens', '80', '--output', str(output)]
                with patch.object(sys, 'argv', argv), patch('run_experiment.run', side_effect=results), \
                        patch('sys.stdout', new_callable=io.StringIO):
                    main()
                with output.open(newline='') as stream:
                    rows = list(csv.DictReader(stream))
                self.assertEqual(len(rows), 2)
                by_probability = {float(row['p10_joint']): row for row in rows}
                self.assertEqual(by_probability[0.]['target_auto'], '')
                self.assertEqual(by_probability[0.]['joint_and_target'], '0.0')
                self.assertEqual(by_probability[.25]['auto_mod_at_50ka'], '0.06')
                self.assertEqual(by_probability[.25]['joint_and_target'], '0.25')
                summary = json.loads(output.with_suffix('.json').read_text())['summary'][0]
                self.assertEqual(summary['P_joint_and_auto'], .125)
                self.assertNotIn('P_autosomal_range', summary)

    def test_cli_mode_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            for mode in ('quick', 'adaptive', 'full'):
                for frequency in (0., 1.):
                    with self.subTest(mode=mode, f=frequency):
                        output = Path(directory) / f'{mode}-{frequency}.csv'
                        completed = subprocess.run([
                            sys.executable, str(ROOT / 'run_experiment.py'), '--scenario', 'neutral',
                            '--mode', mode, '--reps', '2', '--N', '80', '--gens', '80',
                            '--f', str(frequency), '--seed', '0', '--output', str(output),
                        ], cwd=directory, capture_output=True, text=True)
                        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                        with output.open(newline='') as stream:
                            rows = list(csv.DictReader(stream))
                        summary = json.loads(output.with_suffix('.json').read_text())['summary'][0]
                        self.assertEqual(len(rows), 2)
                        for row in rows:
                            self.assertEqual(float(row['p10_joint']), frequency)
                            if mode == 'quick':
                                self.assertEqual(row['auto_evaluation_status'], 'not_evaluated_quick')
                                self.assertEqual(row['auto_mod_at_50ka'], 'NOT_EVALUATED_QUICK')
                                self.assertEqual(row['target_auto'], '')
                                self.assertEqual(row['joint_and_target'], '')
                            elif mode == 'adaptive' and frequency == 0:
                                self.assertEqual(row['auto_evaluation_status'], 'not_evaluated_event_impossible')
                                self.assertEqual(row['auto_mod_at_50ka'], 'NOT_EVALUATED_EVENT_IMPOSSIBLE')
                                self.assertEqual(row['target_auto'], '')
                                self.assertEqual(float(row['joint_and_target']), 0.)
                            else:
                                self.assertEqual(row['auto_evaluation_status'], 'evaluated_at_target')
                                self.assertEqual(float(row['auto_mod_at_50ka']), frequency)
                                self.assertEqual(row['target_auto'], 'False')
                        self.assertEqual('P_autosomal_range' in summary, mode == 'full')
                        self.assertEqual('P_joint_and_auto' in summary, mode != 'quick')
                        if mode != 'quick':
                            self.assertEqual(summary['P_joint_and_auto'], 0.)


if __name__ == '__main__':
    unittest.main()
