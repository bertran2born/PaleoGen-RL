#!/usr/bin/env python3
"""Compare two Monte Carlo runs, preserving distinct marker/autosomal endpoints.
Only stdlib needed. Fisher's exact test treats two runs as independent samples;
sharing seeds does not imply identical random streams under different selection.
"""
from __future__ import annotations
import argparse
import csv
import math


def read_rows(path):
    with open(path, newline='') as f:
        rows=list(csv.DictReader(f))
    if not rows: raise ValueError(f'Empty CSV: {path}')
    return rows


def wilson(k,n,z=1.959963984540054):
    p=k/n; d=1+z*z/n
    m=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return (max(0.0,m-h),min(1.0,m+h))


def lchoose(n,r):
    if r<0 or r>n: return float('-inf')
    return math.lgamma(n+1)-math.lgamma(r+1)-math.lgamma(n-r+1)


def fisher_exact_two_sided(k1,n1,k2,n2):
    total=n1+n2; K=k1+k2
    lo=max(0,K-n2); hi=min(K,n1)
    def mass(x): return math.exp(lchoose(n1,x)+lchoose(n2,K-x)-lchoose(total,K))
    obs=mass(k1)
    return min(1.0, sum(mass(x) for x in range(lo,hi+1) if mass(x)<=obs*(1+1e-10)))


def metrics(rows):
    n=len(rows)
    events={
        'mt_fixed':sum(float(row['mt_mod'])==1 for row in rows),
        'Y_fixed':sum(float(row['Y_mod'])==1 for row in rows),
        'both_fixed':sum(row['joint_fixed'].strip().lower()=='true' for row in rows),
    }
    if 'joint_and_target' in rows[0] and all(row['joint_and_target'] != '' for row in rows):
        events['both_and_auto']=sum(float(row['joint_and_target']) for row in rows)
    return n,events


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('baseline');p.add_argument('experiment')
    a=p.parse_args()
    r=read_rows(a.baseline);e=read_rows(a.experiment)
    n1,m1=metrics(r);n2,m2=metrics(e)
    print(f'Baseline: {a.baseline} ({n1} runs)')
    print(f'Experiment: {a.experiment} ({n2} runs)')
    print('Metric                 Baseline    95% Wilson CI          Experiment    95% Wilson CI       Fisher 2-sided')
    for name in m1:
        if name not in m2: continue
        k1=m1[name];k2=m2[name]
        if not float(k1).is_integer() or not float(k2).is_integer():
            print(f'{name}: weighted outcome; binomial CI inapplicable')
            continue
        k1=int(k1);k2=int(k2)
        c1=wilson(k1,n1);c2=wilson(k2,n2)
        pv=fisher_exact_two_sided(k1,n1,k2,n2)
        print(f'{name:20} {k1:4}/{n1:<4} ({100*k1/n1:5.2f}%) [{100*c1[0]:5.2f},{100*c1[1]:5.2f}]%  '
              f'{k2:4}/{n2:<4} ({100*k2/n2:5.2f}%) [{100*c2[0]:5.2f},{100*c2[1]:5.2f}]%   {pv:.5g}')
    if {row['seed'] for row in r}=={row['seed'] for row in e}:
        print('Matched seed sets, but stochastic trajectories are NOT necessarily pairwise identical.')
    print('Note: the auto metric may involve different numbers of neutral sentinel loci across scenarios.')

if __name__=='__main__':main()
