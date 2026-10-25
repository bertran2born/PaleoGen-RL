"""Full CLI block pulse: initialisation, exact observations, replay and failures."""

from contextlib import redirect_stderr
from dataclasses import replace
import csv
import hashlib
import io
import json
from math import comb
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from run_experiment import Config, SCENARIOS, main, run_block_full
import reich_panmictic_original as original
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap, copy_counts
from paleogen_rl.genetics.pulse import (
    MODEL, RESULT_SCHEMA_VERSION, evaluate_block_pulse, initialise_pulse, load_block_map,
)
from paleogen_rl.genetics.selected import BlockSelection, run_selected


ROOT = Path(__file__).resolve().parents[1]
MAP = dict(panel=dict(panel_id='synthetic-four', block_ids=['a', 'b', 'c', 'd']),
           switch_probabilities=[.1, .1, .1])


def mapping():
    return RecombinationMap(BlockPanel(**MAP['panel']), MAP['switch_probabilities'])


class TestAutosomalPulse(unittest.TestCase):
    def test_initialisation_matches_m2_rounding_sex_bias_and_quota_errors(self):
        for size in (5, 40, 81):
            for f in (0., .05, .5, 1.):
                for male_fraction in (0., .5, 1.):
                    with self.subTest(N=size, f=f, male_fraction=male_fraction):
                        cfg = Config(N=size, f=f, male_frac=male_fraction)
                        rng = np.random.default_rng(17)
                        try:
                            reference = original._init(cfg, rng)
                        except ValueError:
                            with self.assertRaises(ValueError):
                                initialise_pulse(population_size=size, f=f,
                                                 male_fraction=male_fraction, panel=mapping().panel)
                            continue
                        state, declaration = initialise_pulse(population_size=size, f=f,
                                                               male_fraction=male_fraction, panel=mapping().panel)
                        for field, legacy in (('sex', 'sex'), ('mt', 'mt'), ('y', 'Y')):
                            np.testing.assert_array_equal(state[field], reference[legacy])
                        np.testing.assert_array_equal(copy_counts(state['haplotypes']), reference['auto'][:, :4])
                        np.testing.assert_array_equal(state['haplotypes'][:, 0], state['haplotypes'][:, 1])
                        self.assertEqual(declaration['modern_males'], int(reference['mt'][:size//2].sum()))
                        self.assertEqual(declaration['modern_females'], int(reference['mt'][size//2:].sum()))
                        self.assertEqual(declaration['realised_ancestry'], float(reference['mt'].mean()))

    def test_exact_ten_male_probability_and_inclusive_ancestry_target(self):
        panel = BlockPanel('synthetic-one', ('a',))
        declaration = RecombinationMap(panel, ())
        for size, copies in ((24, 2), (100, 5), (100, 6), (100, 14), (100, 15)):
            for both in range(13):
                haps = np.zeros((size, 2, 1), dtype=np.uint8)
                haps.reshape(-1)[:copies] = 1
                sex = np.array([1]*(size//2)+[0]*(size-size//2), dtype=np.uint8)
                mt = np.ones(size, dtype=np.uint8)
                y = np.where(sex == 1, 0, -1).astype(np.int8)
                y[:both] = 1
                final = run_selected(haps, sex, mt, y, recombination_map=declaration,
                                     selection=BlockSelection(), generations=0, seed=17)
                with patch('paleogen_rl.genetics.pulse.run_selected', return_value=final):
                    report = evaluate_block_pulse(population_size=size, f=.5, male_fraction=.5,
                                                  generations=0, seed=17, recombination_map=declaration,
                                                  selection=BlockSelection())
                expected = comb(both, 10)/comb(size//2, 10) if both >= 10 else 0.
                self.assertAlmostEqual(report['sampling']['p10_joint'], expected, places=15)
                target = .03 <= copies/(2*size) <= .07
                self.assertEqual(report['target']['target_auto'], target)
                self.assertAlmostEqual(report['target']['joint_and_target'], expected*target, places=15)
                self.assertEqual(report['sampling']['both_modern_men'], both)
        # The two marker marginals each have 15 modern males, but only 10 overlap.
        haps = np.zeros((40, 2, 1), dtype=np.uint8)
        haps.reshape(-1)[:4] = 1
        sex = np.array([1]*20+[0]*20, dtype=np.uint8)
        mt = np.zeros(40, dtype=np.uint8)
        mt[:15] = 1
        y = np.array([0]*20+[-1]*20, dtype=np.int8)
        y[5:20] = 1
        final = run_selected(haps, sex, mt, y, recombination_map=declaration,
                             selection=BlockSelection(), generations=0, seed=17)
        with patch('paleogen_rl.genetics.pulse.run_selected', return_value=final):
            report = evaluate_block_pulse(population_size=40, f=.5, male_fraction=.5,
                                          generations=0, seed=17, recombination_map=declaration,
                                          selection=BlockSelection())
        self.assertEqual(report['sampling']['both_modern_men'], 10)
        self.assertAlmostEqual(report['sampling']['p10_joint'], 1/comb(20, 10), places=15)
        self.assertAlmostEqual(report['target']['joint_and_target'], 1/comb(20, 10), places=15)

    def test_real_evaluation_matches_selected_engine_at_full_horizon(self):
        for seed in (0, 17, 42):
            selection = BlockSelection(s_mt=.0032, s_y=.0013, mt_partner_block='a',
                                       y_partner_block='c', mt_arch_nuc_mod=.01)
            state, _ = initialise_pulse(population_size=40, f=.5, male_fraction=.5, panel=mapping().panel)
            direct = run_selected(**state, selection=selection, recombination_map=mapping(),
                                  generations=5, seed=seed)
            report = evaluate_block_pulse(population_size=40, f=.5, male_fraction=.5,
                                          generations=5, seed=seed, recombination_map=mapping(), selection=selection)
            self.assertEqual(report['engine_report'], direct.report)
            both = int(((direct.mt[:20] == 1) & (direct.y[:20] == 1)).sum())
            self.assertAlmostEqual(report['sampling']['p10_joint'], comb(both, 10)/comb(20, 10) if both >= 10 else 0.)
            self.assertEqual(report['engine_report']['final_measurement']['generation'], 5)

    def test_incomplete_or_unavailable_final_measurements_are_refused(self):
        state, _ = initialise_pulse(population_size=20, f=.5, male_fraction=.5, panel=mapping().panel)
        for overrides in (dict(generations_completed=0), dict(termination_reason='reproduction_failed'),
                          dict(final_measurement=None)):
            final = run_selected(**state, selection=BlockSelection(), recombination_map=mapping(),
                                 generations=1, seed=17)
            final.report.update(overrides)
            with patch('paleogen_rl.genetics.pulse.run_selected', return_value=final):
                with self.assertRaisesRegex(RuntimeError, 'incomplete block horizon'):
                    evaluate_block_pulse(population_size=20, f=.5, male_fraction=.5,
                                         generations=1, seed=17, recombination_map=mapping(), selection=BlockSelection())

    def cli(self, directory, name, *extra):
        mapfile = Path(directory)/'map.json'
        mapfile.write_text(json.dumps(MAP))
        output = Path(directory)/f'{name}.csv'
        process = subprocess.run([
            sys.executable, str(ROOT/'run_experiment.py'), '--mode', 'full', '--N', '40',
            '--gens', '3', '--reps', '2', '--f', '.5', '--seed', '17',
            '--block-map', str(mapfile), '--mt-partner-block', 'a', '--y-partner-block', 'c',
            '--output', str(output), *extra], cwd=directory, capture_output=True, text=True)
        return process, output, mapfile

    def read(self, output):
        with output.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        def nonfinite(value):
            raise ValueError(f'nonfinite JSON: {value}')
        document = json.loads(output.with_suffix('.json').read_text(), parse_constant=nonfinite)
        return rows, document

    def assert_replay(self, row):
        report = json.loads(row['block_report'])
        declaration = report['engine_report']['recombination_map']
        restored = RecombinationMap(BlockPanel(**declaration['panel']), declaration['switch_probabilities'])
        selection = report['engine_report']['selection']
        config = Config(**json.loads(row['config_realized']))
        replayed = run_block_full(config, restored, selection['mt_partner_block'], selection['y_partner_block'])
        for field, value in replayed.items():
            self.assertEqual(row[field], str(value), field)
        self.assertEqual(row['result_schema_version'], RESULT_SCHEMA_VERSION)
        self.assertEqual(row['model'], MODEL)
        self.assertEqual(row['target_generation'], row['auto_generations_completed'])
        self.assertEqual(report['engine_report']['final_measurement']['allele_copy_denominator'], 320)
        self.assertEqual(report['engine_report']['final_measurement']['partner_block_ids'], ['a', 'c'])
        self.assertEqual(report['convergence_status'], 'not_assessed_for_selected_scenarios')

    def test_cli_all_scenarios_replay_pairing_context_and_repeatability(self):
        with tempfile.TemporaryDirectory() as directory:
            executions = []
            for name in ('first', 'second'):
                process, output, mapfile = self.cli(directory, name, '--scenario', 'all')
                self.assertEqual(process.returncode, 0, process.stdout+process.stderr)
                rows, document = self.read(output)
                self.assertEqual(len(rows), 2*len(SCENARIOS))
                self.assertEqual(document['meta']['model'], MODEL)
                self.assertEqual(document['meta']['result_schema_version'], RESULT_SCHEMA_VERSION)
                expected_hash = hashlib.sha256(mapfile.read_bytes()).hexdigest()
                self.assertEqual(document['meta']['block_map_sha256'], expected_hash)
                for row in rows:
                    self.assert_replay(row)
                    self.assertEqual(row['block_map_sha256'], expected_hash)
                    self.assertEqual(int(row['seed']), 17+int(row['rep']))
                    notes = json.loads(row['approximation_notes'])
                    self.assertIn('autosomal_measurement', notes)
                    self.assertNotIn('autosomal_proxy', notes)
                    self.assertIn('inclus', notes['autosomal_measurement'])
                    self.assertIn('convergence', notes)
                for summary in document['summary']:
                    work = [json.loads(r['block_report'])['engine_report']['work_units']
                            for r in rows if r['scenario'] == summary['name']]
                    self.assertEqual(summary['block_work_units']['candidates_generated'],
                                     sum(w['candidates_generated'] for w in work))
                    self.assertEqual(summary['block_work_units']['state_allele_entries'], 320)
                    summary.pop('time_seconds')
                document['meta'].pop('output')
                executions.append((rows, document))
            self.assertEqual(executions[0], executions[1])

    def test_cli_overrides_and_synthetic_posterior_keep_draw_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            posterior = Path(directory)/'synthetic.txt'
            posterior.write_text('-.004\n0\n.003\n')
            for scenario in ('neutral', 'reich_point'):
                process, output, _ = self.cli(directory, scenario, '--scenario', scenario,
                    '--mt-posterior', str(posterior), '--mt-arch-nuc-mod', '.003', '--y-mod-nuc-arch', '.002')
                self.assertEqual(process.returncode, 0, process.stdout+process.stderr)
                rows, _ = self.read(output)
                for row in rows:
                    self.assert_replay(row)
                    self.assertEqual(row['mt_posterior_sha256'], hashlib.sha256(posterior.read_bytes()).hexdigest())
                    config = json.loads(row['config_realized'])
                    self.assertEqual(config['mt_arch_nuc_mod'], .003)
                    self.assertEqual(config['y_mod_nuc_arch'], .002)
                    if scenario == 'reich_point':
                        seed = int(row['seed'])+27383
                        self.assertEqual(row['mt_selection_source'], 'posterior_draw')
                        self.assertEqual(int(row['mt_posterior_draw_seed']), seed)
                        self.assertEqual(config['s_mt'], float(np.random.default_rng(seed).choice([-.004, 0., .003])))
                    else:
                        self.assertEqual(row['mt_selection_source'], 'posterior_not_applied')
                        self.assertEqual(row['mt_posterior_draw_seed'], '')

    def test_single_replicate_is_strict_json_and_absorbed_markers_keep_full_horizon(self):
        with tempfile.TemporaryDirectory() as directory:
            process, output, _ = self.cli(directory, 'single', '--scenario', 'neutral', '--reps', '1', '--f', '1')
            self.assertEqual(process.returncode, 0, process.stdout+process.stderr)
            rows, document = self.read(output)
            self.assertEqual(rows[0]['generations_completed'], '3')
            self.assertEqual(rows[0]['p10_joint'], '1.0')
            self.assertEqual(rows[0]['auto_mod'], '1.0')
            self.assertEqual(rows[0]['joint_and_target'], '0.0')
            self.assertIsNone(document['summary'][0]['p10_joint_95pct_bootstrap'])
            self.assertIsNone(document['summary'][0]['joint_and_auto_95pct_bootstrap'])

    def test_modes_map_options_and_existing_outputs_fail_before_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            mapfile = Path(directory)/'map.json'
            mapfile.write_text(json.dumps(MAP))
            output = Path(directory)/'new.csv'
            base = ['run_experiment.py', '--scenario', 'neutral', '--mode', 'full', '--N', '40',
                    '--gens', '3', '--reps', '1', '--block-map', str(mapfile),
                    '--mt-partner-block', 'a', '--y-partner-block', 'c', '--output', str(output)]
            cases = [base+extra for extra in (['--mode', 'unsupported'],
                     ['--mt-partner-block', 'missing'], ['--seed', '-1'],
                     ['--output', str(Path(directory)/'bad.json')])]
            for option in ('--output', '--mt-partner-block', '--block-map'):
                without_option = base.copy()
                index = without_option.index(option)
                del without_option[index:index+2]
                cases.append(without_option)
            for argv in cases:
                with patch.object(sys, 'argv', argv), patch('run_experiment.run_block_full') as engine:
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                        main()
                    self.assertEqual(error.exception.code, 2)
                    engine.assert_not_called()
            for destination in (output, output.with_suffix('.json')):
                destination.write_bytes(b'preserve existing output')
                with patch.object(sys, 'argv', base), patch('run_experiment.run_block_full') as engine:
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                        main()
                    engine.assert_not_called()
                self.assertEqual(destination.read_bytes(), b'preserve existing output')
                destination.unlink()
            output.symlink_to(Path(directory)/'missing')
            with patch.object(sys, 'argv', base), patch('run_experiment.run_block_full') as engine:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    main()
                engine.assert_not_called()

    def test_invalid_map_and_initialisation_declarations_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'map.json'
            for declaration in (None, {}, {**MAP, 'unknown': 1},
                                {**MAP, 'switch_probabilities': [.1]},
                                {**MAP, 'switch_probabilities': [.1, .1, .6]},
                                {**MAP, 'panel': dict(panel_id='bad', block_ids=['a', 'a'])}):
                path.write_text(json.dumps(declaration))
                with self.subTest(declaration=declaration), self.assertRaises(ValueError):
                    load_block_map(path)
            path.write_text(json.dumps(MAP))
            restored, digest = load_block_map(path)
            self.assertEqual(restored, mapping())
            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
        for changes in (dict(population_size=1), dict(population_size=True), dict(f=float('nan')),
                        dict(f=True), dict(male_fraction=2), dict(f=1., male_fraction=1.)):
            with self.assertRaises(ValueError):
                initialise_pulse(**{**dict(population_size=40, f=.5, male_fraction=.5,
                                          panel=mapping().panel), **changes})

    def test_unsupported_config_is_never_silently_projected(self):
        cfg = Config(N=40, gens=3, stop_when_absorbed=False)
        for changes in (dict(sel_locus='X'), dict(s=.01), dict(xdrive=.1), dict(dm=.1),
                        dict(pulse2_gen=2), dict(cycle_T=10), dict(oversample=4.),
                        dict(mt_partner_locus=2), dict(stop_when_absorbed=True)):
            with self.subTest(changes=changes), patch('run_experiment.evaluate_block_pulse') as engine:
                with self.assertRaises(ValueError):
                    run_block_full(replace(cfg, **changes), mapping(), 'a', 'c')
                engine.assert_not_called()

    def test_real_reproduction_failure_has_no_success_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            posterior = Path(directory)/'synthetic-lethal.txt'
            posterior.write_text('1.0\n1.0\n')
            process, output, _ = self.cli(directory, 'failure', '--scenario', 'reich_point',
                                          '--f', '0', '--mt-posterior', str(posterior))
            self.assertEqual(process.returncode, 1, process.stdout+process.stderr)
            self.assertIn('reproduction_failed', process.stderr)
            self.assertIn('generations_completed=0', process.stderr)
            self.assertNotIn('Traceback', process.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix('.json').exists())


if __name__ == '__main__':
    unittest.main()
