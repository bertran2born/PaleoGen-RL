"""Synthetic neutral resolution diagnostic, separate from pulse evaluation."""

import argparse
import json
from math import expm1, log, sqrt
from numbers import Real
from pathlib import Path

import numpy as np

from .ancestry import BlockPanel, MEASUREMENT_VERSION
from .inheritance import RecombinationMap, INHERITANCE_VERSION
from .neutral import SIMULATION_VERSION, run_neutral


STUDY_VERSION = 'neutral-autosomal-resolution-v1'
RESOLUTIONS = (8, 32, 128)
SEEDS = tuple(range(410000, 410128))
TARGET = (.03, .07)
Z95 = 1.959963984540054


def _bounded_mean(values, lower, upper):
    mean = float(np.mean(values))
    radius = (upper-lower)*sqrt(log(40)/(2*len(values)))
    return dict(mean=mean, interval=[max(lower, mean-radius), min(upper, mean+radius)],
                method='hoeffding_95_pointwise')


def _target_summary(values):
    hits = sum(TARGET[0] <= value <= TARGET[1] for value in values)
    n = len(values)
    p = hits/n
    denominator = 1+Z95**2/n
    center = (p+Z95**2/(2*n))/denominator
    radius = Z95*sqrt(p*(1-p)/n+Z95**2/(4*n*n))/denominator
    return dict(count=hits, replicates=n, probability=p,
                interval=[max(0., center-radius), min(1., center+radius)],
                method='wilson_95_pointwise')


def run_resolution_study(*, resolutions=RESOLUTIONS, seeds=SEEDS,
                         generations=20, map_length=1.):
    """Compare declared resolutions on the fixed, sex-balanced I13 pulse.

    Every input is validated before simulation. The target and initial state
    are fixed protocol choices, not fitted to the outcome of these runs.
    """
    if (not isinstance(resolutions, (tuple, list)) or len(resolutions) < 3
            or any(type(b) is not int or b < 2 for b in resolutions)
            or any(a >= b for a, b in zip(resolutions, resolutions[1:]))):
        raise ValueError('resolutions must contain at least three increasing integers >= 2')
    if (not isinstance(seeds, (tuple, list)) or not seeds
            or any(type(seed) is not int or seed < 0 for seed in seeds)
            or len(set(seeds)) != len(seeds)):
        raise ValueError('seeds must be distinct nonnegative integers')
    if type(generations) is not int or generations < 0:
        raise ValueError('generations must be a nonnegative integer')
    if (isinstance(map_length, (bool, np.bool_)) or not isinstance(map_length, Real)
            or not np.isfinite(map_length) or map_length < 0):
        raise ValueError('map_length must be finite and nonnegative')
    map_length = float(map_length)
    sex = np.array([1]*20+[0]*20, dtype=np.uint8)
    rows = []
    for blocks in resolutions:
        panel = BlockPanel(f'synthetic-resolution-{blocks}', tuple(f'b{i}' for i in range(blocks)))
        switch = -expm1(-2*map_length/(blocks-1))/2
        mapping = RecombinationMap(panel, (switch,)*(blocks-1))
        initial = np.zeros((40, 2, blocks), dtype=np.uint8)
        initial[[0, 20], :, :] = 1
        replicates = []
        work = dict(offspring_generated=0, block_copy_transmissions=0,
                    state_allele_entries=80*blocks)
        for seed in seeds:
            result = run_neutral(initial, sex, recombination_map=mapping,
                                 generations=generations, seed=seed)
            report = result.report
            final = report['final_measurement']
            replicates.append(dict(seed=seed, generation=final['generation'],
                                   status=final['status'], value=final['value'],
                                   modern_allele_copies=final['modern_allele_copies']))
            for key in ('offspring_generated', 'block_copy_transmissions'):
                work[key] += report['work_units'][key]
        values = [r['value'] for r in replicates]
        rows.append(dict(block_count=blocks, recombination_map=mapping.to_dict(),
                         initial_haplotypes_sha256=report['initial_haplotypes_sha256'],
                         initial_sex_sha256=report['initial_sex_sha256'],
                         allele_copy_denominator=80*blocks, replicates=replicates,
                         ancestry=_bounded_mean(values, 0., 1.), target=_target_summary(values),
                         work_units=work))
    reference = rows[-1]
    differences = []
    for row in rows[:-1]:
        ancestry_deltas, target_deltas = [], []
        for current, fine in zip(row['replicates'], reference['replicates']):
            ancestry_deltas.append(current['value']-fine['value'])
            target_deltas.append(int(TARGET[0] <= current['value'] <= TARGET[1])
                                 - int(TARGET[0] <= fine['value'] <= TARGET[1]))
        differences.append(dict(block_count=row['block_count'],
                                reference_block_count=reference['block_count'],
                                ancestry=_bounded_mean(ancestry_deltas, -1., 1.),
                                target_probability=_bounded_mean(target_deltas, -1., 1.)))
    return dict(
        study_version=STUDY_VERSION, scientific_status='synthetic_neutral_resolution_diagnostic',
        convergence_status='not_assessed', mode='full',
        measurement_version=MEASUREMENT_VERSION, inheritance_version=INHERITANCE_VERSION,
        simulation_version=SIMULATION_VERSION, numpy_version=np.__version__,
        rng_bit_generator=report['rng_bit_generator'],
        protocol=dict(population_size=40, male_n=20, female_n=20,
                      initial_modern_individual_indices=[0, 20],
                      initial_state='both_homologues_modern_at_all_blocks_for_listed_individuals',
                      initial_ancestry=.05, generations=generations, seeds=list(seeds),
                      resolutions=list(resolutions), map_length=map_length,
                      map_rule='r=-expm1(-2*map_length/(B-1))/2',
                      target_interval=list(TARGET), target_inclusive=True,
                      confidence_level=.95, intervals_simultaneous=False),
        resolutions=rows, differences_from_finest=differences,
        total_work_units=dict(
            offspring_generated=sum(r['work_units']['offspring_generated'] for r in rows),
            block_copy_transmissions=sum(r['work_units']['block_copy_transmissions'] for r in rows),
            largest_population_state_allele_entries=max(r['work_units']['state_allele_entries'] for r in rows)),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='new JSON destination (no overwrite)')
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        parser.error('output already exists')
    report = run_resolution_study()
    try:
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write('\n')
    except OSError as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
