"""Conservative neutral geometry and maps; no claim of trajectory convergence."""

from copy import deepcopy
from dataclasses import replace
import hashlib
from itertools import product
import json
from math import expm1, fsum, prod
import unittest
from unittest.mock import patch

import numpy as np

from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.protocol import _canonical
from paleogen_rl.genetics.pulse import evaluate_block_pulse
from paleogen_rl.genetics.selected import BlockSelection
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel, measure_weighted_ancestry
from paleogen_rl.genetics.weighted_protocol import WeightedAutosomalProtocol
from paleogen_rl.genetics.weighted_refinement import FAMILY_VERSION, build_weighted_refinement_family


class TestWeightedRefinement(unittest.TestCase):
    def base(self, length=1., partners=('a', 'd')):
        panel = BlockPanel('synthetic-four', ('a', 'b', 'c', 'd'))
        positions = (1/16, 5/16, 11/16, 15/16)
        switches = tuple(-expm1(-2*(length*(b-a)))/2 for a, b in zip(positions, positions[1:]))
        return WeightedAutosomalProtocol(
            'synthetic-refinement-base', 40, 4, .5, .5, RecombinationMap(panel, switches),
            *partners, WeightedBlockPanel(panel, (1, 3, 3, 1), 'synthetic relative lengths'))

    def family(self, length=1., partners=('a', 'd'), **changes):
        return build_weighted_refinement_family(self.base(length, partners),
                    **{**dict(family_id='synthetic-family', map_length=length), **changes})

    def protocols(self, family):
        return [WeightedAutosomalProtocol.from_dict(row['autosomal_protocol']) for row in family['resolutions']]

    def test_owned_deterministic_hashed_declaration_and_replayable_protocols(self):
        with patch('numpy.random.default_rng', side_effect=AssertionError('unexpected RNG')), \
             patch('paleogen_rl.genetics.pulse.run_selected', side_effect=AssertionError('unexpected engine')):
            family = self.family()
        self.assertEqual(family['family_version'], FAMILY_VERSION)
        self.assertEqual(family['convergence_status'], 'not_established')
        self.assertEqual(family, self.family())
        restored = json.loads(json.dumps(family, allow_nan=False))
        digest = restored.pop('family_sha256')
        self.assertEqual(digest, hashlib.sha256(_canonical(restored).encode('utf-8')).hexdigest())
        protocols = self.protocols(family)
        self.assertEqual(protocols[0], self.base())
        self.assertEqual([len(p.measurement_panel.panel.block_ids) for p in protocols], [4, 8, 20])
        for row, protocol in zip(family['resolutions'], protocols):
            self.assertEqual(protocol.sha256, row['autosomal_protocol_sha256'])
            self.assertEqual(protocol.to_dict()['resolution_control'], {'status': 'not_established'})
        family['base_protocol']['measurement_weights']['block_weights'][0] = 999
        family['resolutions'][0]['autosomal_protocol']['pulse']['f'] = 0.
        self.assertEqual(self.base(), protocols[0])
        self.assertEqual(self.family()['base_protocol'], self.base().to_dict())

    def test_partner_cells_weights_and_neutral_parent_mass_are_conserved(self):
        for partners in (('a', 'd'), ('b', 'd'), ('b', 'b')):
            family = self.family(partners=partners)
            base = self.base(partners=partners)
            base_row = family['resolutions'][0]
            for row, protocol in zip(family['resolutions'], self.protocols(family)):
                weights = protocol.measurement_panel.block_weights
                ids = protocol.measurement_panel.panel.block_ids
                self.assertEqual(protocol.mt_partner_block, base.mt_partner_block)
                self.assertEqual(protocol.y_partner_block, base.y_partner_block)
                for field in ('population_size', 'generations', 'f', 'male_fraction'):
                    self.assertEqual(getattr(protocol, field), getattr(base, field))
                self.assertEqual(row['block_intervals'][0][0], 0.)
                self.assertEqual(row['block_intervals'][-1][1], 1.)
                for left, right in zip(row['block_intervals'], row['block_intervals'][1:]):
                    self.assertEqual(left[1], right[0])
                for parent_index, parent in enumerate(base.measurement_panel.panel.block_ids):
                    children = [i for i, name in enumerate(row['parent_block_ids']) if name == parent]
                    self.assertAlmostEqual(fsum(weights[i] for i in children), base.measurement_panel.block_weights[parent_index], places=14)
                    if parent in partners:
                        self.assertEqual(len(children), 1)
                        index = children[0]
                        self.assertEqual(ids[index], parent)
                        self.assertEqual(row['block_positions'][index], base_row['block_positions'][parent_index])
                        self.assertEqual(row['block_intervals'][index], base_row['block_intervals'][parent_index])
                        self.assertAlmostEqual(protocol.measurement_panel.normalized_weights[index],
                                               base.measurement_panel.normalized_weights[parent_index], places=14)

    def test_nested_midpoints_cells_and_composed_switch_probabilities(self):
        for length in (0., .1, 2.):
            family = self.family(length, refinement_factors=(1, 3, 15))
            for coarse, fine in zip(family['resolutions'], family['resolutions'][1:]):
                coarse_protocol, fine_protocol = self.protocols({'resolutions': [coarse, fine]})
                fine_ids = fine_protocol.measurement_panel.panel.block_ids
                fine_switches = fine_protocol.recombination_map.switch_probabilities
                retained = [fine_ids.index(block) for block in coarse_protocol.measurement_panel.panel.block_ids]
                for position, index in zip(coarse['block_positions'], retained):
                    self.assertEqual(position, fine['block_positions'][index])
                for start, end in coarse['block_intervals']:
                    children = [(a, b) for a, b in fine['block_intervals'] if start <= a < b <= end]
                    self.assertEqual(children[0][0], start)
                    self.assertEqual(children[-1][1], end)
                for index, (left, right) in enumerate(zip(retained, retained[1:])):
                    composed = (1-prod(1-2*r for r in fine_switches[left:right]))/2
                    self.assertAlmostEqual(composed, coarse_protocol.recombination_map.switch_probabilities[index], places=14)
                if length == 0.:
                    self.assertEqual(set(fine_switches), {0.})

    def test_measurement_is_conserved_for_arbitrary_duplicated_parent_states(self):
        counts = np.array([[0, 1, 2, 0], [2, 2, 0, 1], [1, 0, 1, 2]], dtype=np.uint8)
        family = self.family()
        base = self.base()
        reference = measure_weighted_ancestry(counts, base.measurement_panel,
                    generation=4, target_generation=4, mode='full', partner_block_ids=('a', 'd'))
        for row, protocol in zip(family['resolutions'], self.protocols(family)):
            columns = [base.measurement_panel.panel.block_ids.index(parent) for parent in row['parent_block_ids']]
            final = measure_weighted_ancestry(counts[:, columns], protocol.measurement_panel,
                    generation=4, target_generation=4, mode='full', partner_block_ids=('a', 'd'))
            self.assertAlmostEqual(final['value'], reference['value'], places=14)
            for actual, expected in zip(final['partner_diagnostics'], reference['partner_diagnostics']):
                for key in ('value', 'relative_panel_weight', 'weighted_ancestry_contribution'):
                    self.assertAlmostEqual(actual[key], expected[key], places=14)

    def test_invalid_factors_maps_identifiers_and_degenerate_geometry_are_rejected(self):
        for factors in ((), (1, 3), (3, 9, 27), (1, 2, 4), (1, 3, 5), (1, 3, 3), (1, True, 9), (1, 3., 9)):
            with self.subTest(factors=factors), self.assertRaises(ValueError):
                self.family(refinement_factors=factors)
        for length in (-1, True, float('nan'), float('inf'), 10**400, '1'):
            with self.subTest(length=length), self.assertRaises(ValueError):
                build_weighted_refinement_family(self.base(), family_id='family', map_length=length)
        for identity in ('', ' padded ', None):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                self.family(family_id=identity)
        for base in (None, self.base().to_dict(),
                     replace(self.base(), recombination_map=RecombinationMap(self.base().measurement_panel.panel, (0., 0., 0.)))):
            with self.subTest(base=base), self.assertRaises(ValueError):
                build_weighted_refinement_family(base, family_id='family', map_length=1.)
        two = BlockPanel('no-neutral', ('mt', 'y'))
        base = replace(self.base(0.), recombination_map=RecombinationMap(two, (0.,)),
                       measurement_panel=WeightedBlockPanel(two, (1, 1), 'fixture'), mt_partner_block='mt', y_partner_block='y')
        with self.assertRaises(ValueError):
            build_weighted_refinement_family(base, family_id='family', map_length=0.)
        panel = self.base(0.).measurement_panel.panel
        tiny = replace(self.base(0.), measurement_panel=WeightedBlockPanel(panel, (1, 1, 1, 1e-300), 'fixture'))
        with self.assertRaisesRegex(ValueError, 'geometry'):
            build_weighted_refinement_family(tiny, family_id='family', map_length=0.)

    def test_generated_identifier_collision_is_not_silently_accepted(self):
        panel = BlockPanel('collision', ('b::at1of6', 'b', 'c', 'd'))
        base = replace(self.base(0.), recombination_map=RecombinationMap(panel, (0., 0., 0.)),
                       measurement_panel=WeightedBlockPanel(panel, (1, 3, 3, 1), 'fixture'), mt_partner_block='b::at1of6')
        with self.assertRaises(ValueError):
            build_weighted_refinement_family(base, family_id='family', map_length=0.)

    def test_declaration_identity_tracks_inputs_and_remains_json_reconstructible(self):
        family = self.family()
        for changes in (dict(family_id='other'), dict(refinement_factors=(1, 5, 15))):
            self.assertNotEqual(self.family(**changes)['family_sha256'], family['family_sha256'])
        changed = build_weighted_refinement_family(replace(self.base(), f=.4), family_id='synthetic-family', map_length=1.)
        self.assertNotEqual(changed['family_sha256'], family['family_sha256'])
        restored = json.loads(json.dumps(family))
        self.assertEqual(build_weighted_refinement_family(
            WeightedAutosomalProtocol.from_dict(restored['base_protocol']), family_id=restored['family_id'],
            map_length=restored['map_length'], refinement_factors=restored['refinement_factors']), family)
        unchanged = deepcopy(family)
        self.protocols(family)
        self.assertEqual(family, unchanged)

    def test_generated_protocols_execute_with_active_selection_in_all_modes(self):
        for length, seed in product((0., 1.), (0, 17, 42)):
            family = self.family(length)
            for protocol in self.protocols(family):
                args = dict(population_size=protocol.population_size, f=protocol.f,
                            male_fraction=protocol.male_fraction, generations=protocol.generations, seed=seed,
                            recombination_map=protocol.recombination_map, measurement_panel=protocol.measurement_panel,
                            selection=BlockSelection(s_mt=.0032, s_y=.0013,
                                mt_mod_nuc_arch=.01, y_arch_nuc_mod=.01,
                                mt_partner_block=protocol.mt_partner_block, y_partner_block=protocol.y_partner_block))
                full = evaluate_block_pulse(**args)
                quick = evaluate_block_pulse(**args, mode='quick')
                adaptive = evaluate_block_pulse(**args, mode='adaptive')
                self.assertEqual(full['engine_report']['final_measurement']['generation'], protocol.generations)
                self.assertEqual(full['measurement_panel'], protocol.measurement_panel.to_dict())
                self.assertIsNone(quick['ancestry_measurement']['value'])
                self.assertEqual(full['target']['joint_and_target'], adaptive['target']['joint_and_target'])


if __name__ == '__main__':
    unittest.main()
