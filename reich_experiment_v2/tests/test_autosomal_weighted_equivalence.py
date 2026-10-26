"""Declared simultaneous equivalence: analytical fixtures and real I31 controls."""

from copy import deepcopy
import hashlib
import json
from math import ceil, log, sqrt
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
    CRITERIA_VERSION, METRICS, _decision, assess_weighted_equivalence,
    load_weighted_equivalence_criteria, preview_weighted_equivalence,
    validate_weighted_equivalence_criteria,
)


def plan(replicates=3):
    panel = BlockPanel('synthetic-four', ('a', 'b', 'c', 'd'))
    base = WeightedAutosomalProtocol('absorbing-control', 40, 1, 0., .5,
                RecombinationMap(panel, (0., 0., 0.)), 'a', 'd',
                WeightedBlockPanel(panel, (1, 3, 3, 1), 'synthetic control'))
    return dict(plan_version=PLAN_VERSION, plan_id='equivalence-control', seeds=list(range(replicates)),
                scenarios=['neutral'], family=dict(base_protocol=base.to_dict(), family_id='control-family',
                map_length=0., refinement_factors=[1, 3, 9]))


def criteria(declaration):
    # Technical fixture values, never proposed as M3 scientific acceptance margins.
    return dict(criteria_version=CRITERIA_VERSION, criteria_id='technical-test-only',
                study_plan_sha256=hashlib.sha256(_canonical(declaration).encode()).hexdigest(), alpha=.05,
                margins={metric: .4 for metric in METRICS}, max_interval_radius=.2)


class TestWeightedEquivalence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.control_plan = plan(320)
        cls.control_report = run_weighted_resolution_plan(cls.control_plan)

    def test_strict_criteria_roundtrip_hashes_and_owned_snapshots(self):
        declaration = plan()
        original = criteria(declaration)
        normalized = validate_weighted_equivalence_criteria(original, declaration)
        hashes = []
        with tempfile.TemporaryDirectory() as directory:
            for index, payload in enumerate((_canonical(original), json.dumps(original, indent=4))):
                path = Path(directory)/str(index)
                path.write_text(payload)
                restored, digest = load_weighted_equivalence_criteria(path, declaration)
                self.assertEqual(restored, normalized)
                self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
                hashes.append(digest)
            self.assertNotEqual(hashes[0], hashes[1])
        preview = preview_weighted_equivalence(normalized, declaration)
        self.assertEqual(preview['criteria_sha256'], hashlib.sha256(_canonical(normalized).encode()).hexdigest())
        normalized['margins']['ancestry'] = .5
        self.assertEqual(original, criteria(declaration))
        changed = deepcopy(original)
        changed['criteria_id'] = 'other'
        self.assertNotEqual(preview_weighted_equivalence(changed, declaration)['criteria_sha256'], preview['criteria_sha256'])

    def test_simultaneous_radius_required_n_and_no_simulation(self):
        declaration = plan()
        declaration['scenarios'] = ['neutral', 'reich_plus_symmetric_1pct']
        rule = criteria(declaration)
        with patch('numpy.random.default_rng', side_effect=AssertionError('RNG forbidden')), \
             patch('study_weighted_autosomal_resolution.run_block_full', side_effect=AssertionError('engine forbidden')):
            preview = preview_weighted_equivalence(rule, declaration)
        count = 2*2*4
        coefficient = 2*log(2*count/.05)
        self.assertEqual(preview['comparisons'], count)
        self.assertAlmostEqual(preview['simultaneous_radius_unclipped'], sqrt(coefficient/3))
        required = preview['required_replicates_per_cell']
        self.assertEqual(required, ceil(coefficient/.2**2))
        self.assertLessEqual(sqrt(coefficient/required), .2)
        self.assertGreater(sqrt(coefficient/(required-1)), .2)
        self.assertFalse(preview['precision_satisfied'])
        self.assertFalse(preview['comparison_independence_required'])
        # More simultaneous comparisons must not produce a narrower interval.
        simpler = preview_weighted_equivalence(criteria(plan()), plan())
        self.assertGreater(preview['simultaneous_radius_unclipped'], simpler['simultaneous_radius_unclipped'])

    def test_invalid_criteria_and_plan_links_are_rejected(self):
        declaration = plan()
        original = criteria(declaration)
        bad = [None, [], {**original, 'extra': 0}, {**original, 'criteria_version': 'unknown'},
               {**original, 'study_plan_sha256': '0'*64}]
        for key in original:
            changed = deepcopy(original)
            del changed[key]
            bad.append(changed)
        for key, values in (('alpha', (0, 1, True, float('nan'), float('inf'), 10**400)),
                            ('max_interval_radius', (0, -.1, .5, True, 5e-324)),
                            ('criteria_id', ('', ' padded ', None))):
            bad.extend({**original, key: value} for value in values)
        for metric in METRICS:
            for value in (0, -1, 1.1, True, float('nan')):
                changed = deepcopy(original)
                changed['margins'][metric] = value
                bad.append(changed)
            changed = deepcopy(original)
            del changed['margins'][metric]
            bad.append(changed)
        for rule in bad:
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                preview_weighted_equivalence(rule, declaration)
        changed_plan = deepcopy(declaration)
        changed_plan['seeds'].append(999)
        with self.assertRaises(ValueError):
            preview_weighted_equivalence(original, changed_plan)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'criteria.json'
            for payload in ('{"alpha":0.1,"alpha":0.2}', '{', 'null',
                            _canonical(original).replace('"alpha":0.05', '"alpha":NaN')):
                path.write_text(payload)
                with self.assertRaises(ValueError):
                    load_weighted_equivalence_criteria(path, declaration)

    def test_strict_boundaries_and_precision_statuses(self):
        self.assertEqual(_decision([-.1, .1], .2, True), 'equivalence_supported')
        for interval in ([-.2, .1], [-.1, .2], [.2, .3], [-.3, -.2]):
            self.assertEqual(_decision(interval, .2, True), 'inconclusive')
        for interval in ([.21, .3], [-.3, -.21]):
            self.assertEqual(_decision(interval, .2, True), 'difference_detected')
        self.assertEqual(_decision([-.1, .1], .2, False), 'inconclusive_precision')

    def test_real_absorbing_control_supports_only_declared_family(self):
        report = self.control_report
        before = deepcopy(report)
        assessment = assess_weighted_equivalence(criteria(self.control_plan), report)
        self.assertEqual(assessment['status'], 'equivalence_supported_within_declared_family')
        self.assertEqual(assessment['convergence_status'], 'not_established')
        self.assertEqual(len(assessment['comparisons']), 8)
        radius = sqrt(2*log(16/.05)/320)
        for row in assessment['comparisons']:
            self.assertEqual(row['mean_difference'], 0.)
            self.assertAlmostEqual(row['interval'][0], -radius)
            self.assertAlmostEqual(row['interval'][1], radius)
        self.assertEqual(assessment['study_report_sha256'], hashlib.sha256(_canonical(report).encode()).hexdigest())
        self.assertEqual(report, before)
        # Cached pointwise summaries are irrelevant to the simultaneous decision.
        changed = deepcopy(report)
        for scenario in changed['scenarios']:
            scenario['differences_from_finest'] = []
            for row in scenario['resolutions']:
                row['metrics'] = {'invented_cached_mean': 99}
        reassessed = assess_weighted_equivalence(criteria(self.control_plan), changed)
        self.assertEqual(reassessed['comparisons'], assessment['comparisons'])

    def test_real_small_study_is_inconclusive_despite_zero_observed_differences(self):
        declaration = plan()
        report = run_weighted_resolution_plan(declaration)
        assessment = assess_weighted_equivalence(criteria(declaration), report)
        self.assertEqual(assessment['status'], 'inconclusive_precision')
        self.assertTrue(all(row['status'] == 'inconclusive_precision' for row in assessment['comparisons']))
        self.assertTrue(all(row['interval'] == [-1., 1.] for row in assessment['comparisons']))

    def test_controlled_observation_fixtures_exercise_aggregate_decisions(self):
        # Consistent synthetic observation fields, not new simulated trajectories.
        for value, expected in ((1., 'difference_detected'), (.3, 'inconclusive')):
            report = deepcopy(self.control_report)
            for rep in report['scenarios'][0]['resolutions'][0]['replicates']:
                rep['ancestry'] = value
                final = rep['evaluation']['engine_report']['final_measurement']
                final['value'] = value
                final['modern_ancestry_weight'] = value*final['weight_denominator']
            assessment = assess_weighted_equivalence(criteria(self.control_plan), report)
            self.assertEqual(assessment['status'], expected)
            self.assertEqual(assessment['convergence_status'], 'not_established')

    def test_inconsistent_reports_are_rejected(self):
        baseline = run_weighted_resolution_plan(plan())
        mutations = [lambda r: r.update(mode='quick'), lambda r: r.update(study_version='unknown'),
                     lambda r: r.update(plan_sha256='0'*64), lambda r: r['family'].update(map_length=1.),
                     lambda r: r['scenarios'].append(deepcopy(r['scenarios'][0])),
                     lambda r: r['scenarios'][0]['resolutions'].pop()]
        for key, value in (('ancestry', float('nan')), ('p10_joint', 2.), ('joint_and_target', .5),
                           ('target_auto', 0), ('seed', 999), ('generation', 0), ('status', 'not_evaluated_quick')):
            mutations.append(lambda r, key=key, value=value:
                             r['scenarios'][0]['resolutions'][0]['replicates'][0].update({key: value}))
        mutations.extend((
            lambda r: r['scenarios'][0]['resolutions'][0]['replicates'].pop(),
            lambda r: r['scenarios'][0]['resolutions'][0]['replicates'][0]['config_realized'].update(s_mt=.5),
            lambda r: r['scenarios'][0]['resolutions'][0]['replicates'][0]['evaluation']['engine_report']['final_measurement'].update(value=.5),
            lambda r: r['scenarios'][0]['resolutions'][0]['replicates'][0]['evaluation']['engine_report']['final_measurement']['panel'].update(block_weights=[1, 1, 1, 1]),
            lambda r: r['scenarios'][0]['resolutions'][0]['replicates'][0]['evaluation']['engine_report']['final_measurement'].update(modern_ancestry_weight=1.),
        ))
        for mutate in mutations:
            changed = deepcopy(baseline)
            mutate(changed)
            with self.assertRaises(ValueError):
                assess_weighted_equivalence(criteria(plan()), changed)
        for report in (None, {}, baseline['workload_preview']):
            with self.assertRaises(ValueError):
                assess_weighted_equivalence(criteria(plan()), report)


if __name__ == '__main__':
    unittest.main()
