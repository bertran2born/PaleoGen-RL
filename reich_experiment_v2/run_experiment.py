#!/usr/bin/env python3
"""Single-pulse Neandertal ancestry test, built on Reich's SI3 simulator.

Run `python run_experiment.py --scenario all --reps 100 --mode adaptive`.
Run `python run_experiment.py --scenario all --reps 1000 --mode quick` for
fast marker-only screening (NOT valid for final autosomal acceptance).
"""
import argparse
import bz2
import csv
import gzip
import hashlib
import io
import json
from dataclasses import asdict, replace
from pathlib import Path
import sys
import time
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent/'src'))
from epi_pulse import Config, run
from science_contract import load_contract
from paleogen_rl.genetics.pulse import (
    MODEL as BLOCK_MODEL, RESULT_SCHEMA_VERSION as BLOCK_RESULT_SCHEMA_VERSION,
    MODE_RESULT_SCHEMA_VERSION as BLOCK_MODE_RESULT_SCHEMA_VERSION, evaluate_block_pulse, load_block_map,
)
from paleogen_rl.genetics.selected import BlockSelection
from paleogen_rl.genetics.protocol import (
    PROTOCOL_VERSION, PROTOCOL_RESULT_SCHEMA_VERSION, load_autosomal_protocol,
)

RESULT_SCHEMA_VERSION = 'pulse-result-v1'
MODEL = 'panmictic_pulse_reciprocal_epistasis'

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

def require_completed_pass(result, cfg, *, full=False):
    """Reject failed reproduction and horizons not reached by integral passes."""
    generation = result['generations_completed']
    reason = result['termination_reason']
    if reason == 'reproduction_failed':
        raise RuntimeError(f'reproduction_failed: seed={cfg.seed}, '
                           f'generations_completed={generation}, target={cfg.gens}')
    if generation != cfg.gens and (full or reason != 'markers_absorbed'):
        raise RuntimeError(f'incomplete_horizon: seed={cfg.seed}, '
                           f'generations_completed={generation}, target={cfg.gens}, reason={reason}')

def run_mode(cfg, mode):
    """Project raw engine statistics onto the requested evaluation policy.

    auto_mod remains the raw first-pass diagnostic. The historical field
    auto_mod_at_50ka denotes the requested horizon (50 ka only at default gens).
    """
    if mode not in ('full', 'quick', 'adaptive'):
        raise ValueError('mode must be full/quick/adaptive')
    cfg = replace(cfg, stop_when_absorbed=mode != 'full')
    result = run(cfg)
    require_completed_pass(result, cfg, full=mode == 'full')
    if mode == 'quick':
        result.update(auto_mod_at_50ka='NOT_EVALUATED_QUICK',
                      auto_evaluation_status='not_evaluated_quick',
                      target_auto='', joint_and_target='')
    elif mode == 'adaptive' and result['p10_joint'] == 0:
        result.update(auto_mod_at_50ka='NOT_EVALUATED_EVENT_IMPOSSIBLE',
                      auto_evaluation_status='not_evaluated_event_impossible',
                      target_auto='', joint_and_target=0.0)
    else:
        final = result
        if mode == 'adaptive':
            final = run(replace(cfg, stop_when_absorbed=False),
                        accelerate_after_absorption=True)
            require_completed_pass(final, cfg, full=True)
            if abs(final['p10_joint'] - result['p10_joint']) > 1e-12:
                raise RuntimeError('Early absorption check failed: marker results changed')
        result.update(auto_mod_at_50ka=final['auto_mod'],
                      auto_evaluation_status='evaluated_at_target',
                      target_auto=final['target_auto'],
                      joint_and_target=float(result['p10_joint']) * int(final['target_auto']))
    result['auto_generations_completed'] = (
        final['generations_completed']
        if result['auto_evaluation_status'] == 'evaluated_at_target' else '')
    return result

def target_metadata(cfg, contract):
    """Model chronology in generations before present, without historical inference."""
    parameters = {entry['id']: entry['value'] for entry in contract['reference_parameters']}
    mixture = parameters['mixture_generations_ago']
    years = parameters['years_per_generation']
    return dict(result_schema_version=RESULT_SCHEMA_VERSION, model=MODEL,
                science_contract_version=contract['contract_version'],
                target_generation=cfg.gens, mixture_generations_ago=mixture,
                years_per_generation=years, target_generations_ago=mixture-cfg.gens,
                target_age_ka=(mixture-cfg.gens)*years/1000)

def run_block_full(cfg, mapping, mt_partner, y_partner):
    return _run_block(cfg, mapping, mt_partner, y_partner, 'full')


def run_block_mode(cfg, mode, mapping, mt_partner, y_partner):
    if mode not in ('full', 'quick', 'adaptive'):
        raise ValueError('mode must be full/quick/adaptive')
    if mode == 'full':
        return run_block_full(cfg, mapping, mt_partner, y_partner)
    return _run_block(replace(cfg, stop_when_absorbed=False), mapping, mt_partner, y_partner, mode)


def _run_block(cfg, mapping, mt_partner, y_partner, mode):
    """Explicit adapter for the supported M2 parameters; never silently drop mechanisms."""
    costs = ('mt_mod_nuc_arch', 'mt_arch_nuc_mod', 'y_mod_nuc_arch', 'y_arch_nuc_mod')
    supported = {'N', 'f', 'male_frac', 'gens', 'seed', 's', 's_mt', 'sel_locus',
                 'mismatch_dominance', 'stop_when_absorbed', *costs}
    defaults = asdict(Config())
    if not isinstance(cfg, Config):
        raise ValueError('block adapter requires a pulse Config')
    for field, value in asdict(cfg).items():
        if field not in supported and (field not in defaults or value != defaults[field]):
            raise ValueError(f'unsupported block configuration: {field}')
    if cfg.stop_when_absorbed or cfg.sel_locus not in ('none', 'Y'):
        raise ValueError('blocks require full mode and selection on mt/Y only')
    if cfg.sel_locus == 'none' and cfg.s != 0:
        raise ValueError('nonzero s requires sel_locus=Y for blocks')
    selection = BlockSelection(s_mt=cfg.s_mt, s_y=cfg.s if cfg.sel_locus == 'Y' else 0.,
                               **{field: getattr(cfg, field) for field in costs},
                               mt_partner_block=mt_partner, y_partner_block=y_partner,
                               dominance=cfg.mismatch_dominance)
    report = evaluate_block_pulse(population_size=cfg.N, f=cfg.f, male_fraction=cfg.male_frac,
                                  generations=cfg.gens, seed=cfg.seed,
                                  recombination_map=mapping, selection=selection, mode=mode)
    engine = report['engine_report']
    final = engine['final_measurement']
    sampling = {k: v for k, v in report['sampling'].items()
                if k not in ('sample_size', 'replacement', 'generation', 'status')}
    if mode != 'full':
        screen = report['screening_report']
        measurement = report['ancestry_measurement']
        return dict(**sampling, generations_completed=screen['generations_completed'],
                    termination_reason=screen['termination_reason'],
                    marker_generations_completed=report['sampling']['generation'],
                    marker_evaluation_status=report['sampling']['status'],
                    auto_mod=report['stopping_ancestry_diagnostic']['value'],
                    auto_mod_at_50ka=measurement['value'], auto_evaluation_status=measurement['status'],
                    auto_generations_completed=measurement['generation'] if measurement['value'] is not None else '',
                    target_auto=report['target']['target_auto'], joint_and_target=report['target']['joint_and_target'],
                    block_count=measurement['panel']['block_count'],
                    block_report=json.dumps(report, sort_keys=True, separators=(',', ':'), allow_nan=False))
    return dict(**sampling, generations_completed=engine['generations_completed'],
                termination_reason=engine['termination_reason'],
                auto_mod=final['value'], auto_mod_at_50ka=final['value'],
                auto_evaluation_status=final['status'], auto_generations_completed=final['generation'],
                target_auto=report['target']['target_auto'],
                joint_and_target=report['target']['joint_and_target'],
                block_count=final['panel']['block_count'],
                block_report=json.dumps(report, sort_keys=True, separators=(',', ':'), allow_nan=False))


def scientific_context(cfg, mt_selection_source, *, autosomal_blocks=False):
    """Describe limits of the CLI experiment, without evaluating scientific fit."""
    notes = {
        'published_comparison': (
            'La parité locale du code ne reproduit pas les probabilités intégrées '
            'du préprint ; ces sorties ne démontrent pas une histoire évolutive.'),
        'population_size': (
            'N est un recensement simulé ; son assimilation à une taille effective '
            'est une approximation sans calibration du Ne réalisé.'),
        'demography': (
            'Le modèle est un pulse panmictique sans expansion ; '
            'aucune comparaison spatiale calibrée n’est réalisée ici.'),
        'autosomal_proxy': (
            'L’ascendance est un proxy à quelques loci de poids égal, '
            'sujet à discrétisation ; elle ne reconstruit pas un génome.'),
        'sampling': (
            'La probabilité des dix mâles est une statistique simulée distincte '
            'de la fixation et des observations historiques échantillonnées.'),
    }
    if mt_selection_source == 'posterior_draw':
        notes['mt_selection'] = (
            's_mt est tiré par réplicat dans le fichier fourni ; son origine SI1 '
            'n’est pas authentifiée par ce chargement. Ce tirage seul ne reproduit '
            'pas la distribution intégrée publiée.')
    else:
        notes['mt_selection'] = (
            's_mt est fixé par la configuration, sans intégration d’un posterior '
            'mitochondrial, y compris si un fichier fourni reste non appliqué.')
    if cfg.sel_locus == 'Y' and cfg.s != 0:
        notes['y_selection'] = (
            'Le coefficient de sélection Y est fixé ; les incertitudes '
            'des paramètres publiés ne sont pas toutes intégrées.')
    active = any((cfg.mt_mod_nuc_arch, cfg.mt_arch_nuc_mod,
                  cfg.y_mod_nuc_arch, cfg.y_arch_nuc_mod))
    if active:
        notes['epistasis'] = (
            'Les pénalités réciproques sont exploratoires, sans validation '
            'biologique ; leurs partenaires autosomaux sont exclus du proxy, '
            'dont la base diffère de la référence sans ces pénalités.')
    elif cfg.s == 0 and cfg.s_mt == 0:
        notes['neutral_control'] = (
            'Ce contrôle neutre est une hypothèse de simulation, '
            'pas une reproduction de la référence sélectionnée publiée.')
    if autosomal_blocks:
        notes.pop('autosomal_proxy')
        notes['autosomal_measurement'] = (
            'Ascendance totale de blocs phasés de poids égal, partenaires inclus ; '
            'la discrétisation et la recombinaison sont des approximations non calibrées.')
        notes['convergence'] = (
            'La convergence des scénarios sélectionnés n’est pas établie ; '
            'la carte et la résolution sont des choix explicites de cette exécution.')
        if active:
            notes['epistasis'] = (
                'Les pénalités réciproques sont exploratoires, sans validation biologique ; '
                'les blocs partenaires restent inclus dans la mesure totale et sont suivis séparément.')
    return dict(scientific_status='exploratory_simulation',
                published_result_reproduction='not_demonstrated',
                uncertainty_scope='monte_carlo_only', approximation_notes=notes)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scenario',choices=['all',*SCENARIOS],default='all')
    ap.add_argument('--reps',type=int,default=30)
    ap.add_argument('--mode',choices=['full','quick','adaptive'],default='adaptive')
    ap.add_argument('--N',type=int,default=None)
    ap.add_argument('--gens',type=int,default=None)
    ap.add_argument('--f',type=float,default=None)
    ap.add_argument('--male-frac',type=float,default=None)
    ap.add_argument('--seed',type=int,default=62026)
    ap.add_argument('--output',default=None)
    ap.add_argument('--mt-posterior',default=None,
                    help='Optional Reich SI1 posterior txt file: draw s_mt independently per replicate')
    ap.add_argument('--block-map',default=None,
                    help='Explicit JSON block panel/map; enables phased blocks in all three modes')
    ap.add_argument('--mt-partner-block',default=None)
    ap.add_argument('--y-partner-block',default=None)
    ap.add_argument('--autosomal-protocol',default=None,
                    help='Versioned autosomal contract; fixes N, horizon, pulse, map and partners')
    # Optional compositional overrides; the scenario keeps its original Reich
    # Y selection and the SI1 mtDNA posterior unless explicitly replaced.
    for field in ('mt_mod_nuc_arch','mt_arch_nuc_mod','y_mod_nuc_arch','y_arch_nuc_mod'):
        ap.add_argument('--'+field.replace('_','-'),type=float,default=None,
                        help='Override this epistatic penalty in [0,1]')
    args=ap.parse_args()
    autosomal_protocol = None
    protocol_file_sha256 = ''
    block_mapping = None
    block_map_sha256 = ''
    if args.autosomal_protocol is not None:
        if any(value is not None for value in (args.block_map, args.mt_partner_block, args.y_partner_block)):
            ap.error('--autosomal-protocol cannot be combined with map/partner options')
        try:
            autosomal_protocol, protocol_file_sha256 = load_autosomal_protocol(args.autosomal_protocol)
        except (OSError, ValueError) as error:
            ap.error(str(error))
        locked = dict(N=autosomal_protocol.population_size, gens=autosomal_protocol.generations,
                      f=autosomal_protocol.f, male_frac=autosomal_protocol.male_fraction)
        for field, value in locked.items():
            if getattr(args, field) is not None and getattr(args, field) != value:
                ap.error(f'--{field.replace("_", "-")} conflicts with autosomal protocol')
            setattr(args, field, value)
        block_mapping = autosomal_protocol.recombination_map
        args.mt_partner_block = autosomal_protocol.mt_partner_block
        args.y_partner_block = autosomal_protocol.y_partner_block
    else:
        for field, value in dict(N=1450, gens=6993, f=.05, male_frac=.5).items():
            if getattr(args, field) is None:
                setattr(args, field, value)
    if args.reps<1 or args.N<20 or args.gens<1:ap.error('reps >= 1, N >= 20, gens >= 1')
    if not 0 <= args.f <= 1 or not 0<=args.male_frac<=1:ap.error('f and male-frac must be in [0,1]')
    overrides={name:getattr(args,name) for name in (
        'mt_mod_nuc_arch','mt_arch_nuc_mod','y_mod_nuc_arch','y_arch_nuc_mod')
        if getattr(args,name) is not None}
    if any(not 0 <= value <= 1 for value in overrides.values()):
        ap.error('epistatic penalties must lie in [0,1]')
    if overrides and args.output is None:
        ap.error('when overriding epistasis, specify --output to avoid overwriting runs')
    if args.block_map is not None or autosomal_protocol is not None:
        if args.output is None or Path(args.output).suffix != '.csv':
            ap.error('blocks require an explicit --output ending in .csv')
        if args.mt_partner_block is None or args.y_partner_block is None:
            ap.error('blocks require explicit --mt-partner-block and --y-partner-block')
        try:
            if autosomal_protocol is None:
                block_mapping, block_map_sha256 = load_block_map(args.block_map)
            for block in (args.mt_partner_block, args.y_partner_block):
                if block not in block_mapping.panel.block_ids:
                    raise ValueError('partner blocks must belong to the declared panel')
            if args.seed < 0:
                raise ValueError('block seed must be nonnegative')
        except (OSError, ValueError) as error:
            ap.error(str(error))
        for destination in (Path(args.output), Path(args.output).with_suffix('.json')):
            if destination.exists() or destination.is_symlink():
                ap.error(f'block output already exists: {destination}')
    elif args.mt_partner_block is not None or args.y_partner_block is not None:
        ap.error('partner block options require --block-map')
    names=list(SCENARIOS) if args.scenario=='all' else [args.scenario]
    output=Path(args.output or (Path(__file__).parent/'results'/f'{args.mode}_{args.reps}.csv'))
    output.parent.mkdir(parents=True,exist_ok=True)
    summary=[]
    all_rows=[]
    posterior=None
    posterior_sha256=''
    if args.mt_posterior:
        posterior_bytes=Path(args.mt_posterior).read_bytes()
        posterior_sha256=hashlib.sha256(posterior_bytes).hexdigest()
        # Preserve loadtxt's filename-based gzip/bzip2 handling while hashing
        # exactly the file bytes used by this execution.
        payload=posterior_bytes
        if str(args.mt_posterior).endswith('.gz'):
            payload=gzip.decompress(payload)
        elif str(args.mt_posterior).endswith('.bz2'):
            payload=bz2.decompress(payload)
        a=np.loadtxt(io.BytesIO(payload),comments='#')
        posterior=a[:,0] if a.ndim==2 else a
        print(f'Loaded {len(posterior)} SI1 mtDNA fitness gap posterior values',flush=True)
    base=Config(N=args.N,f=args.f,male_frac=args.male_frac,gens=args.gens,
                stop_when_absorbed=args.mode!='full')
    chronology=target_metadata(base, load_contract())
    if block_mapping is not None:
        chronology.update(result_schema_version=(BLOCK_RESULT_SCHEMA_VERSION if args.mode == 'full'
                                                  else BLOCK_MODE_RESULT_SCHEMA_VERSION), model=BLOCK_MODEL)
    if autosomal_protocol is not None:
        chronology['result_schema_version'] = PROTOCOL_RESULT_SCHEMA_VERSION
    for j,name in enumerate(names):
        cfg=replace(base,**{**SCENARIOS[name],**overrides})
        rows=[]
        start=time.monotonic()
        for i in range(args.reps):
            # Paired-replicate seeds: all scenarios share the same replicate index.
            c=replace(cfg,seed=args.seed+i)
            mt_source='fixed' if posterior is None else 'posterior_not_applied'
            draw_seed=''
            if posterior is not None and c.s_mt != 0:
                mt_source='posterior_draw'
                draw_seed=args.seed+i+27383
                draw_rng=np.random.default_rng(draw_seed)
                c=replace(c,s_mt=float(draw_rng.choice(posterior)))
            try:
                if block_mapping is None:
                    res=run_mode(c, args.mode)
                elif args.mode == 'full':
                    res=run_block_full(c, block_mapping, args.mt_partner_block, args.y_partner_block)
                else:
                    res=run_block_mode(c, args.mode, block_mapping, args.mt_partner_block, args.y_partner_block)
            except RuntimeError as error:
                ap.exit(1, f'{name} rep={i}: {error}\n')
            except ValueError as error:
                if block_mapping is None:
                    raise
                ap.exit(1, f'{name} rep={i}: {error}\n')
            context=(scientific_context(c, mt_source) if block_mapping is None else
                     scientific_context(c, mt_source, autosomal_blocks=True))
            row={'scenario':name,'rep':i,'seed':c.seed,'mode':args.mode,
                 'initial_f':args.f,'N':args.N,'gens_requested':args.gens,'s_mt_realized':c.s_mt,
                 **chronology,
                 'config_realized':json.dumps(asdict(c),sort_keys=True,separators=(',', ':'),allow_nan=False),
                 'mt_selection_source':mt_source,'mt_posterior_sha256':posterior_sha256,
                 'mt_posterior_draw_seed':draw_seed,
                 **{key:value for key,value in context.items() if key != 'approximation_notes'},
                 'approximation_notes':json.dumps(context['approximation_notes'],sort_keys=True,ensure_ascii=False),
                 **res}
            if block_mapping is not None:
                row['block_map_sha256'] = block_map_sha256
            if autosomal_protocol is not None:
                row.update(autosomal_protocol_id=autosomal_protocol.protocol_id,
                           autosomal_protocol_version=PROTOCOL_VERSION,
                           autosomal_protocol_sha256=autosomal_protocol.sha256,
                           autosomal_protocol_file_sha256=protocol_file_sha256,
                           autosomal_protocol=autosomal_protocol.canonical_json,
                           resolution_control_status='not_established')
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
        if block_mapping is not None:
            reports = [json.loads(row['block_report']) for row in rows]
            work = [report.get('work_units', report['engine_report']['work_units']) for report in reports]
            metrics['block_work_units'] = {
                key: sum(item[key] for item in work) for key in
                ('candidates_generated', 'accepted_candidates', 'offspring_generated', 'block_copy_transmissions')}
            metrics['block_work_units']['state_allele_entries'] = max(item['state_allele_entries'] for item in work)
            if args.reps == 1:
                if args.mode != 'quick':
                    metrics['joint_and_auto_95pct_bootstrap'] = None
                metrics['p10_joint_95pct_bootstrap'] = None
        metrics['time_seconds']=round(time.monotonic()-start,2)
        # The context describes the scenario policy; realized coefficients remain
        # in each CSV row, including draws that happen to be zero.
        source=('posterior_draw' if posterior is not None and cfg.s_mt != 0
                else 'fixed' if posterior is None else 'posterior_not_applied')
        summary.append(dict(name=name,reps=args.reps,**metrics,
                            scientific_context=(scientific_context(cfg, source) if block_mapping is None
                                                else scientific_context(cfg, source, autosomal_blocks=True))))
        all_rows.extend(rows)
        print(f'{name:<29s}  P(sample 10 both)={metrics["p10_joint"]:.4%}  '
              f'P(mt,Y fixation)={metrics["joint_fixed"]:.4%}  '
              f't={metrics["time_seconds"]:.1f}s',flush=True)
    with output.open('x' if block_mapping is not None else 'w',newline='') as fobj:
        wr=csv.DictWriter(fobj,fieldnames=list(all_rows[0]));wr.writeheader();wr.writerows(all_rows)
    jsonpath=output.with_suffix('.json')
    meta_args = vars(args).copy()
    if autosomal_protocol is None:
        meta_args.pop('autosomal_protocol')
    else:
        meta_args.update(autosomal_protocol_source=args.autosomal_protocol,
                         autosomal_protocol=autosomal_protocol.to_dict(),
                         autosomal_protocol_version=PROTOCOL_VERSION,
                         autosomal_protocol_id=autosomal_protocol.protocol_id,
                         autosomal_protocol_sha256=autosomal_protocol.sha256,
                         autosomal_protocol_file_sha256=protocol_file_sha256,
                         resolution_control_status='not_established')
    if block_mapping is None:
        for field in ('block_map', 'mt_partner_block', 'y_partner_block'):
            meta_args.pop(field)
    else:
        meta_args.update(block_map_sha256=block_map_sha256,
                         recombination_map=block_mapping.to_dict(),
                         convergence_status='not_assessed_for_selected_scenarios')
    with jsonpath.open('x' if block_mapping is not None else 'w') as fobj:
        json.dump(dict(meta=dict(meta_args,scenarios={k:{**SCENARIOS[k],**overrides} for k in names},
            **chronology,
            definition=f'P(ten sampled males each modern mt AND modern Y at generation {args.gens} after pulse)'),
            summary=summary),fobj,indent=2,allow_nan=block_mapping is None)
    print('Wrote:',output,'and',jsonpath,flush=True)

if __name__=='__main__':main()
