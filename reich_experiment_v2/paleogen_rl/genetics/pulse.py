"""Explicit single-pulse initialisation and full-horizon block evaluation."""

import hashlib
import json
from numbers import Real
from pathlib import Path

import numpy as np

from .ancestry import BlockPanel
from .inheritance import RecombinationMap
from .selected import BlockSelection, ReproductionFailure, run_selected


RESULT_SCHEMA_VERSION = 'block-pulse-result-v1'
MODEL = 'panmictic_pulse_phased_blocks_reciprocal_epistasis'
EVALUATION_VERSION = 'block-pulse-evaluation-v1'
MODE_RESULT_SCHEMA_VERSION = 'block-pulse-result-v2'
MODE_EVALUATION_VERSION = 'block-pulse-evaluation-v2'


def load_block_map(path):
    """Read exactly a panel and boundary probabilities, hashing the file bytes."""
    payload = Path(path).read_bytes()
    declaration = json.loads(payload)
    if not isinstance(declaration, dict) or set(declaration) != {'panel', 'switch_probabilities'}:
        raise ValueError('block map must declare exactly panel and switch_probabilities')
    panel = declaration['panel']
    if not isinstance(panel, dict) or set(panel) != {'panel_id', 'block_ids'}:
        raise ValueError('block map panel must declare exactly panel_id and block_ids')
    mapping = RecombinationMap(BlockPanel(**panel), declaration['switch_probabilities'])
    return mapping, hashlib.sha256(payload).hexdigest()


def initialise_pulse(*, population_size, f, male_fraction, panel):
    """M2's deterministic rounding and sex ordering, projected onto phased blocks."""
    if type(population_size) is not int or population_size < 2:
        raise ValueError('population_size must be an integer >= 2')
    if not isinstance(panel, BlockPanel):
        raise ValueError('panel must be a BlockPanel')
    for name, value in (('f', f), ('male_fraction', male_fraction)):
        if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
                or not np.isfinite(value) or not 0 <= value <= 1):
            raise ValueError(f'{name} must be finite in [0,1]')
    f, male_fraction = float(f), float(male_fraction)
    male_n = population_size//2
    female_n = population_size-male_n
    modern_males = int(round(f*population_size*male_fraction))
    modern_females = int(round(f*population_size*(1-male_fraction)))
    if modern_males > male_n or modern_females > female_n:
        raise ValueError('modern pulse exceeds the number of individuals of that sex')
    sex = np.array([1]*male_n+[0]*female_n, dtype=np.uint8)
    modern = np.zeros(population_size, dtype=np.int8)
    modern[:modern_males] = 1
    modern[male_n:male_n+modern_females] = 1
    haplotypes = np.broadcast_to(modern[:, None, None],
                                  (population_size, 2, len(panel.block_ids))).astype(np.uint8, copy=True)
    state = dict(haplotypes=haplotypes, sex=sex, mt=modern.astype(np.uint8),
                 y=np.where(sex == 1, modern, -1).astype(np.int8))
    provenance = dict(initialisation_version='block-pulse-initialisation-v1',
                      population_size=population_size, requested_f=f,
                      requested_male_fraction=male_fraction, modern_males=modern_males,
                      modern_females=modern_females,
                      realised_ancestry=(modern_males+modern_females)/population_size,
                      rule='round_counts_per_sex_modern_individuals_first_homozygous_blocks')
    return state, provenance


def evaluate_block_pulse(*, population_size, f, male_fraction, generations, seed,
                         recombination_map, selection, mode='full'):
    """Evaluate all blocks and the unchanged ten-male/3–7% joint criterion."""
    if not isinstance(recombination_map, RecombinationMap):
        raise ValueError('recombination_map must be a RecombinationMap')
    if not isinstance(selection, BlockSelection):
        raise ValueError('selection must be a BlockSelection')
    if mode not in ('full', 'quick', 'adaptive'):
        raise ValueError('mode must be full/quick/adaptive')
    if mode != 'full':
        return _evaluate_screened(population_size=population_size, f=f, male_fraction=male_fraction,
                                  generations=generations, seed=seed, recombination_map=recombination_map,
                                  selection=selection, mode=mode)
    state, initialisation = initialise_pulse(population_size=population_size, f=f,
                                            male_fraction=male_fraction, panel=recombination_map.panel)
    result = run_selected(**state, recombination_map=recombination_map, selection=selection,
                          generations=generations, seed=seed)
    engine = result.report
    measurement = engine['final_measurement']
    if (engine['termination_reason'] != 'horizon_reached'
            or engine['generations_completed'] != generations or measurement is None
            or measurement['status'] != 'evaluated_at_target'
            or measurement['generation'] != generations
            or measurement['target_generation'] != generations or measurement['mode'] != 'full'):
        raise RuntimeError('incomplete block horizon: final evaluation refused')
    sampling = _sampling(result)
    target = bool(.03 <= measurement['value'] <= .07)
    return dict(evaluation_version=EVALUATION_VERSION,
                convergence_status='not_assessed_for_selected_scenarios',
                initialisation=initialisation, engine_report=engine,
                sampling=sampling,
                target=dict(bounds=[.03, .07], inclusive=True, target_auto=target,
                            joint_and_target=sampling['p10_joint']*int(target)))


def _sampling(result):
    males = result.sex == 1
    male_n = int(males.sum())
    both = int(((result.mt[males] == 1) & (result.y[males] == 1)).sum())
    p10 = float(np.prod([(both-i)/(male_n-i) for i in range(10)])) if both >= 10 else 0.
    return dict(sample_size=10, replacement=False, male_n=male_n,
                both_modern_men=both, p10_joint=p10,
                mt_mod=float((result.mt == 1).mean()), Y_mod=float((result.y[males] == 1).mean()),
                joint_fixed=bool(np.all(result.mt == 1) and np.all(result.y[males] == 1)))


def _combined_work(*reports):
    work = {key: sum(report['work_units'][key] for report in reports) for key in
            ('candidates_generated', 'accepted_candidates', 'offspring_generated', 'block_copy_transmissions')}
    work['state_allele_entries'] = max(report['work_units']['state_allele_entries'] for report in reports)
    return work


def _evaluate_screened(*, population_size, f, male_fraction, generations, seed,
                       recombination_map, selection, mode):
    state, initialisation = initialise_pulse(population_size=population_size, f=f,
                                            male_fraction=male_fraction, panel=recombination_map.panel)
    first = run_selected(**state, recombination_map=recombination_map, selection=selection,
                         generations=generations, seed=seed, stop_when_absorbed=True)
    screen = first.report
    completed = screen['generations_completed']
    absorbed = ((np.all(first.mt == 0) or np.all(first.mt == 1))
                and (np.all(first.y[first.sex == 1] == 0) or np.all(first.y[first.sex == 1] == 1)))
    if not ((screen['termination_reason'] == 'horizon_reached' and completed == generations)
            or (screen['termination_reason'] == 'markers_absorbed' and 0 < completed < generations and absorbed)):
        raise RuntimeError('incomplete block screening: evaluation refused')
    measurement = screen['final_measurement']
    if (measurement is None or measurement['status'] != 'not_evaluated_quick'
            or measurement['value'] is not None or measurement['partner_diagnostics'] is not None
            or measurement['generation'] != completed or measurement['target_generation'] != generations):
        raise RuntimeError('invalid quick block measurement: evaluation refused')
    sampling = _sampling(first)
    target = dict(bounds=[.03, .07], inclusive=True, target_auto=None, joint_and_target=None)
    engine = screen
    work = dict(screen['work_units'])
    measurement = dict(measurement)
    continuation = 'not_requested_quick'
    if mode == 'adaptive':
        measurement.update(mode='adaptive', status='not_evaluated_event_impossible')
        if sampling['p10_joint'] == 0:
            target['joint_and_target'] = 0.
            continuation = 'skipped_event_impossible'
        else:
            try:
                final = evaluate_block_pulse(population_size=population_size, f=f, male_fraction=male_fraction,
                                             generations=generations, seed=seed, recombination_map=recombination_map,
                                             selection=selection)
            except ReproductionFailure as error:
                error.report['total_work_units'] = _combined_work(screen, error.report)
                error.report['screening_report'] = screen
                raise
            if final['sampling'] != sampling:
                raise RuntimeError('block screening mismatch: marker results changed')
            engine = final['engine_report']
            measurement = {**engine['final_measurement'], 'mode': 'adaptive'}
            target = final['target']
            work = _combined_work(screen, engine)
            continuation = 'rerun_to_target'
    return dict(evaluation_version=MODE_EVALUATION_VERSION, mode=mode,
                convergence_status='not_assessed_for_selected_scenarios', initialisation=initialisation,
                screening_report=screen, engine_report=engine, ancestry_measurement=measurement,
                sampling={**sampling, 'generation': completed,
                          'status': 'absorbed_before_target' if completed < generations else 'evaluated_at_target'},
                stopping_ancestry_diagnostic=dict(value=float(first.haplotypes.mean()), generation=completed),
                continuation_status=continuation, work_units=work, target=target)
