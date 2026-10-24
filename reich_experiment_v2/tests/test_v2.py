import unittest
from compare_runs import fisher_exact_two_sided, wilson
from run_experiment import SCENARIOS

class TestV2(unittest.TestCase):
    def test_exact_fisher(self):
        self.assertAlmostEqual(fisher_exact_two_sided(13,500,0,500),0.00022559806976925475,places=9)
    def test_wilson_zero(self):
        self.assertAlmostEqual(wilson(0,500)[1],0.007624340461552241)
    def test_directional_keep_reich_base(self):
        for key in ('reich_plus_favor_mod_0p1pct','reich_plus_favor_mod_0p3pct',
                    'reich_plus_favor_mod_1pct','reich_plus_favor_arch_0p1pct',
                    'reich_plus_favor_arch_0p3pct','reich_plus_favor_arch_1pct'):
            c=SCENARIOS[key]
            self.assertEqual(c['sel_locus'],'Y')
            self.assertEqual(c['s'],0.0013)
            self.assertEqual(c['s_mt'],0.0032)
    def test_new_coefficient_directions(self):
        self.assertEqual(SCENARIOS['reich_plus_favor_mod_1pct']['mt_arch_nuc_mod'],.01)
        self.assertNotIn('mt_mod_nuc_arch',SCENARIOS['reich_plus_favor_mod_1pct'])
        self.assertEqual(SCENARIOS['reich_plus_favor_arch_1pct']['y_mod_nuc_arch'],.01)
        self.assertNotIn('y_arch_nuc_mod',SCENARIOS['reich_plus_favor_arch_1pct'])

if __name__=='__main__': unittest.main()
