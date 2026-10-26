# Faisabilité du budget de confirmation M3 — I33

Ce dossier chiffre la précision simultanée d'I32 avec les coûts logiques I31,
sans simulation. **Ce n'est pas un pré-enregistrement confirmatoire approuvé.**
Le choix des marges scientifiques, de l'architecture et du budget reste ouvert.
Les archives de simulations et la cible 3–7 % sont inchangées.

## Gabarit et périmètre

Le [gabarit](m3-confirmation-budget-plan.json) fixe N=1450, f=0.05,
fraction masculine=0.5 et 6993 générations, comme le régime cible existant.
Les arrondis M2 restent 36 mâles et 36 femelles modernes, sans ajuster f.
Les 17 scénarios nommés, en dominance additive et sans posterior, partagent
la même famille de coût : poids relatifs `(1,3,3,1)`, partenaires aux extrémités,
carte homogène L=1 et facteurs neutres 1/3/9, soit **4/8/20 blocs**.

Ces poids reprennent le contrôle synthétique I30. Leur poids partenaire total
est 0.25, constant entre résolutions, **sans justification biologique** ; ils
ne sont pas proposés comme architecture principale M3. La géométrie et les
paramètres génétiques influencent le surcoût réel de rejet, non estimé ici.
Une famille scientifique différente demanderait un nouveau chiffrage.

Les graines 620000–620002 identifient seulement les trois répétitions du
gabarit de coût ; aucune trajectoire n'est exécutée ou observée. Une étude
avec l'effectif calculé doit déclarer une nouvelle liste de graines, un nouveau
plan et des critères liés à sa nouvelle empreinte, puis les geler avant résultats.

## Hypothèses de précision et de coût

Le chiffrage fixe un risque global de calcul α=0.05 sur les quatre métriques
et toutes les comparaisons à la plus fine résolution : `K=17*(3-1)*4=136`.
Les rayons explorés vont de 0.1 à 0.0001, en fractions absolues.
Pour utiliser le validateur I32, chaque ligne emploie des marges **techniques**
égales à deux fois son rayon. Cela ne les adopte pas comme tolérances scientifiques.
Un rayon de 0.001 représente 0.1 point de pourcentage, pas une erreur relative
de 0.1 %. Les marges d'équivalence et le rayon de précision sont distincts.

I32 impose, pour son rayon simultané conservateur :

```text
n >= ceil(2*log(2*K/alpha)/rayon²)
```

L'effectif annoncé est par scénario et résolution. Il garantit ce rayon sous
les hypothèses d'I32, **pas** une probabilité de conclure à l'équivalence.
Les vrais écarts peuvent dépasser les marges. Les 136 comparaisons peuvent
être dépendantes ; les réplicats doivent être indépendants.

Les coûts sont extrapolés exactement depuis l'aperçu I31, linéairement avec n,
sans créer de liste contenant des millions de graines. Les descendants et
candidats acceptés sont des totaux à achèvement ; candidats et transmissions
sont des minima excluant les rejets. La taille du plus grand état est
`2*1450*20=58000` entrées alléliques. Elle ne mesure ni le pic mémoire, ni la
taille des rapports et leur accumulation en mémoire par le runner.
Ces chiffres ne bornent pas le temps matériel ou le coût d'une parallélisation.
Certains totaux dépassent `2^53` : le rapport conserve des entiers JSON exacts,
à lire avec un désérialiseur préservant les grands entiers, comme celui de Python.

Les effectifs relèvent de la méthode I32 ; **ils ne sont pas une borne inférieure
universelle pour toute méthode statistique possible**. Une autre méthode
nécessiterait une justification et validation de sa couverture, fixées avant
les résultats confirmatoires.

## Résultats de faisabilité

Ces chiffres concernent le seul gabarit ci-dessus et la borne I32, avec
17 scénarios × 3 résolutions. Les transmissions minimales ci-dessous sont
arrondies ; les entiers exacts figurent dans le rapport JSON.

| Rayon simultané (points de pourcentage) | Répétitions par cellule | Évaluations full totales | Transmissions minimales, environ |
| --- | ---: | ---: | ---: |
| 10 | 1 721 | 87 771 | 1.899 × 10¹³ |
| 5 | 6 882 | 350 982 | 7.592 × 10¹³ |
| 1 | 172 031 | 8 773 581 | 1.898 × 10¹⁵ |
| 0.5 | 688 123 | 35 094 273 | 7.591 × 10¹⁵ |
| 0.1 | 17 203 069 | 877 356 519 | 1.898 × 10¹⁷ |
| 0.05 | 68 812 275 | 3 509 426 025 | 7.591 × 10¹⁷ |
| 0.01 | 1 720 306 868 | 87 735 650 268 | 1.898 × 10¹⁹ |

Même un rayon de 1 point demande ici plus de huit millions d'évaluations
full au régime cible. Cette prévision interdit d'assimiler un petit pilote
à une confirmation précise. Elle justifie de confronter les marges au budget
et à la méthode avant de lancer le calcul ; elle ne justifie pas de choisir
des marges larges uniquement pour obtenir une étude plus petite.

## Reproduction

Depuis `reich_experiment_v2/`, dans `nix develop`, exécuter le bloc Python
ci-dessous. La sortie par défaut est `/tmp/m3-confirmation-budget.json` ;
un premier argument permet de choisir une autre destination inexistante.
Le dossier parent doit exister. Une destination existante est refusée.

```python
import hashlib
import json
from pathlib import Path
import platform
import sys
import numpy as np

from study_weighted_autosomal_resolution import (
    ROOT, WEIGHTED_IMPLEMENTATION_FILES, load_weighted_resolution_plan,
    preview_weighted_resolution_plan,
)
from weighted_autosomal_equivalence import CRITERIA_VERSION, METRICS, preview_weighted_equivalence

source = Path('../docs/science/m3-confirmation-budget-plan.json')
plan, file_hash = load_weighted_resolution_plan(source)
workload = preview_weighted_resolution_plan(plan)
workload['plan_file_sha256'] = file_hash
rows = []
for radius in (.1, .05, .01, .005, .001, .0005, .0001):
    criteria = dict(criteria_version=CRITERIA_VERSION, criteria_id=f'cost-only-radius-{radius:g}',
        study_plan_sha256=workload['plan_sha256'], alpha=.05,
        margins={metric: 2*radius for metric in METRICS}, max_interval_radius=radius)
    precision = preview_weighted_equivalence(criteria, plan)
    required = precision['required_replicates_per_cell']
    def scaled(prediction):
        return {key: (value if key in ('state_allele_entries', 'largest_population_state_allele_entries')
                      else value//len(plan['seeds'])*required)
                for key, value in prediction.items()}
    costs = []
    for declared in workload['resolutions']:
        costs.append(dict(block_count=declared['block_count'], refinement_factor=declared['refinement_factor'],
                          **scaled({k: v for k, v in declared.items()
                                    if k not in ('block_count', 'refinement_factor')})))
    rows.append(dict(precision_radius=radius, precision=precision,
                     resolutions=costs, total_workload=scaled(workload['total_workload'])))
paths = (*WEIGHTED_IMPLEMENTATION_FILES, 'weighted_autosomal_equivalence.py')
report = dict(report_version='m3-confirmation-feasibility-v1', scientific_status='planning_only',
    simulation_performed=False, scientific_criteria_adopted=False, convergence_status='not_established',
    mode='full', plan_template=plan, plan_template_sha256=workload['plan_sha256'],
    plan_template_file_sha256=file_hash, workload_template=workload, sensitivity=rows,
    implementation_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
    python_version=platform.python_version(), numpy_version=np.__version__,
    generator='docs/science/m3-confirmation-budget.md:reproduction',
    assumptions=dict(workload['assumptions'],
        template_seeds_are_not_a_confirmation_plan=True, technical_margins_are_twice_radius=True,
        no_large_seed_lists_materialized=True))
output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/tmp/m3-confirmation-budget.json')
with output.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, indent=2, allow_nan=False)
    stream.write('\n')
for row in rows:
    print(row['precision_radius'], row['precision']['required_replicates_per_cell'],
          row['total_workload']['evaluations'], row['total_workload']['block_copy_transmissions_lower_bound_on_completion'])
```

Le [rapport archivé](m3-confirmation-budget.json) conserve les sept lignes,
aperçus, critères techniques, famille, gabarit, empreintes et versions.
Pour reproduire les empreintes d'implémentation, utiliser la révision archivée ;
une révision ultérieure peut conserver les calculs tout en changeant leurs sources.

## Décisions nécessaires avant une confirmation

1. Justifier la famille scientifique : poids et positions partenaires, carte,
   résolutions et portée du seul raffinement neutre.
2. Fixer les quatre marges en unités absolues et leur justification, sans les
   déduire des scores ou des seules valeurs techniques de ce dossier.
3. Fixer risque global et précision, puis confronter le coût au budget réel.
   Si nécessaire, revoir la méthode statistique avec garanties documentées,
   sans assouplir les marges après observation pour forcer une conclusion.
4. Déclarer les graines confirmatoires, l'implémentation et l'environnement ;
   geler le nouveau plan et les critères avant exécution, sans arrêt opportuniste.
5. Exécuter, archiver et évaluer ; conserver une conclusion non concluante ou
   négative si elle est obtenue. L'adoption d'un protocole principal et l'audit
   M3 viennent après ces preuves, jamais du seul succès des tests.

M3 D1 et la convergence restent ouverts. Ce dossier ne requiert aucune
modification des observations, de la cible ou des ressources scientifiques.

## Preuves de validation

Le 26 octobre 2026, **3 tests ciblés, 156 tests autosomaux et 233 tests complets**
réussissent sous Nix, sans échec ni test ignoré. Les contrôles rapides vérifient
identités, portée, sept effectifs et coûts par calcul indépendant, précision
minimale, absence de grandes listes, reproduction documentée avec RNG/moteur
interdits et refus d'écrasement. Aucune simulation du gabarit n'est exécutée,
ni par la génération ni par ces trois tests. La suite complète conserve ses
contrôles de simulation préexistants.

SHA-256 des fichiers archivés :

- gabarit : `8fe96cc03706a61f1707f41e39e203bb22d34c30809eaa15b19bb50fe7d15f18` ;
- rapport : `bf85c49a958d71aab463a2924bcea9e2dc37dbed180e56a3a44482578c3de851`.

Les sources de calcul sont celles de la base `de89c34`, leurs empreintes
figurent dans le rapport. Environnement enregistré : Python 3.14.8 et
NumPy 2.5.3. Ce dossier complète une étape de planification ; il ne valide
ni des marges scientifiques, ni une convergence, ni un protocole principal.
