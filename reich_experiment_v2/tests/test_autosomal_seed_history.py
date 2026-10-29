"""Declared historical seed exclusions: fail before simulation, keep replay intact."""

from contextlib import redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
from math import expm1
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from autosomal_seed_history import (
    AUDIT_VERSION, HISTORY_VERSION, PURPOSES, audit_seed_separation,
    load_seed_history, validate_seed_history,
)
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.protocol import _canonical
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel
from paleogen_rl.genetics.weighted_protocol import WeightedAutosomalProtocol
from study_weighted_autosomal_resolution import (
    ROOT, PLAN_VERSION, main, preview_weighted_resolution_plan, run_weighted_resolution_plan,
)
from weighted_autosomal_equivalence import CRITERIA_VERSION, METRICS, assess_weighted_equivalence


def history():
    # Synthetic provenance references, not a complete inventory of repository seeds.
    return dict(history_version=HISTORY_VERSION, history_id='synthetic-history', sources=[
        dict(source_id=f'synthetic-{purpose}', purpose=purpose,
             source_sha256=hashlib.sha256(purpose.encode()).hexdigest(), seeds=[index, 10])
        for index, purpose in enumerate(PURPOSES)])


def plan():
    panel = BlockPanel('synthetic-four', ('a', 'b', 'c', 'd'))
    positions = (1/16, 5/16, 11/16, 15/16)
    length = .25
    switches = tuple(-expm1(-2*length*(b-a))/2 for a, b in zip(positions, positions[1:]))
    base = WeightedAutosomalProtocol('seed-audit-control', 40, 2, .5, .5,
        RecombinationMap(panel, switches), 'a', 'd',
        WeightedBlockPanel(panel, (1, 3, 3, 1), 'synthetic control'))
    return dict(plan_version=PLAN_VERSION, plan_id='seed-audit-control', seeds=[40, 41, 42],
        scenarios=['neutral', 'reich_plus_symmetric_1pct'], family=dict(base_protocol=base.to_dict(),
        family_id='seed-audit-family', map_length=length, refinement_factors=[1, 3, 9]))


class TestSeedHistory(unittest.TestCase):
    def test_all_collisions_and_sources_are_reported_without_rng_or_engine(self):
        declared = history()
        original = deepcopy(declared)
        with patch('numpy.random.default_rng', side_effect=AssertionError('RNG forbidden')), \
             patch('study_weighted_autosomal_resolution.run_block_full', side_effect=AssertionError('engine forbidden')):
            audit = audit_seed_separation([10, 2, 99], declared)
        self.assertEqual(audit['audit_version'], AUDIT_VERSION)
        self.assertEqual(audit['status'], 'overlap_detected')
        self.assertEqual(audit['excluded_seed_count'], 5)
        self.assertEqual([row['seeds'] for row in audit['collisions']], [[10], [10], [2, 10], [10]])
        for source, conflict in zip(declared['sources'], audit['collisions']):
            for key in ('source_id', 'purpose', 'source_sha256'):
                self.assertEqual(conflict[key], source[key])
        self.assertEqual(declared, original)

    def test_disjointness_scope_hashes_determinism_and_owned_snapshots(self):
        declared = history()
        seeds = [99, 100]
        audit = audit_seed_separation(seeds, declared)
        self.assertEqual(audit, audit_seed_separation(tuple(seeds), declared))
        self.assertEqual(audit['status'], 'disjoint_from_declared_history')
        self.assertEqual(audit['collisions'], [])
        self.assertEqual(audit['scope'], 'declared_sources_only')
        self.assertFalse(audit['statistical_independence_established'])
        self.assertEqual(audit['confirmation_status'], 'not_established')
        self.assertEqual(audit['history_sha256'], hashlib.sha256(_canonical(declared).encode()).hexdigest())
        self.assertEqual(audit['candidate_seeds_sha256'], hashlib.sha256(_canonical(seeds).encode()).hexdigest())
        self.assertIsNone(audit['history_file_sha256'])
        changed = deepcopy(declared)
        changed['sources'][0]['source_sha256'] = 'f'*64
        self.assertNotEqual(audit_seed_separation(seeds, changed)['history_sha256'], audit['history_sha256'])
        audit['history']['sources'][0]['seeds'].append(999)
        audit['candidate_seeds'].append(999)
        self.assertEqual(declared, history())
        self.assertEqual(seeds, [99, 100])
        normalized = validate_seed_history(declared)
        normalized['sources'].clear()
        self.assertEqual(declared, history())

    def test_invalid_history_and_candidates_are_rejected(self):
        original = history()
        invalid = [None, [], {}, {**original, 'extra': 1}, {**original, 'history_version': 'unknown'},
                   {**original, 'sources': []}, {**original, 'sources': 'source'},
                   {**original, 'sources': [None]},
                   {**original, 'sources': [original['sources'][0]]*2}]
        for key in original:
            changed = deepcopy(original)
            del changed[key]
            invalid.append(changed)
        for value in ('', ' padded ', None, 1):
            invalid.append({**original, 'history_id': value})
        for key in original['sources'][0]:
            changed = deepcopy(original)
            del changed['sources'][0][key]
            invalid.append(changed)
        fields = dict(source_id=('', ' padded ', None), purpose=('confirmation', None, [], {}),
                      source_sha256=('', 'G'*64, 'A'*64, 'a'*63, None, 42),
                      seeds=([], [True], [-1], [1.], [1, 1], [None], [[1]], '1'))
        for field, values in fields.items():
            for value in values:
                changed = deepcopy(original)
                changed['sources'][0][field] = value
                invalid.append(changed)
        changed = deepcopy(original)
        changed['sources'][0]['extra'] = 1
        invalid.append(changed)
        for declared in invalid:
            with self.subTest(history=declared), self.assertRaises(ValueError):
                validate_seed_history(declared)
        for seeds in (None, [], [True], [0, False], [-1], [1.], [1, 1], [None], [[1]], '1'):
            with self.subTest(seeds=seeds), self.assertRaises(ValueError):
                audit_seed_separation(seeds, original)

    def test_loader_rejects_ambiguous_json_and_separates_file_from_content_hash(self):
        original = history()
        hashes, audits = [], []
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'history.json'
            for payload in (_canonical(original), json.dumps(original, indent=4)):
                path.write_text(payload)
                restored, digest = load_seed_history(path)
                self.assertEqual(restored, original)
                self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
                hashes.append(digest)
                audits.append(audit_seed_separation([99], restored))
            self.assertNotEqual(hashes[0], hashes[1])
            self.assertEqual(audits[0], audits[1])
            for payload in ('{', 'null', '{"history_id":"a","history_id":"b"}',
                            _canonical(original).replace('"purpose":"sizing"', '"purpose":"sizing","purpose":"selection"'),
                            _canonical(original).replace('"seeds":[0,10]', '"seeds":[NaN]'),
                            _canonical(original).replace('"seeds":[0,10]', '"seeds":[Infinity]')):
                path.write_text(payload)
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    load_seed_history(path)

    def test_api_rejects_reused_seed_under_every_purpose_before_engine(self):
        for purpose in PURPOSES:
            declared = history()
            declared['sources'] = [dict(source_id='other-scenario', purpose=purpose,
                                        source_sha256='a'*64, seeds=[41])]
            with patch('numpy.random.default_rng', side_effect=AssertionError('RNG forbidden')), \
                 patch('study_weighted_autosomal_resolution.run_block_full') as engine:
                for operation in (preview_weighted_resolution_plan, run_weighted_resolution_plan):
                    with self.assertRaisesRegex(ValueError, r'seed history overlap: other-scenario: \[41\]'):
                        operation(plan(), seed_history=declared)
                    with self.assertRaises(ValueError):
                        operation(plan(), seed_history={})
                engine.assert_not_called()

    def test_disjoint_preview_needs_no_rng_and_binds_exact_normalized_plan(self):
        original = plan()
        declared = history()
        with patch('numpy.random.default_rng', side_effect=AssertionError('RNG forbidden')), \
             patch('study_weighted_autosomal_resolution.run_block_full', side_effect=AssertionError('engine forbidden')):
            checked = preview_weighted_resolution_plan(original, seed_history=declared)
            plain = preview_weighted_resolution_plan(original)
        audit = checked.pop('seed_audit')
        self.assertEqual(checked, plain)
        self.assertNotIn('seed_audit', plain)
        self.assertEqual(audit['study_plan_sha256'], plain['plan_sha256'])
        self.assertEqual(audit['candidate_seeds'], original['seeds'])
        declared['sources'][0]['seeds'].append(40)
        self.assertNotIn(40, audit['history']['sources'][0]['seeds'])

    def test_full_simulations_replay_and_equivalence_are_unchanged(self):
        original, declared = plan(), history()
        before = deepcopy((original, declared))
        checked = run_weighted_resolution_plan(original, seed_history=declared)
        plain = run_weighted_resolution_plan(original)
        replay = run_weighted_resolution_plan(checked['plan'], seed_history=checked['seed_audit']['history'])
        self.assertEqual(replay, checked)
        self.assertEqual((original, declared), before)
        self.assertEqual(checked['seed_audit'], checked['workload_preview']['seed_audit'])
        self.assertEqual(checked['seed_audit']['study_plan_sha256'], checked['plan_sha256'])
        rule = dict(criteria_version=CRITERIA_VERSION, criteria_id='technical-seed-test-only',
                    study_plan_sha256=plain['plan_sha256'], alpha=.05,
                    margins={metric: .4 for metric in METRICS}, max_interval_radius=.2)
        checked_assessment = assess_weighted_equivalence(rule, checked)
        plain_assessment = assess_weighted_equivalence(rule, plain)
        for key in ('comparisons', 'status', 'precision', 'convergence_status'):
            self.assertEqual(checked_assessment[key], plain_assessment[key])
        checked.pop('seed_audit')
        checked['workload_preview'].pop('seed_audit')
        self.assertEqual(checked, plain)
        self.assertEqual(checked['convergence_status'], 'not_established')
        self.assertEqual(checked['scientific_status'], 'exploratory_weighted_resolution_diagnostic')
        self.assertIn('autosomal_seed_history.py', checked['implementation_sha256'])

    def test_cli_rejects_invalid_or_conflicting_history_without_output_or_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path, history_path = root/'plan.json', root/'history.json'
            plan_path.write_text(json.dumps(plan()))
            collision = history()
            collision['sources'][0]['seeds'].append(41)
            for payload in (None, '{', '{}', json.dumps(collision)):
                if payload is not None:
                    history_path.write_text(payload)
                for preview in (False, True):
                    output = root/'output.json'
                    with patch('study_weighted_autosomal_resolution.run_block_full') as engine, \
                         patch('numpy.random.default_rng', side_effect=AssertionError('RNG forbidden')), \
                         redirect_stderr(io.StringIO()) as errors, self.assertRaises(SystemExit) as error:
                        main(['--plan', str(plan_path), '--seed-history', str(history_path),
                              '--output', str(output), *(['--preview'] if preview else [])])
                    self.assertEqual(error.exception.code, 1)
                    if payload == json.dumps(collision):
                        self.assertIn('seed history overlap', errors.getvalue())
                        self.assertIn('41', errors.getvalue())
                    engine.assert_not_called()
                    self.assertFalse(output.exists())

    def test_cli_archives_history_file_hash_replays_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path, history_path = root/'plan.json', root/'history.json'
            plan_path.write_text(json.dumps(plan(), indent=2))
            history_path.write_text(json.dumps(history(), indent=2))
            for preview in (False, True):
                output = root/f'{preview}.json'
                argv = [sys.executable, str(ROOT/'study_weighted_autosomal_resolution.py'),
                        '--plan', str(plan_path), '--seed-history', str(history_path),
                        '--output', str(output), *(['--preview'] if preview else [])]
                result = subprocess.run(argv, cwd=directory, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                document = json.loads(output.read_text())
                audit = document['seed_audit']
                self.assertEqual(audit['history_file_sha256'], hashlib.sha256(history_path.read_bytes()).hexdigest())
                self.assertEqual(audit['study_plan_sha256'], document['plan_sha256'])
                self.assertEqual(document['plan_file_sha256'], hashlib.sha256(plan_path.read_bytes()).hexdigest())
                operation = preview_weighted_resolution_plan if preview else run_weighted_resolution_plan
                expected = operation(document['plan'], seed_history=audit['history'])
                document['plan_file_sha256'] = None
                audit['history_file_sha256'] = None
                if not preview:
                    self.assertEqual(document['workload_preview']['seed_audit']['history_file_sha256'],
                                     hashlib.sha256(history_path.read_bytes()).hexdigest())
                    document['workload_preview']['plan_file_sha256'] = None
                    document['workload_preview']['seed_audit']['history_file_sha256'] = None
                self.assertEqual(document, expected)
                before = output.read_bytes()
                result = subprocess.run(argv, cwd=directory, capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(output.read_bytes(), before)
            dangling = root/'dangling.json'
            dangling.symlink_to(root/'missing.json')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main(['--plan', str(plan_path), '--seed-history', str(history_path), '--output', str(dangling)])
            self.assertEqual(error.exception.code, 2)

    def test_documented_example_executes_without_rng_or_engine(self):
        document = ROOT.parent/'docs/science/autosomal-seed-separation.md'
        example = document.read_text().split('```python\n', 1)[1].split('```', 1)[0]
        with patch('numpy.random.default_rng', side_effect=AssertionError('RNG forbidden')), \
             patch('study_weighted_autosomal_resolution.run_block_full', side_effect=AssertionError('engine forbidden')):
            exec(compile(example, str(document), 'exec'), {})


if __name__ == '__main__':
    unittest.main()
