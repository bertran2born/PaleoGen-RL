#!/usr/bin/env python3
"""Exact two-stage Monte Carlo continuation for a previous quick screen.

Because mt/Y have neither reintroduction nor back mutation, once a marker is
absorbed it cannot be re-created. For a quick run with P10=0 the joint event is
provably impossible at 50 ka (provided the pulse2 mechanism is disabled).
Only positive-P10 replicates require re-running the FULL model to check the
independent autosomal ancestry criterion at the correct 50 ka sampling date.
"""
import argparse
import csv
import json
import sys
from pathlib import Path
from dataclasses import replace
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from run_experiment import SCENARIOS,ci_bootstrap,wilson_interval
from src.epi_pulse import Config,run

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('quick_csv')
    ap.add_argument('--out',default=None)
    args=ap.parse_args()
    path=Path(args.quick_csv)
    with path.open(newline='') as f:rows=list(csv.DictReader(f))
    if not rows or not all(r['mode']=='quick' for r in rows):
        ap.error('Pass a nonempty quick-mode result CSV.')
    if any(r.get('pulse2_gen','0') not in ('0','',None) for r in rows):
        ap.error('A second pulse is forbidden in this shortcut.')
    checked=0
    for row in rows:
        score=float(row['p10_joint'])
        if score>0:
            c=Config(N=int(row['N']),gens=int(row['gens_requested']),seed=int(row['seed']),
                     f=float(row['initial_f']),stop_when_absorbed=False,
                     **SCENARIOS[row['scenario']])
            # The original code uses f=0.05 and male_frac=0.5 for all saved screens.
            c=replace(c,s_mt=float(row['s_mt_realized']),male_frac=0.5)
            full=run(c, accelerate_after_absorption=True)
            # This checks our mathematical early-stop claim automatically.
            if abs(full['p10_joint']-score)>1e-12:
                raise RuntimeError(f'Incorrect early-stop semantics at {row["scenario"]} seed {c.seed}: '
                                   f'early={score}, full={full["p10_joint"]}')
            row['auto_mod_at_50ka']=full['auto_mod']
            row['target_auto']=int(full['target_auto'])
            row['joint_and_target']=score*int(full['target_auto'])
            row['full_model_generations']=full['generations_completed']
            checked+=1
        else:
            row['auto_mod_at_50ka']='NOT_EVALUATED_EVENT_IMPOSSIBLE'
            row['target_auto']=''
            row['joint_and_target']=0.
            row['full_model_generations']=''
        row['mode']='adaptive'
    output=Path(args.out or path.with_name(path.stem.replace('quick','adaptive')+'_scored.csv'))
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    results=[]
    for name in sorted(set(r['scenario'] for r in rows)):
        subset=[r for r in rows if r['scenario']==name]
        js=np.array([float(r['p10_joint']) for r in subset])
        jc=np.array([float(r['joint_and_target']) for r in subset])
        results.append(dict(name=name,n=len(subset),n_continued=sum(bool(r['full_model_generations']) for r in subset),
                            P_ten_males=float(js.mean()),P_joint_and_auto=float(jc.mean()),
                            CI95_MC_P_joint_auto=ci_bootstrap(jc),
                            CI95_MC_P_ten_males=ci_bootstrap(js),
                            Wilson95_joint_auto=wilson_interval(float(jc.sum()),len(jc)),
                            Wilson95_ten_males=wilson_interval(float(js.sum()),len(js))))
    summary=output.with_suffix('.json');summary.write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2));print('Wrote',output,summary)

if __name__=='__main__':main()
