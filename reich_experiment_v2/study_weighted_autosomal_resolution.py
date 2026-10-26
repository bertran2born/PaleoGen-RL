"""Explicit full studies of conservative weighted families, without convergence claims."""

import argparse
from dataclasses import asdict
import hashlib
import json
from math import log, sqrt
from pathlib import Path
import platform

import numpy as np

from run_experiment import Config, SCENARIOS, run_block_full
from study_autosomal_resolution import IMPLEMENTATION_FILES, _differences, _metrics, _sum_work
from paleogen_rl.genetics.protocol import _canonical, _keys, _unique_fields
from paleogen_rl.genetics.weighted_protocol import WeightedAutosomalProtocol, _reject_constant
from paleogen_rl.genetics.weighted_refinement import build_weighted_refinement_family


PLAN_VERSION = 'weighted-autosomal-resolution-plan-v1'
STUDY_VERSION = 'weighted-autosomal-resolution-study-v1'
PREVIEW_VERSION = 'weighted-autosomal-resolution-preview-v1'
ROOT = Path(__file__).resolve().parent
WEIGHTED_IMPLEMENTATION_FILES = (*IMPLEMENTATION_FILES, 'study_weighted_autosomal_resolution.py',
    'paleogen_rl/genetics/weighted_ancestry.py', 'paleogen_rl/genetics/weighted_protocol.py',
    'paleogen_rl/genetics/weighted_refinement.py')


def validate_weighted_resolution_plan(plan):
    _keys(plan, ('plan_version', 'plan_id', 'family', 'seeds', 'scenarios'), 'weighted study plan')
    if plan['plan_version'] != PLAN_VERSION:
        raise ValueError('unsupported weighted resolution plan version')
    identity = plan['plan_id']
    if not isinstance(identity, str) or not identity or identity != identity.strip():
        raise ValueError('plan_id must be a nonempty trimmed string')
    _keys(plan['family'], ('base_protocol', 'family_id', 'map_length', 'refinement_factors'), 'family')
    family_input = plan['family']
    base = WeightedAutosomalProtocol.from_dict(family_input['base_protocol'])
    family = build_weighted_refinement_family(base, **{key: family_input[key] for key in
                                ('family_id', 'map_length', 'refinement_factors')})
    seeds, scenarios = plan['seeds'], plan['scenarios']
    if (not isinstance(seeds, (tuple, list)) or not seeds
            or any(type(seed) is not int or seed < 0 for seed in seeds) or len(set(seeds)) != len(seeds)):
        raise ValueError('seeds must be distinct nonnegative integers')
    if (not isinstance(scenarios, (tuple, list)) or not scenarios
            or any(not isinstance(name, str) or name not in SCENARIOS for name in scenarios)
            or len(set(scenarios)) != len(scenarios)):
        raise ValueError('scenarios must be distinct existing scenario names')
    return dict(plan_version=PLAN_VERSION, plan_id=identity, seeds=list(seeds), scenarios=list(scenarios),
                family={key: family[key] for key in ('base_protocol', 'family_id', 'map_length', 'refinement_factors')})


def load_weighted_resolution_plan(path):
    payload = Path(path).read_bytes()
    plan = validate_weighted_resolution_plan(json.loads(payload, object_pairs_hook=_unique_fields,
                                                       parse_constant=_reject_constant))
    return plan, hashlib.sha256(payload).hexdigest()


def preview_weighted_resolution_plan(plan):
    plan = validate_weighted_resolution_plan(plan)
    declaration = plan['family']
    base = WeightedAutosomalProtocol.from_dict(declaration['base_protocol'])
    family = build_weighted_refinement_family(base, **{key: declaration[key] for key in
                                ('family_id', 'map_length', 'refinement_factors')})
    evaluations = len(plan['seeds'])*len(plan['scenarios'])
    offspring = evaluations*base.population_size*base.generations
    rows = [dict(block_count=row['block_count'], refinement_factor=row['refinement_factor'],
                 evaluations=evaluations, offspring_generated_on_completion=offspring,
                 accepted_candidates_on_completion=offspring,
                 candidates_generated_lower_bound_on_completion=offspring,
                 block_copy_transmissions_lower_bound_on_completion=2*row['block_count']*offspring,
                 state_allele_entries=2*base.population_size*row['block_count'])
            for row in family['resolutions']]
    total = {key: sum(row[key] for row in rows) for key in (
        'evaluations', 'offspring_generated_on_completion', 'accepted_candidates_on_completion',
        'candidates_generated_lower_bound_on_completion', 'block_copy_transmissions_lower_bound_on_completion')}
    total['largest_population_state_allele_entries'] = max(row['state_allele_entries'] for row in rows)
    return dict(preview_version=PREVIEW_VERSION, scientific_status='planning_only', simulation_performed=False,
                mode='full', convergence_status='not_established', plan=plan,
                plan_sha256=hashlib.sha256(_canonical(plan).encode('utf-8')).hexdigest(), plan_file_sha256=None,
                family=family, resolutions=rows, total_workload=total,
                precision=dict(confidence_level=.95, intervals_simultaneous=False,
                               bounded_mean_radius_unclipped=sqrt(log(40)/(2*len(plan['seeds']))),
                               paired_difference_radius_unclipped=sqrt(2*log(40)/len(plan['seeds'])),
                               method='hoeffding_95_pointwise'),
                assumptions=dict(completion_required=True, rejection_overhead_included=False,
                                 independent_replicates_required=True, cost_units='logical_counts_not_time',
                                 state_units='allele_entries_one_population_not_peak_memory'))


def run_weighted_resolution_plan(plan):
    preview = preview_weighted_resolution_plan(plan)
    plan, family = preview['plan'], preview['family']
    hashes = {path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in WEIGHTED_IMPLEMENTATION_FILES}
    scenarios = []
    for name in plan['scenarios']:
        rows = []
        for resolution in family['resolutions']:
            protocol = WeightedAutosomalProtocol.from_dict(resolution['autosomal_protocol'])
            replicates = []
            for seed in plan['seeds']:
                config = Config(N=protocol.population_size, gens=protocol.generations, f=protocol.f,
                                male_frac=protocol.male_fraction, seed=seed, stop_when_absorbed=False,
                                **SCENARIOS[name])
                try:
                    evaluated = run_block_full(config, protocol.recombination_map,
                        protocol.mt_partner_block, protocol.y_partner_block, measurement_panel=protocol.measurement_panel)
                except (ValueError, RuntimeError) as error:
                    raise RuntimeError(f'{name} B={resolution["block_count"]} seed={seed}: {error}') from error
                evaluation = json.loads(evaluated['block_report'])
                final = evaluation['engine_report']['final_measurement']
                replicates.append(dict(seed=seed, generation=final['generation'], status=final['status'],
                                       config_realized=asdict(config), ancestry=final['value'],
                                       p10_joint=evaluation['sampling']['p10_joint'],
                                       target_auto=evaluation['target']['target_auto'],
                                       joint_and_target=evaluation['target']['joint_and_target'],
                                       evaluation=evaluation, work_units=dict(evaluation['engine_report']['work_units'])))
            rows.append(dict(block_count=resolution['block_count'], refinement_factor=resolution['refinement_factor'],
                             autosomal_protocol_sha256=protocol.sha256, replicates=replicates,
                             metrics=_metrics(replicates), work_units=_sum_work(replicates)))
        scenarios.append(dict(name=name, parameters=dict(SCENARIOS[name]), resolutions=rows,
                              differences_from_finest=_differences(rows), work_units=_sum_work(rows)))
    return dict(study_version=STUDY_VERSION, scientific_status='exploratory_weighted_resolution_diagnostic',
                simulation_performed=True, mode='full', convergence_status='not_established',
                plan=plan, plan_sha256=preview['plan_sha256'], plan_file_sha256=None, family=family,
                interval_scope='pointwise_monte_carlo_not_equivalence',
                reference='finest_resolution_in_this_study', implementation_sha256=hashes,
                python_version=platform.python_version(), numpy_version=np.__version__,
                rng_bit_generator=evaluation['engine_report']['rng_bit_generator'],
                workload_preview=preview, scenarios=scenarios, total_work_units=_sum_work(scenarios))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='new JSON destination; no overwrite')
    parser.add_argument('--preview', action='store_true', help='forecast logical work without simulation')
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        parser.error('output already exists')
    if not args.output.parent.is_dir():
        parser.error('output parent directory must exist')
    try:
        plan, file_hash = load_weighted_resolution_plan(args.plan)
        report = preview_weighted_resolution_plan(plan) if args.preview else run_weighted_resolution_plan(plan)
        report['plan_file_sha256'] = file_hash
        if not args.preview:
            report['workload_preview']['plan_file_sha256'] = file_hash
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write('\n')
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f'{error}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
