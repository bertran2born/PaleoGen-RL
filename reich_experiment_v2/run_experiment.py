#!/usr/bin/env python3
"""Single-pulse Neandertal ancestry test, built on Reich's SI3 simulator.

Run `python run_experiment.py --scenario all --reps 100 --mode adaptive`.
Run `python run_experiment.py --scenario all --reps 1000 --mode quick` for
fast marker-only screening (NOT valid for final autosomal acceptance).
"""
import argparse
import csv
import json
from dataclasses import asdict, replace
from pathlib import Path
import sys
import time
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent/'src'))
from epi_pulse import Config, run

SCENARIOS = {
 'neutral': dict(),
 'reich_point': dict(s_mt=0.0032, s=0.0013, sel_locus='Y'),
 'symmetric_1pct': dict(mt_mod_nuc_arch=0.01,mt_arch_nuc_mod=0.01,
                        y_mod_nuc_arch=0.01,y_arch_nuc_mod=0.01),
 'symmetric_5pct': dict(mt_mod_nuc_arch=0.05,mt_arch_nuc_mod=0.05,
                        y_mod_nuc_arch=0.05,y_arch_nuc_mod=0.05),
 'direction_mod_1pct': dict(mt_mod_nuc_arch=0.0,mt_arch_nuc_mod=0.01,
                           y_mod_nuc_arch=0.0,y_arch_nuc_mod=0.01),
 'direction_arch_1pct': dict(mt_mod_nuc_arch=0.01,mt_arch_nuc_mod=0.0,
                            y_mod_nuc_arch=0.01,y_arch_nuc_mod=0.0),
 'direction_mod_5pct': dict(mt_mod_nuc_arch=0.0,mt_arch_nuc_mod=0.05,
                           y_mod_nuc_arch=0.0,y_arch_nuc_mod=0.05),
 'direction_arch_5pct': dict(mt_mod_nuc_arch=0.05,mt_arch_nuc_mod=0.0,
                            y_mod_nuc_arch=0.05,y_arch_nuc_mod=0.0),
 'reich_plus_symmetric_1pct': dict(s_mt=0.0032,s=0.0013,sel_locus='Y',
                    mt_mod_nuc_arch=0.01,mt_arch_nuc_mod=0.01,
                    y_mod_nuc_arch=0.01,y_arch_nuc_mod=0.01),
 'reich_plus_symmetric_0p1pct': dict(s_mt=0.0032,s=0.0013,sel_locus='Y',
                    mt_mod_nuc_arch=0.001,mt_arch_nuc_mod=0.001,
                    y_mod_nuc_arch=0.001,y_arch_nuc_mod=0.001),
 'reich_plus_symmetric_0p3pct': dict(s_mt=0.0032,s=0.0013,sel_locus='Y',
                    mt_mod_nuc_arch=0.003,mt_arch_nuc_mod=0.003,
                    y_mod_nuc_arch=0.003,y_arch_nuc_mod=0.003),
 'reich_plus_favor_mod_0p1pct': dict(s_mt=0.0032,s=0.0013,sel_locus='Y',
                    mt_arch_nuc_mod=0.001,y_arch_nuc_mod=0.001),
 'reich_plus_favor_mod_0p3pct': dict(s_mt=0.0032,s=0.0013,sel_locus='Y',
                    mt_arch_nuc_mod=0.003,y_arch_nuc_mod=0.003),
 'reich_plus_favor_mod_1pct': dict(s_mt=0.0032,s=0.0013,sel_locus='Y',
                    mt_arch_nuc_mod=0.01,y_arch_nuc_mod=0.01),
 'reich_plus_favor_arch_0p1pct': dict(s_mt=0.0032,s=0.0013,sel_locus='Y',
                    mt_mod_nuc_arch=0.001,y_mod_nuc_arch=0.001),
 'reich_plus_favor_arch_0p3pct': dict(s_mt=0.0032,s=0.0013,sel_locus='Y',
                    mt_mod_nuc_arch=0.003,y_mod_nuc_arch=0.003),
 'reich_plus_favor_arch_1pct': dict(s_mt=0.0032,s=0.0013,sel_locus='Y',
                    mt_mod_nuc_arch=0.01,y_mod_nuc_arch=0.01),
}

def ci_bootstrap(values, seed=9918, B=400):
    values=np.asarray(values,dtype=float)
    if len(values) <= 1:return [float('nan'),float('nan')]
    rng=np.random.default_rng(seed)
    ix=rng.integers(0,len(values),size=(B,len(values)))
    m=values[ix].mean(axis=1)
    return [float(x) for x in np.quantile(m,[0.025,0.975])]

def wilson_interval(successes, n, z=1.959963984540054):
    """95% Wilson interval for 0/1 outcomes, with finite upper bound at zero."""
    if n <= 0:return [float('nan'),float('nan')]
    p=successes/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den
    delta=z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return [float(max(0,mid-delta)),float(min(1,mid+delta))]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scenario',choices=['all',*SCENARIOS],default='all')
    ap.add_argument('--reps',type=int,default=30)
    ap.add_argument('--mode',choices=['full','quick','adaptive'],default='adaptive')
    ap.add_argument('--N',type=int,default=1450)
    ap.add_argument('--gens',type=int,default=6993)
    ap.add_argument('--f',type=float,default=0.05)
    ap.add_argument('--male-frac',type=float,default=0.5)
    ap.add_argument('--seed',type=int,default=62026)
    ap.add_argument('--output',default=None)
    ap.add_argument('--mt-posterior',default=None,
                    help='Optional Reich SI1 posterior txt file: draw s_mt independently per replicate')
    # Optional compositional overrides; the scenario keeps its original Reich
    # Y selection and the SI1 mtDNA posterior unless explicitly replaced.
    for field in ('mt_mod_nuc_arch','mt_arch_nuc_mod','y_mod_nuc_arch','y_arch_nuc_mod'):
        ap.add_argument('--'+field.replace('_','-'),type=float,default=None,
                        help='Override this epistatic penalty in [0,1]')
    args=ap.parse_args()
    if args.reps<1 or args.N<20 or args.gens<1:ap.error('reps >= 1, N >= 20, gens >= 1')
    if not 0 <= args.f <= 1 or not 0<=args.male_frac<=1:ap.error('f and male-frac must be in [0,1]')
    overrides={name:getattr(args,name) for name in (
        'mt_mod_nuc_arch','mt_arch_nuc_mod','y_mod_nuc_arch','y_arch_nuc_mod')
        if getattr(args,name) is not None}
    if any(not 0 <= value <= 1 for value in overrides.values()):
        ap.error('epistatic penalties must lie in [0,1]')
    if overrides and args.output is None:
        ap.error('when overriding epistasis, specify --output to avoid overwriting runs')
    names=list(SCENARIOS) if args.scenario=='all' else [args.scenario]
    output=Path(args.output or (Path(__file__).parent/'results'/f'{args.mode}_{args.reps}.csv'))
    output.parent.mkdir(parents=True,exist_ok=True)
    summary=[]
    all_rows=[]
    posterior=None
    if args.mt_posterior:
        a=np.loadtxt(args.mt_posterior,comments='#')
        posterior=a[:,0] if a.ndim==2 else a
        print(f'Loaded {len(posterior)} SI1 mtDNA fitness gap posterior values',flush=True)
    base=Config(N=args.N,f=args.f,male_frac=args.male_frac,gens=args.gens,
                stop_when_absorbed=args.mode!='full')
    for j,name in enumerate(names):
        cfg=replace(base,**{**SCENARIOS[name],**overrides})
        rows=[]
        start=time.monotonic()
        for i in range(args.reps):
            # Paired-replicate seeds: all scenarios share the same replicate index.
            c=replace(cfg,seed=args.seed+i)
            if posterior is not None and c.s_mt != 0:
                draw_rng=np.random.default_rng(args.seed+i+27383)
                c=replace(c,s_mt=float(draw_rng.choice(posterior)))
            res=run(c)
            if args.mode=='adaptive' and res['p10_joint']>0:
                full=run(replace(c,stop_when_absorbed=False), accelerate_after_absorption=True)
                if abs(full['p10_joint']-res['p10_joint'])>1e-12:
                    raise RuntimeError('Early absorption check failed: marker results changed')
                res['auto_mod_at_50ka']=full['auto_mod']
                res['target_auto']=full['target_auto']
            elif args.mode=='adaptive':
                # Proof by absorption/terminal time: if p10 is already zero, the
                # ten-male event is impossible at the sampling generation.
                res['auto_mod_at_50ka']='NOT_EVALUATED_EVENT_IMPOSSIBLE'
                res['target_auto']=''
            row={'scenario':name,'rep':i,'seed':c.seed,'mode':args.mode,
                 'initial_f':args.f,'N':args.N,'gens_requested':args.gens,'s_mt_realized':c.s_mt,
                 **res}
            if args.mode=='quick':
                row['target_auto']=''  # Early stopping INVALIDATES ancestry at 50 ka
                row['joint_and_target']=''
            else:
                row['joint_and_target']=float(res['p10_joint']) * int(bool(res['target_auto']))
            rows.append(row)
        keys=['p10_joint','mt_mod','Y_mod','joint_fixed']
        if args.mode=='full':keys.append('auto_mod')
        else:keys.append('auto_mod_at_early_stop')
        if args.mode!='full':
            for row in rows:row['auto_mod_at_early_stop']=row['auto_mod']
        metrics={k:float(np.mean([r[k] for r in rows])) for k in keys}
        if args.mode in ('full','adaptive'):
            if args.mode=='full':
                metrics['P_autosomal_range']=float(np.mean([r['target_auto'] for r in rows]))
            metrics['P_joint_and_auto']=float(np.mean([r['joint_and_target'] for r in rows]))
            metrics['joint_and_auto_95pct_bootstrap']=ci_bootstrap([r['joint_and_target'] for r in rows])
        metrics['p10_joint_95pct_bootstrap']=ci_bootstrap([r['p10_joint'] for r in rows])
        if all(r['p10_joint'] in (0.,1.) for r in rows):
            metrics['P10_Wilson95']=wilson_interval(sum(r['p10_joint'] for r in rows),len(rows))
        if args.mode in ('full','adaptive') and all(r['joint_and_target'] in (0.,1.) for r in rows):
            metrics['P_joint_auto_Wilson95']=wilson_interval(sum(r['joint_and_target'] for r in rows),len(rows))
        metrics['time_seconds']=round(time.monotonic()-start,2)
        summary.append(dict(name=name,reps=args.reps,**metrics))
        all_rows.extend(rows)
        print(f'{name:<29s}  P(sample 10 both)={metrics["p10_joint"]:.4%}  '
              f'P(mt,Y fixation)={metrics["joint_fixed"]:.4%}  '
              f't={metrics["time_seconds"]:.1f}s',flush=True)
    with output.open('w',newline='') as fobj:
        wr=csv.DictWriter(fobj,fieldnames=list(all_rows[0]));wr.writeheader();wr.writerows(all_rows)
    jsonpath=output.with_suffix('.json')
    with jsonpath.open('w') as fobj:
        json.dump(dict(meta=dict(vars(args),scenarios={k:{**SCENARIOS[k],**overrides} for k in names},
            definition='P(ten sampled males each modern mt AND modern Y at 50 ka)'),
            summary=summary),fobj,indent=2)
    print('Wrote:',output,'and',jsonpath,flush=True)

if __name__=='__main__':main()
