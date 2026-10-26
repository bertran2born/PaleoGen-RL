"""Synthetic nested neutral refinements with finite, unchanged partner cells."""

from dataclasses import replace
from fractions import Fraction
import hashlib
from math import expm1, isclose, isfinite
from numbers import Real

from .ancestry import BlockPanel
from .inheritance import RecombinationMap
from .protocol import _canonical
from .weighted_ancestry import WeightedBlockPanel
from .weighted_protocol import WeightedAutosomalProtocol


FAMILY_VERSION = 'weighted-autosomal-refinement-family-v1'
MAP_ABSOLUTE_TOLERANCE = 1e-15


def _switches(positions, map_length):
    return tuple(-expm1(-2*(map_length*(right-left)))/2
                 for left, right in zip(positions, positions[1:]))


def build_weighted_refinement_family(base_protocol, *, family_id, map_length,
                                     refinement_factors=(1, 3, 9)):
    """Return owned JSON data and executable I28 snapshots, without RNG use.

    Relative base weights define contiguous cells on [0,1]. All partners are
    retained; only neutral cells split. Odd, divisible factors retain every
    previous midpoint. This specifies a synthetic uniform genetic map, not an
    empirical genome or an equivalence/convergence test.
    """
    if not isinstance(base_protocol, WeightedAutosomalProtocol):
        raise ValueError('base_protocol must be a WeightedAutosomalProtocol')
    if not isinstance(family_id, str) or not family_id or family_id != family_id.strip():
        raise ValueError('family_id must be a nonempty trimmed string')
    if isinstance(map_length, bool) or not isinstance(map_length, Real):
        raise ValueError('map_length must be finite and nonnegative')
    try:
        map_length = float(map_length)
    except (ValueError, OverflowError) as error:
        raise ValueError('map_length must be representable as a finite float') from error
    if not isfinite(map_length) or map_length < 0:
        raise ValueError('map_length must be finite and nonnegative')
    if (not isinstance(refinement_factors, (list, tuple)) or len(refinement_factors) < 3
            or any(type(k) is not int or k < 1 or k % 2 != 1 for k in refinement_factors)
            or refinement_factors[0] != 1
            or any(b <= a or b % a != 0 for a, b in zip(refinement_factors, refinement_factors[1:]))):
        raise ValueError('at least three increasing odd divisible factors starting at 1 are required')
    factors = tuple(refinement_factors)
    base_panel = base_protocol.measurement_panel
    partners = {base_protocol.mt_partner_block, base_protocol.y_partner_block}
    if not set(base_panel.panel.block_ids)-partners:
        raise ValueError('at least one neutral cell is required for refinement')
    # Rational geometry avoids overflowing raw sums and drifting cell boundaries.
    weights = tuple(Fraction(w) for w in base_panel.block_weights)
    total = sum(weights)
    boundaries = [Fraction(0)]
    for weight in weights:
        boundaries.append(boundaries[-1]+weight/total)
    base_positions = [float((left+right)/2) for left, right in zip(boundaries, boundaries[1:])]
    expected = _switches(base_positions, map_length)
    if any(not isclose(actual, wanted, rel_tol=0., abs_tol=MAP_ABSOLUTE_TOLERANCE)
           for actual, wanted in zip(base_protocol.recombination_map.switch_probabilities, expected)):
        raise ValueError('base map is inconsistent with the declared uniform midpoint geometry')
    resolutions = []
    for factor in factors:
        ids, parent_ids, intervals, positions, refined_weights = [], [], [], [], []
        for index, block in enumerate(base_panel.panel.block_ids):
            count = 1 if block in partners else factor
            left, right = boundaries[index:index+2]
            for part in range(count):
                midpoint = Fraction(2*part+1, 2*count)
                identifier = (block if midpoint == Fraction(1, 2) else
                              f'{block}::at{midpoint.numerator}of{midpoint.denominator}')
                ids.append(identifier)
                parent_ids.append(block)
                intervals.append([float(left+(right-left)*Fraction(part, count)),
                                  float(left+(right-left)*Fraction(part+1, count))])
                positions.append(float(left+(right-left)*midpoint))
                refined_weights.append(base_panel.block_weights[index]/count)
        if (any(not start < center < end for (start, end), center in zip(intervals, positions))
                or any(a >= b for a, b in zip(positions, positions[1:]))):
            raise ValueError('refined geometry cannot be represented by distinct finite float coordinates')
        if factor == 1:
            protocol = base_protocol
        else:
            panel = BlockPanel(f'{family_id}:split{factor}', ids)
            protocol = replace(
                base_protocol, protocol_id=f'{family_id}:split{factor}',
                recombination_map=RecombinationMap(panel, _switches(positions, map_length)),
                measurement_panel=WeightedBlockPanel(panel, refined_weights, base_panel.weight_basis))
        resolutions.append(dict(refinement_factor=factor, block_count=len(ids),
                                parent_block_ids=parent_ids, block_intervals=intervals,
                                block_positions=positions, autosomal_protocol=protocol.to_dict(),
                                autosomal_protocol_sha256=protocol.sha256))
    declaration = dict(
        family_version=FAMILY_VERSION, family_id=family_id,
        scientific_status='synthetic_weighted_neutral_refinement', convergence_status='not_established',
        base_protocol=base_protocol.to_dict(), base_protocol_sha256=base_protocol.sha256,
        refinement_factors=list(factors), map_length=map_length,
        geometry_rule='contiguous_relative_weight_cells_with_midpoint_markers',
        map_rule='r(d)=-expm1(-2*d)/2; d=L*(right_midpoint-left_midpoint)',
        map_absolute_tolerance=MAP_ABSOLUTE_TOLERANCE,
        partner_refinement='unsplit_finite_cells', resolutions=resolutions)
    return {**declaration, 'family_sha256': hashlib.sha256(_canonical(declaration).encode('utf-8')).hexdigest()}
