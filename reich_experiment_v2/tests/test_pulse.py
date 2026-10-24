import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import reich_panmictic_original as reich
from epi_pulse import Config, run, _epistasis_loss

class TestExperiment(unittest.TestCase):
    def test_neutral_matches_original_including_rng(self):
        for seed in (0,17,42,171):
            a=reich.Config(seed=seed,N=200,gens=90,stop_when_absorbed=False)
            b=Config(seed=seed,N=200,gens=90,stop_when_absorbed=False)
            ref=reich.run(a)
            got=run(b)
            for key in ref:self.assertEqual(ref[key],got[key],key)

    def test_all_modern_male_sample(self):
        b=run(Config(N=200,f=1.,gens=1,seed=1,stop_when_absorbed=False))
        self.assertEqual(b['p10_joint'],1.0)
        self.assertTrue(b['joint_fixed'])

    def test_all_archaic_male_sample(self):
        b=run(Config(N=200,f=0.,gens=1,seed=1,stop_when_absorbed=False))
        self.assertEqual(b['p10_joint'],0.)
        self.assertFalse(b['joint_fixed'])

    def test_selected_reference_matches_original(self):
        a=reich.Config(N=200,gens=65,seed=901,stop_when_absorbed=False,
                       sel_locus='Y',s=0.0013,s_mt=0.0032)
        b=Config(N=200,gens=65,seed=901,stop_when_absorbed=False,
                 sel_locus='Y',s=0.0013,s_mt=0.0032)
        for k,v in reich.run(a).items():self.assertEqual(v,run(b)[k])

    def test_female_bias_changes_marker_initial_frequency(self):
        p=reich._init(Config(N=400,f=.05,male_frac=0.0),np.random.default_rng(9))
        males=p['sex']==1
        self.assertEqual((p['Y'][males]==1).sum(),0)
        self.assertAlmostEqual(float(p['mt'][~males].mean()),.1)
        self.assertAlmostEqual(float(p['mt'].mean()),.05)

    def test_reciprocal_mt_penalty(self):
        sx=np.array([0,0,0,0],dtype=int)
        mt=np.array([1,0,1,0],dtype=int)
        y=np.full(4,-1,dtype=int)
        a=np.array([[0,2],[2,0],[2,1],[0,1]],dtype=int)
        cfg=Config(mt_mod_nuc_arch=.3,mt_arch_nuc_mod=.4)
        got=_epistasis_loss(cfg,sx,mt,y,a)
        np.testing.assert_allclose(got,[.3,.4,0.,0.])

    def test_y_penalty_male_only(self):
        sx=np.array([1,1,0],dtype=int)
        mt=np.array([0,0,0],dtype=int)
        y=np.array([1,0,-1],dtype=int)
        a=np.array([[2,0],[0,2],[0,2]],dtype=int)
        cfg=Config(y_mod_nuc_arch=.5,y_arch_nuc_mod=.4)
        got=_epistasis_loss(cfg,sx,mt,y,a)
        np.testing.assert_allclose(got,[.5,.4,0.])

    def test_zero_penalty_molecular_baseline(self):
        a=reich.Config(N=200,gens=20,seed=7,stop_when_absorbed=False)
        b=Config(N=200,gens=20,seed=7,stop_when_absorbed=False)
        pa=reich._init(a,np.random.default_rng(1))
        pb=reich._init(b,np.random.default_rng(1))
        for k in pa:np.testing.assert_array_equal(pa[k],pb[k])
        self.assertEqual(reich.run(a)['auto_mod'],run(b)['auto_mod'])

    def test_absorption_continuation_preserves_marker_event(self):
        for seed in (10,20,30):
            short=Config(N=200,gens=300,seed=seed,stop_when_absorbed=True,
                         sel_locus='Y',s=0.0013,s_mt=0.0032)
            long=Config(N=200,gens=300,seed=seed,stop_when_absorbed=False,
                        sel_locus='Y',s=0.0013,s_mt=0.0032)
            self.assertEqual(run(short)['p10_joint'],
                             run(long,accelerate_after_absorption=True)['p10_joint'])

    def test_loss_validation(self):
        with self.assertRaises(ValueError):
            _epistasis_loss(Config(y_arch_nuc_mod=1.5),
              np.ones(1,dtype=int),np.ones(1,dtype=int),np.ones(1,dtype=int),np.zeros((1,8),dtype=int))

if __name__=='__main__':unittest.main()
