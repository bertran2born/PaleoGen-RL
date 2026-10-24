#!/usr/bin/env python3
"""Plot screening-only P(10 males with both modern markers) with bootstrap CIs.

Results in quick mode are NOT evidence that the autosomal target was met.
"""
import json
from run_experiment import wilson_interval
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
ROOT=Path(__file__).parent
paths=sorted((ROOT/'results').glob('quick_*.json'))
records=[]
for path in paths:
    record=json.loads(path.read_text())
    for row in record['summary']:
        ci=row.get('P10_Wilson95')
        if ci is None:
            ci=wilson_interval(int(round(row['p10_joint']*row['reps'])),row['reps'])
        records.append((row['name'],row['reps'],row['p10_joint'],*ci))
if records:
    # prefer largest sample per same scenario
    best={}
    for record in records:
        name=record[0]
        if name not in best or record[1]>best[name][1]:best[name]=record
    data=list(best.values())
    labels=[r[0].replace('_','\n') for r in data]
    ps=np.array([r[2] for r in data]);lo=np.array([r[3] for r in data]);hi=np.array([r[4] for r in data])
    x=np.arange(len(data))
    fig,ax=plt.subplots(figsize=(max(9,len(data)*1.35),5))
    ax.bar(x,100*ps,alpha=.75)
    ax.errorbar(x,100*ps,yerr=[100*(ps-lo),100*(hi-ps)],fmt='none',ecolor='black',capsize=4)
    ax.axhline(0.25,ls='--',lw=1.4,label='Neutral theoretical double fixation ≈ 0.25%')
    ax.set_xticks(x,labels)
    ax.set_ylabel('P(all 10 males carry modern mtDNA AND modern Y), %')
    ax.set_title('Reich SI3 pulse simulator + reciprocal epistasis: exploratory SCREEN only')
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=9)
    for i,r in enumerate(data):ax.annotate(f'n={r[1]}',xy=(i,0),xytext=(0,5),textcoords='offset points',ha='center',fontsize=8)
    fig.text(.01,.005,'Wilson 95% CIs = Monte Carlo uncertainty only. Quick mode DOES NOT evaluate autosomal ancestry at 50 ka.',fontsize=9)
    fig.tight_layout(rect=(0,.045,1,1))
    output=ROOT/'figures'/'quick_screen.png';output.parent.mkdir(exist_ok=True);fig.savefig(output,dpi=170)
    print(output)
else:print('No quick summary files found')
