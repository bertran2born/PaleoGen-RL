# I32 — Évaluer l'équivalence déclarée avec une précision simultanée

Milestone: M3
Advances: D1, D8, D9 ; objectif O4, exigence R4
Depends on: I31 ; marges scientifiques et protocole principal non adoptés

## Objective

Permettre de déclarer des critères d'équivalence liés à un plan I31, prévoir
leur précision puis évaluer les écarts sans réutiliser les intervalles ponctuels
comme preuve simultanée. Les marges restent des entrées explicites du caller.

## Repository Grounding

- `study_weighted_autosomal_resolution.py` conserve plan, famille et réplicats
  full, mais annonce toujours une convergence non établie.
- Ses quatre métriques et écarts à la résolution la plus fine utilisent des
  intervalles ponctuels ; aucune règle d'équivalence ou précision requise
  n'est déclarée ni évaluée.
- Les plans I31 et familles I30 sont identifiés par contenu ; les critères
  peuvent être liés au plan exact sans modifier ses graines ou paramètres.

## Change Scope

### Inspect

- `reich_experiment_v2/study_weighted_autosomal_resolution.py` — rapports, plans et aperçu.
- `reich_experiment_v2/tests/test_autosomal_weighted_study.py` — disponibilité, provenance et rejeu.
- `docs/science/m3-audit.md` — conditions d'acceptation encore ouvertes.

### Expected change paths

- `reich_experiment_v2/weighted_autosomal_equivalence.py` (new) — contrat strict, précision et évaluation.
- `reich_experiment_v2/tests/test_autosomal_weighted_equivalence.py` (new) — bornes, statuts, erreurs et intégration.
- `docs/science/autosomal-weighted-equivalence.md` (new) — définition statistique, API et limites.

## Required Changes

1. Définir des critères JSON versionnés : identifiant, empreinte du plan I31,
   risque global, marge explicite pour chacune des quatre métriques et rayon
   maximal demandé. Refuser valeurs invalides, champs inconnus/manquants/
   dupliqués et liens de plan incompatibles. Conserver identités canonique/fichier.
2. Prévoir sans simulation le nombre de comparaisons, le rayon simultané
   et l'effectif requis pour la précision déclarée. Couvrir tous les scénarios,
   métriques et résolutions comparées à la plus fine, sans hypothèse
   d'indépendance entre comparaisons ; expliciter l'indépendance des réplicats.
3. Recalculer les écarts depuis les réplicats d'un rapport I31 cohérent,
   sans faire confiance aux agrégats. Refuser panels, horizons, graines ou
   métriques incohérents. Appliquer une inclusion stricte de l'intervalle dans
   les marges et distinguer équivalence soutenue, différence détectée et
   conclusion insuffisante, dont précision insuffisante.
4. Identifier critères, plan et rapport évalué ; conserver la portée limitée
   à la famille déclarée et laisser la convergence M3 non établie. Vérifier
   les cas analytiques, les frontières, les rapports altérés et une intégration
   réelle avec I31, sans choisir de marges scientifiques principales.

## Constraints and Non-goals

- Aucun changement des moteurs, plans, runners, observations, cible ou archives.
- Aucun seuil empirique adopté, étude longue lancée ou résolution principale choisie.
- Un hash lie des déclarations ; il ne prouve ni leur antériorité temporelle
  aux résultats, ni l'authenticité d'une exécution. Documenter cette limite.
- Les résultats synthétiques de test ne sont pas une étude confirmatoire.

## Definition of Done

- [x] ID1 Critères stricts, liens au plan, instantanés et empreintes sont vérifiés.
- [x] ID2 Rayon et effectif simultanés sont vérifiés analytiquement ; aucun moteur/RNG n'est utilisé pour la prévision.
- [x] ID3 Statuts, inclusion stricte, précision et refus de rapports incohérents sont vérifiés, avec intégration I31 réelle.
- [x] ID4 Tests ciblés, autosomaux et complets passent sous Nix ; exemple exécuté, hypothèses et limites documentées.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_weighted_equivalence.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (26 octobre 2026) : les trois commandes réussissent avec
**8/153/230 tests**, sans échec ni test ignoré. ID1 : erreurs strictes,
hashes canonique/fichier, liens et copies indépendantes. ID2 : formule,
effectif minimal, multiplicité et prévision sans RNG/moteur. ID3 : frontières
strictes, rapport I31 absorbant réel à 320 graines × 3 résolutions,
petit lot non concluant, observations synthétiques contrôlées pour les autres
statuts et refus des incohérences. ID4 : suites et [exemple exécuté](../science/autosomal-weighted-equivalence.md),
8 comparaisons, effectif requis 289 pour les seules valeurs techniques de
l'exemple, statut `inconclusive_precision`. Structure, taille, syntaxe et
espaces vérifiés. Aucun fichier collatéral, runner, moteur, archive, observation
ou ressource modifié ; M3 et ses marges scientifiques restent ouverts.
