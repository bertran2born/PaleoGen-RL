# I12 — Transmettre des blocs diploïdes phasés avec recombinaison explicite

Milestone: M3
Advances: D3, D4 (prérequis partiels), R3 ; objectif O2
Depends on: I11 ; M2 techniquement vérifié, dépendance transitive M1 D8/D9 ouverte

## Objective

Produire des descendants diploïdes à partir de blocs parentaux phasés et d’une carte de transmission déclarée. Permettre la mesure I11 et des vérifications mendéliennes pré-enregistrées sans toucher aux tirages du moteur historique.

## Repository Grounding

- `reich_experiment_v2/paleogen_rl/genetics/ancestry.py` mesure un panel fixe depuis des comptes 0/1/2, sans phase ni transmission.
- `reich_experiment_v2/src/reich_panmictic_original.py::_breed` transmet une copie maternelle et une paternelle à chaque locus autosomal indépendant ; son code reste en lecture seule.
- `docs/science/autosomal-block-measurement.md` laisse explicitement ouverts recombinaison, ségrégation, dérive, convergence et intégration CLI.
- Aucun module de transmission phasée n’existe dans `paleogen_rl/genetics/`. Déduire une phase unique des comptes diploïdes historiques serait une hypothèse injustifiée.

## Change Scope

### Inspect

- `docs/milestones/M3-comparable-autosomal-ancestry.md` — héritage, recombinaison et validations pré-enregistrées.
- `reich_experiment_v2/paleogen_rl/genetics/ancestry.py` — panel et mesure communs.
- `reich_experiment_v2/src/reich_panmictic_original.py` — rôles parentaux historiques, en lecture seule.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/inheritance.py` (new) — carte immuable, transmission et projection en comptes diploïdes.
- `reich_experiment_v2/tests/test_autosomal_inheritance.py` (new) — invariants et contrôles statistiques préfixés.
- `docs/science/autosomal-inheritance-protocol.md` (new) — hypothèses, protocole fixé avant exécution, résultats et limites.
- `docs/science/autosomal-block-measurement.md` — lien vers la brique de transmission compatible.

## Required Changes

1. Représenter explicitement les états sous forme individus × deux homologues × blocs binaires, dans l’ordre du panel I11. Fournir leur projection en comptes 0/1/2 sans reconstruire une phase depuis ces comptes.
2. Déclarer pour chaque frontière une probabilité finie de changement d’homologue dans [0,0.5]. Chaque gamète démarre sur un homologue équiprobable puis applique des changements indépendants entre blocs. Sans changement, un homologue entier est transmis ; aucune recombinaison intrabloc n’est supposée.
3. À partir d’indices maternels et paternels fournis, produire exactement un gamète de chaque parent. Le caller gère choix des parents, sexes et sélection ; le module ne les remplace pas. Utiliser exclusivement le générateur fourni, sans modifier les entrées ni consommer du hasard sur erreur de validation.
4. Sérialiser la carte et ses hypothèses. Vérifier répétabilité, origines parentales, états absorbants sur plusieurs générations, proportions mendéliennes et fréquences de changement selon le protocole préfixé. Brancher les comptes produits à la mesure I11 dans les tests.

## Constraints and Non-goals

- Aucun défaut de résolution ou carte humaine calibrée ; les probabilités sont des paramètres de modèle explicites, pas des taux empiriques inférés.
- Aucun remplacement du moteur M2, adaptation du score, intégration CLI, démographie complète, validation de dérive ou étude de convergence.
- Ne modifier ni références, observations, graines historiques ou critères 3–7 % ; ne pas cocher les DoD globaux de M3 pour cette seule brique.

## Definition of Done

- [x] ID1 Phase, carte et projection I11 sont validées ; les configurations incohérentes sont refusées avant tout tirage.
- [x] ID2 Les descendants conservent les origines maternelle/paternelle, les états absorbants et l’intégrité des homologues à recombinaison nulle.
- [x] ID3 Les contrôles mendéliens et de recombinaison passent aux graines et tolérances du protocole écrit avant exécution.
- [x] ID4 Carte sérialisable, répétabilité et absence de mutation des entrées sont vérifiées.
- [x] ID5 Tests ciblés, autosomaux, pulse et complets réussis sous Nix ; limites et non-intégration documentées.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_inheritance.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : les quatre commandes retournent 0 avec respectivement
9, 17, 35 et 94 tests. `test_autosomal_inheritance.py` vérifie projection et
erreurs sans consommation RNG (ID1), origines parentales, homologues entiers,
absence d’allèle nouveau et cinq générations absorbantes (ID2), deux familles
statistiques aux seuils préfixés inchangés (ID3), puis immuabilité, JSON et
répétabilité sans mutation des entrées ni RNG global (ID4). Les suites I11 et M2
restent inchangées (ID5). Le protocole décrit API, complexité et limites.
`git diff --check` réussit. Aucun moteur historique, score, observation, ancienne
assertion ou milestone modifié ; aucun changement collatéral. M3 reste incomplet.
