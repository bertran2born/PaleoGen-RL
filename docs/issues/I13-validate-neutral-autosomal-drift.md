# I13 — Simuler et vérifier la dérive neutre des blocs autosomaux

Milestone: M3
Advances: D4, D5, D9 (périmètre contrôle neutre) ; objectifs O2/O4
Depends on: I11, I12 ; M2 techniquement vérifié, dépendance transitive M1 D8/D9 ouverte

## Objective

Exécuter un contrôle neutre reproductible sur une population de blocs phasés, avec choix explicite des parents par sexe et mesure finale I11. Vérifier sa moyenne théorique sur un lot de graines fixé avant exécution, sans adapter le protocole aux résultats.

## Repository Grounding

- `reich_experiment_v2/paleogen_rl/genetics/inheritance.py` transmet un gamète maternel et paternel, mais laisse le choix des parents au caller.
- `reich_experiment_v2/paleogen_rl/genetics/ancestry.py` mesure un panel fixe à l’horizon déclaré ; aucun simulateur multigénérationnel de population n’existe dans ce package.
- `reich_experiment_v2/src/reich_panmictic_original.py::_step` produit `N//2` mâles puis les femelles restantes ; `_breed` choisit uniformément un père et une mère dans leurs groupes respectifs. Cette référence reste en lecture seule.
- I12 vérifie transmission et recombinaison synthétiques ; la dérive neutre et sa validation statistique restent ouvertes dans son protocole.

## Change Scope

### Inspect

- `docs/milestones/M3-comparable-autosomal-ancestry.md` — contrôle neutre, reproductibilité et coûts.
- `reich_experiment_v2/paleogen_rl/genetics/inheritance.py` et `ancestry.py` — briques existantes à réutiliser.
- `reich_experiment_v2/src/reich_panmictic_original.py` — règles parentales et quotas, en lecture seule.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/neutral.py` (new) — contrôle neutre et rapport traçable.
- `reich_experiment_v2/tests/test_autosomal_neutral.py` (new) — choix parentaux, invariants et contrôle statistique préfixé.
- `docs/science/autosomal-neutral-protocol.md` (new) — hypothèses, paramètres fixés avant test et preuves.
- `docs/science/autosomal-inheritance-protocol.md` — lien vers la validation de population.

## Required Changes

1. Accepter un état initial phasé, ses sexes, une carte I12, une graine et un horizon explicites. Conserver N diploïdes et les quotas M2 ; tirer uniformément les mères parmi les femelles et les pères parmi les mâles, sans sélection, mutation ou migration.
2. Réutiliser la transmission I12 pendant toutes les générations demandées, même aux états absorbants. Retourner l’état final indépendant des entrées et les mesures initiale/finale I11. Le seul mode de ce contrôle est intégral ; aucun critère conjoint mtDNA/Y n’est inventé.
3. Fournir un rapport JSON versionné avec graine, carte, dimensions, générations, provenance de l’état initial et unités de travail déclarées. Une annotation partenaire ne doit modifier ni reproduction ni dénominateur.
4. Valider les entrées, les quotas de sexes, la reproductibilité et les états absorbants. Vérifier la moyenne neutre pour une population initiale équilibrée entre sexes, avec intervalle Monte Carlo défini dans le protocole avant toute exécution.

## Constraints and Non-goals

- Aucun changement M2, score, observations, graines historiques ou ressources tierces ; pas d’initialisation empirique inférée.
- Pas de sélection/DMI, intégration CLI, étude de convergence ou prétention de calibrer le Ne réalisé. Les coûts déclarés sont des unités de travail, pas un benchmark matériel.
- Ne pas modifier les DoD globaux de M3 sur la seule base de ce contrôle séparé.

## Definition of Done

- [x] ID1 Parents et quotas respectent les groupes de sexes ; toutes les générations demandées sont produites avec I12.
- [x] ID2 Répétabilité, conservation des entrées, états absorbants et mesure finale I11 sont vérifiés.
- [x] ID3 La moyenne théorique appartient aux intervalles préfixés pour cartes nulle et active sur le lot de graines déclaré.
- [x] ID4 Le rapport JSON trace paramètres, état initial et unités de travail ; annotations et entrées invalides sont couvertes.
- [x] ID5 Tests ciblés, autosomaux, pulse et complets passent sous Nix ; protocole et limites sont documentés.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_neutral.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : les quatre commandes retournent 0 avec respectivement
8, 25, 35 et 102 tests. `test_autosomal_neutral.py` contrôle les groupes parentaux
et quotas pairs/impairs (ID1), répétabilité et invariants multigénérationnels
(ID2), puis les 1024 graines sur chacune des deux cartes avec intervalle de
Bernstein préfixé inchangé (ID3). Les empreintes de phase, le rejeu, le JSON,
les unités de travail, annotations et erreurs avant création RNG couvrent ID4.
Les tests M2/I11/I12 restent inchangés (ID5). Le protocole documente notamment
la limite des quotas impairs et la non-intégration aux scénarios sélectionnés.
`git diff --check` réussit ; aucun changement collatéral, moteur historique,
score, observation, ancienne assertion ou milestone modifié. M3 reste incomplet.
