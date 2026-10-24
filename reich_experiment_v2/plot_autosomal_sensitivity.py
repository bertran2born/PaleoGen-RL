#!/usr/bin/env python3
"""Illustrate the finite-locus proxy artifact in the long-run neutral fixation LIMIT.
Not a forward simulation result: individual unlinked loci fix independently with P=f.
"""
from pathlib import Path
import csv
import matplotlib.pyplot as plt
root=Path(__file__).parent
with (root/'results/neutral_loci_asymptotic.csv').open() as f:rows=list(csv.DictReader(f))
x=[int(r['n_unlinked_loci']) for r in rows]
y=[100*float(r['P_fraction_between_3_7pct_longrun']) for r in rows]
fig,ax=plt.subplots(figsize=(9,4.5))
ax.plot(x,y,'o-',lw=2)
ax.set_xscale('log',base=2)
ax.set_xticks(x,[str(xx) for xx in x])
ax.set_ylim(-2,102)
ax.set_xlabel('Number of independent neutral ancestry loci (long-run limit)')
ax.set_ylabel('P(3% ≤ modern-ancestry fraction ≤ 7%), %')
ax.set_title('Finite-locus discretization artifact: neutral long-run approximation')
ax.grid(True,alpha=.2)
fig.text(.01,.005,'Analytical independent-locus fixation limit (Binomial(L,0.05)), NOT Reich\'s observed autosomal ancestry.',fontsize=9)
fig.tight_layout(rect=(0,.05,1,1))
fig.savefig(root/'figures/autosomal_loci_limit.png',dpi=170)
print(root/'figures/autosomal_loci_limit.png')
