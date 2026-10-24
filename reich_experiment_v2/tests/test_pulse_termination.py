"""Do not confuse failed reproduction with absorption or the final horizon."""

from dataclasses import replace
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from run_experiment import Config, main, run, run_mode
import reich_panmictic_original as original


ROOT = Path(__file__).resolve().parents[1]


class TestPulseTermination(unittest.TestCase):
    def test_normal_horizon_and_absorption_reasons(self):
        for frequency in (0., 1.):
            cfg = Config(N=80, gens=80, f=frequency, seed=17)
            full = run(replace(cfg, stop_when_absorbed=False))
            short = run(replace(cfg, stop_when_absorbed=True))
            self.assertEqual(full['termination_reason'], 'horizon_reached')
            self.assertEqual(full['generations_completed'], 80)
            self.assertEqual(short['termination_reason'], 'markers_absorbed')
            self.assertEqual(short['generations_completed'], 11)
            for mode in ('full', 'quick', 'adaptive'):
                self.assertEqual(run_mode(cfg, mode)['p10_joint'], frequency)

    def test_real_complete_incompatibility_fails_before_first_generation(self):
        cfg = Config(N=20, gens=3, seed=17, mt_mod_nuc_arch=1.)
        initialize = original._init
        def parents(config, rng):
            population = initialize(replace(config, f=1.), rng)
            population['auto'][:] = 0
            return population
        hook = original._dm_penetrance
        with patch.object(original, '_init', parents):
            result = run(cfg)
        self.assertEqual(result['termination_reason'], 'reproduction_failed')
        self.assertEqual(result['generations_completed'], 0)
        self.assertEqual(result['p10_joint'], 1.)
        self.assertEqual(result['auto_mod'], 0.)
        self.assertIs(original._dm_penetrance, hook)

    def test_failed_attempt_does_not_advance_population_or_counter(self):
        cfg = Config(N=80, gens=8, f=.5, seed=42, stop_when_absorbed=False)
        step = original._step
        def stop_after_three(population, config, rng, generation):
            return None if generation == 3 else step(population, config, rng, generation)
        with patch.object(original, '_step', stop_after_three):
            interrupted = run(cfg)
        expected = run(replace(cfg, gens=3))
        self.assertEqual(interrupted.pop('termination_reason'), 'reproduction_failed')
        self.assertEqual(expected.pop('termination_reason'), 'horizon_reached')
        self.assertEqual(interrupted['generations_completed'], 3)
        self.assertEqual(interrupted, expected)

    def test_all_modes_reject_failure_even_when_event_is_impossible(self):
        for mode in ('full', 'quick', 'adaptive'):
            for probability in (0., 1.):
                with self.subTest(mode=mode, p10=probability):
                    raw = dict(termination_reason='reproduction_failed',
                               generations_completed=3, p10_joint=probability)
                    with patch('run_experiment.run', return_value=raw):
                        with self.assertRaisesRegex(RuntimeError, 'reproduction_failed.*completed=3'):
                            run_mode(Config(gens=80, seed=17), mode)
                    self.assertNotIn('auto_evaluation_status', raw)

    def test_adaptive_rejects_real_failed_continuation_and_incomplete_horizon(self):
        cfg = Config(N=80, gens=80, f=1., seed=17)
        step = original._step
        def stop_at_twelve(population, config, rng, generation):
            return None if generation == 12 else step(population, config, rng, generation)
        def runner(config, **kwargs):
            self.assertEqual(config.seed, cfg.seed)
            if config.stop_when_absorbed:
                return run(config, **kwargs)
            self.assertEqual(kwargs, {'accelerate_after_absorption': True})
            with patch.object(original, '_step', stop_at_twelve):
                return run(config, **kwargs)
        with patch('run_experiment.run', side_effect=runner) as engine:
            with self.assertRaisesRegex(RuntimeError, 'reproduction_failed.*completed=12'):
                run_mode(cfg, 'adaptive')
            self.assertEqual(engine.call_count, 2)
        short = run(replace(cfg, stop_when_absorbed=True))
        for reason in ('markers_absorbed', 'horizon_reached'):
            incomplete = {**short, 'termination_reason': reason}
            with self.subTest(reason=reason):
                with patch('run_experiment.run', side_effect=[short.copy(), incomplete]):
                    with self.assertRaisesRegex(RuntimeError, 'incomplete_horizon'):
                        run_mode(cfg, 'adaptive')
                with patch('run_experiment.run', return_value=incomplete):
                    with self.assertRaisesRegex(RuntimeError, 'incomplete_horizon'):
                        run_mode(cfg, 'full')

    def test_cli_real_incompatibility_has_no_success_export(self):
        initialize = original._init
        def parents(config, rng):
            population = initialize(replace(config, f=1.), rng)
            population['auto'][:] = 0
            return population
        with tempfile.TemporaryDirectory() as directory:
            for mode in ('full', 'quick', 'adaptive'):
                output = Path(directory) / f'{mode}.csv'
                argv = ['run_experiment.py', '--scenario', 'neutral', '--mode', mode,
                        '--N', '20', '--gens', '3', '--reps', '1', '--seed', '17',
                        '--mt-mod-nuc-arch', '1', '--output', str(output)]
                with patch.object(sys, 'argv', argv), patch.object(original, '_init', parents), \
                        patch('sys.stderr', new_callable=io.StringIO) as errors:
                    with self.assertRaises(SystemExit) as stopped:
                        main()
                self.assertEqual(stopped.exception.code, 1)
                self.assertIn('neutral rep=0: reproduction_failed', errors.getvalue())
                self.assertIn('generations_completed=0', errors.getvalue())
                self.assertFalse(output.exists())
                self.assertFalse(output.with_suffix('.json').exists())

    def test_subprocess_reproductive_failure_without_boundary_patches(self):
        with tempfile.TemporaryDirectory() as directory:
            # Synthetic lethal mt selection; this is not the supplied SI1 posterior.
            posterior = Path(directory) / 'synthetic-lethal.txt'
            posterior.write_text('1.0\n1.0\n')
            for mode in ('full', 'quick', 'adaptive'):
                output = Path(directory) / f'{mode}.csv'
                result = subprocess.run([
                    sys.executable, str(ROOT / 'run_experiment.py'), '--scenario', 'reich_point',
                    '--mode', mode, '--N', '20', '--gens', '3', '--reps', '1', '--seed', '17',
                    '--f', '0', '--mt-posterior', str(posterior), '--output', str(output),
                ], cwd=directory, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
                self.assertIn('reproduction_failed', result.stderr)
                self.assertIn('generations_completed=0', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertFalse(output.exists())
                self.assertFalse(output.with_suffix('.json').exists())


if __name__ == '__main__':
    unittest.main()
