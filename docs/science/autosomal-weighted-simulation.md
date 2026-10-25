# Mesure pondérée du moteur sélectionné — I26 / M3

I26 rend la primitive [I25](autosomal-weighted-measurement.md) utilisable par
`paleogen_rl.genetics.selected.run_selected`. Les poids servent exclusivement
au calcul de la mesure sur les états produits. Ils ne modifient ni sélection,
ni transmission, ni tirages, ni arrêt sur absorption, ni compteurs de travail.
Ils ne sont pas une nouvelle hypothèse de viabilité.

## Activation explicite

L'argument optionnel `measurement_panel` doit être un `WeightedBlockPanel`
dont le `BlockPanel` est exactement celui de `recombination_map`, identifiant
et ordre inclus. Un type, nom ou ordre incompatible est refusé avant création
du RNG. Les règles I25 valident les poids et leur justification lors de la
construction du panel.

Sans cet argument, ou avec `None`, le moteur conserve les mesures I11 à poids
égaux et les champs de rapport existants. Les adaptateurs pulse, la CLI et
les contrats I19 n'activent pas cette option. Le mode adaptive appartient
à l'adaptateur pulse et n'est pas intégré à la pondération dans cette Issue.

Exemple **synthétique**, depuis `reich_experiment_v2/` :

```python
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.pulse import initialise_pulse
from paleogen_rl.genetics.selected import BlockSelection, run_selected
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel

blocks = BlockPanel('synthetic-weighted-run', ('mt', 'middle', 'y'))
mapping = RecombinationMap(blocks, (0.1, 0.1))
weighted = WeightedBlockPanel(blocks, (2, 4, 2), 'synthetic example; no empirical calibration')
state, _ = initialise_pulse(population_size=40, f=0.5, male_fraction=0.5, panel=blocks)
selection = BlockSelection(mt_mod_nuc_arch=0.01, mt_partner_block='mt', y_partner_block='y')
result = run_selected(**state, recombination_map=mapping, selection=selection,
                      generations=8, seed=17, measurement_panel=weighted)
assert result.report['final_measurement']['generation'] == 8
assert result.report['final_measurement']['panel']['block_weights'] == [2.0, 4.0, 2.0]
assert result.report['work_units']['offspring_generated'] == 320
```

Ces poids et paramètres illustrent l'API ; ils ne constituent pas un protocole
principal, une carte humaine ou des coûts biologiques validés.

## Rapport, unités et rejeu

Avec pondération, le rapport ajoute :

- `report_version=weighted-selected-autosomal-block-report-v1` ;
- `measurement_panel`, déclaration complète I25 avec poids bruts, poids
  normalisés et justification.

`measurement_version` devient `weighted-autosomal-block-measurement-v1`.
`initial_measurement` et `final_measurement` suivent cette version et son
observable distincte. Les masses pondérées et les dénominateurs ne sont pas
des comptes bruts ; ceux-ci restent des diagnostics séparés, comme dans I25.
L'initialisation est mesurée à génération/horizon zéro. La mesure finale full
doit être à l'horizon demandé.

La version de simulation reste `selected-autosomal-block-simulation-v1` :
la dynamique reproductive ne change pas. La sélection réalisée, carte, graine,
version NumPy, RNG, empreintes des états initiaux et coûts restent présents.
Une mesure pondérée ne doit pas être présentée comme une mesure I11 en ignorant
la version de rapport ou de mesure.

Pour rejouer, reconstruire la carte depuis `recombination_map`, un `BlockPanel`
depuis `measurement_panel['panel_id']` et `['block_ids']`, puis un
`WeightedBlockPanel` depuis ce panel, `['block_weights']` et `['weight_basis']`.
Reconstruire `BlockSelection` depuis `selection`, réutiliser les états initiaux
conservés par le caller, la graine, l'horizon et `max_rounds`. Le rapport ne
contient pas les tableaux initiaux : leurs empreintes ne suffisent pas à les
reconstruire. L'environnement numérique doit être compatible pour un rejeu exact.

## Arrêts et erreurs

`stop_when_absorbed=True` garde l'arrêt quick existant et toute la sélection.
La mesure finale pondérée reste indisponible, même à horizon atteint ou nul.
L'état initial reste une mesure initiale, distincte de la valeur finale refusée.
Les états et la génération d'arrêt sont les mêmes qu'avec les poids égaux.

Une reproduction échouée lève toujours `ReproductionFailure`. Son rapport
conserve les poids, la version de mesure, la mesure initiale, la génération
d'échec et les coûts partiels. `final_measurement` reste nul. Aucune erreur
n'est transformée en observation, en fréquence nulle ou en réussite.

## Preuves et limites

Les tests de `test_autosomal_weighted_selected.py` fixent N=40, quatre
générations, graine 17, cartes uniformes 0/0.1 et poids synthétiques 2/1/1/2.
Les 17 scénarios nommés, avec les trois dominances, donnent **102 comparaisons**.
Les tableaux finaux, marqueurs, compteurs et états RNG finaux sont comparés
exactement avec/sans pondération ; les observateurs ne tirent aucun hasard.
Les mesures sont recalculées directement à partir des tableaux initial/final.
Cette matrice n'extrapole pas une preuve à tous les environnements possibles.

Le rejeu réel utilise une configuration pondérée reconstruite depuis un rapport
JSON strict. Les tests couvrent aussi poids égaux, `None` explicite, horizons
quick 0/1/8, identité de panel invalide avant RNG et une létalité Y réelle.
Cette dernière garde 80 propositions, 20 acceptations partielles et aucune
génération complète, avec mesure finale absente et mêmes coûts que sans poids.

Cette intégration ne démontre pas une convergence entre résolutions : elle
établit que changer le calcul de mesure ne change pas la trajectoire à carte
et paramètres reproductifs fixés. Les familles de cartes/raffinements, la
cohérence des poids et partenaires entre résolutions, l'adaptateur pondéré de
pulse et son protocole versionné restent à établir. Aucune résolution
principale ni marge d'équivalence n'est choisie ; M3 D1 reste ouvert.

Validation de [I26](../issues/I26-measure-weighted-selected-trajectories.md),
25 octobre 2026 : les quatre commandes retournent 0 avec **6 tests ciblés,
11 tests de sélection existants, 109 tests autosomaux et 186 tests complets**,
sans échec ni test ignoré.

| DoD I26 | Preuve dans `tests/test_autosomal_weighted_selected.py` |
| --- | --- |
| ID1 | Panels incompatibles refusés avant RNG ; absence de nouveaux champs sans option, `None` explicite et poids égaux vérifiés. |
| ID2 | 102 comparaisons réelles : tableaux, marqueurs, compteurs et états PCG64 finaux identiques ; tous les autres champs communs des rapports sont comparés. |
| ID3 | Mesures I25 recalculées sur états initial/final, configuration reconstruite depuis JSON et rejeu réel, quick aux horizons 0/1/8 et échec reproductif réel avec coûts partiels. |
| ID4 | Les quatre suites Nix passent ; portée et limites de l'intégration documentées. |

L'exemple Python du document a été extrait et exécuté sous Nix : huit
générations atteintes, ascendance pondérée **0.521875**, **321 candidats**,
**320 descendants acceptés/produits**, **1926 copies transmises** et
**240 entrées alléliques** par état. Cette valeur illustre le comportement
synthétique demandé ; elle ne sert ni à choisir les poids ni à évaluer un
modèle historique.

`git diff --check`, structure/taille de l'Issue, liens locaux et espaces sont
vérifiés. Aucun fichier collatéral, adaptateur pulse, CLI, contrat I19,
observation, score, moteur M2 ou archive n'est modifié. Le rapport I22 garde
son SHA-256 `99cd8cf191a92651cb413edbce10a01502257eaaf6c6b49dd64fa3a85085affd`.
Aucun blocage ne subsiste pour I26 ; le milestone reste inchangé et ouvert.
