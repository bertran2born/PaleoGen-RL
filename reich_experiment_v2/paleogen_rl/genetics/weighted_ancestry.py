"""Explicit weighted measurement, separate from the equal-weight I11 protocol."""

from dataclasses import dataclass, field
from math import fsum, isfinite
from numbers import Real

import numpy as np

from .ancestry import BlockPanel, measure_ancestry


MEASUREMENT_VERSION = 'weighted-autosomal-block-measurement-v1'


@dataclass(frozen=True)
class WeightedBlockPanel:
    panel: BlockPanel
    block_weights: tuple[float, ...]
    weight_basis: str
    normalized_weights: tuple[float, ...] = field(init=False)

    def __post_init__(self):
        if not isinstance(self.panel, BlockPanel):
            raise ValueError('panel must be a BlockPanel')
        if (not isinstance(self.weight_basis, str) or not self.weight_basis
                or self.weight_basis != self.weight_basis.strip()):
            raise ValueError('weight_basis must be a nonempty trimmed explanation')
        if (not isinstance(self.block_weights, (list, tuple))
                or len(self.block_weights) != len(self.panel.block_ids)):
            raise ValueError('one explicit weight is required per block')
        weights = []
        for weight in self.block_weights:
            if isinstance(weight, (bool, np.bool_)) or not isinstance(weight, Real):
                raise ValueError('block weights must be finite and strictly positive')
            try:
                value = float(weight)
            except (ValueError, OverflowError) as error:
                raise ValueError('block weights must be representable as finite floats') from error
            if not isfinite(value) or value <= 0:
                raise ValueError('block weights must be finite and strictly positive')
            weights.append(value)
        # Scale before summing, so large, finite declarations do not overflow.
        largest = max(weights)
        scaled = tuple(weight/largest for weight in weights)
        total = fsum(scaled)
        normalized = tuple(weight/total for weight in scaled)
        if any(weight == 0 for weight in normalized):
            raise ValueError('weight ratios are not representable as positive floats')
        object.__setattr__(self, 'block_weights', tuple(weights))
        object.__setattr__(self, 'normalized_weights', normalized)

    def to_dict(self):
        return dict(panel_id=self.panel.panel_id, block_ids=list(self.panel.block_ids),
                    block_count=len(self.panel.block_ids), weighting='explicit_relative_block_weights',
                    block_weights=list(self.block_weights), normalized_weights=list(self.normalized_weights),
                    weight_basis=self.weight_basis)


def measure_weighted_ancestry(modern_copies, panel, *, generation, target_generation,
                              mode, partner_block_ids=()):
    """Measure sum(w_b * modern_b/(2N))/sum(w_b), retaining all blocks.

    Weight units are relative. The numerator is ancestry weight, not an allele
    count. The unweighted count and denominator are separate diagnostics only.
    No target, score, selection or simulated trajectory is computed here.
    """
    if not isinstance(panel, WeightedBlockPanel):
        raise ValueError('panel must be a WeightedBlockPanel')
    base = measure_ancestry(modern_copies, panel.panel, generation=generation,
                            target_generation=target_generation, mode=mode,
                            partner_block_ids=partner_block_ids)
    denominator = fsum(panel.normalized_weights)
    result = dict(measurement_version=MEASUREMENT_VERSION,
                  observable='total_weighted_diploid_block_ancestry', panel=panel.to_dict(),
                  generation=generation, target_generation=target_generation, mode=mode,
                  status=base['status'], diploid_individuals=base['diploid_individuals'],
                  weight_denominator=denominator, modern_ancestry_weight=None, value=None,
                  unweighted_modern_allele_copies=base['modern_allele_copies'],
                  unweighted_allele_copy_denominator=base['allele_copy_denominator'],
                  partner_block_ids=base['partner_block_ids'], partner_diagnostics=None)
    if mode == 'quick':
        return result
    counts = np.asarray(modern_copies)
    copies_per_individual = 2*base['diploid_individuals']
    fractions = [int(counts[:, column].sum(dtype=np.int64))/copies_per_individual
                 for column in range(len(panel.panel.block_ids))]
    numerator = fsum(weight*fraction for weight, fraction in zip(panel.normalized_weights, fractions))
    result.update(modern_ancestry_weight=numerator, value=numerator/denominator)
    positions = {block: column for column, block in enumerate(panel.panel.block_ids)}
    result['partner_diagnostics'] = [
        {**diagnostic,
         'relative_panel_weight': panel.normalized_weights[positions[diagnostic['block_id']]]/denominator,
         'weighted_ancestry_contribution':
             panel.normalized_weights[positions[diagnostic['block_id']]]*diagnostic['value']/denominator}
        for diagnostic in base['partner_diagnostics']]
    return result
