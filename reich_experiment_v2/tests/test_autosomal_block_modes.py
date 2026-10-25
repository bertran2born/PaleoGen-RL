"""I17 mode references fixed in the protocol before their first execution."""

from copy import deepcopy
import csv
from dataclasses import replace
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from run_experiment import Config, SCENARIOS, run_block_full, run_block_mode
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.pulse import (
    MODE_RESULT_SCHEMA_VERSION, evaluate_block_pulse, initialise_pulse,
)
from paleogen_rl.genetics.selected import BlockSelection, ReproductionFailure, run_selected


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SEEDS = (0, 17, 42)
REFERENCE_SCENARIOS = ('neutral', 'reich_point', 'symmetric_1pct', 'reich_plus_favor_arch_1pct')
DOMINANCES = ('additive', 'dominant', 'recessive')


def mapping(switch=.1):
    return RecombinationMap(BlockPanel('synthetic-four', ('a', 'b', 'c', 'd')), (switch,)*3)


def arguments(**overrides):
    return {**dict(population_size=40, f=1., male_fraction=.5, generations=40, seed=17,
                    recombination_map=mapping(), selection=BlockSelection()), **overrides}


class TestAutosomalBlockModes(unittest.TestCase):
    def test_preregistered_reference_matrix_matches_full(self):
        count = 0
        for scenario, dominance, switch, seed, f in product(
                REFERENCE_SCENARIOS, DOMINANCES, (0., .1), REFERENCE_SEEDS, (0., .5, 1.)):
            cfg = Config(N=40, gens=40, f=f, seed=seed, mismatch_dominance=dominance,
                         stop_when_absorbed=False, **SCENARIOS[scenario])
            with self.subTest(scenario=scenario, dominance=dominance, switch=switch, seed=seed, f=f):
                full = run_block_full(cfg, mapping(switch), 'a', 'c')
                quick = run_block_mode(cfg, 'quick', mapping(switch), 'a', 'c')
                adaptive = run_block_mode(cfg, 'adaptive', mapping(switch), 'a', 'c')
                for field in ('p10_joint', 'mt_mod', 'Y_mod', 'joint_fixed', 'both_modern_men', 'male_n'):
                    self.assertEqual(quick[field], full[field], field)
                    self.assertEqual(adaptive[field], full[field], field)
                self.assertEqual(adaptive['joint_and_target'], full['joint_and_target'])
                self.assertIsNone(quick['auto_mod_at_50ka'])
                self.assertIsNone(quick['target_auto'])
                self.assertIsNone(quick['joint_and_target'])
                report = json.loads(quick['block_report'])
                measurement = report['ancestry_measurement']
                self.assertIsNone(measurement['value'])
                self.assertIsNone(measurement['modern_allele_copies'])
                self.assertIsNone(measurement['partner_diagnostics'])
                self.assertEqual(measurement['allele_copy_denominator'], 320)
                if full['p10_joint'] > 0:
                    self.assertEqual(adaptive['auto_mod_at_50ka'], full['auto_mod'])
                    self.assertEqual(adaptive['auto_generations_completed'], 40)
                else:
                    self.assertIsNone(adaptive['auto_mod_at_50ka'])
                    self.assertIsNone(adaptive['target_auto'])
                    self.assertEqual(adaptive['auto_evaluation_status'], 'not_evaluated_event_impossible')
            count += 1
        self.assertEqual(count, 216)

    def test_quick_states_equal_full_prefix_without_rng_or_selection_change(self):
        for f, seed, switch in product((0., .5, 1.), REFERENCE_SEEDS, (0., .1)):
            state, _ = initialise_pulse(population_size=40, f=f, male_fraction=.5, panel=mapping(switch).panel)
            selection = BlockSelection(mt_mod_nuc_arch=.1, y_arch_nuc_mod=.1,
                                       mt_partner_block='a', y_partner_block='c')
            quick = run_selected(**state, recombination_map=mapping(switch), selection=selection,
                                 generations=40, seed=seed, stop_when_absorbed=True)
            completed = quick.report['generations_completed']
            prefix = run_selected(**state, recombination_map=mapping(switch), selection=selection,
                                  generations=completed, seed=seed)
            for field in ('haplotypes', 'sex', 'mt', 'y'):
                np.testing.assert_array_equal(getattr(quick, field), getattr(prefix, field))
            self.assertEqual(quick.report['work_units'], prefix.report['work_units'])
            if f in (0., 1.):
                self.assertEqual(completed, 1)
                self.assertEqual(quick.report['termination_reason'], 'markers_absorbed')

    def test_synthetic_positive_joint_event_keeps_five_percent_and_all_selection(self):
        panel = BlockPanel('synthetic-fixed-five-percent', tuple(f'b{i}' for i in range(20)))
        haps = np.zeros((40, 2, 20), dtype=np.uint8)
        haps[:, :, 0] = 1
        sex = np.array([1]*20+[0]*20, dtype=np.uint8)
        state = dict(haplotypes=haps, sex=sex, mt=np.ones(40, dtype=np.uint8),
                     y=np.array([1]*20+[-1]*20, dtype=np.int8))
        for seed, switch, coefficient in product(REFERENCE_SEEDS, (0., .1), (0., .1)):
            declaration = RecombinationMap(panel, (switch,)*19)
            selection = BlockSelection(mt_mod_nuc_arch=coefficient, mt_partner_block='b1')
            kwargs = arguments(seed=seed, recombination_map=declaration, selection=selection)
            with patch('paleogen_rl.genetics.pulse.initialise_pulse',
                       return_value=(state, dict(scientific_status='synthetic_test_fixture'))):
                full = evaluate_block_pulse(**kwargs)
                quick = evaluate_block_pulse(**kwargs, mode='quick')
                adaptive = evaluate_block_pulse(**kwargs, mode='adaptive')
            self.assertEqual(full['target']['joint_and_target'], 1.)
            self.assertEqual(adaptive['target']['joint_and_target'], 1.)
            self.assertIsNone(quick['target']['joint_and_target'])
            self.assertEqual(adaptive['ancestry_measurement']['value'], .05)
            self.assertEqual(adaptive['engine_report'], full['engine_report'])
            self.assertEqual(adaptive['screening_report']['generations_completed'], 1)
            work = adaptive['work_units']
            screen_work = adaptive['screening_report']['work_units']
            full_work = full['engine_report']['work_units']
            for field in ('candidates_generated', 'accepted_candidates', 'offspring_generated', 'block_copy_transmissions'):
                self.assertEqual(work[field], screen_work[field]+full_work[field])
            self.assertEqual(work['state_allele_entries'], 1600)
            self.assertEqual(work['offspring_generated'], 41*40)
            if coefficient:
                self.assertGreater(full_work['candidates_generated'], 40*40)

    def test_quick_at_horizon_and_zero_horizon_never_expose_final_values(self):
        for generations in (0, 1, 3):
            report = evaluate_block_pulse(**arguments(f=.5, generations=generations), mode='quick')
            self.assertEqual(report['ancestry_measurement']['status'], 'not_evaluated_quick')
            self.assertIsNone(report['ancestry_measurement']['value'])
            self.assertIsNone(report['target']['target_auto'])
            self.assertIsNone(report['target']['joint_and_target'])
            self.assertLessEqual(report['sampling']['generation'], generations)
        zero = evaluate_block_pulse(**arguments(f=0.), mode='adaptive')
        self.assertEqual(zero['continuation_status'], 'skipped_event_impossible')
        self.assertEqual(zero['work_units'], zero['screening_report']['work_units'])
        self.assertIsNone(zero['ancestry_measurement']['value'])

    def test_screening_and_continuation_errors_are_not_converted_to_success(self):
        kwargs = arguments()
        state, _ = initialise_pulse(population_size=40, f=1., male_fraction=.5, panel=mapping().panel)
        def screen():
            return run_selected(**state, recombination_map=mapping(), selection=BlockSelection(),
                                generations=40, seed=17, stop_when_absorbed=True)
        bad_screen = screen()
        bad_screen.report['termination_reason'] = 'horizon_reached'
        with patch('paleogen_rl.genetics.pulse.run_selected', return_value=bad_screen):
            with self.assertRaisesRegex(RuntimeError, 'incomplete block screening'):
                evaluate_block_pulse(**kwargs, mode='adaptive')
        bad_measurement = screen()
        bad_measurement.report['final_measurement']['value'] = 1.
        with patch('paleogen_rl.genetics.pulse.run_selected', return_value=bad_measurement):
            with self.assertRaisesRegex(RuntimeError, 'invalid quick block measurement'):
                evaluate_block_pulse(**kwargs, mode='quick')
        short = run_selected(**state, recombination_map=mapping(), selection=BlockSelection(), generations=1, seed=17)
        with patch('paleogen_rl.genetics.pulse.run_selected', side_effect=[screen(), short]):
            with self.assertRaisesRegex(RuntimeError, 'incomplete block horizon'):
                evaluate_block_pulse(**kwargs, mode='adaptive')
        changed = run_selected(**state, recombination_map=mapping(), selection=BlockSelection(), generations=40, seed=17)
        changed.mt[0] = 0
        with patch('paleogen_rl.genetics.pulse.run_selected', side_effect=[screen(), changed]):
            with self.assertRaisesRegex(RuntimeError, 'marker results changed'):
                evaluate_block_pulse(**kwargs, mode='adaptive')
        first = screen()
        failure = deepcopy(first.report)
        failure.update(termination_reason='reproduction_failed', final_measurement=None,
                       failed_generation=1, generations_completed=0)
        failure['work_units'].update(offspring_generated=0, accepted_candidates=0)
        failed_work = dict(failure['work_units'])
        with patch('paleogen_rl.genetics.pulse.run_selected', side_effect=[first, ReproductionFailure(failure)]):
            with self.assertRaises(ReproductionFailure) as error:
                evaluate_block_pulse(**kwargs, mode='adaptive')
        self.assertIsNone(error.exception.report['final_measurement'])
        self.assertEqual(error.exception.report['screening_report'], first.report)
        self.assertEqual(error.exception.report['work_units'], failed_work)
        self.assertEqual(error.exception.report['total_work_units']['candidates_generated'],
                         failed_work['candidates_generated']+first.report['work_units']['candidates_generated'])

    def test_invalid_mode_and_stop_flag_fail_before_rng(self):
        with patch('paleogen_rl.genetics.pulse.run_selected') as simulate:
            with self.assertRaises(ValueError):
                evaluate_block_pulse(**arguments(), mode='unknown')
            simulate.assert_not_called()
        state, _ = initialise_pulse(population_size=40, f=.5, male_fraction=.5, panel=mapping().panel)
        with patch('paleogen_rl.genetics.selected.np.random.default_rng') as generator:
            with self.assertRaises(ValueError):
                run_selected(**state, recombination_map=mapping(), selection=BlockSelection(),
                             generations=40, seed=17, stop_when_absorbed=1)
            generator.assert_not_called()

    def cli(self, directory, name, mode, *extra):
        mapfile = Path(directory)/'map.json'
        mapfile.write_text(json.dumps(dict(panel=dict(panel_id='synthetic-four', block_ids=['a', 'b', 'c', 'd']),
                                          switch_probabilities=[.1]*3)))
        output = Path(directory)/f'{name}.csv'
        process = subprocess.run([sys.executable, str(ROOT/'run_experiment.py'), '--scenario', 'all',
            '--mode', mode, '--N', '40', '--f', '.5', '--gens', '3', '--seed', '17', '--reps', '2',
            '--block-map', str(mapfile), '--mt-partner-block', 'a', '--y-partner-block', 'c',
            '--output', str(output), *extra], cwd=directory, capture_output=True, text=True)
        return process, output

    def read(self, output):
        with output.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        def nonfinite(value):
            raise ValueError(value)
        return rows, json.loads(output.with_suffix('.json').read_text(), parse_constant=nonfinite)

    def test_cli_all_scenarios_replay_repeatability_and_costs(self):
        with tempfile.TemporaryDirectory() as directory:
            for mode in ('quick', 'adaptive'):
                executions = []
                for repetition in (0, 1):
                    process, output = self.cli(directory, f'{mode}-{repetition}', mode)
                    self.assertEqual(process.returncode, 0, process.stdout+process.stderr)
                    rows, document = self.read(output)
                    self.assertEqual(len(rows), 2*len(SCENARIOS))
                    self.assertEqual(document['meta']['result_schema_version'], MODE_RESULT_SCHEMA_VERSION)
                    for row in rows:
                        self.assertEqual(row['result_schema_version'], MODE_RESULT_SCHEMA_VERSION)
                        replayed = run_block_mode(Config(**json.loads(row['config_realized'])), mode, mapping(), 'a', 'c')
                        for field, value in replayed.items():
                            self.assertEqual(row[field], '' if value is None else str(value), field)
                    for summary in document['summary']:
                        self.assertNotIn('P_autosomal_range', summary)
                        if mode == 'quick':
                            self.assertNotIn('P_joint_and_auto', summary)
                        work = [json.loads(row['block_report'])['work_units'] for row in rows
                                if row['scenario'] == summary['name']]
                        for field in ('candidates_generated', 'accepted_candidates', 'offspring_generated', 'block_copy_transmissions'):
                            self.assertEqual(summary['block_work_units'][field], sum(w[field] for w in work))
                        summary.pop('time_seconds')
                    document['meta'].pop('output')
                    executions.append((rows, document))
                self.assertEqual(executions[0], executions[1])

    def test_cli_absorption_distinguishes_marker_and_ancestry_generations(self):
        with tempfile.TemporaryDirectory() as directory:
            for mode, f in product(('quick', 'adaptive'), ('0', '1')):
                process, output = self.cli(directory, f'{mode}-{f}', mode, '--scenario', 'neutral',
                                            '--f', f, '--gens', '40', '--reps', '1')
                self.assertEqual(process.returncode, 0, process.stdout+process.stderr)
                rows, document = self.read(output)
                row = rows[0]
                self.assertEqual(row['marker_generations_completed'], '1')
                self.assertEqual(row['marker_evaluation_status'], 'absorbed_before_target')
                if mode == 'adaptive' and f == '1':
                    self.assertEqual(row['auto_generations_completed'], '40')
                    self.assertEqual(row['auto_mod_at_50ka'], '1.0')
                else:
                    self.assertEqual(row['auto_generations_completed'], '')
                    self.assertEqual(row['auto_mod_at_50ka'], '')
                    self.assertEqual(row['target_auto'], '')
                self.assertEqual(row['joint_and_target'], '' if mode == 'quick' else '0.0')
                self.assertIsNone(document['summary'][0]['p10_joint_95pct_bootstrap'])
                if mode == 'quick':
                    self.assertNotIn('joint_and_auto_95pct_bootstrap', document['summary'][0])

    def test_cli_real_reproductive_failures_emit_no_success_files(self):
        with tempfile.TemporaryDirectory() as directory:
            posterior = Path(directory)/'synthetic-lethal.txt'
            posterior.write_text('1\n1\n')
            for mode in ('quick', 'adaptive'):
                process, output = self.cli(directory, mode, mode, '--scenario', 'reich_point',
                    '--f', '0', '--mt-posterior', str(posterior))
                self.assertEqual(process.returncode, 1, process.stdout+process.stderr)
                self.assertIn('reproduction_failed', process.stderr)
                self.assertNotIn('Traceback', process.stderr)
                self.assertFalse(output.exists())
                self.assertFalse(output.with_suffix('.json').exists())


if __name__ == '__main__':
    unittest.main()
