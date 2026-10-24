import contextlib
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from export_public import DOCUMENT_PATHS, MANIFEST_NAME, export_public, main
from verify_provenance import REGISTRY_PATH, REPO_ROOT


class TestPublicExport(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.root = self.directory / 'repo'
        for relative in DOCUMENT_PATHS:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((REPO_ROOT / relative).read_bytes())
        self.registry = json.loads((self.root / REGISTRY_PATH).read_text(encoding='utf-8'))
        self.output = self.directory / 'public.zip'

    def write_registry(self):
        (self.root / REGISTRY_PATH).write_text(json.dumps(self.registry), encoding='utf-8')

    def resource(self, name, status, content=b'synthetic authorized content'):
        relative = 'reich_experiment_v2/source/' + name
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        self.registry['resources'].append({
            'path': relative, 'sha256': hashlib.sha256(content).hexdigest(),
            'redistribution': {'status': status, 'basis': 'Synthetic test fixture only'},
        })
        self.write_registry()
        return relative

    def assert_archive_consistent(self, archive_path):
        with zipfile.ZipFile(archive_path) as archive:
            manifest = json.loads(archive.read(MANIFEST_NAME))
            included = {entry['path']: entry for entry in manifest['included']}
            self.assertEqual(set(archive.namelist()), set(included) | {MANIFEST_NAME})
            self.assertEqual(len(archive.namelist()), len(set(archive.namelist())))
            for relative, entry in included.items():
                self.assertEqual(hashlib.sha256(archive.read(relative)).hexdigest(), entry['sha256'])
                self.assertFalse(Path(relative).is_absolute())
                self.assertNotIn('..', Path(relative).parts)
            for entry in manifest['excluded']:
                self.assertNotIn(entry['path'], archive.namelist())
            return manifest

    def test_only_authorized_resources_and_explicit_documents_included(self):
        authorized = self.resource('authorized.txt', 'authorized')
        unknown = self.resource('unknown.txt', 'not_established', b'PRIVATE UNKNOWN PAYLOAD')
        denied = self.resource('denied.txt', 'not_authorized', b'PRIVATE DENIED PAYLOAD')
        unregistered = 'reich_study/unregistered.dat'
        path = self.root / unregistered
        path.parent.mkdir(parents=True)
        path.write_bytes(b'PRIVATE UNREGISTERED PAYLOAD')
        for relative in ('.aws/credentials', '.git/config', 'unexpected.txt',
                         'reich_experiment_v2/results/example.csv',
                         'reich_experiment_v2/source/__pycache__/example.pyc'):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'PRIVATE OUT OF SELECTION')
        export_public(self.root, self.output)
        manifest = self.assert_archive_consistent(self.output)
        self.assertEqual({e['path'] for e in manifest['included']}, set(DOCUMENT_PATHS) | {authorized})
        excluded = {e['path']: e['reason'] for e in manifest['excluded']}
        self.assertEqual(excluded[unknown], 'not_established')
        self.assertEqual(excluded[denied], 'not_authorized')
        self.assertEqual(excluded[unregistered], 'not_inventoried')
        with zipfile.ZipFile(self.output) as archive:
            contents = b''.join(archive.read(name) for name in archive.namelist())
            self.assertNotIn(b'PRIVATE', contents)

    def test_excluded_resources_need_not_exist_or_be_read(self):
        relative = self.resource('never-read.txt', 'not_authorized')
        read_bytes = Path.read_bytes

        def guard(path):
            if path.is_relative_to(self.root) and path.relative_to(self.root).as_posix() not in DOCUMENT_PATHS:
                raise AssertionError('excluded contents must not be opened')
            return read_bytes(path)

        before = {p: (self.root / p).read_bytes() for p in DOCUMENT_PATHS}
        with patch.object(Path, 'read_bytes', guard), patch(
                'socket.socket', side_effect=AssertionError('network forbidden')):
            manifest = export_public(self.root, self.output)
        self.assertIn(relative, {e['path'] for e in manifest['excluded']})
        self.assertEqual(before, {p: (self.root / p).read_bytes() for p in DOCUMENT_PATHS})
        # All 32 real resources are absent from this fixture and remain excluded.
        self.assertEqual(len(manifest['excluded']), 33)

    def test_missing_or_modified_authorized_file_fails_before_output(self):
        for name, missing in (('missing.txt', True), ('modified.txt', False)):
            relative = self.resource(name, 'authorized')
            path = self.root / relative
            if missing:
                path.unlink()
            else:
                path.write_bytes(b'modified')
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                export_public(self.root, self.output)
            self.assertFalse(self.output.exists())
            # Restore this resource so the next case reaches its own failure.
            path.write_bytes(b'synthetic authorized content')

    def test_invalid_registry_and_contract_fail_before_output(self):
        baseline = deepcopy(self.registry)
        self.registry['resources'][0]['redistribution']['status'] = 'unknown'
        self.write_registry()
        with self.assertRaises(ValueError):
            export_public(self.root, self.output)
        self.assertFalse(self.output.exists())
        self.registry = baseline
        self.write_registry()
        path = self.root / 'docs/science/observations.json'
        contract = json.loads(path.read_text(encoding='utf-8'))
        contract['schema_version'] = 'unsupported'
        path.write_text(json.dumps(contract), encoding='utf-8')
        with self.assertRaises(ValueError):
            export_public(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_selected_file_symlink_rejected(self):
        relative = self.resource('alias.txt', 'authorized')
        path = self.root / relative
        target = self.directory / 'payload.txt'
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'symbolic link'):
            export_public(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_document_symlink_rejected(self):
        path = self.root / DOCUMENT_PATHS[0]
        target = self.directory / 'document.json'
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'symbolic link'):
            export_public(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_parent_directory_symlink_rejected(self):
        self.resource('nested/resource.txt', 'authorized')
        directory = self.root / 'reich_experiment_v2/source/nested'
        target = self.directory / 'moved'
        directory.rename(target)
        directory.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symbolic link'):
            export_public(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_destination_preserved_and_original_directories_protected(self):
        self.output.write_bytes(b'previous archive')
        with self.assertRaises(FileExistsError):
            export_public(self.root, self.output)
        self.assertEqual(self.output.read_bytes(), b'previous archive')
        for relative in ('reich_study/new.zip', 'reich_experiment_v2/source/new.zip'):
            destination = self.root / relative
            with self.subTest(path=relative), self.assertRaisesRegex(ValueError, 'outside original'):
                export_public(self.root, destination)
            self.assertFalse(destination.exists())

    def test_reproducible_zip_and_manifest_hashes(self):
        relative = self.resource('reproducible.txt', 'authorized')
        export_public(self.root, self.output)
        for path in [self.root / p for p in (*DOCUMENT_PATHS, relative)]:
            os.utime(path, (1700000000, 1700000000))
            path.chmod(0o600)
        other = self.directory / 'second.zip'
        export_public(self.root, other)
        self.assertEqual(hashlib.sha256(self.output.read_bytes()).hexdigest(),
                         hashlib.sha256(other.read_bytes()).hexdigest())
        self.assert_archive_consistent(self.output)
        with zipfile.ZipFile(self.output) as archive:
            for info in archive.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.external_attr >> 16, 0o100644)

    def test_failed_destination_write_removes_partial_archive(self):
        with patch('export_public.shutil.copyfileobj', side_effect=OSError('synthetic write failure')):
            with self.assertRaises(OSError):
                export_public(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_cli_success_and_failure(self):
        def invoke():
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(['--root', str(self.root), '--output', str(self.output)])
            return code, json.loads(output.getvalue())
        code, report = invoke()
        self.assertEqual(code, 0)
        self.assertTrue(report['ok'])
        before = self.output.read_bytes()
        code, report = invoke()
        self.assertEqual(code, 1)
        self.assertEqual(report['status'], 'export_failed')
        self.assertEqual(before, self.output.read_bytes())

    def test_real_repository_export_and_cli_from_other_directory(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / 'reich_experiment_v2/export_public.py'),
             '--output', str(self.output)], cwd=self.directory,
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['included_count'], 5)
        self.assertEqual(report['excluded_count'], 32)
        manifest = self.assert_archive_consistent(self.output)
        self.assertEqual({r['path'] for r in manifest['included']}, set(DOCUMENT_PATHS))
        self.assertTrue(all(e['reason'] == 'not_established' for e in manifest['excluded']))


if __name__ == '__main__':
    unittest.main()
