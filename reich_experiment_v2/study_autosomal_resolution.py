"""Synthetic multiresolution diagnostic of the existing selected pulse scenarios."""

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from math import expm1
from numbers import Real
from pathlib import Path

import numpy as np

from run_experiment import Config, SCENARIOS, run_block_full
from paleogen_rl.genetics.ancestry import BlockPanel, MEASUREMENT_VERSION
from paleogen_rl.genetics.inheritance import RecombinationMap, INHERITANCE_VERSION
from paleogen_rl.genetics.selected import SIMULATION_VERSION
from paleogen_rl.genetics.resolution import RESOLUTIONS, SEEDS, _bounded_mean, _target_summary


STUDY_VERSION = 'selected-autosomal-resolution-v1'
STUDY_SCENARIOS = tuple(SCENARIOS)
ROOT = Path(__file__).resolve().parent
IMPLEMENTATION_FILES = (
    'study_autosomal_resolution.py', 'run_experiment.py', 'paleogen_rl/genetics/ancestry.py',
    'paleogen_rl/genetics/inheritance.py', 'paleogen_rl/genetics/selected.py',
    'paleogen_rl/genetics/pulse.py', 'paleogen_rl/genetics/resolution.py',
    'src/epi_pulse.py', 'src/reich_panmictic_original.py', 'flake.lock',
)
WORK_FIELDS = ('candidates_generated', 'accepted_candidates', 'offspring_generated', 'block_copy_transmissions')


def _sum_work(items):
    result = {key: sum(item['work_units'][key] for item in items) for key in WORK_FIELDS}
    result['state_allele_entries'] = max(item['work_units']['state_allele_entries'] for item in items)
    return result


def _metrics(replicates):
    return dict(ancestry=_bounded_mean([r['ancestry'] for r in replicates], 0., 1.),
                target_probability=_target_summary([r['ancestry'] for r in replicates]),
                p10_joint=_bounded_mean([r['p10_joint'] for r in replicates], 0., 1.),
                joint_and_target=_bounded_mean([r['joint_and_target'] for r in replicates], 0., 1.))


def _differences(rows):
    reference = rows[-1]
    result = []
    for row in rows[:-1]:
        differences = {}
        for metric, field in (('ancestry', 'ancestry'), ('target_probability', 'target_auto'),
                              ('p10_joint', 'p10_joint'), ('joint_and_target', 'joint_and_target')):
            deltas = [float(current[field])-float(fine[field])
                      for current, fine in zip(row['replicates'], reference['replicates'])]
            differences[metric] = _bounded_mean(deltas, -1., 1.)
        result.append(dict(block_count=row['block_count'], reference_block_count=reference['block_count'],
                           metrics=differences))
    return result


def run_selected_resolution_study(*, resolutions=RESOLUTIONS, seeds=SEEDS,
                                  scenarios=STUDY_SCENARIOS, generations=20, map_length=1.):
    """Compare full evaluations at fixed synthetic partner positions 0 and 1.

    All input declarations are validated before any simulation. Source hashes
    identify the local implementation; no third-party content is exported.
    """
    if (not isinstance(resolutions, (tuple, list)) or len(resolutions) < 3
            or any(type(b) is not int or b < 2 for b in resolutions)
            or any(a >= b for a, b in zip(resolutions, resolutions[1:]))):
        raise ValueError('resolutions must contain at least three increasing integers >= 2')
    if (not isinstance(seeds, (tuple, list)) or not seeds
            or any(type(seed) is not int or seed < 0 for seed in seeds)
            or len(set(seeds)) != len(seeds)):
        raise ValueError('seeds must be distinct nonnegative integers')
    if (not isinstance(scenarios, (tuple, list)) or not scenarios
            or any(not isinstance(name, str) or name not in SCENARIOS for name in scenarios)
            or len(set(scenarios)) != len(scenarios)):
        raise ValueError('scenarios must be distinct existing scenario names')
    if type(generations) is not int or generations < 0:
        raise ValueError('generations must be a nonnegative integer')
    if (isinstance(map_length, (bool, np.bool_)) or not isinstance(map_length, Real)
            or not np.isfinite(map_length) or map_length < 0):
        raise ValueError('map_length must be finite and nonnegative')
    map_length = float(map_length)
    hashes = {path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in IMPLEMENTATION_FILES}
    scenario_rows = []
    for name in scenarios:
        rows = []
        for blocks in resolutions:
            panel = BlockPanel(f'synthetic-resolution-{blocks}', tuple(f'b{i}' for i in range(blocks)))
            switch = -expm1(-2*map_length/(blocks-1))/2
            mapping = RecombinationMap(panel, (switch,)*(blocks-1))
            config = Config(N=40, f=.05, male_frac=.5, gens=generations,
                            stop_when_absorbed=False, **SCENARIOS[name])
            replicates = []
            for seed in seeds:
                try:
                    evaluated = run_block_full(replace(config, seed=seed), mapping, 'b0', f'b{blocks-1}')
                except (ValueError, RuntimeError) as error:
                    raise RuntimeError(f'{name} B={blocks} seed={seed}: {error}') from error
                evaluation = json.loads(evaluated['block_report'])
                engine = evaluation['engine_report']
                final = engine['final_measurement']
                replicates.append(dict(seed=seed, generation=final['generation'], status=final['status'],
                                       ancestry=final['value'], modern_allele_copies=final['modern_allele_copies'],
                                       **evaluation['sampling'], target_auto=evaluation['target']['target_auto'],
                                       joint_and_target=evaluation['target']['joint_and_target'],
                                       work_units=dict(engine['work_units'])))
            parameters = asdict(config)
            parameters.pop('seed')
            rows.append(dict(block_count=blocks, block_positions=[i/(blocks-1) for i in range(blocks)],
                             recombination_map=mapping.to_dict(), config_parameters=parameters,
                             selection=engine['selection'], partner_panel_weight=2/blocks,
                             allele_copy_denominator=final['allele_copy_denominator'],
                             initialisation=evaluation['initialisation'],
                             initial_state_sha256={field: engine[f'initial_{field}_sha256']
                                                   for field in ('haplotypes', 'sex', 'mt', 'y')},
                             replicates=replicates, metrics=_metrics(replicates), work_units=_sum_work(replicates)))
        scenario_rows.append(dict(name=name, parameters=dict(SCENARIOS[name]), resolutions=rows,
                                  differences_from_finest=_differences(rows), work_units=_sum_work(rows)))
    return dict(study_version=STUDY_VERSION, scientific_status='synthetic_selected_resolution_diagnostic',
                mode='full', convergence_status='not_established',
                numpy_version=np.__version__, rng_bit_generator=engine['rng_bit_generator'],
                measurement_version=MEASUREMENT_VERSION, inheritance_version=INHERITANCE_VERSION,
                simulation_version=SIMULATION_VERSION, implementation_sha256=hashes,
                protocol=dict(population_size=40, f=.05, male_fraction=.5, generations=generations,
                              seeds=list(seeds), resolutions=list(resolutions), scenarios=list(scenarios),
                              map_length=map_length, map_rule='r=-expm1(-2*L/(B-1))/2',
                              partner_positions=dict(mt=0., y=1.), target_interval=[.03, .07],
                              target_inclusive=True, dominance='additive', posterior=None,
                              confidence_level=.95, intervals_simultaneous=False,
                              reference='finest_resolution_in_this_study'),
                scenarios=scenario_rows, total_work_units=_sum_work(scenario_rows))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='new JSON destination (no overwrite)')
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        parser.error('output already exists')
    try:
        report = run_selected_resolution_study()
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write('\n')
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f'{error}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
