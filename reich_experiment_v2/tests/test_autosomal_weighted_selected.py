"""Explicit weighted reporting preserves the selected engine's RNG and dynamics."""

from copy import deepcopy
from itertools import product
import json
import unittest
from unittest.mock import patch

import numpy as np

from run_experiment import SCENARIOS
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap, copy_counts
from paleogen_rl.genetics.pulse import initialise_pulse
from paleogen_rl.genetics.selected import BlockSelection, ReproductionFailure, WEIGHTED_REPORT_VERSION, run_selected
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel, measure_weighted_ancestry


class TestWeightedSelected(unittest.TestCase):
    def inputs(self, fraction=.5, switch=.1):
        mapping = RecombinationMap(BlockPanel('synthetic-four', ('mt', 'n1', 'n2', 'y')), (switch,)*3)
        state, _ = initialise_pulse(population_size=40, f=fraction, male_fraction=.5, panel=mapping.panel)
        weighted = WeightedBlockPanel(mapping.panel, (2, 1, 1, 2), 'synthetic reporting fixture')
        return state, mapping, weighted

    def run_with_rng(self, state, **kwargs):
        constructor = np.random.default_rng
        generators = []
        def record(seed):
            generator = constructor(seed)
            generators.append(generator)
            return generator
        with patch('paleogen_rl.genetics.selected.np.random.default_rng', side_effect=record):
            result = run_selected(**state, **kwargs)
        self.assertEqual(len(generators), 1)
        return result, deepcopy(generators[0].bit_generator.state)

    def assert_states_equal(self, left, right):
        for field in ('haplotypes', 'sex', 'mt', 'y'):
            np.testing.assert_array_equal(getattr(left, field), getattr(right, field))
        self.assertEqual(left.report['work_units'], right.report['work_units'])

    def test_all_named_scenarios_and_dominances_preserve_states_costs_and_rng(self):
        cases = 0
        for (name, parameters), dominance, switch in product(SCENARIOS.items(),
                ('additive', 'dominant', 'recessive'), (0., .1)):
            state, mapping, weighted = self.inputs(switch=switch)
            selection = BlockSelection(**{k: v for k, v in parameters.items() if k not in ('s', 'sel_locus')},
                                       s_y=parameters.get('s', 0.), dominance=dominance,
                                       mt_partner_block='mt', y_partner_block='y')
            kwargs = dict(recombination_map=mapping, selection=selection, generations=4, seed=17)
            with self.subTest(scenario=name, dominance=dominance, switch=switch):
                legacy, expected_rng = self.run_with_rng(state, **kwargs)
                actual, actual_rng = self.run_with_rng(state, **kwargs, measurement_panel=weighted)
                self.assert_states_equal(legacy, actual)
                self.assertEqual(expected_rng, actual_rng)
                self.assertEqual(set(actual.report)-set(legacy.report), {'measurement_panel', 'report_version'})
                for key in legacy.report:
                    if key not in ('initial_measurement', 'final_measurement', 'measurement_version'):
                        self.assertEqual(actual.report[key], legacy.report[key], key)
                self.assertEqual(actual.report['initial_measurement'], measure_weighted_ancestry(
                    copy_counts(state['haplotypes']), weighted, generation=0, target_generation=0,
                    mode='full', partner_block_ids=('mt', 'y')))
                self.assertEqual(actual.report['final_measurement'], measure_weighted_ancestry(
                    copy_counts(actual.haplotypes), weighted, generation=4, target_generation=4,
                    mode='full', partner_block_ids=('mt', 'y')))
            cases += 1
        self.assertEqual(cases, len(SCENARIOS)*6)

    def test_configuration_roundtrip_and_real_replay(self):
        state, mapping, weighted = self.inputs()
        selection = BlockSelection(s_mt=.1, s_y=.05, mt_mod_nuc_arch=.2,
                                   mt_partner_block='mt', y_partner_block='y')
        first = run_selected(**state, recombination_map=mapping, selection=selection,
                             generations=5, seed=73, measurement_panel=weighted)
        report = json.loads(json.dumps(first.report, allow_nan=False))
        declaration = report['measurement_panel']
        restored = WeightedBlockPanel(BlockPanel(declaration['panel_id'], declaration['block_ids']),
                                       declaration['block_weights'], declaration['weight_basis'])
        map_declaration = report['recombination_map']
        restored_map = RecombinationMap(BlockPanel(**map_declaration['panel']), map_declaration['switch_probabilities'])
        replay = run_selected(**state, recombination_map=restored_map,
                              selection=BlockSelection(**report['selection']), generations=report['generations_requested'],
                              seed=report['seed'], max_rounds=report['max_rounds'], measurement_panel=restored)
        self.assert_states_equal(first, replay)
        self.assertEqual(first.report, replay.report)
        self.assertEqual(report['report_version'], WEIGHTED_REPORT_VERSION)
        self.assertEqual(report['measurement_version'], report['final_measurement']['measurement_version'])
        self.assertEqual(report['measurement_panel'], weighted.to_dict())
        for key, value in state.items():
            self.assertFalse(np.shares_memory(value, getattr(first, key)))

    def test_quick_and_zero_horizon_preserve_states_and_unavailability(self):
        for fraction, horizon in product((0., 1.), (0, 1, 8)):
            state, mapping, weighted = self.inputs(fraction=fraction)
            kwargs = dict(recombination_map=mapping, selection=BlockSelection(mt_partner_block='mt'),
                          generations=horizon, seed=42, stop_when_absorbed=True)
            legacy, legacy_rng = self.run_with_rng(state, **kwargs)
            result, actual_rng = self.run_with_rng(state, **kwargs, measurement_panel=weighted)
            self.assert_states_equal(legacy, result)
            self.assertEqual(legacy_rng, actual_rng)
            measurement = result.report['final_measurement']
            self.assertEqual(measurement['status'], 'not_evaluated_quick')
            for field in ('value', 'modern_ancestry_weight', 'unweighted_modern_allele_copies', 'partner_diagnostics'):
                self.assertIsNone(measurement[field])
            self.assertEqual(measurement['generation'], min(horizon, 1))
            self.assertEqual(measurement['target_generation'], horizon)
            self.assertEqual(result.report['initial_measurement']['value'], fraction)

    def test_invalid_measurement_panels_fail_before_rng(self):
        state, mapping, _ = self.inputs()
        invalid = [object(), mapping.panel,
                   WeightedBlockPanel(BlockPanel('another-id', mapping.panel.block_ids), (1,)*4, 'synthetic'),
                   WeightedBlockPanel(BlockPanel('synthetic-four', tuple(reversed(mapping.panel.block_ids))),
                                      (1,)*4, 'synthetic'),
                   WeightedBlockPanel(BlockPanel('synthetic-four', ('mt', 'y')), (1, 1), 'synthetic')]
        with patch('paleogen_rl.genetics.selected.np.random.default_rng') as rng:
            for panel in invalid:
                with self.subTest(panel=panel), self.assertRaises(ValueError):
                    run_selected(**state, recombination_map=mapping, selection=BlockSelection(),
                                 generations=2, seed=17, measurement_panel=panel)
            rng.assert_not_called()

    def test_reproductive_failure_keeps_weighted_configuration_and_partial_costs(self):
        state, mapping, weighted = self.inputs(fraction=0.)
        reports = []
        for measurement in (None, weighted):
            with self.assertRaises(ReproductionFailure) as error:
                run_selected(**state, recombination_map=mapping,
                             selection=BlockSelection(s_y=1., mt_partner_block='mt', y_partner_block='y'),
                             generations=4, seed=17, max_rounds=3, measurement_panel=measurement)
            report = json.loads(json.dumps(error.exception.report, allow_nan=False))
            self.assertIsNone(report['final_measurement'])
            self.assertEqual(report['generations_completed'], 0)
            self.assertEqual(report['failed_generation'], 1)
            reports.append(report)
        self.assertEqual(reports[0]['work_units'], reports[1]['work_units'])
        self.assertEqual(reports[1]['work_units']['candidates_generated'], 80)
        self.assertEqual(reports[1]['work_units']['accepted_candidates'], 20)
        self.assertEqual(reports[1]['work_units']['offspring_generated'], 0)
        self.assertEqual(reports[1]['measurement_panel'], weighted.to_dict())
        self.assertEqual(reports[1]['report_version'], WEIGHTED_REPORT_VERSION)

    def test_equal_weights_and_explicit_none_preserve_the_legacy_contract(self):
        state, mapping, _ = self.inputs()
        kwargs = dict(recombination_map=mapping, selection=BlockSelection(), generations=5, seed=17)
        legacy = run_selected(**state, **kwargs)
        explicit_none = run_selected(**state, **kwargs, measurement_panel=None)
        self.assertEqual(legacy.report, explicit_none.report)
        self.assertNotIn('measurement_panel', legacy.report)
        self.assertNotIn('report_version', legacy.report)
        equal_weights = WeightedBlockPanel(mapping.panel, (7,)*4, 'synthetic equal weights')
        weighted = run_selected(**state, **kwargs, measurement_panel=equal_weights)
        self.assert_states_equal(legacy, weighted)
        for field in ('initial_measurement', 'final_measurement'):
            self.assertAlmostEqual(legacy.report[field]['value'], weighted.report[field]['value'], places=14)
            self.assertNotEqual(legacy.report[field]['measurement_version'], weighted.report[field]['measurement_version'])


if __name__ == '__main__':
    unittest.main()
