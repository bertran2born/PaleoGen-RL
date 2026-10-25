"""Selected resolution diagnostics: direct replay, anchored maps and full cohorts."""

from contextlib import redirect_stderr
import hashlib
import io
import json
from math import exp
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from run_experiment import Config, SCENARIOS, run_block_full
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from study_autosomal_resolution import (
    ROOT, RESOLUTIONS, SEEDS, STUDY_SCENARIOS, STUDY_VERSION,
    _metrics, _differences, main, run_selected_resolution_study,
)


class TestSelectedAutosomalResolution(unittest.TestCase):
    def study(self, **overrides):
        return run_selected_resolution_study(**{**dict(
            resolutions=(2, 4, 9), seeds=(17, 73, 81), generations=3,
            scenarios=('neutral', 'reich_plus_symmetric_1pct')), **overrides})

    def test_analytical_metrics_include_boundaries_and_zero_uncertainty_upper_bound(self):
        values = (.025, .03, .07, .075)
        probabilities = (0., .2, .4, 1.)
        replicates = [dict(ancestry=value, p10_joint=p10, target_auto=.03 <= value <= .07,
                           joint_and_target=p10*int(.03 <= value <= .07))
                      for value, p10 in zip(values, probabilities)]
        metrics = _metrics(replicates)
        self.assertEqual(metrics['target_probability']['count'], 2)
        self.assertEqual(metrics['target_probability']['probability'], .5)
        self.assertAlmostEqual(metrics['ancestry']['mean'], .05)
        self.assertAlmostEqual(metrics['p10_joint']['mean'], .4)
        self.assertAlmostEqual(metrics['joint_and_target']['mean'], .15)
        zeros = _metrics([dict(ancestry=0., p10_joint=0., joint_and_target=0.)]*128)
        self.assertEqual(zeros['joint_and_target']['mean'], 0.)
        self.assertGreater(zeros['joint_and_target']['interval'][1], 0.)
        rows = [dict(block_count=b, replicates=[{**r, 'joint_and_target': r['joint_and_target']*scale}
                                                for r in replicates]) for b, scale in ((2, 0.), (4, .5), (8, 1.))]
        differences = _differences(rows)
        self.assertAlmostEqual(differences[0]['metrics']['joint_and_target']['mean'], -.15)
        self.assertAlmostEqual(differences[1]['metrics']['joint_and_target']['mean'], -.075)
        for delta in differences:
            self.assertEqual(delta['reference_block_count'], 8)
            self.assertEqual(delta['metrics']['ancestry']['mean'], 0.)
            self.assertEqual(delta['metrics']['target_probability']['mean'], 0.)

    def test_each_replicate_replays_directly_with_the_realised_selection(self):
        report = self.study()
        for scenario in report['scenarios']:
            for row in scenario['resolutions']:
                declaration = row['recombination_map']
                mapping = RecombinationMap(BlockPanel(**declaration['panel']), declaration['switch_probabilities'])
                self.assertEqual([r['seed'] for r in row['replicates']], [17, 73, 81])
                self.assertEqual(row['allele_copy_denominator'], 80*row['block_count'])
                for replicate in row['replicates']:
                    config = Config(seed=replicate['seed'], **row['config_parameters'])
                    direct = run_block_full(config, mapping, row['selection']['mt_partner_block'],
                                            row['selection']['y_partner_block'])
                    evaluation = json.loads(direct['block_report'])
                    engine = evaluation['engine_report']
                    self.assertEqual(row['selection'], engine['selection'])
                    self.assertEqual(row['initialisation'], evaluation['initialisation'])
                    self.assertEqual(replicate['ancestry'], direct['auto_mod'])
                    self.assertEqual(replicate['generation'], 3)
                    self.assertEqual(replicate['status'], 'evaluated_at_target')
                    self.assertEqual(replicate['modern_allele_copies'],
                                     engine['final_measurement']['modern_allele_copies'])
                    for field in ('mt_mod', 'Y_mod', 'p10_joint', 'joint_fixed', 'target_auto', 'joint_and_target'):
                        self.assertEqual(replicate[field], direct[field])
                    self.assertEqual(replicate['work_units'], engine['work_units'])
                self.assertEqual(row['metrics'], _metrics(row['replicates']))
                self.assertEqual(row['work_units']['candidates_generated'],
                                 sum(r['work_units']['candidates_generated'] for r in row['replicates']))
            for row, delta in zip(scenario['resolutions'], scenario['differences_from_finest']):
                fine = scenario['resolutions'][-1]
                for field in ('ancestry', 'p10_joint', 'joint_and_target'):
                    self.assertAlmostEqual(delta['metrics'][field]['mean'],
                                           row['metrics'][field]['mean']-fine['metrics'][field]['mean'])
        work = report['total_work_units']
        self.assertEqual(work['offspring_generated'], 2*3*3*40*3)
        self.assertGreaterEqual(work['candidates_generated'], work['offspring_generated'])
        self.assertEqual(work['state_allele_entries'], 80*9)
        self.assertEqual(work['block_copy_transmissions'], sum(
            row['work_units']['block_copy_transmissions'] for scenario in report['scenarios']
            for row in scenario['resolutions']))

    def test_maps_fix_partner_positions_and_endpoint_recombination(self):
        for length in (0., .25, 1.):
            report = self.study(map_length=length)
            for scenario in report['scenarios']:
                for row in scenario['resolutions']:
                    probabilities = np.array(row['recombination_map']['switch_probabilities'])
                    self.assertAlmostEqual((1-float(np.prod(1-2*probabilities)))/2, (1-exp(-2*length))/2)
                    self.assertEqual(row['block_positions'][0], 0.)
                    self.assertEqual(row['block_positions'][-1], 1.)
                    self.assertEqual(row['selection']['mt_partner_block'], 'b0')
                    self.assertEqual(row['selection']['y_partner_block'], f"b{row['block_count']-1}")
                    self.assertEqual(row['partner_panel_weight'], 2/row['block_count'])

    def test_neutral_replicate_still_matches_archived_i14(self):
        archived = json.loads((ROOT.parent/'docs/science/autosomal-resolution-report.json').read_text())
        extended = self.study(resolutions=RESOLUTIONS, seeds=(410000,), scenarios=('neutral',), generations=20)
        for row, previous in zip(extended['scenarios'][0]['resolutions'], archived['resolutions']):
            self.assertEqual(row['recombination_map'], previous['recombination_map'])
            self.assertEqual(row['replicates'][0]['ancestry'], previous['replicates'][0]['value'])
            self.assertEqual(row['replicates'][0]['modern_allele_copies'], previous['replicates'][0]['modern_allele_copies'])

    def test_zero_horizon_keeps_all_initial_target_hits_with_no_joint_success(self):
        report = self.study(generations=0)
        for scenario in report['scenarios']:
            for row in scenario['resolutions']:
                self.assertAlmostEqual(row['metrics']['ancestry']['mean'], .05)
                self.assertEqual(row['metrics']['target_probability']['count'], 3)
                self.assertEqual(row['metrics']['joint_and_target']['mean'], 0.)
        self.assertEqual(report['total_work_units']['candidates_generated'], 0)
        self.assertEqual(report['total_work_units']['block_copy_transmissions'], 0)

    def test_strict_json_repeatability_fixed_protocol_and_source_provenance(self):
        before = np.random.get_state()
        report = self.study()
        self.assertEqual(json.loads(json.dumps(report, allow_nan=False)), report)
        self.assertEqual(report, self.study())
        self.assertEqual(report['study_version'], STUDY_VERSION)
        self.assertEqual(report['mode'], 'full')
        self.assertEqual(report['convergence_status'], 'not_established')
        self.assertEqual(STUDY_SCENARIOS, tuple(SCENARIOS))
        self.assertEqual(RESOLUTIONS, (8, 32, 128))
        self.assertEqual(SEEDS, tuple(range(410000, 410128)))
        for path, digest in report['implementation_sha256'].items():
            self.assertEqual(digest, hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
        for old, new in zip(before, np.random.get_state()):
            np.testing.assert_equal(old, new)

    def test_invalid_declarations_fail_before_simulation(self):
        invalid = [dict(resolutions=(2, 4)), dict(resolutions=(2, 2, 4)),
                   dict(resolutions=(4, 2, 8)), dict(resolutions=(1, 2, 3)),
                   dict(resolutions=(2, 3, 4.)), dict(resolutions=None),
                   dict(seeds=[]), dict(seeds=(1, 1)), dict(seeds=(True,)), dict(seeds=(-1,)),
                   dict(scenarios=()), dict(scenarios=('neutral', 'neutral')),
                   dict(scenarios=('missing',)), dict(scenarios=([],)),
                   dict(generations=-1), dict(generations=True), dict(generations=2.),
                   dict(map_length=float('nan')), dict(map_length=float('inf')),
                   dict(map_length=-.1), dict(map_length=True), dict(map_length='1')]
        with patch('study_autosomal_resolution.run_block_full') as simulate:
            for overrides in invalid:
                with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                    self.study(**overrides)
            simulate.assert_not_called()

    def test_cli_refuses_existing_and_failed_outputs_without_dropping_replicates(self):
        report = self.study()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'report.json'
            with patch('study_autosomal_resolution.run_selected_resolution_study', return_value=report):
                self.assertEqual(main(['--output', str(output)]), 0)
            self.assertEqual(json.loads(output.read_text()), report)
            original = output.read_bytes()
            dangling = Path(directory)/'dangling'
            dangling.symlink_to(Path(directory)/'missing')
            for destination in (output, dangling):
                with patch('study_autosomal_resolution.run_selected_resolution_study') as simulate:
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                        main(['--output', str(destination)])
                    self.assertEqual(error.exception.code, 2)
                    simulate.assert_not_called()
            self.assertEqual(output.read_bytes(), original)
            failed = Path(directory)/'failed.json'
            with patch('study_autosomal_resolution.run_block_full', side_effect=RuntimeError('reproduction_failed')):
                with self.assertRaisesRegex(RuntimeError, 'neutral B=2 seed=17: reproduction_failed'):
                    self.study()
            with patch('study_autosomal_resolution.run_selected_resolution_study', side_effect=RuntimeError('reproduction_failed')):
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    main(['--output', str(failed)])
                self.assertEqual(error.exception.code, 1)
                self.assertFalse(failed.exists())


if __name__ == '__main__':
    unittest.main()
