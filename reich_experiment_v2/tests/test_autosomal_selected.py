"""Selected block engine: I15's fixed analytical and statistical controls."""

from dataclasses import asdict
from itertools import product
import hashlib
import json
from math import log, sqrt
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from epi_pulse import Config, _epistasis_loss
import reich_panmictic_original as original
from run_experiment import SCENARIOS
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap, copy_counts, inherit_diploid
from paleogen_rl.genetics.neutral import run_neutral
from paleogen_rl.genetics.selected import (
    BlockSelection, ReproductionFailure, SIMULATION_VERSION, _survival, run_selected,
)


EXPOSURE = {'additive': (0., .5, 1.), 'dominant': (0., 1., 1.),
            'recessive': (0., 0., 1.)}
SELECTION_SEEDS = (524287, 655357, 786433)


def mapping(blocks=4, switch=.25):
    return RecombinationMap(BlockPanel(f'synthetic-selected-{blocks}',
                                       tuple(f'b{i}' for i in range(blocks))),
                            (switch,)*(blocks-1))


def fixture(size=40, blocks=4):
    rng = np.random.default_rng(963)
    haplotypes = rng.integers(0, 2, size=(size, 2, blocks), dtype=np.uint8)
    sex = np.array([1]*(size//2)+[0]*(size-size//2), dtype=np.uint8)
    mt = rng.integers(0, 2, size=size, dtype=np.uint8)
    y = np.where(sex == 1, rng.integers(0, 2, size=size), -1).astype(np.int8)
    return haplotypes, sex, mt, y


class TestAutosomalSelected(unittest.TestCase):
    def test_viability_matches_analytical_tables_and_m2(self):
        cases = [case for case in product((0, 1), (0, 1), (-1, 0, 1), range(3), range(3))
                 if (case[0] == 0 and case[2] == -1) or (case[0] == 1 and case[2] in (0, 1))]
        sx, mt, y = (np.array([case[i] for case in cases]) for i in range(3))
        counts = np.zeros((len(cases), 3), dtype=np.uint8)
        counts[:, 2] = [case[3] for case in cases]
        counts[:, 1] = [case[4] for case in cases]
        panel = mapping(3).panel
        for dominance, s_mt, s_y in product(EXPOSURE, (-.3, 0., .2), (-.4, 0., .25)):
            with self.subTest(dominance=dominance, s_mt=s_mt, s_y=s_y):
                selection = BlockSelection(s_mt=s_mt, s_y=s_y, mt_mod_nuc_arch=.2,
                                           mt_arch_nuc_mod=.3, y_mod_nuc_arch=.4,
                                           y_arch_nuc_mod=.5, mt_partner_block='b2',
                                           y_partner_block='b1', dominance=dominance)
                expected = []
                for sex, maternal, paternal, mc, yc in cases:
                    weight = 1-abs(s_mt)*(maternal == (0 if s_mt >= 0 else 1))
                    if sex == 1:
                        weight *= 1-abs(s_y)*(paternal == (0 if s_y >= 0 else 1))
                    table = EXPOSURE[dominance]
                    weight *= 1-(.2*table[2-mc] if maternal == 1 else .3*table[mc])
                    if sex == 1 and paternal in (0, 1):
                        weight *= 1-(.4*table[2-yc] if paternal == 1 else .5*table[yc])
                    expected.append(weight)
                actual = _survival(selection, sx, mt, y, counts, panel)
                np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-15)
                config = Config(s_mt=s_mt, s=s_y, sel_locus='Y',
                                mt_mod_nuc_arch=.2, mt_arch_nuc_mod=.3,
                                y_mod_nuc_arch=.4, y_arch_nuc_mod=.5,
                                mt_partner_locus=2, y_partner_locus=1,
                                mismatch_dominance=dominance)
                ref = 1-_epistasis_loss(config, sx, mt, y, counts)
                ref *= 1-abs(s_y)*original._disfavoured_count(config, sx, mt, y, counts, None)
                ref *= 1-abs(s_mt)*(mt == (0 if s_mt >= 0 else 1))
                np.testing.assert_allclose(actual, ref, rtol=0, atol=1e-15)

    def test_each_reciprocal_term_in_isolation_and_y_sex_mask(self):
        cases = list(product((0, 1), (0, 1), (-1, 0, 1), range(3)))
        sx, mt, y = (np.array([case[i] for case in cases]) for i in range(3))
        counts = np.array([[case[3]] for case in cases])
        for dominance, field in product(EXPOSURE, ('mt_mod_nuc_arch', 'mt_arch_nuc_mod',
                                                  'y_mod_nuc_arch', 'y_arch_nuc_mod')):
            with self.subTest(field=field, dominance=dominance):
                selection = BlockSelection(**{field: 1.}, mt_partner_block='b0',
                                           y_partner_block='b0', dominance=dominance)
                actual = _survival(selection, sx, mt, y, counts, mapping(1).panel)
                expected = []
                for sex, maternal, paternal, copies in cases:
                    marker = paternal if field.startswith('y_') else maternal
                    allele = 1 if '_mod_nuc_' in field else 0
                    exposed = EXPOSURE[dominance][2-copies if field.endswith('_arch') else copies]
                    applies = marker == allele and (sex == 1 or field.startswith('mt_'))
                    expected.append(1-exposed if applies else 1.)
                np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-15)

    def test_zero_selection_matches_i13_with_and_without_partner_annotations(self):
        for size, blocks, switch, seed in product((5, 40), (2, 8), (0., .25), (0, 17, 42)):
            inputs = fixture(size, blocks)
            haps, sex, mt, y = inputs
            declaration = mapping(blocks, switch)
            neutral = run_neutral(haps, sex, recombination_map=declaration, generations=5, seed=seed)
            for selection in (BlockSelection(), BlockSelection(mt_partner_block='b0', y_partner_block='b1')):
                with self.subTest(N=size, B=blocks, switch=switch, seed=seed, selection=selection):
                    selected = run_selected(*inputs, recombination_map=declaration,
                                            selection=selection, generations=5, seed=seed)
                    np.testing.assert_array_equal(selected.haplotypes, neutral.haplotypes)
                    np.testing.assert_array_equal(selected.sex, neutral.sex)
                    for field in ('value', 'panel', 'modern_allele_copies', 'allele_copy_denominator'):
                        self.assertEqual(selected.report['final_measurement'][field],
                                         neutral.report['final_measurement'][field])
                    self.assertEqual(selected.report['work_units']['candidates_generated'], size*5)

    def test_parents_markers_and_gametes_are_consistent_for_each_proposal(self):
        for size in (5, 6):
            initial, sex, mt, y = fixture(size, 3)
            observations = []
            selection = BlockSelection(s_mt=.3, s_y=-.2)
            def transmit(population, **kwargs):
                mo, fa = kwargs['mothers'], kwargs['fathers']
                np.testing.assert_array_equal(population, initial)
                self.assertTrue(np.all(sex[mo] == 0))
                self.assertTrue(np.all(sex[fa] == 1))
                result = inherit_diploid(population, **kwargs)
                observations.append((mo, fa, result))
                return result
            def viability(config, proposed_sex, proposed_mt, proposed_y, counts, panel):
                mo, fa, transmitted = observations[-1]
                np.testing.assert_array_equal(proposed_mt, mt[mo])
                np.testing.assert_array_equal(proposed_y, np.where(proposed_sex == 1, y[fa], -1))
                np.testing.assert_array_equal(counts, copy_counts(transmitted))
                return _survival(config, proposed_sex, proposed_mt, proposed_y, counts, panel)
            with patch('paleogen_rl.genetics.selected.inherit_diploid', side_effect=transmit):
                with patch('paleogen_rl.genetics.selected._survival', side_effect=viability):
                    result = run_selected(initial, sex, mt, y, recombination_map=mapping(3),
                                          selection=selection, generations=1, seed=73)
            np.testing.assert_array_equal(result.sex, [1]*(size//2)+[0]*(size-size//2))
            self.assertTrue(np.all(result.y[result.sex == 0] == -1))
            self.assertGreaterEqual(len(observations), 1)

    def test_preregistered_offspring_selection_and_linked_ancestry(self):
        size = 20000
        haps = np.zeros((size, 2, 2), dtype=np.uint8)
        haps[:, 1, :] = 1
        sex = np.array([1]*(size//2)+[0]*(size//2), dtype=np.uint8)
        mt = np.ones(size, dtype=np.uint8)
        y = np.where(sex == 1, 0, -1).astype(np.int8)
        selection = BlockSelection(mt_mod_nuc_arch=1., mt_partner_block='b0')
        tolerance = sqrt(log(2*9/.001)/(2*size))
        for seed in SELECTION_SEEDS:
            with self.subTest(seed=seed):
                result = run_selected(haps, sex, mt, y, recombination_map=mapping(2, 0.),
                                      selection=selection, generations=1, seed=seed)
                counts = copy_counts(result.haplotypes)
                proportions = np.bincount(counts[:, 0], minlength=3)/size
                np.testing.assert_allclose(proportions, [0., .5, .5], atol=tolerance, rtol=0)
                self.assertEqual(proportions[0], 0.)
                np.testing.assert_array_equal(counts[:, 0], counts[:, 1])
                self.assertLessEqual(abs(result.report['final_measurement']['value']-.75), tolerance/2)
                self.assertGreater(result.report['work_units']['candidates_generated'], size)
                self.assertEqual(result.report['work_units']['accepted_candidates'], size)

    def test_named_scenarios_keep_the_same_measurement_panel(self):
        haps = np.zeros((40, 2, 8), dtype=np.uint8)
        haps[[0, 20], :, :] = 1
        sex = np.array([1]*20+[0]*20, dtype=np.uint8)
        mt = haps[:, 0, 0].copy()
        y = np.where(sex == 1, mt.astype(np.int8), -1).astype(np.int8)
        for scenario, parameters in SCENARIOS.items():
            # Fail if a future named scenario introduces an unsupported mechanism.
            self.assertLessEqual(set(parameters), {'s', 's_mt', 'sel_locus', 'mt_mod_nuc_arch',
                                                  'mt_arch_nuc_mod', 'y_mod_nuc_arch', 'y_arch_nuc_mod'})
            self.assertEqual(parameters.get('sel_locus', 'Y'), 'Y')
            for dominance, switch in product(EXPOSURE, (0., .25)):
                with self.subTest(scenario=scenario, dominance=dominance, switch=switch):
                    options = {key: value for key, value in parameters.items() if key not in ('s', 'sel_locus')}
                    selection = BlockSelection(**options, s_y=parameters.get('s', 0.),
                                               mt_partner_block='b0', y_partner_block='b1', dominance=dominance)
                    result = run_selected(haps, sex, mt, y, selection=selection,
                                          recombination_map=mapping(8, switch), generations=4, seed=17)
                    measurement = result.report['final_measurement']
                    self.assertEqual(measurement['panel']['block_count'], 8)
                    self.assertEqual(measurement['allele_copy_denominator'], 640)
                    self.assertEqual(measurement['modern_allele_copies'], int(result.haplotypes.sum()))
                    self.assertEqual(measurement['partner_block_ids'], ['b0', 'b1'])
                    self.assertEqual(measurement['generation'], 4)

    def test_repeatability_owned_states_json_provenance_and_work(self):
        inputs = fixture()
        before = [array.copy() for array in inputs]
        global_before = np.random.get_state()
        options = dict(recombination_map=mapping(), selection=BlockSelection(
            mt_partner_block='b0', y_partner_block='b1', mt_mod_nuc_arch=.3,
            y_arch_nuc_mod=.2, s_mt=-.1, s_y=.1), generations=7, seed=81)
        first = run_selected(*inputs, **options)
        report = json.loads(json.dumps(first.report, allow_nan=False))
        declaration = report['recombination_map']
        restored_map = RecombinationMap(BlockPanel(**declaration['panel']),
                                        declaration['switch_probabilities'])
        replayed = run_selected(*inputs, recombination_map=restored_map,
                                selection=BlockSelection(**report['selection']),
                                generations=report['generations_requested'], seed=report['seed'],
                                max_rounds=report['max_rounds'])
        self.assertEqual(report, replayed.report)
        self.assertEqual(report['simulation_version'], SIMULATION_VERSION)
        self.assertEqual(report['selection'], asdict(options['selection']))
        self.assertEqual(report['recombination_map'], options['recombination_map'].to_dict())
        self.assertEqual(report['termination_reason'], 'horizon_reached')
        self.assertEqual(report['generations_completed'], 7)
        for field, array, initial in zip(('haplotypes', 'sex', 'mt', 'y'),
                                         (first.haplotypes, first.sex, first.mt, first.y), inputs):
            np.testing.assert_array_equal(array, getattr(replayed, field))
            self.assertFalse(np.shares_memory(array, initial))
            self.assertEqual(report[f'initial_{field}_sha256'], hashlib.sha256(initial.tobytes()).hexdigest())
        for old, new in zip(before, inputs):
            np.testing.assert_array_equal(old, new)
        for old, new in zip(global_before, np.random.get_state()):
            np.testing.assert_equal(old, new)
        work = report['work_units']
        self.assertEqual(work['offspring_generated'], 280)
        self.assertEqual(work['accepted_candidates'], 280)
        self.assertGreater(work['candidates_generated'], 280)
        self.assertEqual(work['block_copy_transmissions'], 8*work['candidates_generated'])

    def test_zero_horizon_and_absorption_complete_the_declared_clock(self):
        for modern, switch in product((0, 1), (0., .25)):
            haps = np.full((6, 2, 3), modern, dtype=np.uint8)
            sex = np.array([1, 1, 1, 0, 0, 0], dtype=np.uint8)
            mt = np.full(6, modern, dtype=np.uint8)
            y = np.where(sex == 1, modern, -1).astype(np.int8)
            for generations in (0, 5):
                result = run_selected(haps, sex, mt, y, recombination_map=mapping(3, switch),
                                      selection=BlockSelection(s_mt=.1, s_y=-.1),
                                      generations=generations, seed=17)
                np.testing.assert_array_equal(result.haplotypes, haps)
                self.assertFalse(np.shares_memory(result.haplotypes, haps))
                self.assertFalse(np.shares_memory(result.sex, sex))
                self.assertFalse(np.shares_memory(result.mt, mt))
                self.assertFalse(np.shares_memory(result.y, y))
                self.assertEqual(result.report['generations_completed'], generations)
                self.assertEqual(result.report['final_measurement']['value'], float(modern))

    def test_partial_sex_specific_failure_has_no_final_measurement(self):
        haps, sex, mt, _ = fixture(6, 3)
        y = np.where(sex == 1, 0, -1).astype(np.int8)
        with self.assertRaises(ReproductionFailure) as error:
            run_selected(haps, sex, mt, y, recombination_map=mapping(3),
                         selection=BlockSelection(s_y=1.), generations=4, seed=17, max_rounds=3)
        report = json.loads(json.dumps(error.exception.report, allow_nan=False))
        self.assertEqual(report['termination_reason'], 'reproduction_failed')
        self.assertEqual(report['generations_completed'], 0)
        self.assertEqual(report['failed_generation'], 1)
        self.assertEqual(report['unfilled_offspring_slots'], 3)
        self.assertIsNone(report['final_measurement'])
        self.assertEqual(report['work_units'], dict(candidates_generated=12, accepted_candidates=3,
                                                  offspring_generated=0, block_copy_transmissions=72,
                                                  state_allele_entries=36))

    def test_later_failure_counts_only_complete_generations(self):
        inputs = fixture(6, 3)
        calls = 0
        def force_second_generation_failure(config, sex, mt, y, counts, panel):
            nonlocal calls
            calls += 1
            return np.ones(sex.size) if calls == 1 else np.zeros(sex.size)
        with patch('paleogen_rl.genetics.selected._survival', side_effect=force_second_generation_failure):
            with self.assertRaises(ReproductionFailure) as error:
                run_selected(*inputs, recombination_map=mapping(3), selection=BlockSelection(s_mt=.1),
                             generations=3, seed=17, max_rounds=2)
        report = error.exception.report
        self.assertEqual(report['generations_completed'], 1)
        self.assertEqual(report['failed_generation'], 2)
        self.assertIsNone(report['final_measurement'])
        self.assertEqual(report['work_units']['offspring_generated'], 6)
        self.assertEqual(report['work_units']['accepted_candidates'], 6)
        self.assertEqual(report['work_units']['candidates_generated'], 18)

    def test_invalid_selection_and_population_fail_before_rng(self):
        for options in (dict(s_mt=float('nan')), dict(s_y=1.1), dict(s_y=-1.1),
                        dict(s_mt=True), dict(mt_mod_nuc_arch=-.1), dict(y_arch_nuc_mod=2.),
                        dict(mt_arch_nuc_mod=.2), dict(y_mod_nuc_arch=.2),
                        dict(dominance='unknown'), dict(mt_partner_block=' b0'),
                        dict(y_partner_block=1)):
            with self.subTest(options=options), self.assertRaises(ValueError):
                BlockSelection(**options)
        haps, sex, mt, y = fixture(6, 3)
        valid = dict(haplotypes=haps, sex=sex, mt=mt, y=y, recombination_map=mapping(3),
                     selection=BlockSelection(), generations=3, seed=17)
        invalid = [dict(seed=-1), dict(seed=True), dict(generations=2.), dict(generations=-1),
                   dict(max_rounds=0), dict(max_rounds=True), dict(selection=Config()),
                   dict(recombination_map=None), dict(recombination_map=mapping(4)),
                   dict(selection=BlockSelection(mt_partner_block='missing')),
                   dict(haplotypes=np.ma.array(haps, mask=True)), dict(haplotypes=haps[:, 0, :]),
                   dict(haplotypes=np.full_like(haps, 2)), dict(sex=np.zeros(6, dtype=int)),
                   dict(sex=np.full(6, 2)), dict(sex=sex[:-1]), dict(sex=sex.astype(float)),
                   dict(mt=mt[:-1]), dict(mt=mt.astype(float)), dict(mt=np.full(6, 2)),
                   dict(mt=np.ma.array(mt, mask=True)), dict(y=np.zeros(6, dtype=int)),
                   dict(y=np.full(6, -1)), dict(y=y.astype(float)), dict(y=y[:-1])]
        with patch('paleogen_rl.genetics.selected.np.random.default_rng') as generator:
            for overrides in invalid:
                with self.subTest(overrides=repr(overrides)), self.assertRaises(ValueError):
                    run_selected(**{**valid, **overrides})
            generator.assert_not_called()


if __name__ == '__main__':
    unittest.main()
