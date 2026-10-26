# Évaluation pulse pondérée — I27 / M3

L'API `paleogen_rl.genetics.pulse.evaluate_block_pulse` accepte désormais
`measurement_panel`, le panel pondéré explicite d'I25/I26. Elle l'achemine
dans chaque passe du moteur, y compris la continuation adaptive. Les mêmes
identifiants et ordre de blocs doivent figurer dans la carte et le panel ;
une incompatibilité est refusée avant simulation.

## Versions et critère évalué

Sans panel, les versions et résultats I16/I17 restent inchangés. Avec panel :

| Mode | `evaluation_version` |
| --- | --- |
| full | `weighted-block-pulse-evaluation-v1` |
| quick / adaptive | `weighted-block-pulse-evaluation-v2` |

Chaque évaluation pondérée exporte `measurement_panel`, avec poids bruts,
poids normalisés et justification. Les mesures du moteur suivent I25 et ses
unités ; les rapports moteur suivent I26. Un consommateur doit prendre en
compte ces versions avant toute comparaison avec la mesure I11 à poids égaux.

Le calcul conserve `P10 * indicatrice(0.03 <= A <= 0.07)`, avec A l'ascendance
pondérée explicitement demandée. La règle d'échantillonnage sans remise, les
seuils et les paramètres reproductifs sont inchangés. Les poids ne changent
aucun tirage ni mécanisme de sélection ; ils changent la définition déclarée
de A. Cette observable ne remplace pas implicitement celle des sorties existantes.
Une comparaison de candidats doit fixer le même contrat de mesure.

## Disponibilité et horizon

- Full exige l'horizon complet et une mesure finale de la version et du panel
  attendus. Une mesure incomplète ou d'un autre panel est refusée.
- Quick conserve mesure finale, cible et critère conjoint indisponibles, même
  à horizon atteint. Les poids sont présents dans ses métadonnées.
- Adaptive conserve l'écran I17. Si P10=0, l'ascendance n'est pas évaluée et le
  critère conjoint vaut zéro. Sinon, il rejoue full avec la même graine et les
  mêmes poids, sans retirer la sélection après absorption. L'ascendance finale
  et le critère conjoint doivent coïncider avec full.

Les modes anticipés déclarent `stopping_ancestry_diagnostic`, calculé avec les
poids sur l'état au point d'arrêt. Ce diagnostic contient génération réelle,
version, observable et statut `stopping_state_diagnostic_not_final`. Il peut
être numérique alors que `ancestry_measurement['value']` reste nul : il ne doit
jamais servir à attribuer une réussite à l'horizon final. La mesure initiale
reste elle aussi distincte de la mesure finale.

Les coûts propres à l'écran et à la continuation sont cumulés sans additionner
la taille d'état pour prétendre mesurer un pic mémoire. Un échec reproductif
se propage avec sa configuration pondérée et ses coûts. Si la continuation
échoue, `total_work_units` inclut les coûts de l'écran, dont le rapport est
conservé ; aucune évaluation de réussite n'est retournée. Les seules
continuations ne permettent pas d'estimer l'ascendance marginale de toutes
les trajectoires.

## Exemple synthétique

Depuis `reich_experiment_v2/` :

```python
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.selected import BlockSelection
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel
from paleogen_rl.genetics.pulse import evaluate_block_pulse

blocks = BlockPanel('synthetic-weighted-pulse', ('mt', 'middle', 'y'))
arguments = dict(population_size=40, f=0.5, male_fraction=0.5, generations=4, seed=17,
                 recombination_map=RecombinationMap(blocks, (0.1, 0.1)),
                 selection=BlockSelection(mt_mod_nuc_arch=0.01, mt_partner_block='mt', y_partner_block='y'),
                 measurement_panel=WeightedBlockPanel(blocks, (1, 18, 1), 'synthetic example; no empirical calibration'))
reports = {mode: evaluate_block_pulse(**arguments, mode=mode) for mode in ('full', 'quick', 'adaptive')}
assert reports['quick']['ancestry_measurement']['value'] is None
assert reports['quick']['target']['joint_and_target'] is None
assert reports['adaptive']['target']['joint_and_target'] == reports['full']['target']['joint_and_target']
```

Le panel, les coefficients et la courte démographie de cet exemple sont
synthétiques. Ils ne constituent pas un protocole principal v0.1 ni une
simulation historique calibrée.

Pour rejouer depuis un rapport JSON : reconstruire le panel pondéré à partir
de `measurement_panel`, la carte et `BlockSelection` depuis `engine_report`,
les paramètres du pulse depuis `initialisation`, et reprendre graine/horizon
du moteur. Réutiliser le mode racine, ou full pour le format intégral. Les tests
vérifient ce rejeu dans les trois modes.

## Plan des contrôles et limites

La matrice réelle fixe N=40, horizon=4, graine 17, 17 scénarios nommés, trois
dominances, deux cartes uniformes 0/0.1 et trois fractions 0/0.5/1 : **306
configurations** comparant full/quick/adaptive avec les mêmes poids 1/18/1.
Les marqueurs et coûts full sont aussi comparés au chemin non pondéré.

Les tests analytiques de borne utilisent des états initiaux contrôlés à N=100
et horizon zéro, avec poids 1/2/1. Un nombre de copies du premier bloc de
23/24/25 ou 55/56/57 donne exactement A=copies/800 ; les bornes 0.03/0.07 et
les valeurs voisines sont vérifiées. P10 est recalculé par combinaisons sur
20 mâles doubles modernes parmi 50, distinctement d'une fixation.

Douze contrôles positifs utilisent une fixture monomorphe par bloc : premier
bloc moderne, autres archaïques, marqueurs modernes fixés et poids 1/18/1,
soit A≈0.05. Trois graines, deux cartes et deux intensités de sélection
vérifient le critère positif et le maintien de sélection après absorption.
Cette fixture rend la branche de continuation testable ; elle n'est ni une
nouvelle observation ni un choix de paramètres scientifiques optimisé.

Les erreurs de continuation sont injectées pour vérifier propagation et cumul
de coûts ; des échecs reproductifs réellement exécutés complètent ces contrôles.
Les rapports incohérents, panels incompatibles, poids égaux et absence de panel
sont également couverts. Ces preuves sont distinctes d'une étude de convergence.

La CLI, I19, les lois du moteur, observations et archives ne changent pas dans
I27. Famille de cartes/raffinements, contrat pondéré versionné pour les entrées,
exposition CLI et convergence restent à établir ; M3 D1 reste ouvert.

Validation de [I27](../issues/I27-evaluate-weighted-pulse-modes.md),
26 octobre 2026 : les quatre commandes retournent 0 avec **8 tests ciblés,
9 tests des modes existants, 117 tests autosomaux et 194 tests complets**,
sans échec ni test ignoré.

| DoD I27 | Preuve dans `tests/test_autosomal_weighted_pulse.py` |
| --- | --- |
| ID1 | Panels incompatibles refusés avant moteur ; versions et déclaration dans chaque mode, poids conservés pendant la continuation, compatibilité avec `None` et poids égaux. |
| ID2 | Six états analytiques aux bornes et valeurs voisines, mesures réelles à horizon zéro et P10 recalculé par combinaisons ; fixture positive distinguant mesure pondérée et mesure I11. |
| ID3 | 306 configurations réelles avec accord full/adaptive, marqueurs et coûts contrôlés ; douze contrôles positifs, diagnostic pondéré intermédiaire identifié, erreurs de mesure, échecs réels et continuation échouée contrôlée. |
| ID4 | Les quatre suites passent ; rejeu JSON des trois modes et exemple documentaire exécuté sous Nix. |

Le code Python de l'exemple a été extrait de ce document et exécuté. Full
déclare une cible non satisfaite et un critère conjoint nul ; quick conserve
le critère indisponible ; adaptive déclare `skipped_event_impossible`, avec
critère conjoint nul et ascendance finale non évaluée. Aucun de ces résultats
synthétiques ne valide un modèle historique.

Environnement relevé : Linux x86_64, Python 3.14.8, NumPy 2.5.3. Le verrou Nix
conserve son SHA-256
`a52bdf3a3b9a069175d3af298234c3cf7adeba54540833eed6ad902e9ccc0a64`.
Le plan et le rapport I22 conservent leurs empreintes
`f400cc547acae4143b352013fb68d14c625d1f888e0b60e8d919d2131f65bb10`
et `99cd8cf191a92651cb413edbce10a01502257eaaf6c6b49dd64fa3a85085affd`.
Structure et taille de l'Issue, liens, syntaxe, espaces et `git diff --check`
sont vérifiés. Aucun fichier collatéral, moteur, CLI, contrat I19, observation,
seuil, récompense existante ou archive n'est modifié. Aucun blocage ne subsiste
pour I27 ; le milestone et son statut global restent inchangés.
