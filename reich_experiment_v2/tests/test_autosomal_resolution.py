"""Resolution diagnostics: analytical summaries and replay against I13."""

from contextlib import redirect_stderr
import io
import json
from math import exp, log, sqrt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.neutral import run_neutral
from paleogen_rl.genetics.resolution import (
    RESOLUTIONS, SEEDS, STUDY_VERSION, _bounded_mean, _target_summary,
    main, run_resolution_study,
)


class TestAutosomalResolution(unittest.TestCase):
    def study(self, **kwargs):
        return run_resolution_study(**{**dict(resolutions=(2, 4, 9), seeds=(17, 73, 81),
                                              generations=3), **kwargs})

    def test_target_is_inclusive_and_wilson_handles_zero_and_all_hits(self):
        summary = _target_summary([.029, .03, .05, .07, .071])
        self.assertEqual(summary['count'], 3)
        self.assertEqual(summary['replicates'], 5)
        self.assertEqual(summary['probability'], .6)
        # Independent closed-form checks at the two binomial extremes.
        z2 = 1.959963984540054**2
        zero, all_hits = _target_summary([0.]*10), _target_summary([.05]*10)
        self.assertAlmostEqual(zero['interval'][0], 0.)
        self.assertAlmostEqual(zero['interval'][1], z2/(10+z2))
        self.assertAlmostEqual(all_hits['interval'][0], 10/(10+z2))
        self.assertAlmostEqual(all_hits['interval'][1], 1.)
        bound = _bounded_mean([-.2, .4]*100, -1., 1.)
        self.assertAlmostEqual(bound['mean'], .1)
        self.assertAlmostEqual(bound['interval'][0], .1-sqrt(2*log(40)/200))
        self.assertEqual(_bounded_mean([0.], 0., 1.)['interval'], [0., 1.])

    def test_maps_keep_endpoint_recombination_and_initial_state(self):
        for length in (0., .25, 1.):
            report = self.study(map_length=length)
            self.assertEqual(report['protocol']['map_length'], length)
            for row in report['resolutions']:
                probabilities = row['recombination_map']['switch_probabilities']
                self.assertEqual(len(probabilities), row['block_count']-1)
                odd_switch = (1-float(np.prod(1-2*np.array(probabilities))))/2
                self.assertAlmostEqual(odd_switch, (1-exp(-2*length))/2)
            self.assertEqual(len({r['initial_sex_sha256'] for r in report['resolutions']}), 1)

    def test_every_replicate_replays_directly_and_summaries_match(self):
        report = self.study()
        sex = np.array([1]*20+[0]*20, dtype=np.uint8)
        for row in report['resolutions']:
            blocks = row['block_count']
            initial = np.zeros((40, 2, blocks), dtype=np.uint8)
            initial[[0, 20], :, :] = 1
            declaration = row['recombination_map']
            mapping = RecombinationMap(BlockPanel(**declaration['panel']),
                                       declaration['switch_probabilities'])
            self.assertEqual([r['seed'] for r in row['replicates']], [17, 73, 81])
            for replicate in row['replicates']:
                direct = run_neutral(initial, sex, recombination_map=mapping,
                                     generations=3, seed=replicate['seed']).report
                final = direct['final_measurement']
                for field in ('generation', 'status', 'value', 'modern_allele_copies'):
                    self.assertEqual(replicate[field], final[field])
                self.assertEqual(replicate['generation'], 3)
                self.assertEqual(replicate['status'], 'evaluated_at_target')
                self.assertEqual(replicate['value'], replicate['modern_allele_copies']/(80*blocks))
                self.assertEqual(row['initial_haplotypes_sha256'], direct['initial_haplotypes_sha256'])
            values = [r['value'] for r in row['replicates']]
            self.assertAlmostEqual(row['ancestry']['mean'], sum(values)/3)
            self.assertEqual(row['target']['count'], sum(.03 <= v <= .07 for v in values))
            self.assertEqual(row['work_units'], dict(offspring_generated=360,
                                                    block_copy_transmissions=720*blocks,
                                                    state_allele_entries=80*blocks))
        self.assertEqual(report['total_work_units'], dict(
            offspring_generated=1080, block_copy_transmissions=720*15,
            largest_population_state_allele_entries=720))
        for row, delta in zip(report['resolutions'], report['differences_from_finest']):
            fine = report['resolutions'][-1]
            self.assertEqual(delta['reference_block_count'], 9)
            self.assertAlmostEqual(delta['ancestry']['mean'], row['ancestry']['mean']-fine['ancestry']['mean'])
            self.assertAlmostEqual(delta['target_probability']['mean'],
                                   row['target']['probability']-fine['target']['probability'])

    def test_zero_horizon_analytical_target_and_costs(self):
        report = self.study(generations=0)
        for row in report['resolutions']:
            self.assertAlmostEqual(row['ancestry']['mean'], .05)
            self.assertEqual(row['target']['probability'], 1.)
        for delta in report['differences_from_finest']:
            self.assertEqual(delta['ancestry']['mean'], 0.)
            self.assertEqual(delta['target_probability']['mean'], 0.)
        self.assertEqual(report['total_work_units']['offspring_generated'], 0)
        self.assertEqual(report['total_work_units']['block_copy_transmissions'], 0)

    def test_repeatability_json_and_fixed_protocol(self):
        before = np.random.get_state()
        first = self.study()
        self.assertEqual(first, self.study())
        self.assertEqual(json.loads(json.dumps(first, allow_nan=False)), first)
        self.assertEqual(first['study_version'], STUDY_VERSION)
        self.assertEqual(first['mode'], 'full')
        self.assertEqual(first['convergence_status'], 'not_assessed')
        self.assertEqual(RESOLUTIONS, (8, 32, 128))
        self.assertEqual(SEEDS, tuple(range(410000, 410128)))
        for old, new in zip(before, np.random.get_state()):
            np.testing.assert_equal(old, new)

    def test_invalid_declarations_fail_before_simulation(self):
        invalid = [dict(resolutions=(2, 4)), dict(resolutions=(2, 2, 4)),
                   dict(resolutions=(4, 2, 8)), dict(resolutions=(1, 2, 3)),
                   dict(resolutions=(2, 3, 4.)), dict(resolutions=None),
                   dict(seeds=[]), dict(seeds=(1, 1)), dict(seeds=(True,)),
                   dict(seeds=(-1,)), dict(seeds=None), dict(generations=-1),
                   dict(generations=True), dict(generations=2.),
                   dict(map_length=float('nan')), dict(map_length=float('inf')),
                   dict(map_length=-.1), dict(map_length=True), dict(map_length='1')]
        with patch('paleogen_rl.genetics.resolution.run_neutral') as simulate:
            for overrides in invalid:
                with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                    self.study(**overrides)
            simulate.assert_not_called()

    def test_cli_creates_strict_json_and_refuses_existing_or_dangling_paths(self):
        report = self.study()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)/'report.json'
            with patch('paleogen_rl.genetics.resolution.run_resolution_study', return_value=report):
                self.assertEqual(main(['--output', str(output)]), 0)
            original = output.read_bytes()
            self.assertEqual(json.loads(original), report)
            dangling = Path(temporary)/'dangling'
            dangling.symlink_to(Path(temporary)/'missing')
            for destination in (output, dangling):
                with patch('paleogen_rl.genetics.resolution.run_resolution_study') as simulate:
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                        main(['--output', str(destination)])
                    self.assertEqual(error.exception.code, 2)
                    simulate.assert_not_called()
            self.assertEqual(output.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
