"""Weighted pulse evaluation: unchanged dynamics, explicit endpoint and mode rules."""

from copy import deepcopy
from itertools import product
import json
from math import comb
import unittest
from unittest.mock import patch

import numpy as np

from run_experiment import SCENARIOS
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.pulse import (
    EVALUATION_VERSION, MODE_EVALUATION_VERSION, WEIGHTED_EVALUATION_VERSION,
    WEIGHTED_MODE_EVALUATION_VERSION, evaluate_block_pulse, initialise_pulse,
)
from paleogen_rl.genetics.selected import BlockSelection, ReproductionFailure, run_selected
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel


class TestWeightedPulse(unittest.TestCase):
    def arguments(self, **changes):
        mapping = RecombinationMap(BlockPanel('synthetic-three', ('mt', 'middle', 'y')), (.1, .1))
        return {**dict(population_size=40, f=.5, male_fraction=.5, generations=4, seed=17,
                       recombination_map=mapping,
                       selection=BlockSelection(mt_partner_block='mt', y_partner_block='y'),
                       measurement_panel=WeightedBlockPanel(mapping.panel, (1, 18, 1), 'synthetic fixture')),
                **changes}

    def test_real_reference_matrix_matches_full_and_preserves_marker_costs(self):
        cases = 0
        for (name, parameters), dominance, switch, fraction in product(
                SCENARIOS.items(), ('additive', 'dominant', 'recessive'), (0., .1), (0., .5, 1.)):
            args = self.arguments(f=fraction)
            args['recombination_map'] = RecombinationMap(args['measurement_panel'].panel, (switch, switch))
            args['selection'] = BlockSelection(
                **{k: v for k, v in parameters.items() if k not in ('s', 'sel_locus')},
                s_y=parameters.get('s', 0.), dominance=dominance, mt_partner_block='mt', y_partner_block='y')
            with self.subTest(scenario=name, dominance=dominance, switch=switch, f=fraction):
                full = evaluate_block_pulse(**args)
                quick = evaluate_block_pulse(**args, mode='quick')
                adaptive = evaluate_block_pulse(**args, mode='adaptive')
                legacy = evaluate_block_pulse(**{**args, 'measurement_panel': None})
                self.assertEqual(full['sampling'], legacy['sampling'])
                self.assertEqual(full['engine_report']['work_units'], legacy['engine_report']['work_units'])
                self.assertEqual(full['evaluation_version'], WEIGHTED_EVALUATION_VERSION)
                for result in (quick, adaptive):
                    self.assertEqual(result['evaluation_version'], WEIGHTED_MODE_EVALUATION_VERSION)
                    self.assertEqual(result['measurement_panel'], full['measurement_panel'])
                    for field, value in full['sampling'].items():
                        self.assertEqual(result['sampling'][field], value)
                self.assertIsNone(quick['ancestry_measurement']['value'])
                self.assertIsNone(quick['target']['target_auto'])
                self.assertIsNone(quick['target']['joint_and_target'])
                self.assertEqual(adaptive['target']['joint_and_target'], full['target']['joint_and_target'])
                if full['sampling']['p10_joint'] > 0:
                    self.assertEqual(adaptive['ancestry_measurement']['value'], full['engine_report']['final_measurement']['value'])
                    self.assertEqual(adaptive['engine_report'], full['engine_report'])
                    self.assertEqual(adaptive['continuation_status'], 'rerun_to_target')
                else:
                    self.assertIsNone(adaptive['ancestry_measurement']['value'])
                    self.assertIsNone(adaptive['target']['target_auto'])
                    self.assertEqual(adaptive['continuation_status'], 'skipped_event_impossible')
                for result in (quick, adaptive):
                    work = result['work_units']
                    reports = [result['screening_report']]
                    if result['continuation_status'] == 'rerun_to_target':
                        reports.append(result['engine_report'])
                    for field in ('candidates_generated', 'accepted_candidates', 'offspring_generated', 'block_copy_transmissions'):
                        self.assertEqual(work[field], sum(r['work_units'][field] for r in reports))
                    self.assertEqual(work['state_allele_entries'], 240)
            cases += 1
        self.assertEqual(cases, len(SCENARIOS)*18)

    def test_real_zero_horizon_measurements_at_target_boundaries_and_exact_sampling(self):
        args = self.arguments(population_size=100, generations=0)
        args['measurement_panel'] = WeightedBlockPanel(args['recombination_map'].panel, (1, 2, 1), 'synthetic boundary fixture')
        for copies in (23, 24, 25, 55, 56, 57):
            state, _ = initialise_pulse(population_size=100, f=1., male_fraction=.5,
                                        panel=args['measurement_panel'].panel)
            state['haplotypes'][:] = 0
            state['haplotypes'][:copies//2, :, 0] = 1
            if copies % 2:
                state['haplotypes'][copies//2, 0, 0] = 1
            state['y'][20:50] = 0
            with patch('paleogen_rl.genetics.pulse.initialise_pulse',
                       return_value=(state, {'scientific_status': 'synthetic_boundary_fixture'})):
                report = evaluate_block_pulse(**args)
            self.assertEqual(report['engine_report']['final_measurement']['value'], copies/800)
            self.assertEqual(report['target']['target_auto'], 24 <= copies <= 56)
            probability = comb(20, 10)/comb(50, 10)
            self.assertAlmostEqual(report['sampling']['p10_joint'], probability, places=15)
            self.assertAlmostEqual(report['target']['joint_and_target'], probability*(24 <= copies <= 56), places=15)

    def test_positive_weighted_event_continues_selection_and_labels_stopping_diagnostic(self):
        for seed, switch, coefficient in product((0, 17, 42), (0., .1), (0., .1)):
            args = self.arguments(f=1., generations=8, seed=seed)
            args['recombination_map'] = RecombinationMap(args['measurement_panel'].panel, (switch, switch))
            args['selection'] = BlockSelection(mt_mod_nuc_arch=coefficient, mt_partner_block='middle', y_partner_block='y')
            state, _ = initialise_pulse(population_size=40, f=1., male_fraction=.5, panel=args['measurement_panel'].panel)
            state['haplotypes'][:, :, 1:] = 0
            with patch('paleogen_rl.genetics.pulse.initialise_pulse',
                       return_value=(state, {'scientific_status': 'synthetic_positive_fixture'})):
                full = evaluate_block_pulse(**args)
                quick = evaluate_block_pulse(**args, mode='quick')
                adaptive = evaluate_block_pulse(**args, mode='adaptive')
                legacy = evaluate_block_pulse(**{**args, 'measurement_panel': None})
            self.assertTrue(full['target']['target_auto'])
            self.assertEqual(full['target']['joint_and_target'], 1.)
            self.assertEqual(adaptive['target'], full['target'])
            self.assertEqual(adaptive['engine_report'], full['engine_report'])
            self.assertFalse(legacy['target']['target_auto'])
            self.assertIsNone(quick['ancestry_measurement']['modern_ancestry_weight'])
            self.assertIsNone(quick['target']['joint_and_target'])
            self.assertEqual(adaptive['ancestry_measurement']['generation'], 8)
            self.assertEqual(adaptive['screening_report']['generations_completed'], 1)
            stopping = quick['stopping_ancestry_diagnostic']
            self.assertEqual(stopping['status'], 'stopping_state_diagnostic_not_final')
            self.assertAlmostEqual(stopping['value'], .05)
            self.assertEqual(stopping['generation'], 1)
            if coefficient:
                self.assertGreater(full['engine_report']['work_units']['candidates_generated'], 320)

    def test_none_and_equal_weights_keep_existing_modes_compatible(self):
        args = self.arguments()
        args.pop('measurement_panel')
        for mode in ('full', 'quick', 'adaptive'):
            legacy = evaluate_block_pulse(**args, mode=mode)
            explicit_none = evaluate_block_pulse(**args, mode=mode, measurement_panel=None)
            self.assertEqual(legacy, explicit_none)
            self.assertNotIn('measurement_panel', legacy)
            self.assertEqual(legacy['evaluation_version'], EVALUATION_VERSION if mode == 'full' else MODE_EVALUATION_VERSION)
            panel = WeightedBlockPanel(args['recombination_map'].panel, (7, 7, 7), 'synthetic equal weights')
            weighted = evaluate_block_pulse(**args, mode=mode, measurement_panel=panel)
            self.assertEqual(weighted['sampling'], legacy['sampling'])
            self.assertEqual(weighted['target'], legacy['target'])

    def test_invalid_panels_and_inconsistent_measurements_are_refused(self):
        args = self.arguments()
        with patch('paleogen_rl.genetics.pulse.run_selected') as engine:
            for mode in ('full', 'quick', 'adaptive'):
                for panel in (args['measurement_panel'].panel,
                              WeightedBlockPanel(BlockPanel('different', ('mt', 'middle', 'y')), (1, 2, 1), 'synthetic')):
                    with self.assertRaises(ValueError):
                        evaluate_block_pulse(**{**args, 'measurement_panel': panel}, mode=mode)
            engine.assert_not_called()
        for mode in ('full', 'quick'):
            state, _ = initialise_pulse(population_size=40, f=.5, male_fraction=.5, panel=args['measurement_panel'].panel)
            original = run_selected(**state, recombination_map=args['recombination_map'], selection=args['selection'],
                                    generations=4, seed=17, stop_when_absorbed=(mode == 'quick'),
                                    measurement_panel=args['measurement_panel'])
            for mutation in ('generation', 'version', 'panel', 'early_mass'):
                if mutation == 'early_mass' and mode == 'full':
                    continue
                altered = deepcopy(original)
                measurement = altered.report['final_measurement']
                if mutation == 'generation': measurement['generation'] = 999
                elif mutation == 'version': measurement['measurement_version'] = 'unweighted'
                elif mutation == 'panel': measurement['panel']['block_weights'] = [1, 1, 1]
                else: measurement['modern_ancestry_weight'] = .5
                with patch('paleogen_rl.genetics.pulse.run_selected', return_value=altered):
                    with self.subTest(mode=mode, mutation=mutation), self.assertRaises(RuntimeError):
                        evaluate_block_pulse(**args, mode=mode)

    def test_continuation_failure_preserves_weights_and_accumulates_work(self):
        args = self.arguments(f=1.)
        state, _ = initialise_pulse(population_size=40, f=1., male_fraction=.5, panel=args['measurement_panel'].panel)
        first = run_selected(**state, recombination_map=args['recombination_map'], selection=args['selection'],
                             generations=4, seed=17, stop_when_absorbed=True, measurement_panel=args['measurement_panel'])
        failed_report = deepcopy(first.report)
        failed_report.update(final_measurement=None, termination_reason='reproduction_failed', failed_generation=2)
        failed_report['work_units'] = {**failed_report['work_units'], 'candidates_generated': 70}
        failure = ReproductionFailure(failed_report)
        with patch('paleogen_rl.genetics.pulse.run_selected', side_effect=[first, failure]) as engine:
            with self.assertRaises(ReproductionFailure) as error:
                evaluate_block_pulse(**args, mode='adaptive')
        for call in engine.call_args_list:
            self.assertEqual(call.kwargs['measurement_panel'], args['measurement_panel'])
            self.assertEqual(call.kwargs['seed'], 17)
        report = error.exception.report
        self.assertIsNone(report['final_measurement'])
        self.assertEqual(report['measurement_panel'], args['measurement_panel'].to_dict())
        self.assertEqual(report['total_work_units']['candidates_generated'],
                         70+first.report['work_units']['candidates_generated'])
        self.assertEqual(report['screening_report'], first.report)

    def test_real_reproductive_failure_never_returns_success_in_any_mode(self):
        args = self.arguments(f=0., selection=BlockSelection(s_y=1., mt_partner_block='mt', y_partner_block='y'))
        for mode in ('full', 'quick', 'adaptive'):
            with self.subTest(mode=mode), self.assertRaises(ReproductionFailure) as error:
                evaluate_block_pulse(**args, mode=mode)
            self.assertIsNone(error.exception.report['final_measurement'])
            self.assertEqual(error.exception.report['measurement_panel'], args['measurement_panel'].to_dict())

    def test_json_replay_restores_weights_in_all_modes(self):
        args = self.arguments(f=1., selection=BlockSelection(mt_mod_nuc_arch=.01, mt_partner_block='middle'))
        for mode in ('full', 'quick', 'adaptive'):
            original = evaluate_block_pulse(**args, mode=mode)
            report = json.loads(json.dumps(original, allow_nan=False))
            declaration = report['measurement_panel']
            weighted = WeightedBlockPanel(BlockPanel(declaration['panel_id'], declaration['block_ids']),
                                           declaration['block_weights'], declaration['weight_basis'])
            engine = report['engine_report']
            mapping = RecombinationMap(BlockPanel(**engine['recombination_map']['panel']),
                                        engine['recombination_map']['switch_probabilities'])
            init = report['initialisation']
            replay = evaluate_block_pulse(population_size=init['population_size'], f=init['requested_f'],
                                          male_fraction=init['requested_male_fraction'], generations=engine['generations_requested'],
                                          seed=engine['seed'], recombination_map=mapping,
                                          selection=BlockSelection(**engine['selection']),
                                          measurement_panel=weighted, mode=report.get('mode', 'full'))
            self.assertEqual(replay, report)


if __name__ == '__main__':
    unittest.main()
