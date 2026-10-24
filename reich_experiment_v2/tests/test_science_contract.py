from copy import deepcopy
import json
import sys
import unittest
from unittest.mock import patch

from science_contract import (
    CONTRACT_PATH, load_contract, validate_autosomal_statistic, validate_contract,
)
from verify_provenance import REPO_ROOT, REGISTRY_PATH
from verify_sources import CATALOG_PATH


class TestScienceContract(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((REPO_ROOT / CONTRACT_PATH).read_text(encoding='utf-8'))
        self.catalog = json.loads((REPO_ROOT / CATALOG_PATH).read_text(encoding='utf-8'))
        self.registry = json.loads((REPO_ROOT / REGISTRY_PATH).read_text(encoding='utf-8'))
        self.measurement = {
            'status': 'evaluated', 'value': 0.05, 'generation': 6993,
            'diploid_individuals': 1450, 'allele_copy_denominator': 17400,
            'locus_basis': {
                'kind': 'neutral_proxy', 'weighting': 'equal_diploid_copies',
                'total_loci': 8, 'included_loci': [2, 3, 4, 5, 6, 7],
                'excluded_loci': [0, 1], 'selected_loci': [0, 1],
            },
        }

    def validate(self, contract):
        return validate_contract(contract, self.catalog, self.registry)

    def test_real_contract_loads_without_network_and_is_read_only(self):
        before = deepcopy((self.contract, self.catalog, self.registry))
        with patch('socket.socket', side_effect=AssertionError('network forbidden')):
            self.assertEqual(load_contract(), self.contract)
            self.assertEqual(self.validate(self.contract), self.contract)
        self.assertEqual(before, (self.contract, self.catalog, self.registry))

    def test_four_distinct_statistics_and_reference_parameters(self):
        statistics = {s['id']: s for s in self.contract['statistics']}
        self.assertEqual(set(statistics), {'mt_fixation', 'y_fixation',
                                         'ten_male_joint', 'final_autosomal_ancestry'})
        self.assertEqual(len({s['formula'] for s in statistics.values()}), 4)
        self.assertEqual([statistics[key]['unit'] for key in
                          ('mt_fixation', 'y_fixation', 'ten_male_joint',
                           'final_autosomal_ancestry')],
                         ['boolean', 'boolean', 'probability', 'fraction'])
        parameters = {p['id']: p['value'] for p in self.contract['reference_parameters']}
        self.assertEqual(parameters, {
            'years_per_generation': 28.6, 'mixture_generations_ago': 8741,
            'sampling_generations_ago': 1748, 'modern_uniparental_ne': 7000,
            'archaic_uniparental_ne': 2250, 'neandertal_uniparental_ne': 725,
        })
        self.assertEqual(self.contract['timeline'], {'elapsed_generations': 6993,
                                                    'target_age_ka': 50})

    def test_missing_duplicate_entries_and_version_rejected(self):
        variants = [None, {}, {**self.contract, 'schema_version': '2'},
                    {**self.contract, 'contract_version': 'unversioned'}]
        for group in ('observations', 'statistics', 'reference_parameters'):
            missing = deepcopy(self.contract)
            missing[group].pop()
            variants.append(missing)
            duplicate = deepcopy(self.contract)
            duplicate[group][1] = deepcopy(duplicate[group][0])
            variants.append(duplicate)
        for contract in variants:
            with self.subTest(contract=contract), self.assertRaises(ValueError):
                self.validate(contract)

    def test_status_citation_and_uncertainty_rejected(self):
        variants = []
        for field, value in (('status', 'hypothesis'), ('citations', []),
                             ('sampling', ''), ('unit', None)):
            contract = deepcopy(self.contract)
            contract['observations'][0][field] = value
            variants.append(contract)
        for field, value in (('source_id', 'SI5'), ('content_id', 'sha256:' + '0' * 64),
                             ('pages', []), ('pages', [0]), ('pages', [True]),
                             ('section', '')):
            contract = deepcopy(self.contract)
            contract['observations'][0]['citations'][0][field] = value
            variants.append(contract)
        contract = deepcopy(self.contract)
        contract['observations'][1]['uncertainty']['confidence_level'] = 0.95
        variants.append(contract)
        contract = deepcopy(self.contract)
        contract['observations'][1]['uncertainty']['bounds'] = [0.02, 0.08]
        variants.append(contract)
        contract = deepcopy(self.contract)
        contract['statistics'][3]['target_bounds'] = [0.02, 0.08]
        variants.append(contract)
        for contract in variants:
            with self.subTest(contract=contract), self.assertRaises(ValueError):
                self.validate(contract)

    def test_mode_and_timeline_inconsistency_rejected(self):
        variants = []
        for mode in ('quick', 'adaptive'):
            contract = deepcopy(self.contract)
            contract['mode_semantics'][mode]['final_autosomal'] = 'all_trajectories'
            variants.append(contract)
        contract = deepcopy(self.contract)
        contract['timeline']['elapsed_generations'] = 6000
        variants.append(contract)
        contract = deepcopy(self.contract)
        contract['uncertainty_policy']['simulation_intervals'] = 'historical'
        variants.append(contract)
        for contract in variants:
            with self.subTest(contract=contract), self.assertRaises(ValueError):
                self.validate(contract)

    def test_valid_measurements_at_several_resolutions_and_bounds(self):
        for total, excluded, population in ((8, [], 1450), (8, [0, 1], 1450),
                                            (256, [1, 3], 40), (1024, [], 20)):
            for value in (0, 0.03, 0.05, 0.07, 1):
                measurement = deepcopy(self.measurement)
                included = [i for i in range(total) if i not in excluded]
                measurement.update(value=value, diploid_individuals=population,
                                   allele_copy_denominator=2 * population * len(included))
                measurement['locus_basis'].update(total_loci=total, included_loci=included,
                                                  excluded_loci=excluded, selected_loci=excluded)
                before = deepcopy(measurement)
                with self.subTest(total=total, excluded=excluded, value=value):
                    self.assertEqual(validate_autosomal_statistic(
                        measurement, expected_generation=6993), measurement)
                    self.assertEqual(measurement, before)

    def test_missing_generation_or_basis_rejected(self):
        for field in ('generation', 'locus_basis'):
            measurement = deepcopy(self.measurement)
            del measurement[field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                validate_autosomal_statistic(measurement, expected_generation=6993)
        measurement = deepcopy(self.measurement)
        del measurement['locus_basis']['included_loci']
        with self.assertRaisesRegex(ValueError, 'included_loci'):
            validate_autosomal_statistic(measurement, expected_generation=6993)

    def test_wrong_generation_status_value_population_or_denominator_rejected(self):
        for field, value in (
            ('generation', 100), ('generation', -1), ('generation', True),
            ('generation', 6993.0), ('status', 'not_evaluated'),
            ('value', None), ('value', float('nan')), ('value', float('inf')),
            ('value', -0.01), ('value', 1.01), ('value', '0.05'), ('value', True),
            ('diploid_individuals', 0), ('diploid_individuals', True),
            ('allele_copy_denominator', 17401), ('allele_copy_denominator', None),
        ):
            measurement = deepcopy(self.measurement)
            measurement[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_autosomal_statistic(measurement, expected_generation=6993)
        for horizon in (None, True, -1, 6993.0):
            with self.subTest(horizon=horizon), self.assertRaises(ValueError):
                validate_autosomal_statistic(self.measurement, expected_generation=horizon)

    def test_invalid_loci_or_partition_rejected(self):
        for field, value in (
            ('included_loci', []), ('included_loci', [2, 2]), ('included_loci', [8]),
            ('included_loci', [-1]), ('included_loci', [True]), ('included_loci', [2.0]),
            ('included_loci', 6), ('excluded_loci', [0]), ('excluded_loci', [0, 1, 2]),
            ('selected_loci', [2]), ('selected_loci', [0, 0]), ('selected_loci', None),
            ('total_loci', 0), ('total_loci', True), ('weighting', 'unspecified'),
            ('kind', 'genome_wide'),
        ):
            measurement = deepcopy(self.measurement)
            measurement['locus_basis'][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_autosomal_statistic(measurement, expected_generation=6993)

    def test_actual_small_simulation_is_not_a_50ka_measurement(self):
        sys.path.insert(0, str(REPO_ROOT / 'reich_experiment_v2/src'))
        from epi_pulse import Config, run
        result = run(Config(N=40, gens=6, seed=71, stop_when_absorbed=False))
        measurement = deepcopy(self.measurement)
        measurement.update(value=result['auto_mod'], generation=result['generations_completed'],
                           diploid_individuals=result['pop'],
                           allele_copy_denominator=2 * result['pop'] * 8)
        measurement['locus_basis'].update(included_loci=list(range(8)),
                                          excluded_loci=[], selected_loci=[])
        self.assertEqual(measurement['generation'], 6)
        validate_autosomal_statistic(measurement, expected_generation=6)
        with self.assertRaisesRegex(ValueError, 'final horizon'):
            validate_autosomal_statistic(measurement, expected_generation=6993)


if __name__ == '__main__':
    unittest.main()
