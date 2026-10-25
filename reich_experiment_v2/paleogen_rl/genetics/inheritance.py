"""Phased block inheritance with explicitly declared boundary switch fractions.

This transmission primitive does not sample parents, apply selection, or change
the legacy M2 engine. A caller owns the RNG and all population-level decisions.
"""

from dataclasses import dataclass
from numbers import Real

import numpy as np

from .ancestry import BlockPanel


INHERITANCE_VERSION = 'autosomal-block-inheritance-v1'


@dataclass(frozen=True)
class RecombinationMap:
    """Independent homologue-switch probabilities in the panel's block order."""

    panel: BlockPanel
    switch_probabilities: tuple[float, ...]

    def __post_init__(self):
        if not isinstance(self.panel, BlockPanel):
            raise ValueError('panel must be a BlockPanel')
        if not isinstance(self.switch_probabilities, (list, tuple)):
            raise ValueError('switch_probabilities must be a list or tuple')
        if len(self.switch_probabilities) != len(self.panel.block_ids) - 1:
            raise ValueError('one switch probability is required per adjacent block boundary')
        probabilities = []
        for value in self.switch_probabilities:
            if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
                    or not np.isfinite(value) or not 0 <= value <= .5):
                raise ValueError('switch probabilities must be finite numbers in [0, 0.5]')
            probabilities.append(float(value))
        object.__setattr__(self, 'switch_probabilities', tuple(probabilities))

    def to_dict(self):
        """A full, JSON-compatible model declaration, not a calibrated genome map."""
        return dict(inheritance_version=INHERITANCE_VERSION,
                    model='independent_boundary_switches',
                    panel=dict(panel_id=self.panel.panel_id, block_ids=list(self.panel.block_ids)),
                    switch_probabilities=list(self.switch_probabilities),
                    initial_homologue_probability=.5, within_block_recombination=False,
                    offspring_homologue_order=['maternal', 'paternal'])


def _haplotypes(values):
    if np.ma.isMaskedArray(values) and np.any(np.ma.getmaskarray(values)):
        raise ValueError('haplotypes must not contain masked values')
    array = np.asarray(values)
    if array.ndim != 3 or array.shape[0] == 0 or array.shape[1] != 2 or array.shape[2] == 0:
        raise ValueError('haplotypes must have shape (N > 0, 2, B > 0)')
    if array.dtype.kind not in ('b', 'i', 'u') or np.any((array != 0) & (array != 1)):
        raise ValueError('haplotypes must contain binary allele indicators')
    return array


def copy_counts(haplotypes):
    """Project phase onto integer diploid counts accepted by the I11 measure."""
    return _haplotypes(haplotypes).sum(axis=1, dtype=np.uint8)


def _parent_indices(values, population, name):
    if np.ma.isMaskedArray(values) and np.any(np.ma.getmaskarray(values)):
        raise ValueError(f'{name} must not contain masked indices')
    indices = np.asarray(values)
    if indices.ndim != 1 or indices.size == 0:
        raise ValueError(f'{name} must be a nonempty vector of parent indices')
    if (indices.dtype.kind not in ('i', 'u')
            or np.any((indices < 0) | (indices >= population))):
        raise ValueError(f'{name} must contain integer indices into the parental population')
    return indices


def _gametes(haplotypes, parents, recombination_map, rng):
    children, blocks = parents.size, len(recombination_map.panel.block_ids)
    homologues = np.empty((children, blocks), dtype=np.uint8)
    homologues[:, 0] = rng.integers(0, 2, size=children, dtype=np.uint8)
    if blocks > 1:
        switches = rng.random((children, blocks - 1)) < recombination_map.switch_probabilities
        parity = np.logical_xor.accumulate(switches, axis=1)
        homologues[:, 1:] = homologues[:, :1] ^ parity
    return haplotypes[parents[:, None], homologues, np.arange(blocks)[None, :]]


def inherit_diploid(haplotypes, *, mothers, fathers, recombination_map, rng):
    """Transmit one maternal and one paternal gamete to each declared child.

    Validate all declarations before consuming randomness. Output has shape
    (children, 2, B), dtype uint8, and does not share storage with the parents.
    The caller must enforce parent sexes and eligibility before calling.
    """
    if not isinstance(recombination_map, RecombinationMap):
        raise ValueError('recombination_map must be a RecombinationMap')
    if not isinstance(rng, np.random.Generator):
        raise ValueError('rng must be a caller-owned numpy Generator')
    population = _haplotypes(haplotypes)
    if population.shape[2] != len(recombination_map.panel.block_ids):
        raise ValueError('haplotypes must follow the declared panel block count and order')
    maternal = _parent_indices(mothers, population.shape[0], 'mothers')
    paternal = _parent_indices(fathers, population.shape[0], 'fathers')
    if maternal.size != paternal.size:
        raise ValueError('mothers and fathers must designate the same number of children')
    maternal_gametes = _gametes(population, maternal, recombination_map, rng)
    paternal_gametes = _gametes(population, paternal, recombination_map, rng)
    return np.stack((maternal_gametes, paternal_gametes), axis=1).astype(np.uint8)
