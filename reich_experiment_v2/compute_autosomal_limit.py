#!/usr/bin/env python3
"""Compute discrete-locus neutral long-run approximation from first principles.

If each locus starts at 5% modern and independently fixes modern with probability
0.05 (an idealized independent neutral-locus limit), the number of modern-fixed
loci in the long run follows Binomial(L, 0.05). Not a genome simulator.
"""
from pathlib import Path
from math import comb,ceil,floor
import csv
out=Path(__file__).parent/'results/neutral_loci_asymptotic.csv'
out.parent.mkdir(exist_ok=True)
with out.open('w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['n_unlinked_loci','p_modern_each_locus','min_fixed_modern_loci',
                'max_fixed_modern_loci','P_fraction_between_3_7pct_longrun'])
    for L in [8,16,32,64,128,256,512,1024]:
        k0=ceil(.03*L-1e-12);k1=floor(.07*L+1e-12)
        p=sum(comb(L,k)*(.05**k)*(.95**(L-k)) for k in range(k0,k1+1))
        w.writerow([L,.05,k0,k1,p])
print(out)
