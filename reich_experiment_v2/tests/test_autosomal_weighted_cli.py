"""Weighted CLI integration, provenance and independent API replay."""

from contextlib import redirect_stderr
import csv
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from run_experiment import (
    Config, SCENARIOS, WEIGHTED_PROTOCOL_RESULT_SCHEMA_VERSION, main, run_block_mode,
)
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.pulse import evaluate_block_pulse
from paleogen_rl.genetics.selected import BlockSelection
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel
from paleogen_rl.genetics.weighted_protocol import WeightedAutosomalProtocol, WEIGHTED_PROTOCOL_VERSION


ROOT = Path(__file__).resolve().parents[1]


class TestWeightedCLI(unittest.TestCase):
    def protocol(self, **changes):
        panel = BlockPanel('synthetic-three', ('mt', 'middle', 'y'))
        protocol = WeightedAutosomalProtocol(
            protocol_id='synthetic-cli-v1', population_size=40, generations=4,
            f=.5, male_fraction=.5, recombination_map=RecombinationMap(panel, (.1, .1)),
            mt_partner_block='mt', y_partner_block='y',
            measurement_panel=WeightedBlockPanel(panel, (2, 4, 2), 'synthetic relative lengths'))
        return replace(protocol, **changes)

    def cli(self, directory, name, mode, *, protocol=None, extra=()):
        protocol = self.protocol() if protocol is None else protocol
        source = Path(directory)/f'{name}-protocol.json'
        source.write_text(protocol.canonical_json, encoding='utf-8')
        output = Path(directory)/f'{name}.csv'
        argv = [sys.executable, str(ROOT/'run_experiment.py'), '--weighted-autosomal-protocol', str(source),
                '--scenario', 'all', '--reps', '3', '--seed', '17', '--mode', mode, '--output', str(output)]
        process = subprocess.run([*argv, *extra], cwd=directory, capture_output=True, text=True)
        return process, output, source

    def read(self, output):
        with output.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        def reject(value):
            raise ValueError(value)
        return rows, json.loads(output.with_suffix('.json').read_text(), parse_constant=reject)

    def direct(self, protocol, config, mode):
        selection = BlockSelection(
            s_mt=config.s_mt, s_y=config.s if config.sel_locus == 'Y' else 0.,
            mt_mod_nuc_arch=config.mt_mod_nuc_arch, mt_arch_nuc_mod=config.mt_arch_nuc_mod,
            y_mod_nuc_arch=config.y_mod_nuc_arch, y_arch_nuc_mod=config.y_arch_nuc_mod,
            dominance=config.mismatch_dominance, mt_partner_block=protocol.mt_partner_block,
            y_partner_block=protocol.y_partner_block)
        return evaluate_block_pulse(
            population_size=config.N, f=config.f, male_fraction=config.male_frac,
            generations=config.gens, seed=config.seed, selection=selection, mode=mode,
            recombination_map=protocol.recombination_map, measurement_panel=protocol.measurement_panel)

    def test_all_scenarios_three_seeds_modes_and_source_free_replay(self):
        expected = self.protocol()
        for mode in ('full', 'quick', 'adaptive'):
            with tempfile.TemporaryDirectory() as directory, self.subTest(mode=mode):
                process, output, source = self.cli(directory, mode, mode)
                self.assertEqual(process.returncode, 0, process.stdout+process.stderr)
                rows, document = self.read(output)
                file_hash = hashlib.sha256(source.read_bytes()).hexdigest()
                source.unlink()
                meta = document['meta']
                self.assertEqual(meta['autosomal_protocol'], expected.to_dict())
                self.assertEqual(meta['autosomal_protocol_sha256'], expected.sha256)
                self.assertEqual(meta['autosomal_protocol_file_sha256'], file_hash)
                self.assertEqual(meta['autosomal_protocol_version'], WEIGHTED_PROTOCOL_VERSION)
                self.assertEqual(meta['result_schema_version'], WEIGHTED_PROTOCOL_RESULT_SCHEMA_VERSION)
                self.assertEqual(meta['resolution_control_status'], 'not_established')
                self.assertEqual(meta['autosomal_protocol_source'], str(source))
                self.assertEqual(len(rows), len(SCENARIOS)*3)
                for row in rows:
                    snapshot = WeightedAutosomalProtocol.from_dict(json.loads(row['autosomal_protocol']))
                    self.assertEqual(snapshot.sha256, expected.sha256)
                    self.assertEqual(row['autosomal_protocol_sha256'], expected.sha256)
                    self.assertEqual(row['autosomal_protocol_file_sha256'], file_hash)
                    self.assertEqual(row['autosomal_protocol_version'], WEIGHTED_PROTOCOL_VERSION)
                    self.assertEqual(row['result_schema_version'], WEIGHTED_PROTOCOL_RESULT_SCHEMA_VERSION)
                    self.assertEqual(row['resolution_control_status'], 'not_established')
                    cfg = Config(**json.loads(row['config_realized']))
                    direct = self.direct(snapshot, cfg, mode)
                    self.assertEqual(json.loads(row['block_report']), direct)
                    adapted = run_block_mode(cfg, mode, snapshot.recombination_map,
                                             snapshot.mt_partner_block, snapshot.y_partner_block,
                                             measurement_panel=snapshot.measurement_panel)
                    for field, value in adapted.items():
                        self.assertEqual(row[field], '' if value is None else str(value), field)
                    self.assertEqual(row['target_auto'], '' if direct['target']['target_auto'] is None
                                     else str(direct['target']['target_auto']))
                    notes = json.loads(row['approximation_notes'])
                    self.assertIn('poids relatifs explicitement déclarés', notes['autosomal_measurement'])
                    self.assertNotIn('poids égal', notes['autosomal_measurement'])
                    self.assertEqual(row['scientific_status'], 'exploratory_simulation')
                for summary in document['summary']:
                    matching = [row for row in rows if row['scenario'] == summary['name']]
                    reports = [json.loads(row['block_report']) for row in matching]
                    work = [r.get('work_units', r['engine_report']['work_units']) for r in reports]
                    for key, value in summary['block_work_units'].items():
                        self.assertEqual(value, max(w[key] for w in work) if key == 'state_allele_entries'
                                         else sum(w[key] for w in work))
                    self.assertAlmostEqual(summary['p10_joint'], np.mean([float(r['p10_joint']) for r in matching]))
                    if mode == 'full':
                        self.assertAlmostEqual(summary['auto_mod'], np.mean([float(r['auto_mod_at_50ka']) for r in matching]))
                    if mode != 'quick':
                        self.assertAlmostEqual(summary['P_joint_and_auto'], np.mean([float(r['joint_and_target']) for r in matching]))
                    if mode != 'full':
                        self.assertNotIn('P_autosomal_range', summary)

    def test_absorbed_states_keep_final_availability_and_single_rep_summaries(self):
        for fraction in (0., 1.):
            targets = {}
            for mode in ('full', 'quick', 'adaptive'):
                with tempfile.TemporaryDirectory() as directory, self.subTest(f=fraction, mode=mode):
                    process, output, _ = self.cli(directory, mode, mode, protocol=self.protocol(f=fraction),
                                                  extra=('--scenario', 'neutral', '--reps', '1'))
                    self.assertEqual(process.returncode, 0, process.stdout+process.stderr)
                    rows, doc = self.read(output)
                    row = rows[0]
                    report = json.loads(row['block_report'])
                    targets[mode] = row['joint_and_target']
                    self.assertIsNone(doc['summary'][0]['p10_joint_95pct_bootstrap'])
                    if mode == 'full' or mode == 'adaptive' and fraction == 1.:
                        self.assertEqual(float(row['auto_mod_at_50ka']), fraction)
                        self.assertEqual(int(row['auto_generations_completed']), 4)
                    else:
                        self.assertEqual(row['auto_mod_at_50ka'], '')
                        self.assertEqual(row['target_auto'], '')
                    if mode == 'quick':
                        self.assertEqual(row['joint_and_target'], '')
                        self.assertNotIn('P_joint_and_auto', doc['summary'][0])
                    else:
                        self.assertIsNone(doc['summary'][0]['joint_and_auto_95pct_bootstrap'])
                    if mode == 'adaptive':
                        self.assertEqual(report['continuation_status'], 'rerun_to_target' if fraction else 'skipped_event_impossible')
            self.assertEqual(targets['full'], targets['adaptive'])

    def test_posterior_overrides_and_identical_locked_options_keep_provenance(self):
        for mode in ('full', 'quick', 'adaptive'):
            with tempfile.TemporaryDirectory() as directory:
                posterior = Path(directory)/'synthetic.txt'
                posterior.write_text('-.004\n0\n.003\n')
                process, output, _ = self.cli(directory, mode, mode, extra=(
                    '--scenario', 'reich_point', '--mt-posterior', str(posterior), '--mt-arch-nuc-mod', '.003',
                    '--N', '40', '--gens', '4', '--f', '.5', '--male-frac', '.5'))
                self.assertEqual(process.returncode, 0, process.stdout+process.stderr)
                rows, _ = self.read(output)
                for row in rows:
                    cfg = Config(**json.loads(row['config_realized']))
                    self.assertEqual(cfg.mt_arch_nuc_mod, .003)
                    draw_seed = int(row['seed'])+27383
                    self.assertEqual(int(row['mt_posterior_draw_seed']), draw_seed)
                    self.assertEqual(cfg.s_mt, np.random.default_rng(draw_seed).choice([-.004, 0, .003]))
                    self.assertEqual(cfg.s, SCENARIOS['reich_point']['s'])
                    self.assertEqual(row['mt_selection_source'], 'posterior_draw')
                    self.assertEqual(row['mt_posterior_sha256'], hashlib.sha256(posterior.read_bytes()).hexdigest())
                    self.assertEqual(json.loads(row['block_report']), self.direct(self.protocol(), cfg, mode))

    def test_invalid_inputs_and_conflicts_fail_before_all_engines(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'protocol.json'
            source.write_text(self.protocol().canonical_json)
            output = Path(directory)/'new.csv'
            base = ['run_experiment.py', '--weighted-autosomal-protocol', str(source),
                    '--scenario', 'neutral', '--reps', '1', '--output', str(output)]
            cases = [base+extra for extra in (
                ['--autosomal-protocol', str(source)], ['--block-map', 'missing'],
                ['--mt-partner-block', 'mt'], ['--y-partner-block', 'y'],
                ['--N', '1450'], ['--gens', '6993'], ['--f', '.05'], ['--male-frac', '.6'],
                ['--seed', '-1'], ['--reps', '0'], ['--output', str(output.with_suffix('.txt'))])]
            cases.append(base[:-2])
            for argv in cases:
                with self.subTest(argv=argv), patch.object(sys, 'argv', argv), \
                     patch('run_experiment.run_block_full') as full, \
                     patch('run_experiment.run_block_mode') as screened, \
                     patch('run_experiment.run_mode') as legacy:
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                        main()
                    self.assertEqual(error.exception.code, 2)
                    full.assert_not_called()
                    screened.assert_not_called()
                    legacy.assert_not_called()
                self.assertFalse(output.exists())
                self.assertFalse(output.with_suffix('.json').exists())
            for payload in ('{"pulse":{"f":0,"f":1}}', '{', 'null',
                            (ROOT.parent/'docs/science/autosomal-protocol-synthetic.json').read_text(),
                            self.protocol().canonical_json.replace('"status":"not_established"', '"status":"converged"')):
                source.write_text(payload)
                with patch.object(sys, 'argv', base), patch('run_experiment.evaluate_block_pulse') as engine:
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                        main()
                    self.assertEqual(error.exception.code, 2)
                    engine.assert_not_called()
                self.assertFalse(output.exists())

    def test_existing_destinations_are_preserved_before_simulation(self):
        for suffix in ('.csv', '.json'):
            with tempfile.TemporaryDirectory() as directory:
                source = Path(directory)/'protocol.json'
                source.write_text(self.protocol().canonical_json)
                output = Path(directory)/'keep.csv'
                existing = output.with_suffix(suffix)
                existing.write_bytes(b'preserve')
                argv = ['run_experiment.py', '--weighted-autosomal-protocol', str(source), '--output', str(output)]
                with patch.object(sys, 'argv', argv), patch('run_experiment.evaluate_block_pulse') as engine:
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                        main()
                    self.assertEqual(error.exception.code, 2)
                    engine.assert_not_called()
                self.assertEqual(existing.read_bytes(), b'preserve')

    def test_real_reproduction_failure_emits_no_success_files_in_any_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            posterior = Path(directory)/'synthetic-lethal.txt'
            posterior.write_text('1\n1\n')
            for mode in ('full', 'quick', 'adaptive'):
                process, output, _ = self.cli(directory, mode, mode, protocol=self.protocol(f=0.), extra=(
                    '--scenario', 'reich_point', '--mt-posterior', str(posterior), '--reps', '1'))
                self.assertEqual(process.returncode, 1, process.stdout+process.stderr)
                self.assertIn('reproduction_failed', process.stderr)
                self.assertNotIn('Traceback', process.stderr)
                self.assertFalse(output.exists())
                self.assertFalse(output.with_suffix('.json').exists())


if __name__ == '__main__':
    unittest.main()
