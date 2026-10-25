"""Fast integrity checks for the fixed I22 scientific archive, without long reruns."""

from copy import deepcopy
import hashlib
import json
from math import comb, expm1, fsum, log, sqrt
from pathlib import Path
import re
import unittest

from paleogen_rl.genetics.protocol import AutosomalProtocol
from study_autosomal_resolution import validate_resolution_plan


SCIENCE = Path(__file__).resolve().parents[2]/'docs/science'
PLAN_PATH = SCIENCE/'autosomal-target-regime-plan.json'
REPORT_PATH = SCIENCE/'autosomal-target-regime-report.json'
PLAN_FILE_SHA256 = 'f400cc547acae4143b352013fb68d14c625d1f888e0b60e8d919d2131f65bb10'
PARAMETERS = {
    'neutral': {},
    'reich_point': dict(s_mt=.0032, s=.0013, sel_locus='Y'),
    'reich_plus_symmetric_1pct': dict(s_mt=.0032, s=.0013, sel_locus='Y',
                                    mt_mod_nuc_arch=.01, mt_arch_nuc_mod=.01,
                                    y_mod_nuc_arch=.01, y_arch_nuc_mod=.01),
}
WORK = ('candidates_generated', 'accepted_candidates', 'offspring_generated', 'block_copy_transmissions')


class TestAutosomalTargetRegime(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN_PATH.read_text())
        self.report = json.loads(REPORT_PATH.read_text())

    def check_sum(self, parent, children):
        for field in WORK:
            self.assertEqual(parent[field], sum(child[field] for child in children))
        self.assertEqual(parent['state_allele_entries'], max(child['state_allele_entries'] for child in children))

    def check_bounded_mean(self, summary, values, lower=0., upper=1.):
        mean = fsum(values)/len(values)
        self.assertAlmostEqual(summary['mean'], mean, places=14)
        radius = (upper-lower)*sqrt(log(40)/(2*len(values)))
        for actual, expected in zip(summary['interval'], (max(lower, mean-radius), min(upper, mean+radius))):
            self.assertAlmostEqual(actual, expected, places=14)
        self.assertEqual(summary['method'], 'hoeffding_95_pointwise')

    def check_archive(self, report):
        plan = validate_resolution_plan(self.plan)
        self.assertEqual(report['plan'], plan)
        self.assertEqual(report['plan_file_sha256'], PLAN_FILE_SHA256)
        canonical = json.dumps(plan, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
        self.assertEqual(report['plan_sha256'], hashlib.sha256(canonical.encode()).hexdigest())
        self.assertEqual(report['study_version'], 'selected-autosomal-resolution-v2')
        self.assertEqual(report['mode'], 'full')
        self.assertEqual(report['convergence_status'], 'not_established')
        self.assertEqual([s['name'] for s in report['scenarios']], plan['scenarios'])
        identities = {}
        for scenario in report['scenarios']:
            self.assertEqual(scenario['parameters'], PARAMETERS[scenario['name']])
            rows = scenario['resolutions']
            self.assertEqual([row['block_count'] for row in rows], plan['resolutions'])
            for row in rows:
                blocks = row['block_count']
                contract = AutosomalProtocol.from_dict(row['autosomal_protocol'])
                self.assertEqual(contract.sha256, row['autosomal_protocol_sha256'])
                self.assertEqual(identities.setdefault(blocks, contract.sha256), contract.sha256)
                self.assertEqual(contract.population_size, 1450)
                self.assertEqual(contract.generations, 6993)
                self.assertEqual((contract.f, contract.male_fraction), (.05, .5))
                self.assertEqual(contract.mt_partner_block, 'b0')
                self.assertEqual(contract.y_partner_block, f'b{blocks-1}')
                self.assertEqual(contract.recombination_map.to_dict(), row['recombination_map'])
                expected_switch = -expm1(-2/(blocks-1))/2
                self.assertEqual(contract.recombination_map.switch_probabilities, (expected_switch,)*(blocks-1))
                self.assertEqual(row['block_positions'], [i/(blocks-1) for i in range(blocks)])
                self.assertEqual(row['partner_panel_weight'], 2/blocks)
                self.assertEqual(row['allele_copy_denominator'], 2900*blocks)
                config = row['config_parameters']
                for key, expected in dict(N=1450, gens=6993, f=.05, male_frac=.5, stop_when_absorbed=False).items():
                    self.assertEqual(config[key], expected)
                for key, expected in scenario['parameters'].items():
                    self.assertEqual(config[key], expected)
                for key in ('s', 's_mt', 'mt_mod_nuc_arch', 'mt_arch_nuc_mod', 'y_mod_nuc_arch', 'y_arch_nuc_mod'):
                    self.assertEqual(config[key], scenario['parameters'].get(key, 0.))
                selection = row['selection']
                self.assertEqual(selection['s_mt'], config['s_mt'])
                self.assertEqual(selection['s_y'], config['s'])
                for key in ('mt_mod_nuc_arch', 'mt_arch_nuc_mod', 'y_mod_nuc_arch', 'y_arch_nuc_mod'):
                    self.assertEqual(selection[key], config[key])
                self.assertEqual(selection['dominance'], 'additive')
                self.assertEqual(selection['mt_partner_block'], contract.mt_partner_block)
                self.assertEqual(selection['y_partner_block'], contract.y_partner_block)
                self.assertEqual(row['initialisation']['modern_males'], 36)
                self.assertEqual(row['initialisation']['modern_females'], 36)
                self.assertEqual(row['initialisation']['realised_ancestry'], 72/1450)
                replicates = row['replicates']
                self.assertEqual([r['seed'] for r in replicates], plan['seeds'])
                for replicate in replicates:
                    self.assertEqual(replicate['generation'], 6993)
                    self.assertEqual(replicate['status'], 'evaluated_at_target')
                    value = replicate['modern_allele_copies']/row['allele_copy_denominator']
                    self.assertEqual(replicate['ancestry'], value)
                    self.assertTrue(0 <= value <= 1)
                    males, both = replicate['male_n'], replicate['both_modern_men']
                    self.assertEqual(males, 725)
                    self.assertTrue(0 <= both <= males)
                    probability = comb(both, 10)/comb(males, 10) if both >= 10 else 0.
                    self.assertAlmostEqual(replicate['p10_joint'], probability, places=14)
                    self.assertEqual(replicate['target_auto'], .03 <= value <= .07)
                    self.assertAlmostEqual(replicate['joint_and_target'], probability*int(.03 <= value <= .07), places=14)
                    work = replicate['work_units']
                    self.assertEqual(work['offspring_generated'], 1450*6993)
                    self.assertEqual(work['accepted_candidates'], 1450*6993)
                    self.assertGreaterEqual(work['candidates_generated'], work['accepted_candidates'])
                    self.assertEqual(work['block_copy_transmissions'], 2*blocks*work['candidates_generated'])
                    self.assertEqual(work['state_allele_entries'], 2900*blocks)
                for field in ('ancestry', 'p10_joint', 'joint_and_target'):
                    self.check_bounded_mean(row['metrics'][field], [r[field] for r in replicates])
                target = row['metrics']['target_probability']
                hits = sum(r['target_auto'] for r in replicates)
                self.assertEqual((target['count'], target['replicates'], target['probability']), (hits, 2, hits/2))
                self.assertEqual(target['method'], 'wilson_95_pointwise')
                z = 1.959963984540054
                center = (hits/2+z*z/4)/(1+z*z/2)
                radius = z*sqrt((hits/2)*(1-hits/2)/2+z*z/16)/(1+z*z/2)
                for actual, expected in zip(target['interval'], (max(0., center-radius), min(1., center+radius))):
                    self.assertAlmostEqual(actual, expected, places=14)
                self.check_sum(row['work_units'], [r['work_units'] for r in replicates])
            self.assertEqual(len(scenario['differences_from_finest']), 2)
            for row, difference in zip(rows[:-1], scenario['differences_from_finest']):
                self.assertEqual(difference['block_count'], row['block_count'])
                self.assertEqual(difference['reference_block_count'], 128)
                for metric, field in (('ancestry', 'ancestry'), ('target_probability', 'target_auto'),
                                      ('p10_joint', 'p10_joint'), ('joint_and_target', 'joint_and_target')):
                    values = [float(a[field])-float(b[field]) for a, b in zip(row['replicates'], rows[-1]['replicates'])]
                    self.check_bounded_mean(difference['metrics'][metric], values, -1., 1.)
            self.check_sum(scenario['work_units'], [row['work_units'] for row in rows])
        self.check_sum(report['total_work_units'], [s['work_units'] for s in report['scenarios']])

    def test_fixed_plan_and_complete_archive(self):
        self.assertEqual(hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest(), PLAN_FILE_SHA256)
        self.assertEqual(self.plan, dict(plan_version='selected-autosomal-resolution-plan-v1',
                                       plan_id='target-regime-pilot-i22', population_size=1450,
                                       f=.05, male_fraction=.5, generations=6993, map_length=1.,
                                       resolutions=[8, 32, 128], seeds=[520000, 520001],
                                       scenarios=list(PARAMETERS)))
        self.check_archive(self.report)

    def test_tampered_counts_horizons_metrics_maps_and_costs_are_detected(self):
        for mutation in ('horizon', 'seed', 'copies', 'probability', 'target', 'metric', 'cost', 'map', 'hash'):
            report = deepcopy(self.report)
            row = report['scenarios'][0]['resolutions'][0]
            replicate = row['replicates'][0]
            if mutation == 'horizon': replicate['generation'] -= 1
            elif mutation == 'seed': replicate['seed'] = 999
            elif mutation == 'copies': replicate['modern_allele_copies'] += 1
            elif mutation == 'probability': replicate['p10_joint'] += .1
            elif mutation == 'target': replicate['target_auto'] = not replicate['target_auto']
            elif mutation == 'metric': row['metrics']['ancestry']['mean'] += .1
            elif mutation == 'cost': replicate['work_units']['candidates_generated'] += 1
            elif mutation == 'map': row['recombination_map']['switch_probabilities'][0] = .5
            else: row['autosomal_protocol_sha256'] = '0'*64
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                self.check_archive(report)

    def test_archive_is_strict_json_and_records_implementation_identity(self):
        def reject(value):
            raise ValueError(value)
        self.assertEqual(json.loads(REPORT_PATH.read_text(), parse_constant=reject), self.report)
        hashes = self.report['implementation_sha256']
        self.assertIn('study_autosomal_resolution.py', hashes)
        self.assertIn('paleogen_rl/genetics/protocol.py', hashes)
        self.assertIn('flake.lock', hashes)
        for digest in hashes.values():
            self.assertIsNotNone(re.fullmatch('[0-9a-f]{64}', digest))


if __name__ == '__main__':
    unittest.main()
