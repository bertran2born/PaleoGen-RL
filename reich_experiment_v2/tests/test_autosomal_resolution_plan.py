"""Declared studies preserve the I18 statistics and I19 measurement contracts."""

from contextlib import redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from paleogen_rl.genetics.protocol import AutosomalProtocol
from run_experiment import Config, run_block_full
from study_autosomal_resolution import (
    ROOT, PLAN_VERSION, PLANNED_STUDY_VERSION, main, load_resolution_plan,
    run_resolution_plan, validate_resolution_plan,
)


class TestAutosomalResolutionPlan(unittest.TestCase):
    def plan(self):
        return dict(plan_version=PLAN_VERSION, plan_id='synthetic-test',
                    population_size=40, f=.5, male_fraction=.5, generations=2,
                    map_length=.25, resolutions=[2, 3, 5], seeds=[17, 73],
                    scenarios=['neutral', 'reich_plus_symmetric_1pct'])

    def test_target_regime_can_be_declared_without_simulation(self):
        plan = self.plan()
        plan.update(population_size=1450, f=.05, generations=6993,
                    resolutions=[8, 32, 128], seeds=list(range(510000, 510128)))
        with patch('study_autosomal_resolution.run_block_full') as simulate:
            validated = validate_resolution_plan(plan)
            simulate.assert_not_called()
        self.assertEqual(validated, plan)

    def test_multiple_demographies_replay_directly_and_trace_work(self):
        for population, fraction, male_fraction, horizon in ((20, .2, .25, 1), (41, .1, .5, 3), (60, .5, .5, 2)):
            plan = self.plan()
            plan.update(population_size=population, f=fraction, male_fraction=male_fraction, generations=horizon)
            report = run_resolution_plan(plan)
            self.assertEqual(report['study_version'], PLANNED_STUDY_VERSION)
            self.assertEqual(report['convergence_status'], 'not_established')
            self.assertEqual(report['plan'], plan)
            identities = {}
            for scenario in report['scenarios']:
                for row in scenario['resolutions']:
                    contract = AutosomalProtocol.from_dict(row['autosomal_protocol'])
                    self.assertEqual(contract.sha256, row['autosomal_protocol_sha256'])
                    previous = identities.setdefault(row['block_count'], contract.sha256)
                    self.assertEqual(previous, contract.sha256)
                    self.assertEqual(contract.population_size, population)
                    self.assertEqual(contract.f, fraction)
                    self.assertEqual(contract.male_fraction, male_fraction)
                    self.assertEqual(contract.generations, horizon)
                    self.assertEqual(row['allele_copy_denominator'], 2*population*row['block_count'])
                    for replicate in row['replicates']:
                        config = Config(**row['config_parameters'], seed=replicate['seed'])
                        direct = run_block_full(config, contract.recombination_map,
                                                contract.mt_partner_block, contract.y_partner_block)
                        evaluation = json.loads(direct['block_report'])
                        self.assertEqual(row['initialisation'], evaluation['initialisation'])
                        self.assertEqual(replicate['ancestry'], direct['auto_mod'])
                        self.assertEqual(replicate['generation'], horizon)
                        for field in ('p10_joint', 'joint_and_target', 'target_auto'):
                            self.assertEqual(replicate[field], direct[field])
                        self.assertEqual(replicate['work_units'], evaluation['engine_report']['work_units'])
            self.assertEqual(report['total_work_units']['offspring_generated'],
                             population*plan['generations']*len(plan['seeds'])*3*2)
            for path, digest in report['implementation_sha256'].items():
                self.assertEqual(digest, hashlib.sha256((ROOT/path).read_bytes()).hexdigest())

    def test_owned_normalization_and_canonical_identity(self):
        plan = self.plan()
        plan.update(f=0, map_length=1)
        normalized = validate_resolution_plan(plan)
        plan['seeds'].append(999)
        self.assertEqual(normalized['seeds'], [17, 73])
        self.assertIs(type(normalized['f']), float)
        with tempfile.TemporaryDirectory() as directory:
            hashes, reports = [], []
            for index, payload in enumerate((json.dumps(normalized), json.dumps(normalized, indent=3, sort_keys=True))):
                path = Path(directory)/str(index)
                path.write_text(payload)
                restored, digest = load_resolution_plan(path)
                hashes.append(digest)
                reports.append(run_resolution_plan(restored))
            self.assertNotEqual(hashes[0], hashes[1])
            self.assertEqual(reports[0], reports[1])
            snapshot = reports[0]['plan']
            encoded = json.dumps(snapshot, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
            self.assertEqual(reports[0]['plan_sha256'], hashlib.sha256(encoded.encode()).hexdigest())
        changed = deepcopy(normalized)
        changed['plan_id'] = 'another-declaration'
        self.assertNotEqual(run_resolution_plan(changed)['plan_sha256'], reports[0]['plan_sha256'])

    def test_invalid_plans_fail_before_engine(self):
        base = self.plan()
        invalid = [None, [], {**base, 'extra': True}]
        for field in base:
            changed = deepcopy(base)
            changed.pop(field)
            invalid.append(changed)
        for field, value in (
                ('plan_version', 'unknown'), ('plan_id', ' bad '), ('plan_id', ''),
                ('population_size', 19), ('population_size', True), ('population_size', 40.),
                ('generations', 0), ('generations', -1), ('generations', True), ('generations', 2.),
                ('f', float('nan')), ('f', float('inf')), ('f', True), ('f', -.1),
                ('male_fraction', 2.), ('male_fraction', True), ('male_fraction', float('nan')),
                ('map_length', -1), ('map_length', float('inf')), ('map_length', True),
                ('resolutions', [2, 3]), ('resolutions', [3, 2, 4]), ('resolutions', [2, 2, 4]),
                ('resolutions', [True, 3, 4]), ('resolutions', [2, 3, 4.]),
                ('seeds', []), ('seeds', [1, 1]), ('seeds', [-1]), ('seeds', [True]),
                ('scenarios', []), ('scenarios', ['neutral', 'neutral']), ('scenarios', ['unknown'])):
            invalid.append({**base, field: value})
        invalid.append({**base, 'f': 1., 'male_fraction': 1.})
        with patch('study_autosomal_resolution.run_block_full') as simulate:
            for plan in invalid:
                with self.subTest(plan=plan), self.assertRaises(ValueError):
                    run_resolution_plan(plan)
            simulate.assert_not_called()

    def test_duplicate_and_nonfinite_json_are_rejected(self):
        plan = self.plan()
        payloads = [json.dumps(plan)[:-1]+',"seeds":[1]}',
                    json.dumps({**plan, 'map_length': float('nan')}),
                    json.dumps({**plan, 'map_length': float('inf')}), '{invalid']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'bad.json'
            for payload in payloads:
                path.write_text(payload)
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    load_resolution_plan(path)

    def test_cli_outputs_replay_after_source_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/'plan.json', Path(directory)/'report.json'
            source.write_text(json.dumps(self.plan()))
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            result = subprocess.run([sys.executable, str(ROOT/'study_autosomal_resolution.py'),
                                     '--plan', str(source), '--output', str(output)],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(report['plan_file_sha256'], digest)
            source.unlink()
            replayed = run_resolution_plan(report['plan'])
            report['plan_file_sha256'] = None
            self.assertEqual(report, replayed)
            self.assertEqual(json.loads(json.dumps(report, allow_nan=False)), report)

    def test_cli_errors_preserve_destinations_and_never_write_partial_success(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/'plan.json', Path(directory)/'result.json'
            source.write_text(json.dumps(self.plan()))
            args = ['--plan', str(source), '--output', str(output)]
            output.write_bytes(b'preserve')
            with patch('study_autosomal_resolution.run_resolution_plan') as simulate:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    main(args)
                self.assertEqual(error.exception.code, 2)
                simulate.assert_not_called()
            self.assertEqual(output.read_bytes(), b'preserve')
            output.unlink()
            output.symlink_to(Path(directory)/'absent')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main(args)
            self.assertEqual(error.exception.code, 2)
            output.unlink()
            source.write_text('{invalid')
            with patch('study_autosomal_resolution.run_block_full') as simulate:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    main(args)
                self.assertEqual(error.exception.code, 1)
                simulate.assert_not_called()
            source.write_text(json.dumps(self.plan()))
            with patch('study_autosomal_resolution.run_block_full', side_effect=RuntimeError('reproduction_failed')):
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    main(args)
                self.assertEqual(error.exception.code, 1)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
