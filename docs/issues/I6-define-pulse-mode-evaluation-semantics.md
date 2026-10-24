# I6 — Rendre explicite l’évaluation autosomale selon le mode pulse

Milestone: M2
Advances: D5, D6, D7 ; objectifs O3 et O4
Depends on: I5 ; contrats I1–I3 présents ; M1 D8/D9 ouverts, poursuite de M2 demandée explicitement

## Objective

Garantir que les résultats distinguent une ascendance mesurée à l’horizon demandé d’une mesure à l’arrêt précoce. Vérifier que le calcul adaptatif préserve l’événement des dix mâles et ne transforme pas une mesure non évaluée en réussite autosomale.

## Repository Grounding

- `reich_experiment_v2/run_experiment.py` vide déjà `target_auto` et `joint_and_target` en mode `quick`, mais conserve `auto_mod` sans statut explicite d’évaluation finale.
- La branche adaptative positive relance la même graine avec accélération après absorption ; la branche impossible utilise `NOT_EVALUATED_EVENT_IMPOSSIBLE`. Cette colonne finale existe dans les deux branches adaptatives, mais pas dans les modes `quick` et `full` ; le CSV prend ses colonnes dans la première ligne.
- `reich_experiment_v2/src/epi_pulse.py` fournit générations réalisées, probabilité sans remise et filtre autosomal ; l’accélération peut changer les autosomes individuels après absorption.
- I5 vérifie les trajectoires de référence ; `test_pulse.py` ne compare la continuation accélérée que sur trois graines sélectionnées.

## Change Scope

### Inspect

- `docs/milestones/M2-pulse-reference-parity.md` — invariants des trois modes.
- `reich_experiment_v2/src/epi_pulse.py` — arrêt, accélération et statistiques existantes.
- `reich_experiment_v2/tests/test_pulse_reference.py` — preuves de référence à préserver.

### Expected change paths

- `reich_experiment_v2/run_experiment.py` — résultats de mode explicites et schéma homogène.
- `reich_experiment_v2/tests/test_pulse_modes.py` (new) — contrats des modes, continuation et sorties publiques.
- `docs/science/pulse-reference.md` — sémantique des champs et portée des preuves I6.

## Required Changes

1. Exposer pour les trois modes un statut autosomal final explicite et des champs homogènes, y compris lorsque des trajectoires adaptatives positives et impossibles se succèdent. Conserver les mesures brutes et les colonnes historiques compatibles.
2. En `quick`, rendre la valeur finale indisponible et laisser vides filtre final et événement conjoint. En `adaptive`, poursuivre toute trajectoire de probabilité positive avec la même configuration/graine ; sinon laisser le filtre indisponible et l’événement conjoint nul. En `full`, utiliser la mesure finale pour les deux indicateurs.
3. Comparer l’événement mtDNA/Y adaptatif au mode intégral sur une matrice reproductible neutre/sélectionnée comprenant absence, présence totale et polymorphisme, avant et après absorption. Couvrir aussi une épistasie active et un événement possible sans fixation.
4. Tester les sorties CSV/JSON et les deux ordres des branches adaptatives, avec une mesure précoce dans 3–7 % qui ne doit pas devenir une réussite finale.

## Constraints and Non-goals

- Ne modifier ni moteurs, ni tirages, ni coefficients ou seuils scientifiques.
- Ne pas exiger l’identité des autosomes accélérés avec ceux du mode intégral.
- Ne pas enrichir ici toutes les métadonnées de M2 D8 ni clôturer M1/M2.

## Definition of Done

- [x] ID1 Les trois modes exportent un statut et une disponibilité finale non ambigus, avec schéma homogène.
- [x] ID2 Une mesure précoce dans la cible ne compte jamais comme réussite finale non évaluée ; les deux ordres adaptatifs sont couverts.
- [x] ID3 La matrice réelle documentée conserve l’événement mtDNA/Y entre `adaptive` et `full`, dont un cas positif sans fixation.
- [x] ID4 Les tests CLI vérifient les champs CSV et les statistiques JSON propres à chaque mode.
- [x] ID5 Les tests ciblés, pulse et complets réussissent sous Nix sans affaiblissement des tests existants.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_pulse_modes.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (24 octobre 2026) : les trois commandes réussissent avec respectivement
4, 18 et 60 tests. Dans `test_pulse_modes.py`,
`test_real_seeded_mode_matrix` vérifie ID1/ID3 sur 36 configurations ;
`test_controlled_early_ancestry_and_continuation` et
`test_mixed_adaptive_csv_in_both_orders` vérifient ID2 ;
`test_cli_mode_outputs` vérifie ID4 avec six appels CLI réels.
La suite complète inclut les contrôles scientifiques, de provenance et la parité
I5 sans modification des assertions existantes (ID5). Le diff ne touche aucun
moteur, ressource tierce ou résultat archivé. La portée et les champs sont décrits
dans `docs/science/pulse-reference.md`, section I6. Aucun critère du milestone
n'est modifié : M1 D8/D9 et les autres travaux de M2 restent ouverts.
