"""Offline validators for the observation contract and explicit final measurements.

These entry points do not migrate or reinterpret historical simulator outputs.
"""

import json
from pathlib import Path

from verify_provenance import REPO_ROOT, REGISTRY_PATH
from verify_sources import CATALOG_PATH, nonempty, validate_catalog


CONTRACT_PATH = Path('docs/science/observations.json')
OBSERVATION_IDS = {'sampled_uniparental_pattern', 'reported_autosomal_ancestry'}
STATISTIC_IDS = {'mt_fixation', 'y_fixation', 'ten_male_joint', 'final_autosomal_ancestry'}
PARAMETER_IDS = {'years_per_generation', 'mixture_generations_ago',
                 'sampling_generations_ago', 'modern_uniparental_ne',
                 'archaic_uniparental_ne', 'neandertal_uniparental_ne'}


def require(condition, field):
    if not condition:
        raise ValueError(f'invalid or missing {field}')


def positive_int(value):
    return type(value) is int and value > 0


def fraction(value):
    # Comparisons also reject NaN and infinities; bool is not a measurement.
    return type(value) in (int, float) and 0 <= value <= 1


def validate_contract(contract, catalog, registry):
    sources = {s['id']: s for s in validate_catalog(catalog, registry)}
    require(isinstance(contract, dict), 'contract')
    require(contract.get('schema_version') == '1', 'schema_version')
    require(contract.get('contract_version') == 'science-observations-v1', 'contract_version')
    for group, expected_ids, status in (
        ('observations', OBSERVATION_IDS, 'observation'),
        ('statistics', STATISTIC_IDS, 'hypothesis'),
        ('reference_parameters', PARAMETER_IDS, 'hypothesis'),
    ):
        entries = contract.get(group)
        require(isinstance(entries, list) and len(entries) == len(expected_ids), group)
        seen = set()
        for entry in entries:
            require(isinstance(entry, dict), group + ' entry')
            identity = entry.get('id')
            require(isinstance(identity, str) and identity in expected_ids
                    and identity not in seen, group + '.id')
            seen.add(identity)
            require(entry.get('status') == status, identity + '.status')
            for field in ('definition', 'unit', 'sampling'):
                require(nonempty(entry.get(field)), identity + '.' + field)
            if group == 'statistics':
                for field in ('formula', 'denominator'):
                    require(nonempty(entry.get(field)), identity + '.' + field)
            if group == 'reference_parameters':
                value = entry.get('value')
                require(type(value) in (int, float) and 0 < value < float('inf'),
                        identity + '.value')
            uncertainty = entry.get('uncertainty')
            require(isinstance(uncertainty, dict), identity + '.uncertainty')
            expected_kind = ('reported_range' if identity == 'reported_autosomal_ancestry'
                             else 'not_quantified')
            require(uncertainty.get('kind') == expected_kind
                    and 'confidence_level' in uncertainty
                    and uncertainty['confidence_level'] is None, identity + '.uncertainty')
            if expected_kind == 'reported_range':
                require(uncertainty.get('bounds') == [0.03, 0.07], identity + '.bounds')
            if identity == 'final_autosomal_ancestry':
                require(entry.get('target_bounds') == [0.03, 0.07], identity + '.target_bounds')
            citations = entry.get('citations')
            require(isinstance(citations, list) and bool(citations), identity + '.citations')
            for citation in citations:
                require(isinstance(citation, dict), identity + '.citation')
                source_id = citation.get('source_id')
                require(isinstance(source_id, str) and source_id in sources, 'citation.source_id')
                require(citation.get('content_id') == sources[source_id]['version']['content_id'],
                        'citation.content_id')
                pages = citation.get('pages')
                require(isinstance(pages, list) and bool(pages)
                        and all(positive_int(p) for p in pages), 'citation.pages')
                require(nonempty(citation.get('section')), 'citation.section')
    parameters = {p['id']: p['value'] for p in contract['reference_parameters']}
    timeline = contract.get('timeline')
    require(isinstance(timeline, dict), 'timeline')
    elapsed = timeline.get('elapsed_generations')
    require(positive_int(elapsed)
            and elapsed == parameters['mixture_generations_ago']
            - parameters['sampling_generations_ago'], 'timeline.elapsed_generations')
    require(timeline.get('target_age_ka') == 50, 'timeline.target_age_ka')
    require(contract.get('mode_semantics') == {
        'quick': {'final_autosomal': 'unavailable'},
        'full': {'final_autosomal': 'all_trajectories'},
        'adaptive': {'final_autosomal': 'event_possible_trajectories_only'},
    }, 'mode_semantics')
    require(contract.get('uncertainty_policy') == {
        'simulation_intervals': 'monte_carlo_only', 'historical_confidence_level': None,
    }, 'uncertainty_policy')
    return contract


def load_contract(root=REPO_ROOT):
    root = Path(root)
    def read(path):
        return json.loads((root / path).read_text(encoding='utf-8'))
    return validate_contract(read(CONTRACT_PATH), read(CATALOG_PATH), read(REGISTRY_PATH))


def validate_autosomal_statistic(measurement, *, expected_generation):
    """Accept an evaluated neutral diploid proxy at an explicitly requested horizon.

    Ancestry value and metadata are caller declarations. This function validates
    their consistency; it cannot establish that a simulation actually reached them.
    """
    require(type(expected_generation) is int and expected_generation >= 0, 'expected_generation')
    require(isinstance(measurement, dict), 'autosomal measurement')
    require(measurement.get('status') == 'evaluated', 'status')
    generation = measurement.get('generation')
    require(type(generation) is int and generation >= 0, 'generation')
    require(generation == expected_generation, 'generation (final horizon)')
    require(fraction(measurement.get('value')), 'value')
    population = measurement.get('diploid_individuals')
    require(positive_int(population), 'diploid_individuals')
    basis = measurement.get('locus_basis')
    require(isinstance(basis, dict), 'locus_basis')
    require(basis.get('kind') == 'neutral_proxy', 'locus_basis.kind')
    require(basis.get('weighting') == 'equal_diploid_copies', 'locus_basis.weighting')
    total = basis.get('total_loci')
    require(positive_int(total), 'locus_basis.total_loci')
    groups = {}
    for name in ('included_loci', 'excluded_loci', 'selected_loci'):
        loci = basis.get(name)
        require(isinstance(loci, list)
                and all(type(i) is int and 0 <= i < total for i in loci), 'locus_basis.' + name)
        require(len(set(loci)) == len(loci), 'locus_basis.' + name + ' (duplicates)')
        groups[name] = set(loci)
    included, excluded, selected = (groups[name] for name in
                                     ('included_loci', 'excluded_loci', 'selected_loci'))
    require(bool(included), 'locus_basis.included_loci')
    require(not included & excluded and len(included | excluded) == total,
            'locus_basis partition')
    require(selected <= excluded, 'locus_basis selected loci must be excluded')
    denominator = measurement.get('allele_copy_denominator')
    require(positive_int(denominator) and denominator == 2 * population * len(included),
            'allele_copy_denominator')
    return measurement
