"""Extension of David Reich's October 2026 SI3 panmictic pulse engine.

Only an additional family of sex-aware, reciprocal epistatic viability terms has been
inserted into Reich's implementation. All baseline functions remain identical in the
absence of the new terms. Provenance: SI3codebase.zip / mechanisms_code/cluster/panmictic_sim.py.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from reich_panmictic_original import *
import reich_panmictic_original as original

@dataclass
class Config(original.Config):
    # Penalize mismatch between maternal mtDNA and an autosomal nuclear partner.
    mt_mod_nuc_arch: float = 0.0
    mt_arch_nuc_mod: float = 0.0
    # Penalize mismatch between paternal Y and a DIFFERENT autosomal partner (males only).
    y_mod_nuc_arch: float = 0.0
    y_arch_nuc_mod: float = 0.0
    mt_partner_locus: int = 0
    y_partner_locus: int = 1
    mismatch_dominance: str = 'additive'  # 'additive', 'dominant', 'recessive'


def _nuclear_carrier(autosome, locus, archaic: bool, dominance: str):
    """A dominance-aware probability/penetrance in [0,1], per diploid genotype."""
    count = 2 - autosome[:, locus] if archaic else autosome[:, locus]
    if dominance == 'additive': return count / 2.0
    if dominance == 'dominant': return (count > 0).astype(float)
    if dominance == 'recessive': return (count == 2).astype(float)
    raise ValueError('dominance must be additive/dominant/recessive')


def _epistasis_loss(cfg: Config, sx, mt, y, auto):
    """Combined loss as 1 - product of the 4 independent viability terms.

    Because partners are autosomal, female and male mitochondrial costs can differ
    by mtDNA and nuclear genotype, while Y-related costs apply ONLY to sons.
    No term is assumed beneficial for modern ancestry; all 4 are nonnegative costs.
    """
    if any(not 0 <= v <= 1 for v in (cfg.mt_mod_nuc_arch,
                  cfg.mt_arch_nuc_mod,cfg.y_mod_nuc_arch,cfg.y_arch_nuc_mod)):
        raise ValueError('epistasis coefficients must lie in [0,1]')
    dom = cfg.mismatch_dominance
    mt_arch = _nuclear_carrier(auto,cfg.mt_partner_locus,True,dom)
    mt_mod = _nuclear_carrier(auto,cfg.mt_partner_locus,False,dom)
    y_arch  = _nuclear_carrier(auto,cfg.y_partner_locus,True,dom)
    y_mod   = _nuclear_carrier(auto,cfg.y_partner_locus,False,dom)
    male = sx == 1
    survival = ((1.0-cfg.mt_mod_nuc_arch*((mt == 1)*mt_arch))
               *(1.0-cfg.mt_arch_nuc_mod*((mt == 0)*mt_mod))
               *(1.0-cfg.y_mod_nuc_arch*(male & (y == 1))*y_arch)
               *(1.0-cfg.y_arch_nuc_mod*(male & (y == 0))*y_mod))
    return 1.0 - survival


def run_extended(cfg: Config, *, accelerate_after_absorption: bool = False):
    """Full Reich WF reproduction, with new reciprocal DMI viability terms.

    N, f, demography, Mendelian inheritance and sampling generation unchanged.
    """
    rng = np.random.default_rng(cfg.seed)
    exclude_autos = set()
    exclude_x = set()
    if cfg.sel_locus == 'auto': exclude_autos.add(cfg.auto_locus)
    if cfg.sel_locus == 'X': exclude_x.add(cfg.x_locus)
    if cfg.dm and cfg.dm_focal == 'auto': exclude_autos.add(cfg.dm_focal_locus)
    if cfg.dm and cfg.dm_partner == 'auto': exclude_autos.add(cfg.dm_partner_locus)
    if cfg.dm and cfg.dm_focal == 'X': exclude_x.add(cfg.dm_focal_locus)
    if cfg.dm and cfg.dm_partner == 'X': exclude_x.add(cfg.dm_partner_locus)
    if cfg.xdrive: exclude_x.add(original.DRIVER_XLOCUS)
    active = any((cfg.mt_mod_nuc_arch,cfg.mt_arch_nuc_mod,
                  cfg.y_mod_nuc_arch,cfg.y_arch_nuc_mod))
    if active:
        exclude_autos.update([cfg.mt_partner_locus, cfg.y_partner_locus])
        # Work inside one process, single task at a time. Restore globals even on error.
        saved = original._dm_penetrance
        def joint_penetrance(c, sx, mt, Yc, auto, X):
            new = _epistasis_loss(c, sx, mt, Yc, auto)
            if c.dm > 0:
                prior_dm = getattr(c, "_original_dm", 0.0)
                if prior_dm: # evaluate ORIGINAL mechanism at its original penetrance
                    prior = saved(c, sx, mt, Yc, auto, X) * prior_dm / c.dm
                    return 1.0-(1.0-prior)*(1.0-new)
                return new
            return new
        original._dm_penetrance = joint_penetrance
    else:
        saved = None
    try:
        # copied unmodified generational schedule; we only change per-birth selection
        # trigger through cfg.dm, which original._breed consults.
        from dataclasses import replace
        P = original._init(cfg,rng)
        no_more_marker_selection = False
        eligible_to_accelerate = (not active and cfg.sel_locus in ('none','Y','mt')
            and cfg.dm == 0 and cfg.xdrive == 0 and cfg.xdrive_cost == 0
            and not cfg.pulse2_gen and cfg.cycle_T == 0)
        for g in range(cfg.gens):
            cur = cfg
            if no_more_marker_selection:
                # Once BOTH uniparental markers are absorbed, their alleles cannot
                # segregate. All selection acting only on them then has genotype-
                # independent survival weights, so it may be switched off WITHOUT
                # changing the distribution of neutral autosomal inheritance.
                # Different random draws after the switch are expected.
                cur = replace(cfg,s=0,s_mt=0,sel_locus='none')
            if cfg.cycle_T > 0 and cfg.cycle_R > 1.0:
                m,a=(cfg.cycle_R+1)/2.0,(cfg.cycle_R-1)/2.0
                k = (m+a*np.sin(2*np.pi*g/cfg.cycle_T+cfg.cycle_phase))/np.sqrt(cfg.cycle_R)
                cur=replace(cfg,N=max(20,int(round(cfg.N*k))))
            if active:
                # _breed uses cfg.dm for both activation and penalty multiplicand.
                # Replace dm by 1.0 *within breeding* but pass original dm
                # through `_original_dm` so old and new interactions can combine.
                cur=replace(cur,dm=1.0)
                setattr(cur, '_original_dm',cfg.dm)
            nxt=original._step(P,cur,rng,g)
            if nxt is None: break
            P=nxt
            if cfg.pulse2_gen and g==cfg.pulse2_gen:
                P=original._second_pulse(P,cfg,rng)
            if ((cfg.stop_when_absorbed or (accelerate_after_absorption and eligible_to_accelerate))
                    and g%10==0 and g>0
                    and (not cfg.pulse2_gen or g>cfg.pulse2_gen)):
                male=P['sex']==1
                pm=float((P['mt']==1).mean())
                py=float((P['Y'][male]==1).mean()) if male.any() else 0.0
                if pm in (0.0,1.0) and py in (0.0,1.0):
                    if cfg.stop_when_absorbed:break
                    if accelerate_after_absorption and eligible_to_accelerate:
                        no_more_marker_selection=True
        data=original._stats(P,tuple(exclude_autos),tuple(exclude_x))
        men=P['sex']==1
        both=int(((P['mt'][men]==1)&(P['Y'][men]==1)).sum())
        nm=int(men.sum())
        # Exact simple random sample WITHOUT replacement: all 10 carry both alleles.
        import math
        p10=float(np.prod([(both-i)/(nm-i) for i in range(10)])) if both>=10 and nm>=10 else 0.0
        data.update(both_modern_men=both, male_n=nm,
                    p10_joint=p10, joint_fixed=bool(data['mt_mod'] == 1.0 and data['Y_mod'] == 1.0),
                    generations_completed=g+1,
                    target_auto=bool(0.03 <= data['auto_mod'] <= 0.07))
        return data
    finally:
        if active: original._dm_penetrance=saved

# Public interface: always include ten-male joint statistics, including neutral controls.
run = run_extended
