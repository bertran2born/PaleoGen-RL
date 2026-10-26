# I30 — Construire des raffinements pondérés conservant les partenaires

Milestone: M3
Advances: D1, D8 ; objectifs O1/O4, exigences R1/R2/R3/R4
Depends on: I25, I28, I29 ; convergence et protocole principal non établis

## Objective

Construire une famille reproductible d'au moins trois protocoles pondérés
emboîtés conservant poids, positions et identité des partenaires sélectionnés.
Ce préalable permet de raffiner la représentation neutre sans réintroduire
le changement de poids sélectionné des anciennes études.

## Repository Grounding

- `study_autosomal_resolution.py` génère des cartes à longueur fixée, mais
  attribue aux deux partenaires un poids total `2/B` variable avec la résolution.
- I25 valide des poids explicites ; I28 conserve carte et partenaires dans
  `WeightedAutosomalProtocol`. I29 permet d'exécuter ces contrats via la CLI.
- `inheritance.py` applique des changements d'homologue indépendants par
  frontière ; leurs probabilités composées doivent rester cohérentes aux
  positions déjà représentées.
- L'audit M3 laisse D1 et la convergence ouverts malgré les rapports D8.

## Change Scope

### Inspect

- `reich_experiment_v2/study_autosomal_resolution.py` — cartes et confondant historique.
- `reich_experiment_v2/paleogen_rl/genetics/weighted_protocol.py`, `weighted_ancestry.py` et `inheritance.py` — contrats existants.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/weighted_refinement.py` (new) — construction et provenance de famille.
- `reich_experiment_v2/tests/test_autosomal_weighted_refinement.py` (new) — conservation, cartes, erreurs et rejeu.
- `docs/science/autosomal-weighted-refinement.md` (new) — hypothèses synthétiques, API et preuves.

## Required Changes

1. Construire explicitement une famille depuis un protocole I28, un identifiant,
   une longueur de carte et des facteurs croissants de subdivision neutre.
   Conserver démographie, horizon, pulse et partenaires. Refuser les entrées
   incohérentes avant de produire une famille ; aucun moteur ni RNG ne doit
   être appelé par la construction.
2. Déclarer une géométrie synthétique explicite : les poids relatifs définissent
   des cellules contiguës sur [0,1], chaque bloc étant représenté en son centre.
   Garder les cellules partenaires intactes ; subdiviser les autres de manière
   emboîtée, en conservant leurs poids totaux et les positions déjà présentes.
3. Utiliser une carte homogène déclarée avec `r(d)=-expm1(-2*d)/2`.
   Vérifier la compatibilité du protocole de départ et la composition des
   transitions entre positions conservées. Tracer cellules, positions,
   correspondances parent/enfant et contrats I28 complets avec empreintes,
   ainsi qu'une version et une identité de contenu de la famille.
4. Vérifier conservation de la mesure sur des états dupliqués, poids/positions
   partenaires, emboîtement et transitions à carte nulle/active. Vérifier
   sérialisation, déterminisme et utilisation des protocoles produits par
   l'évaluation existante, sans revendiquer une convergence des trajectoires.

## Constraints and Non-goals

- Ne changer ni moteur, CLI, études existantes, archives, observations ou cible.
- Aucune carte humaine ou pondération empirique adoptée. Les partenaires restent
  des cellules finies sans recombinaison interne ; leur propre raffinement reste hors périmètre.
- Aucun seuil d'équivalence choisi, lancement d'étude confirmatoire ou protocole
  principal adopté ; une conservation analytique n'est pas une preuve statistique.

## Definition of Done

- [x] ID1 La famille fournit au moins trois résolutions emboîtées, validées et identifiées, avec contrats rejouables et correspondances complètes.
- [x] ID2 Poids et positions partenaires, poids totaux des cellules et mesure sur états dupliqués sont conservés dans les tolérances numériques documentées.
- [x] ID3 Cartes nulles/actives conservent les transitions composées ; erreurs, déterminisme et exécution des contrats produits sont vérifiés.
- [x] ID4 Tests ciblés, autosomaux et complets réussissent sous Nix ; exemple exécuté, hypothèses et limites documentés.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_weighted_refinement.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (26 octobre 2026) : les trois commandes retournent 0 avec
**8/139/216 tests**, sans échec ni test ignoré. ID1 : reconstruction JSON,
empreintes, instantanés indépendants et facteurs 1/3/9 et 1/3/15. ID2 :
partenaires extrêmes, intérieurs ou partagés, masse par parent et mesure
sur états dupliqués. ID3 : composition aux positions conservées, cartes de
longueur 0/0.1/2, erreurs explicites, construction sans RNG/moteur, puis
54 évaluations réelles (3 résolutions × 2 cartes × 3 graines × 3 modes).
ID4 : suites réussies et [exemple exécuté](../science/autosomal-weighted-refinement.md),
donnant 4/8/20 blocs et un poids partenaire total constant de 0.25.
Structure, taille, syntaxe et espaces vérifiés ; aucun fichier collatéral,
moteur, archive ou ressource externe modifié. M3 reste ouvert, sans mise à
jour de ses DoD ou adoption principale.
