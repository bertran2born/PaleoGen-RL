# I5 — Vérifier les trajectoires reproductibles du pulse de référence

Milestone: M2
Advances: D1, D2, D3, D10 (partiellement)
Depends on: I1–I3 ; M1 D8/D9 restent ouverts, démarrage de M2 demandé explicitement

## Objective

Vérifier la parité des populations simulées, génération par génération, entre la référence locale et son extension à pénalités nulles. Démontrer aussi la répétabilité des sorties publiques, sans changer les flux aléatoires.

## Repository Grounding

- `reich_experiment_v2/tests/test_pulse.py` compare les statistiques finales, mais pas les populations successives.
- `reich_experiment_v2/src/epi_pulse.py::run_extended` emploie `_init` et `_step` du moteur original ; les quatre pénalités nulles désactivent la nouvelle sélection.
- `Config` contient dominance, arrêt à absorption et graine. La CLI expose `neutral` et `reich_point`, avec résultats CSV/JSON et durée variable.
- M1 reste incomplet sur les rapports et leur validation globale. Les contrats scientifiques et sources I1–I3 nécessaires à cette vérification sont présents.

## Change Scope

### Inspect

- `docs/milestones/M2-pulse-reference-parity.md` — invariants de parité et reproductibilité.
- `reich_experiment_v2/src/reich_panmictic_original.py` — primitives et statistiques de référence, en lecture seule.
- `reich_experiment_v2/src/epi_pulse.py` et `reich_experiment_v2/run_experiment.py` — extension et scénario public.
- `reich_experiment_v2/tests/test_pulse.py` — couverture existante à conserver.

### Expected change paths

- `reich_experiment_v2/tests/test_pulse_reference.py` (new) — matrice de parité, répétabilité et contrôles de non-contamination.
- `docs/science/pulse-reference.md` (new) — protocole, cas vérifiés et portée des preuves.

## Required Changes

1. Comparer exactement les états initiaux puis chaque population produite par `_step`, sans tirage RNG supplémentaire. Matrice fixée : graines 0, 17, 42 ; fréquences 0, 0.05, 1 ; scénarios neutre et sélectionné `reich_point` ; trois dominances ; arrêt à absorption activé/désactivé. Documenter taille et horizon courts.
2. Comparer les statistiques partagées avec le moteur original et recalculer indépendamment, depuis la population finale, les indicateurs ajoutés de l'extension, dont la probabilité sans remise des dix mâles. Inclure un cas polymorphe où cet événement reste possible sans fixation.
3. Vérifier la répétabilité à configurations/graines identiques, y compris après épistasie active ou erreur pendant celle-ci ; le moteur suivant ne doit pas être contaminé.
4. Exécuter deux fois chaque scénario CLI vers des destinations temporaires distinctes ; comparer CSV et statistiques JSON, hors destinations et durées variables. Distinguer cette vérification locale d'une reproduction des probabilités intégrées du préprint.

## Constraints and Non-goals

- Aucun changement du moteur original, des sorties archivées, du score ou des paramètres par défaut.
- Ne pas étendre cette preuve à l'identité des autosomes après accélération : cette optimisation peut changer le flux RNG.
- Ne pas clôturer M1 ni M2 dans cette Issue ; les sorties enrichies et la sémantique complète des modes restent hors périmètre.

## Definition of Done

- [x] ID1 La matrice documentée compare exactement chaque population et les statistiques partagées.
- [x] ID2 Les indicateurs supplémentaires concordent avec un calcul indépendant ; un événement des dix mâles positif sans fixation est couvert.
- [x] ID3 Les tests démontrent répétabilité et restauration du moteur après épistasie active, y compris sur erreur.
- [x] ID4 Deux exécutions CLI de chaque scénario donnent des résultats identiques hors métadonnées explicitement variables.
- [x] ID5 Les tests ciblés, les tests pulse existants et la suite complète réussissent sous Nix.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_pulse_reference.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (24 octobre 2026) : 4 tests ciblés réussis, dont matrice de 108 configurations,
calcul combinatoire, restauration sur erreur et répétabilité CLI ; 14 tests pulse
et 56 tests complets réussis. Aucun moteur modifié.
