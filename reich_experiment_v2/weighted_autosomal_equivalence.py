"""Declared finite-family equivalence; no default scientific margins or adoption."""

import hashlib
import json
from dataclasses import asdict
from math import ceil, fsum, isfinite, log, sqrt
from numbers import Real
from pathlib import Path

from paleogen_rl.genetics.protocol import _canonical, _keys, _unique_fields
from paleogen_rl.genetics.selected import BlockSelection
from paleogen_rl.genetics.weighted_ancestry import MEASUREMENT_VERSION
from paleogen_rl.genetics.weighted_protocol import WeightedAutosomalProtocol, _reject_constant
from study_weighted_autosomal_resolution import (
    Config, SCENARIOS, STUDY_VERSION, preview_weighted_resolution_plan, validate_weighted_resolution_plan,
)


CRITERIA_VERSION = 'weighted-autosomal-equivalence-criteria-v1'
ASSESSMENT_VERSION = 'weighted-autosomal-equivalence-assessment-v1'
METRICS = ('ancestry', 'target_probability', 'p10_joint', 'joint_and_target')


def _digest(value):
    return hashlib.sha256(_canonical(value).encode('utf-8')).hexdigest()


def _number(value, field, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f'{field} must be a finite number')
    try:
        value = float(value)
    except (ValueError, OverflowError) as error:
        raise ValueError(f'{field} must be representable as a finite float') from error
    if not isfinite(value) or not (0 < value <= 1 if positive else 0 <= value <= 1):
        raise ValueError(f'{field} must be in {"(0,1]" if positive else "[0,1]"}')
    return value


def validate_weighted_equivalence_criteria(criteria, plan):
    plan = validate_weighted_resolution_plan(plan)
    _keys(criteria, ('criteria_version', 'criteria_id', 'study_plan_sha256', 'alpha',
                     'margins', 'max_interval_radius'), 'equivalence criteria')
    if criteria['criteria_version'] != CRITERIA_VERSION:
        raise ValueError('unsupported equivalence criteria version')
    identity = criteria['criteria_id']
    if not isinstance(identity, str) or not identity or identity != identity.strip():
        raise ValueError('criteria_id must be a nonempty trimmed string')
    if criteria['study_plan_sha256'] != _digest(plan):
        raise ValueError('criteria must bind the exact study plan')
    alpha = _number(criteria['alpha'], 'alpha', positive=True)
    if alpha == 1:
        raise ValueError('alpha must be strictly less than 1')
    _keys(criteria['margins'], METRICS, 'margins')
    margins = {key: _number(criteria['margins'][key], key, positive=True) for key in METRICS}
    radius = _number(criteria['max_interval_radius'], 'max_interval_radius', positive=True)
    if radius > min(margins.values()) or radius*radius == 0:
        raise ValueError('precision radius must be representable and no larger than any margin')
    return dict(criteria_version=CRITERIA_VERSION, criteria_id=identity, study_plan_sha256=_digest(plan),
                alpha=alpha, margins=margins, max_interval_radius=radius)


def load_weighted_equivalence_criteria(path, plan):
    payload = Path(path).read_bytes()
    criteria = json.loads(payload, object_pairs_hook=_unique_fields, parse_constant=_reject_constant)
    return validate_weighted_equivalence_criteria(criteria, plan), hashlib.sha256(payload).hexdigest()


def preview_weighted_equivalence(criteria, plan):
    plan = validate_weighted_resolution_plan(plan)
    criteria = validate_weighted_equivalence_criteria(criteria, plan)
    comparisons = len(plan['scenarios'])*(len(plan['family']['refinement_factors'])-1)*len(METRICS)
    # Union bound of two-sided Hoeffding bounds for paired differences in [-1,1].
    coefficient = 2*(log(2*comparisons)-log(criteria['alpha']))
    quotient = coefficient/criteria['max_interval_radius']**2
    if not isfinite(quotient):
        raise ValueError('requested precision exceeds representable planning arithmetic')
    required = ceil(quotient)
    radius = sqrt(coefficient/len(plan['seeds']))
    # Avoid an optimistic ceil at a floating-point boundary.
    if sqrt(coefficient/required) > criteria['max_interval_radius']:
        required += 1
    return dict(criteria=criteria, criteria_sha256=_digest(criteria), study_plan_sha256=_digest(plan),
                comparisons=comparisons, replicates_per_cell=len(plan['seeds']),
                simultaneous_radius_unclipped=radius, required_replicates_per_cell=required,
                precision_satisfied=radius <= criteria['max_interval_radius'],
                confidence_level=1-criteria['alpha'], method='hoeffding_union_bound_paired_differences',
                independent_replicates_required=True, comparison_independence_required=False,
                convergence_status='not_established')


def _decision(interval, margin, precision):
    lower, upper = interval
    if lower > margin or upper < -margin:
        return 'difference_detected'
    if not precision:
        return 'inconclusive_precision'
    if lower > -margin and upper < margin:
        return 'equivalence_supported'
    return 'inconclusive'


def _values(replicate, seed, protocol, scenario):
    horizon = protocol.generations
    if (type(replicate['seed']) is not int or replicate['seed'] != seed
            or type(replicate['generation']) is not int or replicate['generation'] != horizon
            or replicate['status'] != 'evaluated_at_target'):
        raise ValueError('replicate seed, generation or availability disagrees with plan')
    ancestry = _number(replicate['ancestry'], 'ancestry')
    p10 = _number(replicate['p10_joint'], 'p10_joint')
    joint = _number(replicate['joint_and_target'], 'joint_and_target')
    target = replicate['target_auto']
    if type(target) is not bool or target != (.03 <= ancestry <= .07) or joint != p10*target:
        raise ValueError('replicate target or joint criterion is inconsistent')
    evaluation = replicate['evaluation']
    engine = evaluation['engine_report']
    final = engine['final_measurement']
    panel = protocol.measurement_panel.to_dict()
    config = Config(N=protocol.population_size, gens=horizon, f=protocol.f,
                    male_frac=protocol.male_fraction, seed=seed, stop_when_absorbed=False, **SCENARIOS[scenario])
    selection = BlockSelection(s_mt=config.s_mt, s_y=config.s if config.sel_locus == 'Y' else 0.,
                    **{key: getattr(config, key) for key in ('mt_mod_nuc_arch', 'mt_arch_nuc_mod',
                                                           'y_mod_nuc_arch', 'y_arch_nuc_mod')},
                    mt_partner_block=protocol.mt_partner_block, y_partner_block=protocol.y_partner_block,
                    dominance=config.mismatch_dominance)
    if (_canonical(replicate['config_realized']) != _canonical(asdict(config))
            or engine['seed'] != seed or engine['selection'] != asdict(selection)
            or engine['recombination_map'] != protocol.recombination_map.to_dict()):
        raise ValueError('realized configuration or engine disagrees with the planned scenario')
    if (engine['generations_completed'] != horizon or engine['termination_reason'] != 'horizon_reached'
            or final['generation'] != horizon or final['target_generation'] != horizon
            or final['status'] != 'evaluated_at_target' or final['mode'] != 'full'
            or final['measurement_version'] != MEASUREMENT_VERSION or final['panel'] != panel
            or final['value'] != ancestry or evaluation['measurement_panel'] != panel
            or evaluation['sampling']['p10_joint'] != p10
            or evaluation['target'] != dict(bounds=[.03, .07], inclusive=True,
                                           target_auto=target, joint_and_target=joint)):
        raise ValueError('evaluation does not contain the declared full weighted observation')
    mass, denominator = float(final['modern_ancestry_weight']), float(final['weight_denominator'])
    if (not isfinite(mass) or not isfinite(denominator) or denominator <= 0
            or abs(mass/denominator-ancestry) > 1e-14):
        raise ValueError('weighted mass and denominator disagree with ancestry')
    return dict(ancestry=ancestry, target_probability=float(target), p10_joint=p10, joint_and_target=joint)


def assess_weighted_equivalence(criteria, report):
    """Recompute simultaneous intervals from full I31 replicates, not cached metrics.

    This verifies relevant plan/family/observation consistency, not authenticity
    of simulation or temporal preregistration. A finite-family result never
    changes the global M3 convergence/adoption status.
    """
    try:
        if (report['study_version'] != STUDY_VERSION or report['mode'] != 'full'
                or report['simulation_performed'] is not True):
            raise ValueError('assessment requires a full I31 study')
        plan = validate_weighted_resolution_plan(report['plan'])
        preview = preview_weighted_equivalence(criteria, plan)
        family = preview_weighted_resolution_plan(plan)['family']
        if report['plan_sha256'] != preview['study_plan_sha256'] or _canonical(report['family']) != _canonical(family):
            raise ValueError('study plan or refinement family is inconsistent')
        if [s['name'] for s in report['scenarios']] != plan['scenarios']:
            raise ValueError('study scenarios must match the exact plan order')
        results = []
        for scenario in report['scenarios']:
            rows = scenario['resolutions']
            if len(rows) != len(family['resolutions']):
                raise ValueError('missing or extra resolution')
            values = []
            for row, declared in zip(rows, family['resolutions']):
                if (row['block_count'] != declared['block_count']
                        or row['refinement_factor'] != declared['refinement_factor']
                        or row['autosomal_protocol_sha256'] != declared['autosomal_protocol_sha256']
                        or len(row['replicates']) != len(plan['seeds'])):
                    raise ValueError('resolution identity or replicate count disagrees with plan')
                protocol = WeightedAutosomalProtocol.from_dict(declared['autosomal_protocol'])
                values.append([_values(rep, seed, protocol, scenario['name'])
                               for rep, seed in zip(row['replicates'], plan['seeds'])])
            for row, current in zip(rows[:-1], values[:-1]):
                for metric in METRICS:
                    mean = fsum(a[metric]-b[metric] for a, b in zip(current, values[-1]))/len(current)
                    radius = preview['simultaneous_radius_unclipped']
                    interval = [max(-1., mean-radius), min(1., mean+radius)]
                    margin = preview['criteria']['margins'][metric]
                    results.append(dict(scenario=scenario['name'], block_count=row['block_count'],
                                        reference_block_count=rows[-1]['block_count'], metric=metric,
                                        mean_difference=mean, interval=interval, margin=margin,
                                        status=_decision(interval, margin, preview['precision_satisfied'])))
        statuses = {row['status'] for row in results}
        if 'difference_detected' in statuses:
            status = 'difference_detected'
        elif statuses == {'equivalence_supported'}:
            status = 'equivalence_supported_within_declared_family'
        elif not preview['precision_satisfied']:
            status = 'inconclusive_precision'
        else:
            status = 'inconclusive'
        return dict(assessment_version=ASSESSMENT_VERSION, status=status, convergence_status='not_established',
                    criteria=preview['criteria'], criteria_sha256=preview['criteria_sha256'],
                    study_plan_sha256=preview['study_plan_sha256'], study_report_sha256=_digest(report),
                    family_sha256=family['family_sha256'], precision=preview, comparisons=results)
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError('malformed or incomplete I31 report') from error
