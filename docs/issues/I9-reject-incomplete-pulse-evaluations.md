# I9 — Refuser les évaluations pulse interrompues par échec reproductif

Milestone: M2
Advances: D5, D7, D8, D10 ; objectifs O3/O4, invariant I1
Depends on: I5–I8 ; M1 D8/D9 ouverts, poursuite explicite de M2

## Objective

Empêcher qu’une population antérieure à l’horizon demandé soit présentée comme une évaluation finale après échec de reproduction. Distinguer cet échec d’un arrêt normal à absorption, sans changer les règles de simulation.

## Repository Grounding

- `reich_experiment_v2/src/reich_panmictic_original.py::_step` retourne `None` si un quota reproductif ne peut être rempli ; cette source tierce reste en lecture seule.
- `reich_experiment_v2/src/epi_pulse.py::run_extended` interrompt alors la boucle et conserve la population précédente. Son compteur `g+1` inclut néanmoins la tentative échouée et aucune raison de terminaison n’est fournie.
- `reich_experiment_v2/run_experiment.py::run_mode` accepte ces statistiques comme celles du passage demandé, y compris dans une continuation adaptative. Le statut `evaluated_at_target` ne vérifie pas l’horizon effectivement réalisé.
- La CLI accepte les pénalités égales à 1 : une incompatibilité complète peut rendre la reproduction impossible sans qu’il s’agisse d’une absorption des marqueurs.

## Change Scope

### Inspect

- `docs/milestones/M2-pulse-reference-parity.md` — disponibilité des mesures et génération associée.
- `reich_experiment_v2/src/reich_panmictic_original.py` — échec reproductif, en lecture seule.
- `reich_experiment_v2/tests/test_pulse_reference.py` — parité des trajectoires à conserver.

### Expected change paths

- `reich_experiment_v2/src/epi_pulse.py` — générations réellement produites et raison de terminaison.
- `reich_experiment_v2/run_experiment.py` — refus explicite des passages échoués ou incomplets.
- `reich_experiment_v2/tests/test_pulse_termination.py` (new) — échecs réels/contrôlés et exports.
- `reich_experiment_v2/tests/test_pulse_modes.py` — métadonnées de terminaison des fixtures existantes.
- `docs/science/pulse-reference.md` — contrat et preuves I9.

## Required Changes

1. Le moteur étendu doit compter seulement les générations effectivement produites et déclarer distinctement horizon atteint, absorption des marqueurs et échec reproductif. Les statistiques brutes d’une population conservée restent des diagnostics de cette population.
2. Tout mode CLI doit refuser un passage marqué comme échec reproductif. Un passage intégral, y compris la continuation adaptative, ne peut fournir une évaluation finale que si son compteur atteint l’horizon demandé.
3. Signaler le motif et la génération de l’échec par un diagnostic explicite et un code CLI non nul, sans écrire de nouveaux CSV/JSON de succès. Aucun remplacement implicite par zéro ou changement de dénominateur statistique.
4. Vérifier un échec reproductif réel dû à une incompatibilité complète, une interruption après plusieurs générations et un échec de continuation. Préserver les arrêts normaux à absorption et les trajectoires de référence réussies.

## Constraints and Non-goals

- Ne changer ni viabilité, reproduction, tirages, seuils ou paramètres ; ne pas modifier le moteur tiers.
- Ne pas contourner l’échec par de nouveaux essais, une autre graine ou des coefficients réduits.
- Ne pas migrer les archives ni clôturer M1/M2.

## Definition of Done

- [x] ID1 Le compteur exclut les tentatives échouées et les trois raisons de terminaison sont testées.
- [x] ID2 Les trois modes refusent un échec reproductif ; une continuation incomplète ne reçoit jamais le statut final.
- [x] ID3 Une incompatibilité complète réelle produit un diagnostic CLI non nul sans nouveaux fichiers résultats.
- [x] ID4 Les arrêts à absorption et les sorties de référence réussies restent compatibles ; les tests ciblés, pulse et complets passent sous Nix.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_pulse_termination.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (24 octobre 2026) : les trois commandes réussissent sous Nix avec
respectivement 7, 33 et 75 tests. `test_pulse_termination.py` vérifie ID1
aux générations zéro et trois, ID2 dans les trois modes et après continuation,
ID3 avec incompatibilité réelle sur population initiale synthétique puis avec
trois sous-processus de sélection mitochondriale létale synthétique.
Les cas normaux et la matrice de parité I5 restent validés (ID4).
Dans `test_pulse_modes.py`, les fixtures déclarent désormais leur raison de
terminaison ; le cas de divergence P10 atteint l'horizon pour isoler cette
assertion existante, conservée. `git diff --check` réussit. Aucun changement
collatéral hors des chemins annoncés, aucun moteur tiers, ressource ou résultat
archivé modifié. M2 et sa dépendance M1 restent ouverts ; aucun milestone modifié.
