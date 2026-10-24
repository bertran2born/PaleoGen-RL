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

from verify_provenance import REGISTRY_PATH, REPO_ROOT
from verify_sources import CATALOG_PATH, main, validate_catalog, verify_sources


class TestSources(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.catalog = json.loads((REPO_ROOT / CATALOG_PATH).read_text(encoding='utf-8'))
        self.registry = {'schema_version': '1', 'resources': []}
        # The validator must accept alternate content, rather than hard-code real hashes.
        for index, source in enumerate(self.catalog['sources']):
            content = f'Synthetic document {index}\n'.encode()
            path = self.root / source['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            source['sha256'] = hashlib.sha256(content).hexdigest()
            source['version']['content_id'] = 'sha256:' + source['sha256']
            self.registry['resources'].append({
                'path': source['path'], 'sha256': source['sha256'],
                'redistribution': {'status': 'not_established', 'basis': 'Synthetic fixture'},
            })

    def test_valid_deterministic_and_read_only(self):
        before = deepcopy((self.catalog, self.registry))
        contents = {s['path']: (self.root / s['path']).read_bytes()
                    for s in self.catalog['sources']}
        report = verify_sources(self.root, self.catalog, self.registry)
        self.assertTrue(report['ok'])
        self.assertEqual(report, verify_sources(self.root, self.catalog, self.registry))
        self.assertEqual(before, (self.catalog, self.registry))
        self.assertEqual(contents, {p: (self.root / p).read_bytes() for p in contents})

    def test_missing_modified_and_unchanged(self):
        sources = self.catalog['sources']
        (self.root / sources[0]['path']).unlink()
        (self.root / sources[1]['path']).write_bytes(b'changed')
        report = verify_sources(self.root, self.catalog, self.registry)
        self.assertFalse(report['ok'])
        self.assertEqual({r['id']: r['status'] for r in report['sources']}, {
            sources[0]['id']: 'missing', sources[1]['id']: 'modified',
            **{s['id']: 'ok' for s in sources[2:]},
        })

    def test_missing_duplicate_and_invalid_identity(self):
        variants = [None, {}, {'schema_version': '2', 'sources': []}]
        missing = deepcopy(self.catalog)
        missing['sources'].pop()
        variants.append(missing)
        duplicate = deepcopy(self.catalog)
        duplicate['sources'][1] = deepcopy(duplicate['sources'][0])
        variants.append(duplicate)
        unknown = deepcopy(self.catalog)
        unknown['sources'][1]['id'] = 'SI5'
        variants.append(unknown)
        for catalog in variants:
            with self.subTest(catalog=catalog), self.assertRaises(ValueError):
                validate_catalog(catalog, self.registry)

    def test_invalid_metadata_parent_version_and_evidence(self):
        variants = []
        for key, value in (
            ('path', '../outside.pdf'), ('path', self.catalog['sources'][0]['path']),
            ('title', ''), ('sha256', '0' * 64), ('parent_id', 'SI2'),
            ('publication_status', 'peer_reviewed'), ('version', None),
            ('identification', None),
        ):
            catalog = deepcopy(self.catalog)
            catalog['sources'][1][key] = value
            variants.append(catalog)
        for index, section, key, value in (
            (1, 'version', 'content_id', 'sha256:' + '0' * 64),
            (1, 'version', 'posted_date', '2026-10-13'),
            (1, 'version', 'label', 'v2'),
            (1, 'version', 'basis', ''),
            (0, 'version', 'posted_date', '2026-02-30'),
            (0, 'version', 'posted_date', None),
            (1, 'identification', 'page', 0),
            (1, 'identification', 'page', True),
            (1, 'identification', 'heading', ''),
            (0, 'identification', 'status_evidence', ''),
            (0, 'identification', 'date_evidence', ''),
        ):
            catalog = deepcopy(self.catalog)
            catalog['sources'][index][section][key] = value
            variants.append(catalog)
        for catalog in variants:
            with self.subTest(catalog=catalog), self.assertRaises(ValueError):
                validate_catalog(catalog, self.registry)

    def test_inventory_disagreement_and_missing_entry(self):
        registry = deepcopy(self.registry)
        registry['resources'].pop()
        with self.assertRaises(ValueError):
            validate_catalog(self.catalog, registry)
        registry = deepcopy(self.registry)
        registry['resources'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'sha256 mismatch'):
            validate_catalog(self.catalog, registry)

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            outside = Path(directory) / 'outside.pdf'
            outside.write_bytes(b'outside')
            path = self.root / self.catalog['sources'][0]['path']
            path.unlink()
            path.symlink_to(outside)
            report = verify_sources(self.root, self.catalog, self.registry)
            self.assertFalse(report['ok'])
            self.assertEqual(next(r['status'] for r in report['sources']
                                  if r['id'] == 'reich-preprint'), 'outside_root')

    def test_cli_exit_codes_and_no_rewrite(self):
        for relative, data in ((CATALOG_PATH, self.catalog), (REGISTRY_PATH, self.registry)):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data), encoding='utf-8')
        before = (self.root / CATALOG_PATH).read_bytes()

        def invoke():
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(['--root', str(self.root)])
            return code, json.loads(output.getvalue())

        self.assertEqual(invoke()[0], 0)
        (self.root / self.catalog['sources'][0]['path']).unlink()
        self.assertEqual(invoke()[0], 1)
        self.assertEqual((self.root / CATALOG_PATH).read_bytes(), before)
        (self.root / CATALOG_PATH).write_text('{invalid', encoding='utf-8')
        code, report = invoke()
        self.assertEqual(code, 1)
        self.assertEqual(report['status'], 'invalid_sources')

    def test_real_catalog_and_citation_evidence(self):
        catalog = json.loads((REPO_ROOT / CATALOG_PATH).read_text(encoding='utf-8'))
        registry = json.loads((REPO_ROOT / REGISTRY_PATH).read_text(encoding='utf-8'))
        sources = {s['id']: s for s in validate_catalog(catalog, registry)}
        self.assertTrue(verify_sources(REPO_ROOT, catalog, registry)['ok'])
        self.assertEqual(sources['reich-preprint']['doi'], '10.64898/2026.03.11.711219')
        self.assertEqual(sources['reich-preprint']['version']['posted_date'], '2026-10-13')
        for number, filename in enumerate(('media-1.pdf', 'media-3.pdf',
                                           'media-5.pdf', 'media-7.pdf'), 1):
            source = sources[f'SI{number}']
            self.assertEqual(source['path'], f'reich_study/{filename}')
            self.assertEqual(source['identification']['page'], 1)
            self.assertEqual(source['identification']['heading'],
                             f'Supplementary Information section {number}')
            self.assertIsNone(source['version']['posted_date'])
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / 'reich_experiment_v2/verify_sources.py')],
            cwd=self.root, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)['ok'])


if __name__ == '__main__':
    unittest.main()
