"""Check the local resource inventory without updating it or using the network."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = Path('docs/science/provenance.json')
RESOURCE_DIRS = ('reich_study', 'reich_experiment_v2/source')
REFERENCE = 'reich_experiment_v2/src/reich_panmictic_original.py'
POLICIES = {'authorized', 'not_authorized', 'not_established'}


def in_scope(path):
    parts = PurePosixPath(path).parts
    return (
        path == REFERENCE or any(path.startswith(d + '/') for d in RESOURCE_DIRS)
    ) and '__pycache__' not in parts and not path.endswith(('.pyc', '.pyo'))


def resource_paths(root):
    """Discover resources independently of the registry, including new files."""
    paths = {REFERENCE}  # A missing reference must still be reported.
    for directory in RESOURCE_DIRS:
        for path in (root / directory).rglob('*'):
            relative = path.relative_to(root).as_posix()
            if (path.is_file() or path.is_symlink()) and in_scope(relative):
                paths.add(relative)
    return paths


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_registry(registry):
    if not isinstance(registry, dict) or registry.get('schema_version') != '1':
        raise ValueError('unsupported schema_version (expected "1")')
    resources = registry.get('resources')
    if not isinstance(resources, list) or not resources:
        raise ValueError('resources must be a nonempty list')
    seen = set()
    for entry in resources:
        if not isinstance(entry, dict):
            raise ValueError('resource must be an object')
        path = entry.get('path')
        if (not isinstance(path, str) or not path
                or PurePosixPath(path).is_absolute()
                or '..' in PurePosixPath(path).parts
                or PurePosixPath(path).as_posix() != path
                or not in_scope(path)):
            raise ValueError(f'invalid resource path: {path!r}')
        if path in seen:
            raise ValueError(f'duplicate resource path: {path}')
        seen.add(path)
        digest = entry.get('sha256')
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError(f'invalid sha256: {path}')
        policy = entry.get('redistribution')
        if (not isinstance(policy, dict)
                or not isinstance(policy.get('status'), str)
                or policy['status'] not in POLICIES
                or not isinstance(policy.get('basis'), str)
                or not policy['basis'].strip()):
            raise ValueError(f'invalid redistribution policy: {path}')
    return resources


def verify(root, registry):
    """Return a deterministic report; an integrity success grants no rights."""
    root = Path(root).resolve()
    entries = {e['path']: e for e in validate_registry(registry)}
    results = []
    for relative in sorted(resource_paths(root) | entries.keys()):
        path = root / relative
        result = {'path': relative}
        if not path.resolve().is_relative_to(root):
            result['status'] = 'outside_root'
        elif relative not in entries:
            result['status'] = 'unregistered'
        else:
            result['expected_sha256'] = entries[relative]['sha256']
            try:
                result['actual_sha256'] = sha256(path)
                result['status'] = (
                    'ok' if result['actual_sha256'] == result['expected_sha256']
                    else 'modified'
                )
            except FileNotFoundError:
                result['status'] = 'missing'
            except OSError as error:
                result.update(status='unreadable', error=str(error))
        results.append(result)
    return {'schema_version': '1', 'ok': all(r['status'] == 'ok' for r in results),
            'resources': results}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=REPO_ROOT,
                        help='Repository root (defaults to the script location)')
    parser.add_argument('--registry', type=Path,
                        help='Registry JSON (defaults to ROOT/docs/science/provenance.json)')
    args = parser.parse_args(argv)
    try:
        registry_path = args.registry or args.root / REGISTRY_PATH
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        report = verify(args.root, registry)
    except (OSError, ValueError) as error:
        report = {'schema_version': '1', 'ok': False,
                  'status': 'invalid_registry', 'error': str(error)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
