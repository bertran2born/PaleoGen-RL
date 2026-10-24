"""Analytical tests of the fixed block measurement; no genome simulation."""

from dataclasses import FrozenInstanceError
import json
import unittest

import numpy as np

from paleogen_rl.genetics.ancestry import BlockPanel, MEASUREMENT_VERSION, measure_ancestry


class TestAutosomalAncestry(unittest.TestCase):
    def measure(self, counts, panel, **overrides):
        arguments = dict(generation=7, target_generation=7, mode='full')
        arguments.update(overrides)
        return measure_ancestry(counts, panel, **arguments)

    def test_analytical_homozygous_and_heterozygous_panels(self):
        for population in (1, 3, 20):
            for blocks in (1, 8, 32):
                panel = BlockPanel(f'synthetic-{blocks}', tuple(f'b{i}' for i in range(blocks)))
                for copies in (0, 1, 2):
                    with self.subTest(N=population, B=blocks, copies=copies):
                        counts = np.full((population, blocks), copies, dtype=np.int8)
                        result = self.measure(counts, panel)
                        self.assertEqual(result['value'], copies / 2)
                        self.assertEqual(result['modern_allele_copies'], copies * population * blocks)
                        self.assertEqual(result['allele_copy_denominator'], 2 * population * blocks)
                        self.assertEqual(result['diploid_individuals'], population)
                        self.assertEqual(result['panel']['block_count'], blocks)
                        self.assertEqual(result['panel']['block_ids'], list(panel.block_ids))

    def test_mixed_panel_uses_all_blocks_and_preserves_inputs(self):
        panel = BlockPanel('synthetic-mixed', ('a', 'b', 'c'))
        counts = np.array([[2, 0, 1], [0, 1, 0]], dtype=np.int64)
        before = counts.copy()
        result = self.measure(counts, panel)
        self.assertEqual(result['modern_allele_copies'], 4)
        self.assertEqual(result['allele_copy_denominator'], 12)
        self.assertEqual(result['value'], 1 / 3)
        np.testing.assert_array_equal(counts, before)
        self.assertEqual(result['partner_diagnostics'], [])
        # Python nested lists and unsigned integer arrays have the same meaning.
        self.assertEqual(self.measure(counts.tolist(), panel), result)
        self.assertEqual(self.measure(counts.astype(np.uint8), panel), result)

    def test_partner_annotations_never_change_total_or_panel(self):
        panel = BlockPanel('synthetic-partners', ('a', 'b', 'c'))
        counts = np.array([[2, 0, 1], [2, 0, 0]])
        baseline = self.measure(counts, panel)
        for partners in ((), ('a',), ('b',), ('c', 'a'), panel.block_ids):
            with self.subTest(partners=partners):
                result = self.measure(counts, panel, partner_block_ids=partners)
                for field in ('value', 'modern_allele_copies', 'allele_copy_denominator',
                              'observable', 'panel', 'measurement_version'):
                    self.assertEqual(result[field], baseline[field], field)
                self.assertEqual(result['partner_block_ids'],
                                 [block for block in panel.block_ids if block in partners])
        diagnostic = self.measure(counts, panel, partner_block_ids=('b', 'a'))
        self.assertEqual(diagnostic['partner_diagnostics'], [
            dict(block_id='a', modern_allele_copies=4, allele_copy_denominator=4, value=1.),
            dict(block_id='b', modern_allele_copies=0, allele_copy_denominator=4, value=0.),
        ])
        self.assertEqual(diagnostic['value'], 5 / 12)
        self.assertEqual(diagnostic, self.measure(counts, panel, partner_block_ids=('a', 'b')))

    def test_panel_is_immutable_and_copies_declared_order(self):
        blocks = ['a', 'b']
        panel = BlockPanel('synthetic-immutable', blocks)
        blocks.append('c')
        self.assertEqual(panel.block_ids, ('a', 'b'))
        with self.assertRaises(FrozenInstanceError):
            panel.block_ids = ('c',)
        # Column order belongs to the declaration; no implicit sorting of counts.
        result = self.measure([[2, 0]], panel, partner_block_ids=('a',))
        self.assertEqual(result['partner_diagnostics'][0]['value'], 1.)
        reversed_panel = BlockPanel('synthetic-reversed', ('b', 'a'))
        result = self.measure([[2, 0]], reversed_panel, partner_block_ids=('a',))
        self.assertEqual(result['partner_diagnostics'][0]['value'], 0.)

    def test_quick_has_no_final_value_even_at_target(self):
        panel = BlockPanel('synthetic-quick', ('a',))
        for generation in (0, 3, 7):
            result = self.measure([[2]], panel, mode='quick', generation=generation,
                                  partner_block_ids=('a',))
            self.assertEqual(result['status'], 'not_evaluated_quick')
            self.assertIsNone(result['value'])
            self.assertIsNone(result['modern_allele_copies'])
            self.assertIsNone(result['partner_diagnostics'])
            self.assertEqual(result['generation'], generation)
            self.assertEqual(result['target_generation'], 7)
            self.assertEqual(result['allele_copy_denominator'], 2)

    def test_evaluated_modes_require_declared_final_generation(self):
        panel = BlockPanel('synthetic-horizon', ('a',))
        full = self.measure([[1]], panel)
        adaptive = self.measure([[1]], panel, mode='adaptive')
        self.assertEqual(full['status'], 'evaluated_at_target')
        self.assertEqual({**full, 'mode': 'adaptive'}, adaptive)
        for mode in ('full', 'adaptive'):
            for generation in (0, 6, 8):
                with self.subTest(mode=mode, generation=generation), self.assertRaises(ValueError):
                    self.measure([[1]], panel, mode=mode, generation=generation)
        with self.assertRaises(ValueError):
            self.measure([[1]], panel, mode='quick', generation=8)

    def test_invalid_panels_counts_and_partner_references_are_rejected(self):
        for panel_id, blocks in (
            ('', ('a',)), (' ', ('a',)), ('x', ()), ('x', ('a', 'a')),
            ('x', ('',)), ('x', (1,)), ('x', (' a',)), ('x', 'abc'),
        ):
            with self.subTest(panel_id=panel_id, blocks=blocks), self.assertRaises(ValueError):
                BlockPanel(panel_id, blocks)
        panel = BlockPanel('synthetic-validation', ('a', 'b'))
        for counts in (
            [], np.empty((0, 2), dtype=int), [[0]], [[0, 1, 2]], [0, 1],
            [[[0, 1]]], [[0, -1]], [[0, 3]], [[0., 1.]], [[True, False]],
            [[0., float('nan')]], [[0., float('inf')]], [['0', '1']],
            np.array([[0, None]], dtype=object),
            np.ma.array([[0, 1]], mask=[[False, True]]),
        ):
            with self.subTest(counts=repr(counts)), self.assertRaises(ValueError):
                self.measure(counts, panel)
        for partners in (('missing',), ('a', 'a'), (0,), 'a', (' a',)):
            with self.subTest(partners=partners), self.assertRaises(ValueError):
                self.measure([[0, 1]], panel, partner_block_ids=partners)
        with self.assertRaises(ValueError):
            self.measure([[0, 1]], None)

    def test_metadata_validation_and_json_round_trip(self):
        panel = BlockPanel('synthetic-json', ('a', 'b'))
        for mode in ('full', 'quick', 'adaptive'):
            result = self.measure([[0, 2], [1, 1]], panel, mode=mode, partner_block_ids=('b',))
            self.assertEqual(result['measurement_version'], MEASUREMENT_VERSION)
            self.assertEqual(result['observable'], 'total_diploid_block_ancestry')
            self.assertEqual(result['panel']['weighting'], 'equal_diploid_copies')
            self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        for field in ('generation', 'target_generation'):
            for value in (None, True, -1, 7., '7', np.int64(7)):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.measure([[0, 1]], panel, **{field: value})
        with self.assertRaises(ValueError):
            self.measure([[0, 1]], panel, mode='other')


if __name__ == '__main__':
    unittest.main()
