"""Fixed-n Bernstein bounds: independent constants, coverage and I31 controls."""

from copy import deepcopy
import hashlib
import json
from math import exp, fsum, lgamma, log, sqrt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.protocol import _canonical
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel
from paleogen_rl.genetics.weighted_protocol import WeightedAutosomalProtocol
from study_weighted_autosomal_resolution import PLAN_VERSION, run_weighted_resolution_plan
from weighted_autosomal_equivalence import (
    CRITERIA_VERSION, ASSESSMENT_VERSION, BERNSTEIN_CRITERIA_VERSION,
    BERNSTEIN_ASSESSMENT_VERSION, BERNSTEIN_METHOD, METRICS,
    empirical_bernstein_interval, preview_weighted_equivalence, assess_weighted_equivalence,
    validate_weighted_equivalence_criteria, load_weighted_equivalence_criteria,
)


def plan(n=160):
    panel = BlockPanel('constant-control', ('a', 'b', 'c', 'd'))
    base = WeightedAutosomalProtocol('constant-control', 40, 1, 0., .5,
        RecombinationMap(panel, (0., 0., 0.)), 'a', 'd', WeightedBlockPanel(panel, (1, 3, 3, 1), 'synthetic control'))
    return dict(plan_version=PLAN_VERSION, plan_id='bernstein-control', seeds=list(range(n)), scenarios=['neutral'],
                family=dict(base_protocol=base.to_dict(), family_id='control-family', map_length=0., refinement_factors=[1, 3, 9]))


def criteria(declaration, bernstein=True):
    rule = dict(criteria_version=BERNSTEIN_CRITERIA_VERSION if bernstein else CRITERIA_VERSION,
                criteria_id='technical-control-only', study_plan_sha256=hashlib.sha256(_canonical(declaration).encode()).hexdigest(),
                alpha=.05, margins={metric: .4 for metric in METRICS}, max_interval_radius=.2)
    if bernstein:
        rule['method'] = BERNSTEIN_METHOD
    return rule


class TestEmpiricalBernstein(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = plan()
        cls.report = run_weighted_resolution_plan(cls.plan)

    def test_formula_two_tails_unbiased_variance_and_range_scaling(self):
        values = [-1., 0., 1.]
        result = empirical_bernstein_interval(values, comparisons=3, alpha=.04)
        budget = log(4*3/.04)
        self.assertEqual(result['mean_difference'], 0.)
        self.assertEqual(result['sample_variance'], 1.)
        self.assertAlmostEqual(result['log_budget'], budget)
        self.assertAlmostEqual(result['radius_unclipped'], sqrt(2*budget/3)+14*budget/(3*2))
        unit_variance = fsum((x-.5)**2 for x in (0., .5, 1.))/2
        one_sided_unit_radius = sqrt(2*unit_variance*budget/3)+7*budget/(3*2)
        self.assertAlmostEqual(result['radius_unclipped'], 2*one_sided_unit_radius)
        self.assertEqual(values, [-1., 0., 1.])

    def test_constant_and_near_constant_variance_keeps_positive_residual(self):
        for constant in (-1., .125, 1.):
            result = empirical_bernstein_interval([constant]*100, comparisons=8, alpha=.05)
            self.assertEqual(result['sample_variance'], 0.)
            self.assertGreater(result['radius_unclipped'], 0.)
            self.assertAlmostEqual(result['radius_unclipped'], 14*log(640)/(3*99))
        small = empirical_bernstein_interval([1., 1.-1e-10]*50, comparisons=8, alpha=.05)
        self.assertGreater(small['sample_variance'], 0.)
        self.assertLess(small['sample_variance'], 1e-18)
        reflected = empirical_bernstein_interval([-1., -1.+1e-10]*50, comparisons=8, alpha=.05)
        self.assertEqual(small['radius_unclipped'], reflected['radius_unclipped'])
        self.assertEqual(small['interval'], [-reflected['interval'][1], -reflected['interval'][0]])

    def test_exact_discrete_coverage_by_enumerating_all_binomial_counts(self):
        # Exhaustive support for each finite Bernoulli experiment; not a proof for all laws.
        for n, comparisons, alpha in ((30, 1, .1), (1000, 1, .1), (100, 4, .05)):
            intervals = [empirical_bernstein_interval([-1.]*k+[1.]*(n-k), comparisons=comparisons, alpha=alpha)['interval']
                         for k in range(n+1)]
            for probability in (.001, .01, .1, .5, .9, .99):
                masses = [exp(lgamma(n+1)-lgamma(k+1)-lgamma(n-k+1)+k*log(probability)+(n-k)*log(1-probability))
                          for k in range(n+1)]
                mean = 1-2*probability
                missed = fsum(mass for mass, (lower, upper) in zip(masses, intervals) if mean < lower or mean > upper)
                self.assertAlmostEqual(fsum(masses), 1., places=10)
                self.assertLessEqual(missed, alpha/comparisons+1e-10)

    def test_planning_distinguishes_zero_variance_and_range_guarantee(self):
        declaration = self.plan
        with patch('numpy.random.default_rng', side_effect=AssertionError('RNG forbidden')), \
             patch('study_weighted_autosomal_resolution.run_block_full', side_effect=AssertionError('engine forbidden')):
            preview = preview_weighted_equivalence(criteria(declaration), declaration)
        self.assertIsNone(preview['precision_satisfied'])
        self.assertIsNone(preview['required_replicates_per_cell'])
        self.assertTrue(preview['precision_is_outcome_dependent'])
        self.assertTrue(preview['sample_size_must_be_fixed'])
        budget = log(4*8/.05)
        zero = preview['zero_variance_required_replicates_per_cell']
        worst = preview['worst_case_sufficient_replicates_per_cell']
        self.assertLessEqual(14*budget/(3*(zero-1)), .2)
        self.assertGreater(14*budget/(3*(zero-2)), .2)
        def radius(n):
            return sqrt(2*budget/(n-1))+14*budget/(3*(n-1))
        self.assertLessEqual(radius(worst), .2)
        self.assertGreater(radius(worst-1), .2)
        self.assertLess(zero, worst)
        self.assertFalse(preview['precision_guaranteed_from_range'])

    def test_strict_version_method_roundtrip_and_invalid_inputs(self):
        declaration = self.plan
        rule = criteria(declaration)
        normalized = validate_weighted_equivalence_criteria(rule, declaration)
        self.assertEqual(normalized, rule)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'criteria.json'
            path.write_text(json.dumps(rule, indent=3))
            restored, digest = load_weighted_equivalence_criteria(path, declaration)
            self.assertEqual(restored, normalized)
            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
        for value in (None, 'best_after_results', 'hoeffding'):
            with self.assertRaises(ValueError):
                preview_weighted_equivalence({**rule, 'method': value}, declaration)
        missing = dict(rule)
        del missing['method']
        with self.assertRaises(ValueError):
            preview_weighted_equivalence(missing, declaration)
        with self.assertRaises(ValueError):
            preview_weighted_equivalence(criteria(plan(1)), plan(1))
        for values in ([], [0.], [True, 0.], [float('nan'), 0.], [2., 0.], ['0', 0.], [10**400, 0.]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                empirical_bernstein_interval(values, comparisons=1, alpha=.05)
        for comparisons, alpha in ((0, .05), (True, .05), (1, 0), (1, 1), (1, True)):
            with self.assertRaises(ValueError):
                empirical_bernstein_interval([0., 0.], comparisons=comparisons, alpha=alpha)

    def test_real_absorbing_i31_control_uses_observed_per_comparison_precision(self):
        before = deepcopy(self.report)
        result = assess_weighted_equivalence(criteria(self.plan), self.report)
        self.assertEqual(result['assessment_version'], BERNSTEIN_ASSESSMENT_VERSION)
        self.assertEqual(result['status'], 'equivalence_supported_within_declared_family')
        self.assertEqual(result['convergence_status'], 'not_established')
        self.assertTrue(result['precision']['precision_satisfied'])
        for row in result['comparisons']:
            self.assertEqual(row['sample_variance'], 0.)
            self.assertAlmostEqual(row['radius_unclipped'], 14*log(640)/(3*159))
            self.assertTrue(row['precision_satisfied'])
        self.assertEqual(self.report, before)
        # Cross-method comparison is a technical check, not a permitted post-hoc choice.
        old = assess_weighted_equivalence(criteria(self.plan, False), self.report)
        self.assertEqual(old['assessment_version'], ASSESSMENT_VERSION)
        self.assertEqual(old['status'], 'inconclusive_precision')
        self.assertNotIn('sample_variance', old['comparisons'][0])

    def test_observation_variance_can_prevent_precision_without_relaxing_margins(self):
        report = deepcopy(self.report)
        # Controlled observation fields, not additional simulated trajectories.
        for index, rep in enumerate(report['scenarios'][0]['resolutions'][0]['replicates']):
            value = float(index % 2)
            rep['ancestry'] = value
            final = rep['evaluation']['engine_report']['final_measurement']
            final.update(value=value, modern_ancestry_weight=value*final['weight_denominator'])
        result = assess_weighted_equivalence(criteria(self.plan), report)
        self.assertEqual(result['status'], 'inconclusive_precision')
        self.assertFalse(result['precision']['precision_satisfied'])
        ancestry = next(r for r in result['comparisons'] if r['block_count'] == 4 and r['metric'] == 'ancestry')
        self.assertGreater(ancestry['sample_variance'], .25)
        self.assertGreater(ancestry['radius_unclipped'], .2)
        self.assertTrue(any(r['precision_satisfied'] for r in result['comparisons']))
        self.assertEqual(result['criteria']['margins'], criteria(self.plan)['margins'])

    def test_v1_planning_archive_remains_numerically_identical(self):
        path = Path(__file__).resolve().parents[2]/'docs/science/m3-confirmation-budget.json'
        archive = json.loads(path.read_text())
        for row in archive['sensitivity']:
            self.assertEqual(preview_weighted_equivalence(row['precision']['criteria'], archive['plan_template']), row['precision'])
        invalid = deepcopy(self.report)
        invalid['scenarios'][0]['resolutions'][0]['replicates'][0]['generation'] = 0
        with self.assertRaises(ValueError):
            assess_weighted_equivalence(criteria(self.plan), invalid)


if __name__ == '__main__':
    unittest.main()
