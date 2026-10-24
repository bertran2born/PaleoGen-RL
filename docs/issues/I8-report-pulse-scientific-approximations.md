# I8 — Signaler les approximations scientifiques dans les résultats pulse

Milestone: M2
Advances: D9 ; objectif O4, invariant I3
Depends on: I3, I5–I7 ; M1 D8/D9 ouverts, poursuite explicite de M2

## Objective

Rendre les limites de comparaison avec les résultats publiés visibles dans les sorties scientifiques produites par la CLI. Chaque résultat doit rester identifiable comme simulation, même après extraction d’une ligne CSV ou d’une synthèse JSON hors du README.

## Repository Grounding

- `reich_experiment_v2/run_experiment.py` exporte depuis I7 configuration réalisée, modèle et chronologie, mais aucune qualification scientifique explicite des estimations ou de leurs intervalles.
- `README.md` distingue le scénario `reich_point` approximatif des probabilités intégrées du préprint ; un tirage mitochondrial ne réalise pas à lui seul cette intégration, et le coefficient Y reste fixé.
- `docs/science/observations.md` distingue observations, statistiques simulées et incertitude Monte Carlo ; le recensement n’est pas un Ne calibré et le proxy autosomal à quelques loci n’est pas une mesure génomique.
- Les overrides peuvent activer une épistasie dans un scénario nommé `neutral` ou supprimer les pénalités d’un scénario épistatique. Le nom seul ne suffit donc pas à caractériser la simulation.

## Change Scope

### Inspect

- `docs/milestones/M2-pulse-reference-parity.md` — D9 et portée des preuves de parité.
- `README.md` et `docs/science/observations.md` — limites scientifiques existantes, sans nouvelle inférence externe.
- `reich_experiment_v2/tests/test_pulse_metadata.py` — rejeu et métadonnées compatibles.
- `reich_experiment_v2/src/epi_pulse.py` — activation réelle des pénalités et proxy, en lecture seule.

### Expected change paths

- `reich_experiment_v2/run_experiment.py` — contexte scientifique des lignes CSV et synthèses JSON.
- `reich_experiment_v2/tests/test_pulse_scientific_context.py` (new) — classification, limites et invariance numérique.
- `docs/science/pulse-reference.md` — contrat des champs et preuves I8.

## Required Changes

1. Exporter dans chaque ligne CSV et chaque synthèse JSON un statut explicite de simulation exploratoire, l’absence de reproduction démontrée des résultats intégrés publiés et la portée uniquement Monte Carlo des intervalles. La parité I5 ne doit pas être présentée comme validation historique.
2. Associer des explications lisibles aux approximations du recensement/Ne, du pulse sans expansion et du proxy autosomal. Distinguer coefficient mitochondrial fixé et tirage dans un fichier fourni, sans authentifier implicitement ce fichier comme posterior SI1.
3. Signaler l’épistasie exploratoire et ses exclusions autosomales selon les coefficients effectifs, indépendamment du nom du scénario. Conserver la distinction entre contrôle neutre et référence sélectionnée, ainsi que les statuts d’évaluation I6.
4. Vérifier les trois modes, scénarios de référence et overrides inversant l’activation épistatique ; démontrer que les indicateurs et configurations restent identiques après ajout du contexte.

## Constraints and Non-goals

- Aucun changement des moteurs, paramètres, observations, seuils, graines ou intervalles.
- Aucune estimation nouvelle d’écart numérique au préprint ni affirmation de plausibilité biologique.
- Ne pas migrer les archives ni produire le rapport scientifique général de M1 ; ne pas clôturer M1/M2.

## Definition of Done

- [x] ID1 Chaque ligne CSV et synthèse JSON qualifie simulation, reproduction publiée non démontrée et incertitude Monte Carlo.
- [x] ID2 Les explications couvrent les approximations documentées et distinguent coefficient mitochondrial fixé et tiré sans authentification implicite.
- [x] ID3 Les pénalités réalisées déterminent la présence des limites épistatiques, y compris après overrides inverses.
- [x] ID4 Les tests vérifient les trois modes et l’invariance des indicateurs/configurations ; les tests ciblés, pulse et complets passent sous Nix.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_pulse_scientific_context.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (24 octobre 2026) : les trois commandes réussissent sous Nix avec
respectivement 4, 26 et 68 tests. Dans `test_pulse_scientific_context.py`,
`test_cli_context_in_all_modes_and_reference_scenarios` vérifie ID1/ID2 sur
les trois modes et trois scénarios ; `test_posterior_is_not_implicitly_authenticated`
vérifie les cas tiré/non appliqué sur une fixture synthétique ;
`test_overrides_determine_epistasis_instead_of_scenario_name` vérifie ID3.
`test_context_is_descriptive_and_does_not_change_results` compare les sorties
numériques et configurations de tous les scénarios avec contexte réel et inerte
(ID4). Les tests existants restent inchangés ; `git diff --check` réussit.
Aucun changement collatéral hors des chemins annoncés, aucun moteur ou résultat
archivé modifié. Ces preuves couvrent M2 D9 pour les nouvelles sorties CLI ;
aucun milestone n'est modifié ou déclaré achevé, M1 D8/D9 restant ouverts.
