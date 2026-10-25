"""Full-horizon neutral Wright-Fisher control using phased autosomal blocks.

This separate control reuses I11/I12 and does not change the historical engine,
initialize a pulse, or implement selection and uniparental marker events.
"""

from dataclasses import dataclass
import hashlib

import numpy as np

from .ancestry import measure_ancestry
from .inheritance import RecombinationMap, copy_counts, inherit_diploid


SIMULATION_VERSION = 'neutral-autosomal-block-simulation-v1'


@dataclass
class NeutralRun:
    """Owned final arrays and a separately JSON-serializable report."""

    haplotypes: np.ndarray
    sex: np.ndarray
    report: dict


def run_neutral(haplotypes, sex, *, recombination_map, generations, seed,
                partner_block_ids=()):
    """Run a fixed-size neutral population through every requested generation.

    Initial males (sex=1) must number N//2 and females (sex=0) N-N//2.
    Their input order is arbitrary; children are ordered males then females.
    All randomness belongs to a fresh local Generator with the explicit seed.
    """
    if not isinstance(recombination_map, RecombinationMap):
        raise ValueError('recombination_map must be a RecombinationMap')
    for name, value in (('generations', generations), ('seed', seed)):
        if type(value) is not int or value < 0:
            raise ValueError(f'{name} must be a nonnegative integer')
    initial_counts = copy_counts(haplotypes)
    population_size, blocks = initial_counts.shape
    if blocks != len(recombination_map.panel.block_ids):
        raise ValueError('initial haplotypes must match the declared panel block count')
    if np.ma.isMaskedArray(sex) and np.any(np.ma.getmaskarray(sex)):
        raise ValueError('sex must not contain masked values')
    initial_sex = np.asarray(sex)
    if initial_sex.ndim != 1 or initial_sex.size != population_size:
        raise ValueError('sex must have one entry per diploid individual')
    if initial_sex.dtype.kind not in ('b', 'i', 'u') or np.any((initial_sex != 0) & (initial_sex != 1)):
        raise ValueError('sex must contain only female=0 or male=1')
    male_n = population_size // 2
    female_n = population_size - male_n
    if male_n == 0 or int((initial_sex == 1).sum()) != male_n:
        raise ValueError('sex counts must match the M2 quotas N//2 males and N-N//2 females')
    initial_measurement = measure_ancestry(
        initial_counts, recombination_map.panel, generation=0, target_generation=0,
        mode='full', partner_block_ids=partner_block_ids)
    population = np.asarray(haplotypes, dtype=np.uint8).copy()
    current_sex = initial_sex.astype(np.uint8, copy=True)
    initial_haplotypes_sha256 = hashlib.sha256(population.tobytes()).hexdigest()
    initial_sex_sha256 = hashlib.sha256(current_sex.tobytes()).hexdigest()
    offspring_sex = np.concatenate((np.ones(male_n, dtype=np.uint8),
                                    np.zeros(female_n, dtype=np.uint8)))
    rng = np.random.default_rng(seed)
    completed = 0
    for _ in range(generations):
        mothers = rng.choice(np.flatnonzero(current_sex == 0), size=population_size)
        fathers = rng.choice(np.flatnonzero(current_sex == 1), size=population_size)
        population = inherit_diploid(population, mothers=mothers, fathers=fathers,
                                     recombination_map=recombination_map, rng=rng)
        current_sex = offspring_sex.copy()
        completed += 1
    final_measurement = measure_ancestry(
        copy_counts(population), recombination_map.panel, generation=completed,
        target_generation=generations, mode='full', partner_block_ids=partner_block_ids)
    report = dict(
        simulation_version=SIMULATION_VERSION, model='sex_structured_neutral_wright_fisher',
        scientific_status='neutral_simulation', mode='full', seed=seed,
        numpy_version=np.__version__, rng_bit_generator=type(rng.bit_generator).__name__,
        population_size=population_size, male_n=male_n, female_n=female_n,
        generations_requested=generations, generations_completed=completed,
        termination_reason='horizon_reached', recombination_map=recombination_map.to_dict(),
        initial_haplotypes_sha256=initial_haplotypes_sha256, initial_sex_sha256=initial_sex_sha256,
        initial_measurement=initial_measurement, final_measurement=final_measurement,
        work_units=dict(offspring_generated=population_size*completed,
                        block_copy_transmissions=2*population_size*blocks*completed,
                        state_allele_entries=2*population_size*blocks),
    )
    return NeutralRun(haplotypes=population, sex=current_sex, report=report)
