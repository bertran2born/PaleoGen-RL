"""Weighted declarations: strict inputs, content identity and source-free replay."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
import hashlib
from itertools import product
import json
from pathlib import Path
import tempfile
import unittest

from run_experiment import SCENARIOS
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.protocol import AutosomalProtocol, load_autosomal_protocol
from paleogen_rl.genetics.pulse import evaluate_block_pulse
from paleogen_rl.genetics.selected import BlockSelection
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel
from paleogen_rl.genetics.weighted_protocol import (
    WEIGHTED_PROTOCOL_VERSION, WeightedAutosomalProtocol, load_weighted_autosomal_protocol,
)


class TestWeightedProtocol(unittest.TestCase):
    def protocol(self):
        panel = BlockPanel('synthetic-three', ('mt', 'middle', 'y'))
        return WeightedAutosomalProtocol(
            protocol_id='synthetic-weighted-v1', population_size=40, generations=4,
            f=.5, male_fraction=.5, recombination_map=RecombinationMap(panel, (.1, .1)),
            mt_partner_block='mt', y_partner_block='y',
            measurement_panel=WeightedBlockPanel(panel, (2, 4, 2), 'synthetic relative lengths'))

    def evaluate(self, protocol, seed, mode, parameters):
        selection = BlockSelection(
            **{key: value for key, value in parameters.items() if key not in ('s', 'sel_locus')},
            s_y=parameters.get('s', 0.), mt_partner_block=protocol.mt_partner_block,
            y_partner_block=protocol.y_partner_block)
        return evaluate_block_pulse(
            population_size=protocol.population_size, f=protocol.f, male_fraction=protocol.male_fraction,
            generations=protocol.generations, recombination_map=protocol.recombination_map,
            measurement_panel=protocol.measurement_panel, selection=selection, seed=seed, mode=mode)

    def test_roundtrip_owns_inputs_and_snapshots_are_independent(self):
        document = self.protocol().to_dict()
        restored = WeightedAutosomalProtocol.from_dict(document)
        self.assertEqual(restored, self.protocol())
        self.assertEqual(restored.to_dict(), document)
        self.assertEqual(WeightedAutosomalProtocol.from_dict(json.loads(restored.canonical_json)), restored)
        document['measurement_weights']['block_weights'][0] = 9
        document['recombination_map']['panel']['block_ids'][0] = 'changed'
        document['measurement']['target_interval'][0] = 0.
        snapshot = restored.to_dict()
        snapshot['measurement_weights']['block_weights'].append(3)
        snapshot['measurement']['target_interval'][1] = 1.
        self.assertEqual(restored.to_dict(), self.protocol().to_dict())
        self.assertEqual(restored.measurement_panel.normalized_weights, (.25, .5, .25))
        for target, attribute, value in ((restored, 'generations', 8),
                                         (restored.measurement_panel, 'weight_basis', 'changed')):
            with self.assertRaises(FrozenInstanceError):
                setattr(target, attribute, value)

    def test_canonical_and_file_hashes_have_distinct_meanings(self):
        protocol = self.protocol()
        hashes = []
        with tempfile.TemporaryDirectory() as directory:
            for number, content in enumerate((protocol.canonical_json,
                    json.dumps(protocol.to_dict(), indent=2),
                    json.dumps(dict(reversed(list(protocol.to_dict().items()))), indent=4))):
                path = Path(directory)/str(number)
                path.write_text(content, encoding='utf-8')
                restored, file_hash = load_weighted_autosomal_protocol(path)
                self.assertEqual(restored.sha256, protocol.sha256)
                self.assertEqual(file_hash, hashlib.sha256(path.read_bytes()).hexdigest())
                hashes.append(file_hash)
        self.assertEqual(len(set(hashes)), 3)
        self.assertEqual(protocol.sha256, hashlib.sha256(protocol.canonical_json.encode('utf-8')).hexdigest())

    def test_identity_covers_every_declared_parameter_including_weight_basis(self):
        protocol = self.protocol()
        panel = protocol.measurement_panel.panel
        for changes in (
                dict(protocol_id='other'), dict(population_size=42), dict(generations=5),
                dict(f=.4), dict(male_fraction=.4), dict(mt_partner_block='middle'),
                dict(y_partner_block='middle'), dict(recombination_map=RecombinationMap(panel, (.2, .1))),
                dict(measurement_panel=WeightedBlockPanel(panel, (3, 4, 2), 'synthetic relative lengths')),
                dict(measurement_panel=WeightedBlockPanel(panel, (2, 4, 2), 'another justification')),
                dict(measurement_panel=WeightedBlockPanel(panel, (4, 8, 4), 'synthetic relative lengths'))):
            with self.subTest(changes=changes):
                self.assertNotEqual(replace(protocol, **changes).sha256, protocol.sha256)
        for changed_panel in (BlockPanel('renamed', panel.block_ids),
                              BlockPanel(panel.panel_id, ('y', 'middle', 'mt'))):
            changed = replace(protocol, recombination_map=RecombinationMap(changed_panel, (.1, .1)),
                              measurement_panel=WeightedBlockPanel(changed_panel, (2, 4, 2), 'synthetic relative lengths'))
            self.assertNotEqual(changed.sha256, protocol.sha256)
        scaled = replace(protocol, measurement_panel=WeightedBlockPanel(panel, (4, 8, 4), 'synthetic relative lengths'))
        self.assertEqual(scaled.measurement_panel.normalized_weights, protocol.measurement_panel.normalized_weights)

    def test_invalid_declarations_and_false_convergence_are_rejected(self):
        original = self.protocol().to_dict()
        cases = []
        for key in original:
            missing = deepcopy(original)
            del missing[key]
            cases.append(missing)
        for section in ('pulse', 'partners', 'measurement', 'resolution_control', 'measurement_weights',
                        'recombination_map'):
            for key in original[section]:
                missing = deepcopy(original)
                del missing[section][key]
                cases.append(missing)
            extra = deepcopy(original)
            extra[section]['unknown'] = 0
            cases.append(extra)
        for key, value in (('extra', 0), ('protocol_id', ' bad '), ('protocol_version', 'unknown'),
                           ('population_size', 19), ('population_size', True), ('population_size', 40.),
                           ('generations', 0), ('generations', True), ('generations', 4.)):
            cases.append({**original, key: value})
        for section, key, values in (
                ('pulse', 'f', (True, -.1, 1.1, float('nan'), float('inf'))),
                ('pulse', 'male_fraction', (True, -1, 2, float('nan'))),
                ('partners', 'mt', ('absent', None)),
                ('recombination_map', 'switch_probabilities', ([.1], [.6, .1], [True, .1])),
                ('measurement', 'sample_size', (11, 10., True)),
                ('measurement', 'sample_replacement', (0, True)),
                ('measurement', 'target_interval', ([0., 1.],)),
                ('measurement', 'measurement_version', ('autosomal-block-measurement-v1',)),
                ('measurement', 'observable', ('total_diploid_block_ancestry',)),
                ('measurement', 'weighting', ('equal_diploid_copies', 'exclude_partners')),
                ('resolution_control', 'status', ('validated', 'converged')),
                ('measurement_weights', 'block_weights',
                 ([], [1, 2], [0, 1, 1], [-1, 1, 1], [True, 1, 1], ['1', 1, 1],
                  [float('nan'), 1, 1], [float('inf'), 1, 1], [10**400, 1, 1], [1e308, 1e-308, 1])),
                ('measurement_weights', 'weight_basis', ('', ' padded ', None))):
            for value in values:
                changed = deepcopy(original)
                changed[section][key] = value
                cases.append(changed)
        impossible = deepcopy(original)
        impossible['pulse'] = dict(f=1., male_fraction=1.)
        for change in ({'panel_id': 'synthetic-three', 'block_ids': ['mt', 'mt', 'y']},
                       {'panel_id': 'synthetic-three'},
                       {**original['recombination_map']['panel'], 'unknown': 0}):
            changed = deepcopy(original)
            changed['recombination_map']['panel'] = change
            cases.append(changed)
        for key in ('normalized_weights', 'panel'):
            changed = deepcopy(original)
            changed['measurement_weights'][key] = []
            cases.append(changed)
        cases.extend((impossible, None, [], 0))
        for declaration in cases:
            with self.subTest(declaration=declaration), self.assertRaises(ValueError):
                WeightedAutosomalProtocol.from_dict(declaration)

    def test_panel_identity_order_and_direct_construction_are_validated(self):
        protocol = self.protocol()
        for panel in (None, protocol.recombination_map.panel,
                      WeightedBlockPanel(BlockPanel('other', ('mt', 'middle', 'y')), (2, 4, 2), 'fixture'),
                      WeightedBlockPanel(BlockPanel('synthetic-three', ('y', 'middle', 'mt')), (2, 4, 2), 'fixture')):
            with self.subTest(panel=panel), self.assertRaises(ValueError):
                replace(protocol, measurement_panel=panel)
        for changes in (dict(population_size=19), dict(generations=0), dict(mt_partner_block='missing'),
                        dict(f=1., male_fraction=1.), dict(recombination_map=None)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(protocol, **changes)

    def test_file_loader_rejects_duplicate_fields_nonfinite_and_malformed_json(self):
        valid = self.protocol().canonical_json
        invalid = [valid.replace('"f":0.5', '"f":0.5,"f":0.4'),
                   valid.replace('"block_weights":[', '"block_weights":[],"block_weights":['),
                   valid.replace('"protocol_id":', '"protocol_id":"duplicate","protocol_id":'),
                   '{', '[]', 'null']
        invalid.extend(valid.replace('[2.0,4.0,2.0]', f'[{value},4.0,2.0]')
                       for value in ('NaN', 'Infinity', '-Infinity', '1e999'))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'contract.json'
            for content in invalid:
                self.assertNotEqual(content, valid)
                path.write_text(content)
                with self.subTest(content=content), self.assertRaises(ValueError):
                    load_weighted_autosomal_protocol(path)

    def test_existing_equal_weight_format_remains_distinct_even_with_equal_weights(self):
        protocol = self.protocol()
        legacy = AutosomalProtocol(**{field.name: getattr(protocol, field.name) for field in fields(AutosomalProtocol)})
        equal = replace(protocol, measurement_panel=WeightedBlockPanel(protocol.recombination_map.panel, (1, 1, 1), 'fixture'))
        self.assertNotEqual(equal.sha256, legacy.sha256)
        with self.assertRaises(ValueError):
            AutosomalProtocol.from_dict(equal.to_dict())
        with self.assertRaises(ValueError):
            WeightedAutosomalProtocol.from_dict(legacy.to_dict())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'protocol.json'
            path.write_text(equal.canonical_json)
            with self.assertRaises(ValueError):
                load_autosomal_protocol(path)
            path.write_text(legacy.canonical_json)
            self.assertEqual(load_autosomal_protocol(path)[0], legacy)
            with self.assertRaises(ValueError):
                load_weighted_autosomal_protocol(path)

    def test_source_free_replay_matches_direct_api_for_all_scenarios_modes_and_seeds(self):
        expected = self.protocol()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'input.json'
            source.write_text(expected.canonical_json)
            loaded, _ = load_weighted_autosomal_protocol(source)
            snapshot = json.loads(loaded.canonical_json)
            source.unlink()
            restored = WeightedAutosomalProtocol.from_dict(snapshot)
            self.assertEqual(restored.to_dict()['protocol_version'], WEIGHTED_PROTOCOL_VERSION)
            for (name, parameters), seed, mode in product(SCENARIOS.items(), (0, 17, 42), ('full', 'quick', 'adaptive')):
                with self.subTest(scenario=name, seed=seed, mode=mode):
                    self.assertEqual(self.evaluate(restored, seed, mode, parameters),
                                     self.evaluate(expected, seed, mode, parameters))


if __name__ == '__main__':
    unittest.main()
