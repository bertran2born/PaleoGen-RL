"""Weighted full studies: independent replay, statistics, planning and CLI."""

from contextlib import redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
from math import expm1, log, sqrt
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from run_experiment import Config, SCENARIOS
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.protocol import _canonical
from paleogen_rl.genetics.pulse import evaluate_block_pulse
from paleogen_rl.genetics.selected import BlockSelection, ReproductionFailure
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel
from paleogen_rl.genetics.weighted_protocol import WeightedAutosomalProtocol
from study_weighted_autosomal_resolution import (
    ROOT, PLAN_VERSION, STUDY_VERSION, PREVIEW_VERSION, main,
    load_weighted_resolution_plan, preview_weighted_resolution_plan,
    run_weighted_resolution_plan, validate_weighted_resolution_plan,
)


class TestWeightedStudy(unittest.TestCase):
    def plan(self):
        panel = BlockPanel('synthetic-four', ('a', 'b', 'c', 'd'))
        positions = (1/16, 5/16, 11/16, 15/16)
        length = .25
        switches = tuple(-expm1(-2*(length*(b-a)))/2 for a, b in zip(positions, positions[1:]))
        protocol = WeightedAutosomalProtocol(
            'synthetic-study-base', 40, 3, .05, .5, RecombinationMap(panel, switches),
            'a', 'd', WeightedBlockPanel(panel, (1, 3, 3, 1), 'synthetic relative lengths'))
        return dict(plan_version=PLAN_VERSION, plan_id='synthetic-study',
                    family=dict(base_protocol=protocol.to_dict(), family_id='synthetic-family',
                                map_length=length, refinement_factors=[1, 3, 9]),
                    seeds=[17, 18, 19], scenarios=['neutral', 'reich_plus_symmetric_1pct'])

    def direct(self, config, protocol):
        selection = BlockSelection(
            s_mt=config.s_mt, s_y=config.s if config.sel_locus == 'Y' else 0.,
            **{name: getattr(config, name) for name in
               ('mt_mod_nuc_arch', 'mt_arch_nuc_mod', 'y_mod_nuc_arch', 'y_arch_nuc_mod')},
            mt_partner_block=protocol.mt_partner_block, y_partner_block=protocol.y_partner_block,
            dominance=config.mismatch_dominance)
        return evaluate_block_pulse(population_size=config.N, f=config.f, male_fraction=config.male_frac,
                    generations=config.gens, seed=config.seed, recombination_map=protocol.recombination_map,
                    selection=selection, measurement_panel=protocol.measurement_panel)

    def test_all_scenarios_replay_reports_metrics_and_paired_differences(self):
        plan = self.plan()
        plan['scenarios'] = list(SCENARIOS)
        report = run_weighted_resolution_plan(plan)
        self.assertEqual(report['study_version'], STUDY_VERSION)
        self.assertEqual(report['convergence_status'], 'not_established')
        self.assertEqual(report['mode'], 'full')
        for path, digest in report['implementation_sha256'].items():
            self.assertEqual(digest, hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
        for scenario in report['scenarios']:
            for row, declared in zip(scenario['resolutions'], report['family']['resolutions']):
                protocol = WeightedAutosomalProtocol.from_dict(declared['autosomal_protocol'])
                self.assertEqual(row['autosomal_protocol_sha256'], protocol.sha256)
                self.assertEqual([r['seed'] for r in row['replicates']], plan['seeds'])
                for replicate in row['replicates']:
                    cfg = Config(**replicate['config_realized'])
                    actual = self.direct(cfg, protocol)
                    self.assertEqual(actual, replicate['evaluation'])
                    final = actual['engine_report']['final_measurement']
                    self.assertEqual(final['value'], final['modern_ancestry_weight']/final['weight_denominator'])
                    self.assertEqual(replicate['ancestry'], final['value'])
                    self.assertEqual(replicate['generation'], 3)
                    self.assertEqual(replicate['target_auto'], .03 <= final['value'] <= .07)
                    self.assertEqual(replicate['joint_and_target'], actual['sampling']['p10_joint']*replicate['target_auto'])
                    self.assertEqual(replicate['work_units'], actual['engine_report']['work_units'])
                values = [r['ancestry'] for r in row['replicates']]
                self.assertAlmostEqual(row['metrics']['ancestry']['mean'], np.mean(values))
                radius = sqrt(log(40)/(2*len(values)))
                self.assertEqual(row['metrics']['ancestry']['interval'],
                                 [max(0., np.mean(values)-radius), min(1., np.mean(values)+radius)])
                hits = sum(.03 <= value <= .07 for value in values)
                self.assertEqual(row['metrics']['target_probability']['count'], hits)
                self.assertEqual(row['metrics']['target_probability']['probability'], hits/len(values))
                for metric in ('p10_joint', 'joint_and_target'):
                    self.assertEqual(row['metrics'][metric]['mean'], np.mean([r[metric] for r in row['replicates']]))
            finest = scenario['resolutions'][-1]['replicates']
            for delta, row in zip(scenario['differences_from_finest'], scenario['resolutions'][:-1]):
                for metric, field in (('ancestry', 'ancestry'), ('target_probability', 'target_auto'),
                                      ('p10_joint', 'p10_joint'), ('joint_and_target', 'joint_and_target')):
                    differences = [float(a[field])-float(b[field]) for a, b in zip(row['replicates'], finest)]
                    self.assertEqual(delta['metrics'][metric]['mean'], np.mean(differences))
                    radius = sqrt(2*log(40)/len(differences))
                    self.assertEqual(delta['metrics'][metric]['interval'],
                                     [max(-1., np.mean(differences)-radius), min(1., np.mean(differences)+radius)])

    def test_preview_no_rng_or_engine_and_observed_costs_respect_bounds(self):
        plan = self.plan()
        before = deepcopy(plan)
        with patch('study_weighted_autosomal_resolution.run_block_full', side_effect=AssertionError('engine forbidden')), \
             patch('numpy.random.default_rng', side_effect=AssertionError('RNG forbidden')):
            preview = preview_weighted_resolution_plan(plan)
            target_regime = deepcopy(plan)
            target_regime['family']['base_protocol'].update(population_size=1450, generations=6993)
            large_preview = preview_weighted_resolution_plan(target_regime)
            self.assertEqual(large_preview['total_workload']['offspring_generated_on_completion'], 18*1450*6993)
        self.assertEqual(plan, before)
        self.assertEqual(preview['preview_version'], PREVIEW_VERSION)
        self.assertFalse(preview['simulation_performed'])
        self.assertEqual(preview['total_workload']['evaluations'], 18)
        self.assertEqual(preview['total_workload']['offspring_generated_on_completion'], 2160)
        self.assertEqual(preview['total_workload']['block_copy_transmissions_lower_bound_on_completion'], 46080)
        self.assertEqual(preview['total_workload']['largest_population_state_allele_entries'], 1600)
        actual = run_weighted_resolution_plan(plan)
        total_work = actual['total_work_units']
        for predicted, index in zip(preview['resolutions'], range(3)):
            work = [s['resolutions'][index]['work_units'] for s in actual['scenarios']]
            for field in ('offspring_generated', 'accepted_candidates'):
                self.assertEqual(sum(w[field] for w in work), predicted[f'{field}_on_completion'])
                self.assertEqual(sum(s['work_units'][field] for s in actual['scenarios']), total_work[field])
            for field in ('candidates_generated', 'block_copy_transmissions'):
                self.assertGreaterEqual(sum(w[field] for w in work), predicted[f'{field}_lower_bound_on_completion'])
            self.assertEqual(max(w['state_allele_entries'] for w in work), predicted['state_allele_entries'])
        preview['plan']['seeds'].append(999)
        self.assertEqual(plan, before)

    def test_canonical_identity_file_hash_roundtrip_and_owned_snapshots(self):
        plan = self.plan()
        normalized = validate_weighted_resolution_plan(plan)
        with tempfile.TemporaryDirectory() as directory:
            hashes, reports = [], []
            for number, payload in enumerate((_canonical(normalized), json.dumps(normalized, indent=4))):
                path = Path(directory)/str(number)
                path.write_text(payload)
                restored, digest = load_weighted_resolution_plan(path)
                hashes.append(digest)
                self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
                reports.append(run_weighted_resolution_plan(restored))
                path.unlink()
                self.assertEqual(run_weighted_resolution_plan(reports[-1]['plan']), reports[-1])
            self.assertNotEqual(hashes[0], hashes[1])
            self.assertEqual(reports[0], reports[1])
        self.assertEqual(reports[0]['plan_sha256'], hashlib.sha256(_canonical(normalized).encode()).hexdigest())
        for key, value in (('plan_id', 'other'), ('seeds', [0, 42]), ('scenarios', ['neutral'])):
            changed = {**plan, key: value}
            self.assertNotEqual(preview_weighted_resolution_plan(changed)['plan_sha256'], reports[0]['plan_sha256'])
        normalized['family']['base_protocol']['pulse']['f'] = .8
        normalized['seeds'].append(999)
        self.assertEqual(plan, self.plan())

    def test_invalid_plan_fields_values_and_duplicate_json_fail_before_engine(self):
        original = self.plan()
        cases = [None, [], {**original, 'extra': 1}, {**original, 'plan_version': 'unknown'}]
        for field in original:
            changed = deepcopy(original)
            del changed[field]
            cases.append(changed)
        for field, values in (('plan_id', ('', ' padded ', None)),
                ('seeds', ([], [1, 1], [-1], [True], [1.], '1')),
                ('scenarios', ([], ['absent'], ['neutral', 'neutral'], [None]))):
            cases.extend({**original, field: value} for value in values)
        for key, value in (('map_length', -1), ('map_length', float('nan')),
                            ('refinement_factors', [1, 2, 4]), ('unknown', 'ignored?')):
            changed = deepcopy(original)
            changed['family'][key] = value
            cases.append(changed)
        for key in original['family']:
            changed = deepcopy(original)
            del changed['family'][key]
            cases.append(changed)
        with patch('study_weighted_autosomal_resolution.run_block_full') as engine:
            for plan in cases:
                with self.subTest(plan=plan), self.assertRaises(ValueError):
                    run_weighted_resolution_plan(plan)
            engine.assert_not_called()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'plan.json'
            for payload in ('{"seeds":[1],"seeds":[2]}', '{', 'null',
                            _canonical(original).replace('"map_length":0.25', '"map_length":NaN'),
                            _canonical(original).replace('"f":0.05', '"f":0.05,"f":0.1')):
                path.write_text(payload)
                with self.assertRaises(ValueError):
                    load_weighted_resolution_plan(path)

    def test_cli_runs_preview_and_full_and_rejects_existing_destinations(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory)/'plan.json'
            plan_path.write_text(json.dumps(self.plan()))
            for preview in (True, False):
                output = Path(directory)/f'{preview}.json'
                argv = [sys.executable, str(ROOT/'study_weighted_autosomal_resolution.py'), '--plan',
                        str(plan_path), '--output', str(output), *(['--preview'] if preview else [])]
                result = subprocess.run(argv, cwd=directory, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                document = json.loads(output.read_text(), parse_constant=lambda value: self.fail(value))
                file_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest()
                self.assertEqual(document['plan_file_sha256'], file_hash)
                expected = preview_weighted_resolution_plan(self.plan()) if preview else run_weighted_resolution_plan(self.plan())
                document['plan_file_sha256'] = None
                if not preview:
                    self.assertEqual(document['workload_preview']['plan_file_sha256'], file_hash)
                    document['workload_preview']['plan_file_sha256'] = None
                self.assertEqual(document, expected)
                before = output.read_bytes()
                result = subprocess.run(argv, cwd=directory, capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(output.read_bytes(), before)
            dangling = Path(directory)/'dangling.json'
            dangling.symlink_to(Path(directory)/'missing')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main(['--plan', str(plan_path), '--output', str(dangling)])
            self.assertEqual(error.exception.code, 2)
            with patch('study_weighted_autosomal_resolution.run_block_full') as engine:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    main(['--plan', str(plan_path), '--output', str(Path(directory)/'absent/report.json')])
                self.assertEqual(error.exception.code, 2)
                engine.assert_not_called()

    def test_cli_invalid_plan_and_reproductive_failure_publish_no_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path, output = Path(directory)/'plan.json', Path(directory)/'report.json'
            path.write_text('{')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main(['--plan', str(path), '--output', str(output)])
            self.assertEqual(error.exception.code, 1)
            self.assertFalse(output.exists())
            path.write_text(json.dumps(self.plan()))
            failure = ReproductionFailure(dict(seed=17, generations_completed=0, failed_generation=1))
            with patch('study_weighted_autosomal_resolution.run_block_full', side_effect=failure), \
                 redirect_stderr(io.StringIO()) as errors, self.assertRaises(SystemExit) as error:
                main(['--plan', str(path), '--output', str(output)])
            self.assertEqual(error.exception.code, 1)
            self.assertIn('neutral B=4 seed=17', errors.getvalue())
            self.assertIn('reproduction_failed', errors.getvalue())
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
