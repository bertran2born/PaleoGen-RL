"""Validate locally identified scientific sources against the resource inventory."""

import argparse
from datetime import date
import json
from pathlib import Path
import re

from verify_provenance import REPO_ROOT, REGISTRY_PATH, sha256, validate_registry


CATALOG_PATH = Path('docs/science/sources.json')
PREPRINT_ID = 'reich-preprint'
SOURCE_IDS = {PREPRINT_ID, 'SI1', 'SI2', 'SI3', 'SI4'}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate_catalog(catalog, registry):
    """Validate bibliographic declarations, not the scientific claims in the PDFs."""
    inventory = {r['path']: r for r in validate_registry(registry)}
    if not isinstance(catalog, dict) or catalog.get('schema_version') != '1':
        raise ValueError('unsupported source schema_version (expected "1")')
    sources = catalog.get('sources')
    if not isinstance(sources, list) or len(sources) != len(SOURCE_IDS):
        raise ValueError('expected the preprint and SI1–SI4')
    ids, paths = set(), set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError('source must be an object')
        identity, path = source.get('id'), source.get('path')
        if not isinstance(identity, str) or identity not in SOURCE_IDS or identity in ids:
            raise ValueError('invalid or duplicate source id')
        ids.add(identity)
        if (not isinstance(path, str) or path not in inventory
                or not path.startswith('reich_study/') or not path.endswith('.pdf')
                or path in paths):
            raise ValueError(f'invalid or duplicate source path: {identity}')
        paths.add(path)
        if not nonempty(source.get('title')):
            raise ValueError(f'missing title: {identity}')
        if source.get('sha256') != inventory[path]['sha256']:
            raise ValueError(f'catalog/inventory sha256 mismatch: {identity}')
        if source.get('publication_status') != 'preprint_not_peer_reviewed':
            raise ValueError(f'invalid publication_status: {identity}')
        preprint = identity == PREPRINT_ID
        if ('parent_id' not in source
                or source['parent_id'] != (None if preprint else PREPRINT_ID)):
            raise ValueError(f'invalid parent_id: {identity}')
        version = source.get('version')
        if (not isinstance(version, dict)
                or version.get('content_id') != 'sha256:' + source['sha256']
                or not nonempty(version.get('basis'))
                or version.get('label') != ('v2' if preprint else 'local_content_version')
                or 'posted_date' not in version):
            raise ValueError(f'invalid content version: {identity}')
        if preprint:
            posted = version['posted_date']
            if not isinstance(posted, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', posted):
                raise ValueError('invalid preprint posted_date')
            date.fromisoformat(posted)
            doi = source.get('doi')
            if not isinstance(doi, str) or not re.fullmatch(r'10\.\d{4,9}/\S+', doi):
                raise ValueError('invalid preprint DOI')
        elif version['posted_date'] is not None:
            raise ValueError(f'standalone supplement date not established: {identity}')
        evidence = source.get('identification')
        if (not isinstance(evidence, dict)
                or type(evidence.get('page')) is not int or evidence['page'] < 1
                or not nonempty(evidence.get('heading'))
                or evidence.get('method') != 'local_pdf_text_review'):
            raise ValueError(f'invalid identification evidence: {identity}')
        if preprint and any(not nonempty(evidence.get(key))
                            for key in ('status_evidence', 'date_evidence')):
            raise ValueError('missing preprint status/date evidence')
    return sources


def verify_sources(root, catalog, registry):
    root = Path(root).resolve()
    sources = validate_catalog(catalog, registry)
    results = []
    for source in sorted(sources, key=lambda source: source['id']):
        path = root / source['path']
        result = {'id': source['id'], 'path': source['path']}
        if not path.resolve().is_relative_to(root):
            result['status'] = 'outside_root'
        else:
            try:
                actual = sha256(path)
                result.update(actual_sha256=actual,
                              status='ok' if actual == source['sha256'] else 'modified')
            except FileNotFoundError:
                result['status'] = 'missing'
            except OSError as error:
                result.update(status='unreadable', error=str(error))
        results.append(result)
    return {'schema_version': '1', 'ok': all(r['status'] == 'ok' for r in results),
            'sources': results}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    try:
        catalog = json.loads((args.root / CATALOG_PATH).read_text(encoding='utf-8'))
        registry = json.loads((args.root / REGISTRY_PATH).read_text(encoding='utf-8'))
        report = verify_sources(args.root, catalog, registry)
    except (ValueError, OSError) as error:
        report = {'schema_version': '1', 'ok': False,
                  'status': 'invalid_sources', 'error': str(error)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
