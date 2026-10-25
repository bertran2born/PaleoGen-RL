"""Block inheritance with offspring mt/Y viability and optional marker stopping.

The historical engine and its Config are intentionally separate. This API
supports marker selection and the four reciprocal marker/block interactions.
"""

from dataclasses import asdict, dataclass
import hashlib
from numbers import Real

import numpy as np

from .ancestry import MEASUREMENT_VERSION, measure_ancestry
from .inheritance import INHERITANCE_VERSION, RecombinationMap, copy_counts, inherit_diploid
from .weighted_ancestry import (
    MEASUREMENT_VERSION as WEIGHTED_MEASUREMENT_VERSION, WeightedBlockPanel, measure_weighted_ancestry,
)


SIMULATION_VERSION = 'selected-autosomal-block-simulation-v1'
WEIGHTED_REPORT_VERSION = 'weighted-selected-autosomal-block-report-v1'
COEFFICIENTS = ('s_mt', 's_y', 'mt_mod_nuc_arch', 'mt_arch_nuc_mod',
                'y_mod_nuc_arch', 'y_arch_nuc_mod')


@dataclass(frozen=True)
class BlockSelection:
    s_mt: float = 0.
    s_y: float = 0.
    mt_mod_nuc_arch: float = 0.
    mt_arch_nuc_mod: float = 0.
    y_mod_nuc_arch: float = 0.
    y_arch_nuc_mod: float = 0.
    mt_partner_block: str | None = None
    y_partner_block: str | None = None
    dominance: str = 'additive'

    def __post_init__(self):
        for field in COEFFICIENTS:
            value = getattr(self, field)
            lower = -1 if field in ('s_mt', 's_y') else 0
            if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
                    or not np.isfinite(value) or not lower <= value <= 1):
                raise ValueError(f'{field} must be finite in [{lower}, 1]')
            object.__setattr__(self, field, float(value))
        if self.dominance not in ('additive', 'dominant', 'recessive'):
            raise ValueError('dominance must be additive/dominant/recessive')
        for field in ('mt_partner_block', 'y_partner_block'):
            block = getattr(self, field)
            if block is not None and (not isinstance(block, str) or not block or block != block.strip()):
                raise ValueError(f'{field} must be a trimmed identifier or None')
        if (self.mt_mod_nuc_arch or self.mt_arch_nuc_mod) and self.mt_partner_block is None:
            raise ValueError('active mt interactions require mt_partner_block')
        if (self.y_mod_nuc_arch or self.y_arch_nuc_mod) and self.y_partner_block is None:
            raise ValueError('active Y interactions require y_partner_block')


@dataclass
class SelectedRun:
    haplotypes: np.ndarray
    sex: np.ndarray
    mt: np.ndarray
    y: np.ndarray
    report: dict


class ReproductionFailure(RuntimeError):
    """Bounded rejection exhausted; report never contains a final measurement."""

    def __init__(self, report):
        self.report = report
        super().__init__(f"reproduction_failed: seed={report['seed']}, "
                         f"generations_completed={report['generations_completed']}, "
                         f"failed_generation={report['failed_generation']}")


def _survival(selection, sex, mt, y, counts, panel):
    """Offspring viability for validated arrays (also usable in reference tests)."""
    male = sex == 1
    survival = ((1-abs(selection.s_mt)*(mt == (0 if selection.s_mt >= 0 else 1)))
                * (1-abs(selection.s_y)*(male & (y == (0 if selection.s_y >= 0 else 1)))))

    def exposure(block, archaic):
        copies = counts[:, panel.block_ids.index(block)]
        incompatible = 2-copies if archaic else copies
        if selection.dominance == 'additive':
            return incompatible/2
        if selection.dominance == 'dominant':
            return incompatible > 0
        return incompatible == 2

    for coefficient, marker, allele, block, archaic, y_only in (
        (selection.mt_mod_nuc_arch, mt, 1, selection.mt_partner_block, True, False),
        (selection.mt_arch_nuc_mod, mt, 0, selection.mt_partner_block, False, False),
        (selection.y_mod_nuc_arch, y, 1, selection.y_partner_block, True, True),
        (selection.y_arch_nuc_mod, y, 0, selection.y_partner_block, False, True),
    ):
        if coefficient:
            applies = marker == allele
            if y_only:
                applies = applies & male
            survival *= 1-coefficient*applies*exposure(block, archaic)
    return survival


def _marker(values, size, name, allowed):
    if np.ma.isMaskedArray(values) and np.any(np.ma.getmaskarray(values)):
        raise ValueError(f'{name} must not contain masked values')
    array = np.asarray(values)
    if (array.ndim != 1 or array.size != size or array.dtype.kind not in ('b', 'i', 'u')
            or not np.all(np.isin(array, allowed))):
        raise ValueError(f'{name} must have one integer entry per individual in {allowed}')
    return array


def run_selected(haplotypes, sex, mt, y, *, recombination_map, selection,
                 generations, seed, max_rounds=200, stop_when_absorbed=False, measurement_panel=None):
    """Run fixed-size, separate-sex reproduction and offspring rejection.

    Parent groups are sampled uniformly. Failed slots are retried with their
    assigned sex, always from the previous generation. Zero selection consumes
    exactly the block RNG stream of run_neutral, irrespective of annotations.
    Full mode is the default. Optional stopping checks both markers after each
    complete generation and always leaves final ancestry unavailable.
    An explicit weighted measurement panel changes only the measurement report,
    never selection, inheritance, random draws or marker stopping.
    """
    if not isinstance(recombination_map, RecombinationMap):
        raise ValueError('recombination_map must be a RecombinationMap')
    if measurement_panel is not None and (
            not isinstance(measurement_panel, WeightedBlockPanel)
            or measurement_panel.panel != recombination_map.panel):
        raise ValueError('measurement_panel must be weighted and match the recombination panel exactly')
    if not isinstance(selection, BlockSelection):
        raise ValueError('selection must be a BlockSelection')
    if type(stop_when_absorbed) is not bool:
        raise ValueError('stop_when_absorbed must be a bool')
    for name, value, minimum in (('generations', generations, 0), ('seed', seed, 0),
                                  ('max_rounds', max_rounds, 1)):
        if type(value) is not int or value < minimum:
            raise ValueError(f'{name} must be an integer >= {minimum}')
    counts = copy_counts(haplotypes)
    size, blocks = counts.shape
    panel = recombination_map.panel
    if blocks != len(panel.block_ids):
        raise ValueError('haplotypes must match the declared panel')
    sx = _marker(sex, size, 'sex', (0, 1))
    maternal = _marker(mt, size, 'mt', (0, 1))
    paternal = _marker(y, size, 'y', (-1, 0, 1))
    male_n, female_n = size//2, size-size//2
    if male_n == 0 or int((sx == 1).sum()) != male_n:
        raise ValueError('sex counts must match N//2 males and N-N//2 females')
    if np.any(paternal[sx == 0] != -1) or np.any(paternal[sx == 1] == -1):
        raise ValueError('Y must be 0/1 in males and -1 in females')
    partners = tuple(dict.fromkeys(block for block in
                     (selection.mt_partner_block, selection.y_partner_block) if block is not None))
    measure = measure_ancestry if measurement_panel is None else measure_weighted_ancestry
    measured_panel = panel if measurement_panel is None else measurement_panel
    initial_measurement = measure(counts, measured_panel, generation=0, target_generation=0,
                                         mode='full', partner_block_ids=partners)
    population = np.asarray(haplotypes, dtype=np.uint8).copy()
    sx, maternal, paternal = (sx.astype(np.uint8, copy=True), maternal.astype(np.uint8, copy=True),
                              paternal.astype(np.int8, copy=True))
    offspring_sex = np.array([1]*male_n+[0]*female_n, dtype=np.uint8)
    selecting = any(getattr(selection, field) for field in COEFFICIENTS)
    rng = np.random.default_rng(seed)
    report = dict(
        simulation_version=SIMULATION_VERSION,
        measurement_version=MEASUREMENT_VERSION if measurement_panel is None else WEIGHTED_MEASUREMENT_VERSION,
        inheritance_version=INHERITANCE_VERSION, model='sex_structured_selected_blocks',
        scientific_status='exploratory_block_simulation', mode='quick' if stop_when_absorbed else 'full', seed=seed,
        numpy_version=np.__version__, rng_bit_generator=type(rng.bit_generator).__name__,
        selection=asdict(selection), recombination_map=recombination_map.to_dict(),
        population_size=size, male_n=male_n, female_n=female_n, max_rounds=max_rounds,
        generations_requested=generations, generations_completed=0,
        termination_reason='horizon_reached', final_measurement=None,
        initial_measurement=initial_measurement,
        work_units=dict(candidates_generated=0, accepted_candidates=0, offspring_generated=0,
                        block_copy_transmissions=0, state_allele_entries=2*size*blocks),
    )
    if measurement_panel is not None:
        report.update(report_version=WEIGHTED_REPORT_VERSION, measurement_panel=measurement_panel.to_dict())
    for name, array in (('haplotypes', population), ('sex', sx), ('mt', maternal), ('y', paternal)):
        report[f'initial_{name}_sha256'] = hashlib.sha256(array.tobytes()).hexdigest()
    work = report['work_units']
    for generation in range(generations):
        mothers, fathers = np.flatnonzero(sx == 0), np.flatnonzero(sx == 1)
        pending = np.arange(size)
        next_population = np.empty_like(population)
        next_mt, next_y = np.empty_like(maternal), np.empty_like(paternal)
        for _ in range(max_rounds):
            mo = rng.choice(mothers, size=pending.size)
            fa = rng.choice(fathers, size=pending.size)
            proposed = inherit_diploid(population, mothers=mo, fathers=fa,
                                       recombination_map=recombination_map, rng=rng)
            proposed_mt = maternal[mo]
            proposed_y = np.where(offspring_sex[pending] == 1, paternal[fa], -1).astype(np.int8)
            work['candidates_generated'] += int(pending.size)
            work['block_copy_transmissions'] += int(2*blocks*pending.size)
            if selecting:
                weights = _survival(selection, offspring_sex[pending], proposed_mt,
                                    proposed_y, copy_counts(proposed), panel)
                keep = rng.random(pending.size) < weights
            else:
                keep = np.ones(pending.size, dtype=bool)
            accepted = pending[keep]
            next_population[accepted] = proposed[keep]
            next_mt[accepted] = proposed_mt[keep]
            next_y[accepted] = proposed_y[keep]
            work['accepted_candidates'] += int(accepted.size)
            pending = pending[~keep]
            if pending.size == 0:
                break
        if pending.size:
            report.update(termination_reason='reproduction_failed', failed_generation=generation+1,
                          unfilled_offspring_slots=int(pending.size))
            raise ReproductionFailure(report)
        population, sx, maternal, paternal = next_population, offspring_sex.copy(), next_mt, next_y
        report['generations_completed'] += 1
        work['offspring_generated'] += size
        if stop_when_absorbed:
            mt_absorbed = np.all(maternal == 0) or np.all(maternal == 1)
            male_y = paternal[sx == 1]
            y_absorbed = np.all(male_y == 0) or np.all(male_y == 1)
            if mt_absorbed and y_absorbed and report['generations_completed'] < generations:
                report['termination_reason'] = 'markers_absorbed'
                break
    report['final_measurement'] = measure(
        copy_counts(population), measured_panel, generation=report['generations_completed'], target_generation=generations,
        mode='quick' if stop_when_absorbed else 'full', partner_block_ids=partners)
    return SelectedRun(population, sx, maternal, paternal, report)
