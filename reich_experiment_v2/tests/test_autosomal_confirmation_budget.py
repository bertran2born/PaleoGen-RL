"""Fast integrity and independent arithmetic checks of the I33 planning archive."""

from contextlib import chdir, redirect_stdout
import hashlib
import io
import json
from math import ceil, log, sqrt
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from run_experiment import SCENARIOS
from paleogen_rl.genetics.protocol import _canonical
from paleogen_rl.genetics.weighted_protocol import WeightedAutosomalProtocol
from study_weighted_autosomal_resolution import load_weighted_resolution_plan


ROOT = Path(__file__).resolve().parents[1]
SCIENCE = ROOT.parent/'docs/science'
PLAN_PATH = SCIENCE/'m3-confirmation-budget-plan.json'
REPORT_PATH = SCIENCE/'m3-confirmation-budget.json'
DOC_PATH = SCIENCE/'m3-confirmation-budget.md'
PLAN_SHA256 = '8fe96cc03706a61f1707f41e39e203bb22d34c30809eaa15b19bb50fe7d15f18'
REPORT_SHA256 = 'bf85c49a958d71aab463a2924bcea9e2dc37dbed180e56a3a44482578c3de851'


class TestConfirmationBudget(unittest.TestCase):
    def setUp(self):
        self.plan, _ = load_weighted_resolution_plan(PLAN_PATH)
        self.report = json.loads(REPORT_PATH.read_text())

    def test_fixed_inputs_identity_scope_and_no_scientific_adoption(self):
        self.assertEqual(hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest(), PLAN_SHA256)
        self.assertEqual(hashlib.sha256(REPORT_PATH.read_bytes()).hexdigest(), REPORT_SHA256)
        report = self.report
        self.assertEqual(report['plan_template'], self.plan)
        self.assertEqual(report['plan_template_file_sha256'], PLAN_SHA256)
        self.assertEqual(report['plan_template_sha256'], hashlib.sha256(_canonical(self.plan).encode()).hexdigest())
        self.assertEqual(report['report_version'], 'm3-confirmation-feasibility-v1')
        self.assertEqual(report['scientific_status'], 'planning_only')
        self.assertFalse(report['simulation_performed'])
        self.assertFalse(report['scientific_criteria_adopted'])
        self.assertEqual(report['convergence_status'], 'not_established')
        self.assertEqual(report['mode'], 'full')
        self.assertEqual(self.plan['seeds'], [620000, 620001, 620002])
        self.assertEqual(self.plan['scenarios'], list(SCENARIOS))
        base = WeightedAutosomalProtocol.from_dict(self.plan['family']['base_protocol'])
        self.assertEqual((base.population_size, base.generations, base.f, base.male_fraction), (1450, 6993, .05, .5))
        self.assertEqual(round(base.f*base.population_size*base.male_fraction), 36)
        self.assertEqual(base.measurement_panel.block_weights, (1., 3., 3., 1.))
        family = report['workload_template']['family']
        self.assertEqual([r['block_count'] for r in family['resolutions']], [4, 8, 20])
        for row in family['resolutions']:
            contract = WeightedAutosomalProtocol.from_dict(row['autosomal_protocol'])
            ids = contract.measurement_panel.panel.block_ids
            weights = contract.measurement_panel.normalized_weights
            self.assertAlmostEqual(weights[ids.index('a')]+weights[ids.index('d')], .25)
        for digest in report['implementation_sha256'].values():
            self.assertRegex(digest, r'^[0-9a-f]{64}$')
        # Archived source hashes identify their revision, not arbitrary future code.
        for path in ('weighted_autosomal_equivalence.py', 'study_weighted_autosomal_resolution.py', 'flake.lock'):
            self.assertIn(path, report['implementation_sha256'])

    def test_all_precision_rows_and_exact_integer_workloads(self):
        report = self.report
        radii = [.1, .05, .01, .005, .001, .0005, .0001]
        self.assertEqual([r['precision_radius'] for r in report['sensitivity']], radii)
        comparisons = 17*2*4
        coefficient = 2*log(2*comparisons/.05)
        previous = 0
        for row in report['sensitivity']:
            radius = row['precision_radius']
            precision = row['precision']
            n = precision['required_replicates_per_cell']
            self.assertEqual(n, ceil(coefficient/radius**2))
            self.assertLessEqual(sqrt(coefficient/n), radius)
            self.assertGreater(sqrt(coefficient/(n-1)), radius)
            self.assertGreater(n, previous)
            previous = n
            self.assertEqual(precision['comparisons'], comparisons)
            self.assertEqual(precision['replicates_per_cell'], 3)
            self.assertFalse(precision['precision_satisfied'])
            self.assertEqual(precision['criteria']['alpha'], .05)
            self.assertTrue(all(value == 2*radius for value in precision['criteria']['margins'].values()))
            self.assertEqual(precision['criteria_sha256'], hashlib.sha256(_canonical(precision['criteria']).encode()).hexdigest())
            total = row['total_workload']
            self.assertEqual(total['evaluations'], 17*3*n)
            self.assertEqual(total['offspring_generated_on_completion'], 17*3*n*1450*6993)
            self.assertEqual(total['accepted_candidates_on_completion'], total['offspring_generated_on_completion'])
            self.assertEqual(total['candidates_generated_lower_bound_on_completion'], total['offspring_generated_on_completion'])
            self.assertEqual(total['block_copy_transmissions_lower_bound_on_completion'], 2*17*n*1450*6993*(4+8+20))
            self.assertEqual(total['largest_population_state_allele_entries'], 58000)
            for resolution, blocks in zip(row['resolutions'], (4, 8, 20)):
                self.assertEqual(resolution['block_count'], blocks)
                self.assertEqual(resolution['evaluations'], 17*n)
                self.assertEqual(resolution['offspring_generated_on_completion'], 17*n*1450*6993)
                self.assertEqual(resolution['block_copy_transmissions_lower_bound_on_completion'], 2*blocks*17*n*1450*6993)
                self.assertEqual(resolution['state_allele_entries'], 2*1450*blocks)
            for key in ('evaluations', 'offspring_generated_on_completion', 'accepted_candidates_on_completion',
                        'candidates_generated_lower_bound_on_completion', 'block_copy_transmissions_lower_bound_on_completion'):
                self.assertEqual(total[key], sum(r[key] for r in row['resolutions']))
                self.assertIs(type(total[key]), int)
        self.assertGreater(report['sensitivity'][-1]['total_workload']['offspring_generated_on_completion'], 2**53)

    def test_documented_reproduction_uses_no_engine_rng_or_overwrite(self):
        code = DOC_PATH.read_text().split('```python\n', 1)[1].split('```', 1)[0]
        with tempfile.TemporaryDirectory() as directory, chdir(ROOT):
            output = Path(directory)/'budget.json'
            with patch.object(sys, 'argv', ['budget', str(output)]), redirect_stdout(io.StringIO()), \
                 patch('numpy.random.default_rng', side_effect=AssertionError('RNG forbidden')), \
                 patch('study_weighted_autosomal_resolution.run_block_full', side_effect=AssertionError('engine forbidden')), \
                 patch('paleogen_rl.genetics.pulse.run_selected', side_effect=AssertionError('engine forbidden')):
                exec(compile(code, str(DOC_PATH), 'exec'), {})
                regenerated = json.loads(output.read_text())
                # Future source/runtime versions can differ without rewriting the archive.
                for field in ('implementation_sha256', 'python_version', 'numpy_version'):
                    regenerated[field] = self.report[field]
                self.assertEqual(regenerated, self.report)
                before = output.read_bytes()
                with self.assertRaises(FileExistsError):
                    exec(compile(code, str(DOC_PATH), 'exec'), {})
                self.assertEqual(output.read_bytes(), before)
            self.assertEqual(len(regenerated['plan_template']['seeds']), 3)


if __name__ == '__main__':
    unittest.main()
