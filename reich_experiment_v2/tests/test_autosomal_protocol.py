"""Content-bound measurement contracts and their three-mode CLI integration."""

from contextlib import redirect_stderr
from copy import deepcopy
import csv
from dataclasses import FrozenInstanceError, replace
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from run_experiment import Config, SCENARIOS, main, run_block_mode
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.protocol import (
    AutosomalProtocol, PROTOCOL_RESULT_SCHEMA_VERSION, PROTOCOL_VERSION, load_autosomal_protocol,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT.parent/'docs/science/autosomal-protocol-synthetic.json'


class TestAutosomalProtocol(unittest.TestCase):
    def protocol(self):
        return load_autosomal_protocol(EXAMPLE)[0]

    def test_roundtrip_owned_snapshot_and_immutable_configuration(self):
        original = json.loads(EXAMPLE.read_text())
        protocol = AutosomalProtocol.from_dict(original)
        self.assertEqual(protocol.to_dict(), original)
        self.assertEqual(AutosomalProtocol.from_dict(json.loads(protocol.canonical_json)), protocol)
        original['recombination_map']['panel']['block_ids'].append('extra')
        original['recombination_map']['switch_probabilities'][0] = .5
        snapshot = protocol.to_dict()
        snapshot['measurement']['target_interval'][0] = 0.
        self.assertEqual(len(protocol.recombination_map.panel.block_ids), 4)
        self.assertEqual(protocol.recombination_map.switch_probabilities[0], .1)
        self.assertEqual(protocol.to_dict()['measurement']['target_interval'], [.03, .07])
        with self.assertRaises(FrozenInstanceError):
            protocol.generations = 4

    def test_canonical_identity_ignores_formatting_but_file_hash_does_not(self):
        protocol = self.protocol()
        with tempfile.TemporaryDirectory() as directory:
            hashes = []
            for name, payload in (('compact', protocol.canonical_json),
                                  ('pretty', json.dumps(protocol.to_dict(), indent=5)),
                                  ('sorted', json.dumps(protocol.to_dict(), sort_keys=True))):
                path = Path(directory)/name
                path.write_text(payload)
                restored, file_hash = load_autosomal_protocol(path)
                self.assertEqual(restored.sha256, protocol.sha256)
                self.assertEqual(file_hash, hashlib.sha256(path.read_bytes()).hexdigest())
                hashes.append(file_hash)
            self.assertEqual(len(set(hashes)), 3)
        self.assertEqual(protocol.sha256, hashlib.sha256(protocol.canonical_json.encode()).hexdigest())

    def test_identity_changes_with_each_locked_parameter(self):
        protocol = self.protocol()
        mapping = RecombinationMap(protocol.recombination_map.panel, (.2, .1, .1))
        reordered = RecombinationMap(BlockPanel('synthetic-four', ('b', 'a', 'c', 'd')), (.1, .1, .1))
        for changes in (dict(protocol_id='another-name'), dict(population_size=42), dict(generations=4),
                        dict(f=.4), dict(male_fraction=.6), dict(recombination_map=mapping),
                        dict(recombination_map=reordered), dict(mt_partner_block='b'), dict(y_partner_block='d')):
            with self.subTest(changes=changes):
                self.assertNotEqual(replace(protocol, **changes).sha256, protocol.sha256)
        # The historical regime is expressible without claiming it was simulated or calibrated.
        historical = replace(protocol, population_size=1450, generations=6993, f=.05)
        self.assertEqual(historical.to_dict()['resolution_control']['status'], 'not_established')

    def test_invalid_missing_unknown_and_falsely_validated_contracts_are_rejected(self):
        document = self.protocol().to_dict()
        bad = []
        for field in document:
            changed = deepcopy(document)
            changed.pop(field)
            bad.append(changed)
        for field, value in (('protocol_version', 'unknown'), ('protocol_id', ' bad '),
                             ('population_size', 19), ('population_size', 40.), ('population_size', True),
                             ('generations', 0), ('generations', True), ('extra', 'ignored?'),
                             ('resolution_control', {'status': 'validated'}),
                             ('resolution_control', {'status': 'converged'})):
            bad.append({**document, field: value})
        for section, field, value in (
                ('pulse', 'f', True), ('pulse', 'f', float('nan')),
                ('pulse', 'male_fraction', 2.), ('pulse', 'unknown', 0),
                ('partners', 'mt', 'missing'), ('partners', 'unknown', 'a'),
                ('measurement', 'sample_size', 11), ('measurement', 'sample_size', 10.),
                ('measurement', 'sample_replacement', 0), ('measurement', 'sample_replacement', True),
                ('measurement', 'target_interval', [0., .1]), ('measurement', 'weighting', 'exclude_partners'),
                ('recombination_map', 'switch_probabilities', [.1]),
                ('recombination_map', 'unknown', 'ignored?')):
            changed = deepcopy(document)
            changed[section][field] = value
            bad.append(changed)
        impossible = deepcopy(document)
        impossible['pulse'] = dict(f=1., male_fraction=1.)
        bad.append(impossible)
        for declaration in bad:
            with self.subTest(declaration=declaration), self.assertRaises(ValueError):
                AutosomalProtocol.from_dict(declaration)
        with tempfile.TemporaryDirectory() as directory:
            duplicate = Path(directory)/'duplicate.json'
            duplicate.write_text('{"pulse":{"f":0,"f":1}}')
            with self.assertRaisesRegex(ValueError, 'duplicate protocol field'):
                load_autosomal_protocol(duplicate)

    def cli(self, directory, name, mode, *, protocol=True, extra=()):
        output = Path(directory)/f'{name}.csv'
        contract = Path(directory)/f'{name}-protocol.json'
        contract.write_bytes(EXAMPLE.read_bytes())
        argv = [sys.executable, str(ROOT/'run_experiment.py'), '--scenario', 'all', '--mode', mode,
                '--reps', '2', '--seed', '17', '--output', str(output)]
        if protocol:
            argv.extend(['--autosomal-protocol', str(contract)])
        else:
            declaration = self.protocol().to_dict()
            mapfile = Path(directory)/f'{name}-map.json'
            mapfile.write_text(json.dumps(declaration['recombination_map']))
            argv.extend(['--N', '40', '--gens', '3', '--f', '.5', '--male-frac', '.5',
                         '--block-map', str(mapfile), '--mt-partner-block', 'a', '--y-partner-block', 'c'])
        process = subprocess.run([*argv, *extra], cwd=directory, capture_output=True, text=True)
        return process, output, contract

    def read(self, output):
        with output.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        def nonfinite(value):
            raise ValueError(value)
        return rows, json.loads(output.with_suffix('.json').read_text(), parse_constant=nonfinite)

    def test_all_scenarios_and_modes_match_explicit_map_and_replay_without_source(self):
        expected = self.protocol()
        for mode in ('full', 'quick', 'adaptive'):
            with tempfile.TemporaryDirectory() as directory, self.subTest(mode=mode):
                process, output, source = self.cli(directory, 'protocol', mode)
                self.assertEqual(process.returncode, 0, process.stdout+process.stderr)
                rows, document = self.read(output)
                file_hash = hashlib.sha256(source.read_bytes()).hexdigest()
                source.unlink()
                plain_process, plain_output, _ = self.cli(directory, 'plain', mode, protocol=False)
                self.assertEqual(plain_process.returncode, 0, plain_process.stdout+plain_process.stderr)
                plain_rows, _ = self.read(plain_output)
                self.assertEqual(len(rows), 2*len(SCENARIOS))
                self.assertEqual(document['meta']['autosomal_protocol'], expected.to_dict())
                self.assertEqual(document['meta']['autosomal_protocol_sha256'], expected.sha256)
                self.assertEqual(document['meta']['autosomal_protocol_file_sha256'], file_hash)
                self.assertEqual(document['meta']['result_schema_version'], PROTOCOL_RESULT_SCHEMA_VERSION)
                self.assertEqual(document['meta']['resolution_control_status'], 'not_established')
                for row, plain in zip(rows, plain_rows):
                    snapshot = AutosomalProtocol.from_dict(json.loads(row['autosomal_protocol']))
                    self.assertEqual(snapshot.sha256, row['autosomal_protocol_sha256'])
                    self.assertEqual(snapshot.sha256, expected.sha256)
                    self.assertEqual(row['autosomal_protocol_version'], PROTOCOL_VERSION)
                    self.assertEqual(row['autosomal_protocol_file_sha256'], file_hash)
                    self.assertEqual(row['result_schema_version'], PROTOCOL_RESULT_SCHEMA_VERSION)
                    self.assertEqual(row['block_map_sha256'], '')
                    self.assertEqual(row['resolution_control_status'], 'not_established')
                    config = Config(**json.loads(row['config_realized']))
                    replayed = run_block_mode(config, mode, snapshot.recombination_map,
                                               snapshot.mt_partner_block, snapshot.y_partner_block)
                    for field, value in replayed.items():
                        self.assertEqual(row[field], '' if value is None else str(value), field)
                    for field in plain:
                        if field not in ('result_schema_version', 'block_map_sha256'):
                            self.assertEqual(row[field], plain[field], field)

    def test_posterior_overrides_and_matching_explicit_values_remain_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            posterior = Path(directory)/'synthetic.txt'
            posterior.write_text('-.004\n0\n.003\n')
            process, output, _ = self.cli(directory, 'selected', 'adaptive', extra=(
                '--scenario', 'reich_point', '--mt-posterior', str(posterior), '--mt-arch-nuc-mod', '.003',
                '--N', '40', '--gens', '3', '--f', '.5', '--male-frac', '.5'))
            self.assertEqual(process.returncode, 0, process.stdout+process.stderr)
            rows, document = self.read(output)
            self.assertEqual(len(rows), 2)
            for row in rows:
                config = json.loads(row['config_realized'])
                self.assertEqual(config['mt_arch_nuc_mod'], .003)
                self.assertEqual(row['mt_selection_source'], 'posterior_draw')
                self.assertEqual(int(row['mt_posterior_draw_seed']), int(row['seed'])+27383)
                self.assertEqual(row['mt_posterior_sha256'], hashlib.sha256(posterior.read_bytes()).hexdigest())
            self.assertEqual(document['meta']['autosomal_protocol_sha256'], self.protocol().sha256)

    def test_conflicting_options_and_existing_outputs_fail_before_any_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'new.csv'
            base = ['run_experiment.py', '--autosomal-protocol', str(EXAMPLE), '--scenario', 'neutral',
                    '--mode', 'full', '--reps', '1', '--output', str(output)]
            cases = [base+extra for extra in (['--N', '41'], ['--N', '1450'], ['--gens', '4'],
                     ['--gens', '6993'], ['--f', '.05'], ['--male-frac', '.6'],
                     ['--block-map', 'missing.json'], ['--mt-partner-block', 'a'], ['--y-partner-block', 'c'])]
            cases.append(base[:-2])
            for argv in cases:
                with self.subTest(argv=argv), patch.object(sys, 'argv', argv):
                    with patch('run_experiment.run_block_full') as full, \
                         patch('run_experiment.run_block_mode') as screened, patch('run_experiment.run_mode') as legacy:
                        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                            main()
                        self.assertEqual(error.exception.code, 2)
                        full.assert_not_called()
                        screened.assert_not_called()
                        legacy.assert_not_called()
                self.assertFalse(output.exists())
                self.assertFalse(output.with_suffix('.json').exists())
            output.with_suffix('.json').write_bytes(b'preserve')
            with patch.object(sys, 'argv', base), patch('run_experiment.run_block_full') as full:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    main()
                full.assert_not_called()
            self.assertEqual(output.with_suffix('.json').read_bytes(), b'preserve')


if __name__ == '__main__':
    unittest.main()
