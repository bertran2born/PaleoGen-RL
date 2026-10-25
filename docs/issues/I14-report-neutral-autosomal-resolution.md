# I14 — Rapporter la sensibilité neutre à la résolution autosomale

Milestone: M3
Advances: D8, D9 (contrôle neutre) ; objectifs O4/O2
Depends on: I11–I13 ; validation technique M2 présente, M1 D8/D9 ouverts

## Objective

Produire un rapport rejouable comparant au moins trois résolutions croissantes du contrôle neutre. Quantifier les écarts de fréquence finale et de probabilité dans 3–7 %, avec incertitude Monte Carlo et coût déclaré, sans choisir rétroactivement une résolution principale.

## Repository Grounding

- `reich_experiment_v2/paleogen_rl/genetics/neutral.py::run_neutral` simule un panel à horizon intégral et fournit mesures I11, carte I12, empreintes et unités de travail.
- `reich_experiment_v2/tests/test_autosomal_neutral.py` valide la moyenne neutre sur huit blocs ; aucune comparaison multirésolution n'est fournie.
- `docs/science/autosomal-neutral-protocol.md` déclare explicitement la convergence et l'intégration aux scénarios hors du périmètre I13.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/ancestry.py`, `inheritance.py`, `neutral.py` — mesure, carte et moteur réutilisables.
- `reich_experiment_v2/tests/test_autosomal_neutral.py` — population synthétique et conventions.
- `docs/milestones/M3-comparable-autosomal-ancestry.md` — coûts et limites attendus.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/resolution.py` (new) — étude neutre et export JSON explicite.
- `reich_experiment_v2/tests/test_autosomal_resolution.py` (new) — contrôle des comparaisons, rejeu et erreurs.
- `docs/science/autosomal-resolution-protocol.md` (new) — protocole fixé avant exécution, résultats et limites.
- `docs/science/autosomal-resolution-report.json` (new, generated) — résultats reproductibles du protocole.

## Required Changes

1. Comparer des panels croissants sur la population synthétique équilibrée I13, au même horizon intégral, avec le même lot de graines explicites et une étendue de recombinaison synthétique constante. Déclarer comment la carte varie avec la résolution ; ne pas conserver arbitrairement une même probabilité par frontière.
2. Conserver tous les réplicats, leurs graines et mesures finales. Rapporter moyenne d'ascendance, fréquence inclusive dans 3–7 %, incertitudes et écarts entre résolutions ; les bornes statistiques et paramètres sont documentés avant exécution.
3. Fournir version, provenance numérique, initialisation, cartes, dimensions et coûts logiques par résolution et cumulés. L'export JSON refuse une destination existante et ne nécessite aucune ressource tierce.
4. Tester les calculs sur des cas analytiques, leur accord avec des simulations directes I13, la répétabilité, les entrées invalides et la protection des sorties. Exécuter et archiver l'étude sous Nix, sans seuil de convergence choisi après lecture des résultats.

## Constraints and Non-goals

- Aucun changement des moteurs historiques, observations, récompenses ou graines existantes.
- Pas de sélection/DMI, calibration empirique, temps matériel, intégration pulse ou choix d'une résolution scientifiquement suffisante.
- Ne pas cocher les critères globaux M3 sur la seule base de cette étude neutre synthétique.

## Definition of Done

- [x] ID1 Trois résolutions croissantes partagent population, horizon, graines et étendue déclarée ; cartes et mesures finales sont traçables.
- [x] ID2 Les statistiques, bornes et écarts incluent tous les réplicats et sont vérifiés sur cas analytiques et simulations directes.
- [x] ID3 Le rapport JSON reproductible déclare provenance et coûts par résolution/cumulés ; les entrées invalides et l'écrasement sont refusés.
- [x] ID4 L'étude fixée avant exécution est archivée avec ses résultats et limites, sans proclamation de convergence globale.
- [x] ID5 Tests ciblés, autosomaux, pulse et complets réussissent sous Nix.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_resolution.py'
nix develop -c python -m paleogen_rl.genetics.resolution --output ../docs/science/autosomal-resolution-report.json
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : commandes ci-dessus réussies, **7/32/35/109 tests**
respectivement ; génération du rapport : code 0. Les tests de carte et rejeu
direct I13 vérifient ID1 ; cas analytiques, cibles inclusives, Wilson aux
extrêmes et différences vérifient ID2. JSON strict, répétabilité, empreintes,
coûts, erreurs et refus d'écrasement vérifient ID3. Une seconde exécution de
`run_resolution_study()` est identique au JSON archivé. Le protocole préfixé et
ses résultats documentés vérifient ID4 ; les quatre suites Nix vérifient ID5.
Contrôles de whitespace réussis sur les cinq nouveaux fichiers. Aucun fichier
préexistant ni milestone modifié ; aucun commit ni push effectué.
