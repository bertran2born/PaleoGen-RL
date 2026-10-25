# Blocs phasés sous sélection — protocole I15 / M3

## Portée et paramètres fixés avant les tests

Le moteur I15 ajoute mtDNA/Y et viabilité des descendants à la transmission I12.
Il reçoit une population initiale explicite ; il ne choisit pas une carte, une
résolution ou une histoire démographique. N reste constant avec N//2 mâles et
N−N//2 femelles. Les simulations sont intégrales, y compris après absorption.
Le moteur historique et les résultats archivés ne sont pas modifiés.

Contrôle statistique fixé avant exécution : N=20 000 (10 000 par sexe), tous
parents hétérozygotes en phase (homologue 0 archaïque, homologue 1 moderne)
sur deux blocs, tous mtDNA modernes, Y archaïque chez les mâles et −1 chez les
femelles. Recombinaison nulle. Seul coût actif : mt moderne × partenaire
archaïque, coefficient 1, dominance additive, partenaire au premier bloc.
Les proportions 0/1/2 modernes avant sélection sont 1/4, 1/2, 1/4 ; leurs
viabilités sont 0, 1/2, 1. Parmi les survivants, les proportions sont donc
**0, 1/2, 1/2**, et l'ascendance attendue est **3/4** sur chaque bloc lié.
Une génération, graines **524287, 655357, 786433**. Pour les neuf proportions
(trois génotypes × trois graines), tolérance absolue Hoeffding
`sqrt(log(2*9/0.001)/(2*20000))`, environ **0.0157** ; le génotype inviable
doit en outre être strictement absent. Aucun seuil ou graine ne sera ajusté.
Ce test vérifie la sélection des descendants et sa liaison au panel, pas une
plausibilité biologique du coefficient 1.

## Contrat scientifique et API

`BlockSelection` déclare `s_mt` et `s_y` dans [−1,1], quatre coûts dans [0,1]
et une dominance `additive`, `dominant` ou `recessive`. Une valeur positive de s
pénalise le marqueur archaïque, une négative pénalise le moderne, de |s|.
Chaque viabilité de base vaut `1−|s|*indicatrice_défavorisée` ; le terme Y
est limité aux mâles. Les quatre facteurs DMI sont ceux de M2, avec exposition
nucléaire 0, 1/2, 1 (additif), présence (dominant) ou homozygotie (récessif)
de l'ascendance incompatible. La viabilité finale est le produit des six
facteurs, évalué sur les marqueurs et blocs **du descendant**.

Les partenaires sont des identifiants explicites du panel ; ils doivent être
déclarés pour chaque interaction active. Des annotations sans coûts sont
permises et ne changent ni tirages ni dénominateur. Un même bloc peut être
déclaré explicitement partenaire des deux marqueurs. Ces identifiants ne sont
pas des gènes humains calibrés. Tous les blocs, y compris sélectionnés, restent
dans la mesure totale I11 ; les partenaires ont des diagnostics distincts.

`run_selected(haplotypes, sex, mt, y, recombination_map=..., selection=...,
generations=..., seed=..., max_rounds=200)` retourne des tableaux finaux possédés
et un rapport JSON. Les mâles portent Y=0/1 ; les femelles Y=−1 ; sex et mt
sont binaires. Toutes les déclarations sont validées avant création du RNG.
Les mécanismes X, drive, sélection autosomale directe, DMI SI3 génériques,
stérilité F1, second pulse et démographie variable ne font pas partie de cette
API ; aucun objet Config M2 n'est accepté ou partiellement ignoré.

## Reproduction, hasard et limites d'exécution

Chaque génération réserve les places des fils puis des filles selon les quotas.
Pour les places en attente : tirage uniforme avec remise des mères, puis des
pères, transmission I12 des deux gamètes, mtDNA maternel et Y paternel chez les
fils (−1 chez les filles). Si un coefficient est non nul, un tirage uniforme par
proposition décide sa survie. Les places rejetées sont reproposées avec les
mêmes sexes depuis les **parents de la génération précédente** ; les survivants
partiels ne deviennent jamais parents dans cette génération.

Ce rejet réalise la reproduction conditionnelle à la survie et au sexe, comme
M2, mais avec un ordre de tirages propre : aucune parité des trajectoires RNG
sélectionnées avec M2 n'est revendiquée. À coefficients tous nuls, aucun tirage
de survie n'a lieu ; les tirages et blocs sont exactement ceux d'I13. Les
annotations de partenaires n'activent pas la sélection. Le RNG est local.

Après `max_rounds` lots insuffisants dans une génération, `ReproductionFailure`
porte un rapport avec horizon complété, génération échouée et coûts, et
`final_measurement=null`. La génération partielle n'est pas comptée comme
produite. Cela peut refléter une faible viabilité ou une incompatibilité totale :
le statut n'affirme pas une extinction biologique certaine. Aucune valeur
partielle ne devient une statistique finale ; aucun filtrage des échecs en
succès n'est permis. Le moteur n'écrit aucun fichier.

## Traçabilité et coûts

Le format `selected-autosomal-block-simulation-v1` conserve configuration, carte,
versions I11/I12, NumPy, générateur, graine, dimensions, quotas et horizon.
Les empreintes SHA-256 portent sur les octets C des états initiaux normalisés :
blocs, sexe et mtDNA en uint8, Y en int8. Le caller doit conserver ces états
pour rejouer ; les empreintes seules ne permettent pas leur reconstruction.
Les mesures initiale et finale I11 ont chacune leur génération explicite.

`candidates_generated` compte tous les candidats ; `accepted_candidates` compte
les survivants, y compris ceux d'une génération finalement échouée ;
`offspring_generated` compte seulement N × générations complètes.
`block_copy_transmissions=2*B*candidates_generated` inclut les rejets.
`state_allele_entries=2*N*B` décrit une population, pas le pic des allocations.
Sans historique, la mémoire du moteur est O(N*B) ; le temps dépend des rejets
et est borné par O((generations*max_rounds+1)*N*B). Ces unités ne mesurent pas
le temps matériel et n'affirment pas une calibration du Ne réalisé.

Cette étape avance M3 D1/D2/D4/D9/D10 sans les clore : les scénarios nommés sont
exercés par tests, mais la CLI utilise encore sa métrique historique. Modes
`quick`/`adaptive`, événement conjoint et convergence sélectionnée restent
ouverts. La résolution principale et la carte empirique restent des décisions
ouvertes, sans bloquer ce moteur paramétrable. M1 D8/D9 restent également ouverts.

## Exemple synthétique exécutable

Depuis `reich_experiment_v2/`, dans l'environnement Nix :

```python
import numpy as np
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.selected import BlockSelection, run_selected

panel = BlockPanel('synthetic-eight', tuple(f'b{i}' for i in range(8)))
mapping = RecombinationMap(panel, (0.1,)*7)
initial = np.zeros((40, 2, 8), dtype=np.uint8)
initial[[0, 20], :, :] = 1
sex = np.array([1]*20+[0]*20, dtype=np.uint8)
mt = initial[:, 0, 0].copy()
y = np.where(sex == 1, mt.astype(np.int8), -1).astype(np.int8)
selection = BlockSelection(s_mt=0.0032, s_y=0.0013,
                           mt_partner_block='b0', y_partner_block='b1',
                           mt_arch_nuc_mod=0.01, y_arch_nuc_mod=0.01)
result = run_selected(initial, sex, mt, y, recombination_map=mapping,
                      selection=selection, generations=10, seed=17)
assert result.report['generations_completed'] == 10
assert result.report['final_measurement']['allele_copy_denominator'] == 640
assert result.report['final_measurement']['status'] == 'evaluated_at_target'
```

Cette carte et cet horizon illustrent l'API ; ils ne sont pas une calibration
humaine ni une mesure d'ascendance à 50 ka.

## Vérification du 25 octobre 2026

Depuis `reich_experiment_v2/`, les quatre commandes de
[l'issue I15](../issues/I15-simulate-selected-autosomal-blocks.md) réussissent
sous Nix : **11 tests ciblés, 43 autosomaux, 35 pulse, 120 complets**.
L'exemple ci-dessus a également été extrait du document et exécuté sous Nix
avec ses trois assertions réussies.

Correspondance des preuves dans `tests/test_autosomal_selected.py` :

| DoD I15 | Preuves |
| --- | --- |
| ID1 | `test_viability_matches_analytical_tables_and_m2` : 1 458 viabilités comparées aux tables indépendantes et à M2, avec signes mt/Y et trois dominances ; `test_each_reciprocal_term_in_isolation_and_y_sex_mask` : 432 cas isolés, coefficients 1 inclus. |
| ID2 | `test_parents_markers_and_gametes_are_consistent_for_each_proposal` observe les parents et candidats, quotas pairs/impairs ; `test_preregistered_offspring_selection_and_linked_ancestry` valide les proportions 0, 1/2, 1/2 et les blocs liés sur les trois graines préfixées. |
| ID3 | `test_zero_selection_matches_i13_with_and_without_partner_annotations` couvre 48 configurations N/B/carte/graine, chacune avec deux déclarations partenaires, sur cinq générations. |
| ID4 | `test_named_scenarios_keep_the_same_measurement_panel` exerce tous les scénarios du dictionnaire courant, trois dominances et cartes nulle/active, sur quatre générations. |
| ID5 | `test_repeatability_owned_states_json_provenance_and_work` reconstruit configuration/carte depuis le JSON et rejoue avec les états initiaux ; cas d'horizon nul, absorption, entrées invalides et échecs de reproduction partiels/tardifs. |
| ID6 | Les quatre suites Nix ci-dessus et l'exemple documenté passent ; aucune assertion antérieure n'a été changée. |

Les lignes adversariales du test isolé (Y=0/1 chez des femelles, ou −1 chez des
mâles) interrogent seulement le masque de la fonction interne de viabilité :
elles ne sont pas des états biologiques acceptés par `run_selected`. La parité
M2 est vérifiée sur les génotypes valides. Le test d'échec tardif force la
viabilité par fixture pour contrôler la comptabilité ; l'échec limité aux fils
provient réellement d'une sélection Y de coefficient 1 avec tous les pères Y=0.

Les graines, proportions et tolérances du contrôle de sélection sont restées
inchangées après exécution. Les moteurs, tests antérieurs, observations, scores
et fichiers milestone restent inchangés. Les travaux I14 préexistants restent
présents sans modification. Aucun commit ni push n'a été effectué.
