# I18 — Comparer la résolution autosomale des scénarios sélectionnés

Milestone: M3
Advances: D8, D9, D10 ; objectifs O4/O1
Depends on: I14–I17 ; M1 D8/D9 ouverts

## Objective

Produire un diagnostic multirésolution reproductible pour les scénarios sélectionnés, complétant le contrôle neutre I14. Comparer ascendance finale, cible 3–7 % et critère conjoint avec incertitudes et coûts, sans choisir rétroactivement une résolution principale.

## Repository Grounding

- `reich_experiment_v2/paleogen_rl/genetics/resolution.py` compare 8/32/128 blocs uniquement avec `run_neutral`, sans mtDNA/Y ni sélection.
- `reich_experiment_v2/run_experiment.py::run_block_full` évalue désormais tous les scénarios nommés à horizon complet avec carte et partenaires explicites ; ses résultats contiennent le rapport I15 et le critère conjoint.
- I17 vérifie les modes sur une carte fixée, mais aucune étude multirésolution sélectionnée n'est présente.
- Les partenaires sont des identifiants de blocs : conserver leurs indices 0/1 quand B change déplacerait implicitement le second partenaire sur la carte.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/resolution.py` — statistiques et carte synthétique I14.
- `reich_experiment_v2/run_experiment.py` — scénarios, adaptateur et configuration réalisée.
- `reich_experiment_v2/paleogen_rl/genetics/pulse.py` et `selected.py` — rapports et erreurs.

### Expected change paths

- `reich_experiment_v2/study_autosomal_resolution.py` (new) — étude sélectionnée et export explicite.
- `reich_experiment_v2/tests/test_autosomal_selected_resolution.py` (new) — calculs, rejeu, cartes et erreurs.
- `docs/science/autosomal-selected-resolution-protocol.md` (new) — plan fixé avant exécution, résultats, limites et état M3.
- `docs/science/autosomal-selected-resolution-report.json` (new, generated) — résultats complets rejouables.

## Required Changes

1. Comparer au moins trois résolutions croissantes pour tous les scénarios actuels, sur la population, horizon et lot de graines déclarés avant exécution. Réutiliser le moteur intégral et les statistiques existants, sans filtrage ni changement des paramètres scientifiques historiques.
2. Définir une étendue de recombinaison constante et des positions partenaires constantes entre résolutions. Tracer carte complète, annotations et poids des blocs sélectionnés ; expliciter que leur poids 1/B est une approximation de discrétisation, pas une longueur biologique calibrée.
3. Conserver les résultats individuels, mesurer les écarts à la résolution la plus fine et fournir des intervalles Monte Carlo pour ascendance, probabilité cible et critère conjoint. Un zéro observé ne devient pas une probabilité vraie nulle et un intervalle contenant zéro ne démontre pas l'équivalence.
4. Exporter un JSON strict versionné avec configuration réalisée, graines, initialisation, provenance du code et coûts effectifs, rejets inclus. Refuser une destination existante et propager tout échec de simulation sans rapport de réussite incomplet.
5. Archiver l'étude sous Nix et vérifier son rejeu. Rapporter les preuves acquises et lacunes de M3 sans cocher les critères globaux ni annoncer une calibration ou convergence non démontrée.

## Constraints and Non-goals

- Aucun changement des moteurs, CLI existante, observations, récompenses, graines ou archives précédentes.
- Pas de nouveaux scénarios, posterior empirique, calibration du Ne, résolution par défaut scientifique ou clôture globale M3.

## Definition of Done

- [x] ID1 Tous les scénarios sont comparés à trois résolutions avec paramètres, graines, étendue et positions partenaires déclarés.
- [x] ID2 Statistiques, écarts, incertitudes et coûts concordent avec les réplicats et des évaluations directes ; cas analytiques couverts.
- [x] ID3 Le rapport versionné est rejouable, conserve la provenance et tous les réplicats, et refuse erreurs/écrasements.
- [x] ID4 L'étude archivée et son protocole documentent résultats, limites et progression M3 sans proclamation de convergence.
- [x] ID5 Tests ciblés, autosomaux, pulse et complets réussissent sous Nix.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_selected_resolution.py'
nix develop -c python study_autosomal_resolution.py --output ../docs/science/autosomal-selected-resolution-report.json
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : l'export retourne 0 et conserve **6 528 évaluations**
(17 scénarios × 3 résolutions × 128 graines), sans échec ni filtrage (ID1).
Huit tests vérifient cartes, évaluations directes, statistiques analytiques,
coûts, provenance, erreurs et protections de sortie (ID2/ID3). Une seconde
exécution CLI dans une destination temporaire reproduit le JSON **octet pour
octet**, empreintes comprises. Le protocole donne résultats et état M3 (ID4).
Les suites ciblée/autosomale/pulse/complète passent sous Nix : **8/71/35/148 tests**
(ID5). Contrôles de whitespace sans diagnostic. Aucun fichier préexistant,
moteur, observation, score, graine ou milestone modifié ; I14–I17 conservées.
Aucun commit ni push.
