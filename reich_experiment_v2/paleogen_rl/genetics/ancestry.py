"""Measure total ancestry on an explicit, equally weighted diploid block panel.

This module does not simulate inheritance, choose a resolution, or replace the
legacy neutral-locus proxy. Partner annotations never redefine the total panel.
"""

from dataclasses import dataclass

import numpy as np


MEASUREMENT_VERSION = 'autosomal-block-measurement-v1'


def _identifiers(values, field, *, allow_empty=False):
    if not isinstance(values, (list, tuple)):
        raise ValueError(f'{field} must be a list or tuple of identifiers')
    result = tuple(values)
    if not result and not allow_empty:
        raise ValueError(f'{field} must not be empty')
    if any(not isinstance(item, str) or not item or item != item.strip() for item in result):
        raise ValueError(f'{field} must contain nonempty, trimmed string identifiers')
    if len(set(result)) != len(result):
        raise ValueError(f'{field} must contain unique identifiers')
    return result


@dataclass(frozen=True)
class BlockPanel:
    """Column order and identity of an equal-weight measurement panel.

    An identifier is a caller declaration, not proof of genomic calibration.
    A caller-provided list is copied to an immutable tuple.
    """

    panel_id: str
    block_ids: tuple[str, ...]

    def __post_init__(self):
        _identifiers((self.panel_id,), 'panel_id')
        object.__setattr__(self, 'block_ids', _identifiers(self.block_ids, 'block_ids'))


def measure_ancestry(modern_copies, panel, *, generation, target_generation,
                     mode, partner_block_ids=()):
    """Return a JSON-compatible final measurement or explicit quick unavailability.

    modern_copies has shape (diploid individuals, declared blocks), with integer
    entries 0/1/2. Every declared block contributes to the total, including any
    annotated partner. All inconsistencies raise ValueError. An evaluated result
    requires an explicitly final state; this function cannot prove its provenance.
    """
    if not isinstance(panel, BlockPanel):
        raise ValueError('panel must be a BlockPanel')
    if mode not in ('quick', 'full', 'adaptive'):
        raise ValueError('mode must be quick/full/adaptive')
    for name, value in (('generation', generation), ('target_generation', target_generation)):
        if type(value) is not int or value < 0:
            raise ValueError(f'{name} must be a nonnegative integer')
    if generation > target_generation:
        raise ValueError('generation exceeds target_generation')
    if mode != 'quick' and generation != target_generation:
        raise ValueError('evaluated ancestry requires generation == target_generation')
    partners = _identifiers(partner_block_ids, 'partner_block_ids', allow_empty=True)
    if not set(partners) <= set(panel.block_ids):
        raise ValueError('partner_block_ids must belong to the declared panel')
    # Canonical panel order, independent of the order of partner declarations.
    partner_set = set(partners)
    partners = [block for block in panel.block_ids if block in partner_set]
    if np.ma.isMaskedArray(modern_copies) and np.any(np.ma.getmaskarray(modern_copies)):
        raise ValueError('modern_copies must not contain masked or missing values')
    counts = np.asarray(modern_copies)
    if counts.ndim != 2 or counts.shape[0] == 0 or counts.shape[1] != len(panel.block_ids):
        raise ValueError('modern_copies must have shape (N > 0, panel block count)')
    if counts.dtype.kind not in ('i', 'u') or np.any((counts < 0) | (counts > 2)):
        raise ValueError('modern_copies must contain integer diploid copy counts in [0, 2]')
    population = int(counts.shape[0])
    result = dict(
        measurement_version=MEASUREMENT_VERSION,
        observable='total_diploid_block_ancestry',
        panel=dict(panel_id=panel.panel_id, block_ids=list(panel.block_ids),
                   block_count=len(panel.block_ids), weighting='equal_diploid_copies'),
        generation=generation, target_generation=target_generation, mode=mode,
        status='not_evaluated_quick' if mode == 'quick' else 'evaluated_at_target',
        diploid_individuals=population,
        allele_copy_denominator=2 * population * len(panel.block_ids),
        modern_allele_copies=None, value=None,
        partner_block_ids=partners, partner_diagnostics=None,
    )
    if mode == 'quick':
        return result
    modern = int(counts.sum(dtype=np.int64))
    result.update(modern_allele_copies=modern,
                  value=modern / result['allele_copy_denominator'])
    columns = {block: column for column, block in enumerate(panel.block_ids)}
    diagnostics = []
    for block in partners:
        block_modern = int(counts[:, columns[block]].sum(dtype=np.int64))
        diagnostics.append(dict(block_id=block, modern_allele_copies=block_modern,
                                allele_copy_denominator=2 * population,
                                value=block_modern / (2 * population)))
    result['partner_diagnostics'] = diagnostics
    return result
