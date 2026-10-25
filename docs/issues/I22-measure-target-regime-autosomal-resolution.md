# I22 — Mesurer le diagnostic autosomal au régime démographique cible

Milestone: M3
Advances: D8, D9, D10 ; objectif O4
Depends on: I18, I19, I21 ; résolution principale et convergence non établies

## Objective

Archiver un premier diagnostic multirésolution intégral à N=1450 et 6993 générations avec le runner I21. Mesurer écarts et coûts au régime cible afin de documenter les limites du petit contrôle I18, sans sélectionner une résolution sur ces seuls résultats.

## Repository Grounding

- `reich_experiment_v2/study_autosomal_resolution.py` accepte un plan versionné et conserve tous les réplicats, contrats I19, intervalles et compteurs de travail.
- `docs/science/autosomal-selected-resolution-report.json` porte sur N=40 et 20 générations ; aucun diagnostic archivé de résolution à l'horizon cible n'est présent.
- Le runner utilise des partenaires aux extrémités d'un segment abstrait et des blocs de poids égaux ; le poids sélectionné varie avec la résolution.
- Le protocole I21 trace les choix mais ne fournit ni scellement temporel, ni critère d'équivalence, ni calibration humaine.

## Change Scope

### Inspect

- `docs/science/autosomal-resolution-plan.md` — format et limites du plan.
- `docs/science/autosomal-selected-resolution-protocol.md` — carte, statistiques et interprétation I18.
- `reich_experiment_v2/tests/test_autosomal_resolution_plan.py` — provenance et rejeu existants.

### Expected change paths

- `docs/science/autosomal-target-regime-plan.json` (new) — plan fixe avant résultats.
- `docs/science/autosomal-target-regime-report.json` (new, generated) — résultats bruts et agrégés.
- `docs/science/autosomal-target-regime-diagnostic.md` (new) — résultats, coût, limites et vérification.
- `reich_experiment_v2/tests/test_autosomal_target_regime.py` (new) — intégrité scientifique des artefacts archivés.

## Required Changes

1. Déclarer avant exécution N=1450, f=0.05, fraction masculine=0.5, 6993 générations, étendue L=1, résolutions 8/32/128, graines 520000/520001 et scénarios `neutral`, `reich_point`, `reich_plus_symmetric_1pct`. Conserver le plan et ses empreintes, sans ajustement après observation.
2. Exécuter sous Nix les 18 évaluations full sans filtrer les échecs ou les résultats nuls. Conserver les conventions I18/I21, paramètres réalisés, état initial arrondi, horizons, cartes, contrats, incertitudes et coûts.
3. Vérifier la cohérence des artefacts avec le plan et les données individuelles : échantillonnage sans remise, cible inclusive 3–7 %, agrégats, différences, dénominateurs et coûts. Rejouer directement une trajectoire archivée à chacune des trois résolutions dans le même environnement.
4. Rapporter les écarts observés et la précision disponible. Un petit lot, un zéro ou un intervalle contenant zéro ne démontrent ni équivalence ni impossibilité biologique. Maintenir la convergence non établie et distinguer coûts logiques et durée matérielle.

## Constraints and Non-goals

- Aucun changement du moteur, des observations, des récompenses, des estimateurs, des anciens plans ou archives.
- Aucun choix de résolution principale, calibration humaine, étude exhaustive des scénarios ou clôture M3.
- La réussite de l'Issue dépend de la vérification du diagnostic, pas d'une amélioration des scores.

## Definition of Done

- [x] ID1 Le plan fixé est inchangé ; le rapport contient exactement les 18 évaluations attendues, toutes à l'horizon déclaré.
- [x] ID2 Les tests d'intégrité relient protocole, réplicats, statistiques et coûts ; les altérations significatives sont détectées.
- [x] ID3 Une trajectoire réelle par résolution est rejouée à l'identique et la provenance d'implémentation est vérifiée.
- [x] ID4 Le diagnostic documente résultats et limites sans valider la convergence ; les tests ciblés, autosomaux et complets passent sous Nix.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python study_autosomal_resolution.py --plan ../docs/science/autosomal-target-regime-plan.json --output ../docs/science/autosomal-target-regime-report.json
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_target_regime.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Le rejeu long est exécuté séparément pour éviter de le répéter dans chaque
suite ; sa commande et ses preuves figurent dans le diagnostic.

Preuves (25 octobre 2026) : génération terminée avec code 0 et 18 évaluations
sans exclusion ; le plan conserve son empreinte avant/après (ID1). Les trois
tests ciblés vérifient la cohérence scientifique et détectent neuf altérations
(ID2). Les onze empreintes d'implémentation concordent et trois trajectoires
sélectionnées sont rejouées à l'identique, coûts inclus (ID3). Les suites ciblée,
autosomale et complète retournent 0 avec **3/88/165 tests** ; résultats et limites
figurent dans le [diagnostic](../science/autosomal-target-regime-diagnostic.md)
(ID4). Aucun moteur, ancien fichier ou milestone modifié. Les quatre DoD sont
vérifiés ; la convergence et le protocole principal M3 restent non établis.
