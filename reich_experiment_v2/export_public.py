"""Build a local scientific-documentation ZIP, filtering external resource rights."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import zipfile

from science_contract import CONTRACT_PATH, validate_contract
from verify_provenance import (
    REFERENCE, REGISTRY_PATH, REPO_ROOT, RESOURCE_DIRS, resource_paths, validate_registry,
)
from verify_sources import CATALOG_PATH


DOCUMENT_PATHS = (
    'docs/science/observations.json',
    'docs/science/observations.md',
    'docs/science/provenance.json',
    'docs/science/provenance.md',
    'docs/science/sources.json',
)
MANIFEST_NAME = 'export_manifest.json'


def regular_bytes(root, relative):
    """Read an explicitly selected regular file, rejecting symbolic-link aliases."""
    if (not isinstance(relative, str) or '\\' in relative or '\x00' in relative
            or PurePosixPath(relative).is_absolute()
            or '..' in PurePosixPath(relative).parts
            or PurePosixPath(relative).as_posix() != relative):
        raise ValueError('invalid export path')
    path = root / relative
    for component in (path, *path.parents):
        if component == root:
            break
        if component.is_symlink():
            raise ValueError(f'symbolic link in selected path: {relative}')
    if not path.is_file():
        raise ValueError(f'selected regular file missing: {relative}')
    return path.read_bytes()


def export_public(root, output):
    """Validate before creating the destination; copy only approved, hashed bytes."""
    root = Path(root).resolve()
    output = Path(output).absolute()
    resolved_output = output.resolve()
    for directory in RESOURCE_DIRS:
        if (resolved_output.is_relative_to(root / directory)
                or resolved_output.is_relative_to((root / directory).resolve())):
            raise ValueError('output must be outside original resource directories')
    if resolved_output == root / REFERENCE:
        raise ValueError('output must not replace the reference engine')
    if output.exists() or output.is_symlink():
        raise FileExistsError('output already exists')

    payload = {path: regular_bytes(root, path) for path in DOCUMENT_PATHS}
    registry = json.loads(payload[REGISTRY_PATH.as_posix()])
    entries = {e['path']: e for e in validate_registry(registry)}
    validate_contract(json.loads(payload[CONTRACT_PATH.as_posix()]),
                      json.loads(payload[CATALOG_PATH.as_posix()]), registry)
    included = []
    excluded = []
    for path in sorted(resource_paths(root) | entries.keys()):
        entry = entries.get(path)
        if entry is None:
            excluded.append({'path': path, 'reason': 'not_inventoried'})
            continue
        policy = entry['redistribution']
        if policy['status'] != 'authorized':
            excluded.append({'path': path, 'sha256': entry['sha256'],
                             'reason': policy['status'], 'basis': policy['basis']})
            continue
        content = regular_bytes(root, path)
        if hashlib.sha256(content).hexdigest() != entry['sha256']:
            raise ValueError(f'authorized resource sha256 mismatch: {path}')
        payload[path] = content
    for path, content in sorted(payload.items()):
        record = {'path': path, 'sha256': hashlib.sha256(content).hexdigest()}
        if path in DOCUMENT_PATHS:
            record['reason'] = 'scientific_contract_document'
        else:
            record.update(reason='authorized', basis=entries[path]['redistribution']['basis'])
        included.append(record)
    manifest = {
        'schema_version': '1', 'export_kind': 'scientific_contract_and_resources',
        'contract_version': json.loads(payload[CONTRACT_PATH.as_posix()])['contract_version'],
        'limitations': 'Documentation bundle; not an executable v0.1 release or a publication.',
        'included': included, 'excluded': excluded,
    }
    payload[MANIFEST_NAME] = (json.dumps(manifest, ensure_ascii=False, indent=2,
                                         sort_keys=True) + '\n').encode('utf-8')
    # Build completely before creating the destination. Timestamps, modes and order
    # are fixed; the bytes hashed above are the same bytes passed to the archive.
    with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as staging:
        with zipfile.ZipFile(staging, 'w', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=9) as archive:
            for path, content in sorted(payload.items()):
                info = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, content, compresslevel=9)
        staging.seek(0)
        # Exclusive creation also prevents overwriting a destination created while
        # validation was running. Parent directories must already exist.
        stream = output.open('xb')
        try:
            with stream:
                shutil.copyfileobj(staging, stream)
        except BaseException:
            output.unlink()
            raise
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=REPO_ROOT)
    parser.add_argument('--output', type=Path, required=True,
                        help='New local ZIP path; parent directory must exist')
    args = parser.parse_args(argv)
    try:
        manifest = export_public(args.root, args.output)
        report = {'schema_version': '1', 'ok': True,
                  'included_count': len(manifest['included']),
                  'excluded_count': len(manifest['excluded'])}
    except (OSError, ValueError, RuntimeError) as error:
        report = {'schema_version': '1', 'ok': False,
                  'status': 'export_failed', 'error': str(error)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
