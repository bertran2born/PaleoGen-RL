"""Forecast logical full-study work without evaluating scientific outcomes."""

from contextlib import redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
from math import sqrt
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from study_autosomal_resolution import (
    ROOT, PREVIEW_VERSION, load_resolution_plan, main, preview_resolution_plan, run_resolution_plan,
)


class TestAutosomalWorkloadPreview(unittest.TestCase):
    def plan(self):
        return dict(plan_version='selected-autosomal-resolution-plan-v1', plan_id='preview-test',
                    population_size=40, f=.5, male_fraction=.5, generations=2, map_length=.25,
                    resolutions=[2, 3, 5], seeds=[17, 73],
                    scenarios=['neutral', 'reich_plus_symmetric_1pct'])

    def test_preview_uses_no_engine_or_rng_and_owns_its_snapshot(self):
        plan = self.plan()
        before = deepcopy(plan)
        with patch('study_autosomal_resolution.run_block_full', side_effect=AssertionError('engine forbidden')), \
             patch('study_autosomal_resolution.run_selected_resolution_study', side_effect=AssertionError('study forbidden')), \
             patch('study_autosomal_resolution.np.random.default_rng', side_effect=AssertionError('rng forbidden')):
            preview = preview_resolution_plan(plan)
            self.assertEqual(preview, preview_resolution_plan(plan))
        self.assertEqual(plan, before)
        preview['plan']['seeds'].append(999)
        self.assertEqual(plan, before)
        self.assertEqual(preview['preview_version'], PREVIEW_VERSION)
        self.assertFalse(preview['simulation_performed'])
        self.assertEqual(preview['scientific_status'], 'planning_only')
        self.assertEqual(preview['mode'], 'full')
        self.assertEqual(preview['convergence_status'], 'not_established')
        self.assertEqual(preview['total_workload'], dict(
            evaluations=12, offspring_generated_on_completion=960, accepted_candidates_on_completion=960,
            candidates_generated_lower_bound_on_completion=960,
            block_copy_transmissions_lower_bound_on_completion=6400,
            largest_population_state_allele_entries=400))
        self.assertEqual([row['evaluations'] for row in preview['resolutions']], [4, 4, 4])

    def test_costs_agree_with_actual_neutral_and_selected_runs(self):
        for scenario in ('neutral', 'reich_plus_symmetric_1pct'):
            plan = self.plan()
            plan['scenarios'] = [scenario]
            preview = preview_resolution_plan(plan)
            actual = run_resolution_plan(plan)
            for prediction, observed in zip(preview['resolutions'], actual['scenarios'][0]['resolutions']):
                work = observed['work_units']
                self.assertEqual(prediction['block_count'], observed['block_count'])
                self.assertEqual(prediction['offspring_generated_on_completion'], work['offspring_generated'])
                self.assertEqual(prediction['accepted_candidates_on_completion'], work['accepted_candidates'])
                self.assertEqual(prediction['state_allele_entries'], work['state_allele_entries'])
                for field in ('candidates_generated', 'block_copy_transmissions'):
                    minimum = prediction[f'{field}_lower_bound_on_completion']
                    self.assertLessEqual(minimum, work[field])
                    if scenario == 'neutral':
                        self.assertEqual(minimum, work[field])

    def test_i22_is_previewed_without_repeating_long_simulations(self):
        directory = ROOT.parent/'docs/science'
        plan, _ = load_resolution_plan(directory/'autosomal-target-regime-plan.json')
        archive = json.loads((directory/'autosomal-target-regime-report.json').read_text())
        preview = preview_resolution_plan(plan)
        self.assertEqual(preview['plan_sha256'], archive['plan_sha256'])
        self.assertEqual(preview['total_workload']['evaluations'], 18)
        self.assertEqual(preview['total_workload']['offspring_generated_on_completion'], 182517300)
        self.assertEqual(preview['total_workload']['largest_population_state_allele_entries'], 371200)
        total = preview['total_workload']
        self.assertLessEqual(total['block_copy_transmissions_lower_bound_on_completion'],
                             archive['total_work_units']['block_copy_transmissions'])
        radius = preview['precision']['bounded_mean_radius_unclipped']
        for scenario in archive['scenarios']:
            for row in scenario['resolutions']:
                self.assertAlmostEqual(row['metrics']['joint_and_target']['interval'][1], radius)

    def test_precision_is_unclipped_pointwise_and_depends_only_on_replicates(self):
        radii = []
        for count in (1, 4, 16):
            plan = self.plan()
            plan['seeds'] = list(range(count))
            preview = preview_resolution_plan(plan)
            precision = preview['precision']
            self.assertEqual(precision['replicates_per_scenario_resolution'], count)
            self.assertEqual(precision['confidence_level'], .95)
            self.assertFalse(precision['intervals_simultaneous'])
            self.assertIn('outcome_dependent', precision['target_probability_interval'])
            self.assertAlmostEqual(precision['paired_difference_radius_unclipped'],
                                   2*precision['bounded_mean_radius_unclipped'])
            radii.append(precision['bounded_mean_radius_unclipped'])
            changed = deepcopy(plan)
            changed['scenarios'] = ['neutral']
            changed['generations'] = 6993
            self.assertEqual(preview_resolution_plan(changed)['precision'], precision)
        self.assertGreater(radii[0], 1.)
        self.assertAlmostEqual(radii[0]/radii[1], sqrt(4))
        self.assertAlmostEqual(radii[1]/radii[2], sqrt(4))

    def test_formatting_independence_and_cli_file_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            reports, hashes = [], []
            for index, payload in enumerate((json.dumps(self.plan()), json.dumps(self.plan(), indent=4, sort_keys=True))):
                source, output = Path(directory)/f'{index}.json', Path(directory)/f'{index}-preview.json'
                source.write_text(payload)
                process = subprocess.run([sys.executable, str(ROOT/'study_autosomal_resolution.py'),
                                          '--preview', '--plan', str(source), '--output', str(output)],
                                         cwd=directory, capture_output=True, text=True)
                self.assertEqual(process.returncode, 0, process.stdout+process.stderr)
                report = json.loads(output.read_text())
                digest = report.pop('plan_file_sha256')
                self.assertEqual(digest, hashlib.sha256(source.read_bytes()).hexdigest())
                hashes.append(digest)
                reports.append(report)
            self.assertNotEqual(hashes[0], hashes[1])
            self.assertEqual(reports[0], reports[1])
            self.assertEqual(json.loads(json.dumps(reports[0], allow_nan=False)), reports[0])

    def test_cli_requires_a_plan_and_preserves_existing_destinations(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/'plan.json', Path(directory)/'preview.json'
            source.write_text(json.dumps(self.plan()))
            before = source.read_bytes()
            with patch('study_autosomal_resolution.run_resolution_plan', side_effect=AssertionError('engine forbidden')):
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    main(['--preview', '--output', str(output)])
                self.assertEqual(error.exception.code, 2)
                self.assertFalse(output.exists())
                self.assertEqual(main(['--preview', '--plan', str(source), '--output', str(output)]), 0)
            previous = output.read_bytes()
            for destination in (output, source):
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    main(['--preview', '--plan', str(source), '--output', str(destination)])
                self.assertEqual(error.exception.code, 2)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(output.read_bytes(), previous)
            dangling = Path(directory)/'dangling'
            dangling.symlink_to(Path(directory)/'absent')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(['--preview', '--plan', str(source), '--output', str(dangling)])

    def test_invalid_plan_is_rejected_without_output_or_simulation(self):
        plan = self.plan()
        plan['generations'] = 0
        with patch('study_autosomal_resolution.run_block_full') as engine:
            with self.assertRaises(ValueError):
                preview_resolution_plan(plan)
            with tempfile.TemporaryDirectory() as directory:
                source, output = Path(directory)/'bad.json', Path(directory)/'output.json'
                source.write_text(json.dumps(plan))
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    main(['--preview', '--plan', str(source), '--output', str(output)])
                self.assertEqual(error.exception.code, 1)
                self.assertFalse(output.exists())
            engine.assert_not_called()


if __name__ == '__main__':
    unittest.main()
