import contextlib
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from verify_provenance import (
    REFERENCE, REGISTRY_PATH, REPO_ROOT, main, resource_paths, sha256,
    validate_registry, verify,
)


class TestProvenance(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.paths = [REFERENCE, 'reich_study/example.zip',
                      'reich_experiment_v2/source/example.txt']
        for index, relative in enumerate(self.paths):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f'resource {index}\n'.encode())
        self.registry = {'schema_version': '1', 'resources': [
            {'path': p, 'sha256': hashlib.sha256(
                (self.root / p).read_bytes()).hexdigest(),
             'redistribution': {'status': 'not_established',
                                'basis': 'Synthetic test fixture'}}
            for p in self.paths
        ]}

    def test_pristine_and_read_only(self):
        before = {p: (self.root / p).read_bytes() for p in self.paths}
        registry_before = deepcopy(self.registry)
        first = verify(self.root, self.registry)
        self.assertTrue(first['ok'])
        self.assertEqual(first, verify(self.root, self.registry))
        self.assertEqual([r['path'] for r in first['resources']], sorted(self.paths))
        self.assertEqual(self.registry, registry_before)
        self.assertEqual(before, {p: (self.root / p).read_bytes() for p in self.paths})

    def test_missing_modified_and_unregistered(self):
        (self.root / self.paths[0]).unlink()
        (self.root / self.paths[1]).write_bytes(b'changed')
        new = 'reich_experiment_v2/source/new.py'
        (self.root / new).write_bytes(b'new')
        report = verify(self.root, self.registry)
        self.assertFalse(report['ok'])
        self.assertEqual({r['path']: r['status'] for r in report['resources']}, {
            self.paths[0]: 'missing', self.paths[1]: 'modified',
            self.paths[2]: 'ok', new: 'unregistered',
        })

    def test_cache_excluded_but_other_resources_included(self):
        for relative in ('reich_experiment_v2/source/__pycache__/cache.pyc',
                         'reich_experiment_v2/source/cache.pyo'):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'cache')
        self.assertEqual(resource_paths(self.root), set(self.paths))

    def test_invalid_registry(self):
        invalid = [None, [], {}, {'schema_version': '2', 'resources': []},
                   {'schema_version': '1', 'resources': []},
                   {'schema_version': '1', 'resources': [None]}]
        for field, value in (
            ('path', '/reich_study/example.zip'), ('path', '../example.zip'),
            ('path', 'reich_study/../../outside'),
            ('path', 'reich_study/./example.zip'),
            ('path', 'reich_study//example.zip'),
            ('path', 'results/example.csv'), ('path', None),
            ('sha256', 'bad'), ('sha256', '0' * 63), ('sha256', None),
            ('redistribution', None),
            ('redistribution', {'status': 'unknown', 'basis': 'unknown'}),
            ('redistribution', {'status': [], 'basis': 'unknown'}),
            ('redistribution', {'status': 'authorized', 'basis': ' '}),
        ):
            registry = deepcopy(self.registry)
            registry['resources'][0][field] = value
            invalid.append(registry)
        duplicate = deepcopy(self.registry)
        duplicate['resources'].append(deepcopy(duplicate['resources'][0]))
        invalid.append(duplicate)
        for registry in invalid:
            with self.subTest(registry=registry), self.assertRaises(ValueError):
                validate_registry(registry)

    def test_symlink_outside_root_is_not_hashed(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / 'external'
            target.write_bytes(b'external')
            path = self.root / self.paths[1]
            path.unlink()
            path.symlink_to(target)
            report = verify(self.root, self.registry)
            self.assertFalse(report['ok'])
            entry = next(r for r in report['resources'] if r['path'] == self.paths[1])
            self.assertEqual(entry['status'], 'outside_root')
            self.assertNotIn('actual_sha256', entry)

    def test_cli_exit_codes_and_no_registry_rewrite(self):
        registry_path = self.root / REGISTRY_PATH
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(json.dumps(self.registry), encoding='utf-8')
        original = registry_path.read_bytes()

        def invoke():
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(['--root', str(self.root)])
            return code, json.loads(output.getvalue())

        self.assertEqual(invoke()[0], 0)
        (self.root / self.paths[1]).write_bytes(b'changed')
        self.assertEqual(invoke()[0], 1)
        self.assertEqual(registry_path.read_bytes(), original)
        registry_path.write_text('{broken', encoding='utf-8')
        code, report = invoke()
        self.assertEqual(code, 1)
        self.assertEqual(report['status'], 'invalid_registry')

    def test_real_registry_coverage_integrity_and_policies(self):
        registry_path = REPO_ROOT / REGISTRY_PATH
        before = registry_path.read_bytes()
        registry = json.loads(before)
        resources = validate_registry(registry)
        self.assertEqual({r['path'] for r in resources}, resource_paths(REPO_ROOT))
        self.assertTrue(verify(REPO_ROOT, registry)['ok'])
        for entry in resources:
            with self.subTest(path=entry['path']):
                self.assertEqual(entry['redistribution']['status'], 'not_established')
                self.assertTrue(entry['redistribution']['basis'].strip())
                # Independently verify the stored hash, without the helper.
                self.assertEqual(entry['sha256'], hashlib.sha256(
                    (REPO_ROOT / entry['path']).read_bytes()).hexdigest())
        self.assertEqual(before, registry_path.read_bytes())

    def test_real_cli_from_another_working_directory(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / 'reich_experiment_v2/verify_provenance.py')],
            cwd=self.root, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(json.loads(result.stdout)['ok'])


if __name__ == '__main__':
    unittest.main()
