"""Declared seed separation, without claims of statistical independence or acceptance."""

import hashlib
import json
from pathlib import Path

from paleogen_rl.genetics.protocol import _canonical, _keys, _unique_fields
from paleogen_rl.genetics.weighted_protocol import _reject_constant


HISTORY_VERSION = 'autosomal-seed-history-v1'
AUDIT_VERSION = 'autosomal-seed-separation-v1'
PURPOSES = ('sizing', 'selection', 'exploration', 'engineering')


def _identity(value, field):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f'{field} must be a nonempty trimmed string')
    return value


def _seeds(values, field):
    if (not isinstance(values, (tuple, list)) or not values
            or any(type(seed) is not int or seed < 0 for seed in values)
            or len(set(values)) != len(values)):
        raise ValueError(f'{field} must contain distinct nonnegative integer seeds')
    return list(values)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode('utf-8')).hexdigest()


def validate_seed_history(history):
    """Return an owned declaration; source hashes are references, not authentication."""
    _keys(history, ('history_version', 'history_id', 'sources'), 'seed history')
    if history['history_version'] != HISTORY_VERSION:
        raise ValueError('unsupported seed history version')
    identity = _identity(history['history_id'], 'history_id')
    sources = history['sources']
    if not isinstance(sources, (tuple, list)) or not sources:
        raise ValueError('seed history sources must be nonempty')
    normalized, seen = [], set()
    for source in sources:
        _keys(source, ('source_id', 'purpose', 'source_sha256', 'seeds'), 'seed history source')
        source_id = _identity(source['source_id'], 'source_id')
        if source_id in seen:
            raise ValueError(f'duplicate seed history source_id: {source_id}')
        seen.add(source_id)
        if source['purpose'] not in PURPOSES:
            raise ValueError(f'seed history purpose must be one of {", ".join(PURPOSES)}')
        digest = source['source_sha256']
        if (not isinstance(digest, str) or len(digest) != 64
                or any(character not in '0123456789abcdef' for character in digest)):
            raise ValueError('source_sha256 must be a lowercase SHA-256 digest')
        normalized.append(dict(source_id=source_id, purpose=source['purpose'], source_sha256=digest,
                               seeds=_seeds(source['seeds'], f'{source_id} seeds')))
    return dict(history_version=HISTORY_VERSION, history_id=identity, sources=normalized)


def load_seed_history(path):
    payload = Path(path).read_bytes()
    history = json.loads(payload, object_pairs_hook=_unique_fields, parse_constant=_reject_constant)
    return validate_seed_history(history), hashlib.sha256(payload).hexdigest()


def audit_seed_separation(seeds, history):
    """Compare against every declared source, irrespective of scenario or purpose.

    Disjoint integer seeds alone do not prove independent data, exhaustive
    history or temporal preregistration. No source file is opened by this API.
    """
    candidates = _seeds(seeds, 'candidate seeds')
    history = validate_seed_history(history)
    candidate_set = set(candidates)
    excluded, collisions = set(), []
    for source in history['sources']:
        excluded.update(source['seeds'])
        shared = sorted(candidate_set.intersection(source['seeds']))
        if shared:
            collisions.append(dict(source_id=source['source_id'], purpose=source['purpose'],
                                   source_sha256=source['source_sha256'], seeds=shared))
    return dict(audit_version=AUDIT_VERSION,
                status='overlap_detected' if collisions else 'disjoint_from_declared_history',
                candidate_seeds=candidates, candidate_seeds_sha256=_digest(candidates),
                history=history, history_sha256=_digest(history), history_file_sha256=None,
                excluded_seed_count=len(excluded), collisions=collisions,
                scope='declared_sources_only', statistical_independence_established=False,
                confirmation_status='not_established')
