# I35 — Valider et adopter le protocole principal autosomal M3

Milestone: M3
Advances: D1, D2, D3, D4, D5, D6, D7, D8, D9, D10 ; exigence R4
Depends on: I29–I34 ; architecture, marges et budget scientifiques à fixer

## Objective

Clôturer M3 uniquement après une confirmation réelle et l'adoption du même
protocole principal pour tous les scénarios. Une conclusion insuffisante ou
négative doit laisser le milestone ouvert, sans modifier les critères.

## Repository Grounding

- Le milestone coche D2–D10 mais laisse D1 et l'acceptation scientifique ouverts.
- I31 exécute des familles I30 et conserve les réplicats full ; I32/I34 évaluent
  une équivalence simultanée sous critères explicites liés au plan.
- Les poids `(1,3,3,1)`, les marges et le budget des exemples ne sont pas
  adoptés scientifiquement. I33 ne contient qu'un chiffrage sans simulation.
- `run_experiment.py` conserve le proxy historique par défaut ; son option
  pondérée explicite n'est pas une adoption de protocole principal.

## Change Scope

### Inspect

- `reich_experiment_v2/run_experiment.py` — activation des moteurs et contexte scientifique.
- `reich_experiment_v2/study_weighted_autosomal_resolution.py` et `weighted_autosomal_equivalence.py` — confirmation et évaluation.
- `docs/science/m3-audit.md` — preuves techniques et limites historiques.

### Expected change paths

- `docs/science/m3-confirmation-plan.json` et `m3-confirmation-criteria.json` (new) — décisions et critères gelés avant résultats.
- `docs/science/m3-confirmation-report.json` et `m3-confirmation-assessment.json` (new, generated) — preuves réelles de confirmation.
- `docs/science/m3-engineering-benchmark.json` (new, generated) — mesure d'ingénierie exclue de la confirmation.
- `reich_experiment_v2/run_experiment.py` — protocole principal adopté seulement après acceptation, compatibilité historique explicite.
- `reich_experiment_v2/tests/test_m3_principal_protocol.py` (new) — invariants d'adoption, disponibilité et rejeu.
- `docs/science/m3-final-audit.md` (new) — décisions, correspondance D1–D10, limites et preuves.
- `docs/milestones/M3-comparable-autosomal-ancestry.md` — clôture conditionnelle aux preuves.

L'adoption finale est intrinsèquement transversale ; les données générées ne
comptent pas comme chemins primaires. Ne créer les plans confirmatoires
qu'après fixation des décisions scientifiques, sans convertir le gabarit I33
en protocole approuvé par simple changement d'étiquette.

## Required Changes

1. Fixer explicitement architecture, portée scientifique, quatre marges absolues,
   risque global, méthode, précision, règle d'adoption et budget. Déclarer
   un effectif fixe, les graines et tous les scénarios avant les résultats ;
   tracer le gel du plan, des critères et de l'implémentation.
2. Exécuter la confirmation à l'horizon prévu, conserver tous les résultats,
   coûts et erreurs, puis évaluer les critères déclarés. Une conclusion
   d'équivalence dans la famille finie ne doit pas devenir une convergence
   universelle ou une calibration biologique.
3. Adopter une seule définition/panel pour la métrique principale des 17
   scénarios seulement si la règle d'acceptation est satisfaite. Préserver le
   moteur de référence par une entrée historique explicite et le rejeu des
   formats existants ; tracer les preuves de contrôle de résolution.
4. Auditer chaque DoD et relancer les validations Nix. Cochement de D1 et
   statut DONE uniquement après satisfaction de leurs conditions ; sinon,
   conserver les critères ouverts et documenter le blocage sans commit partiel.

## Constraints and Non-goals

- Ne changer ni observations, cible, coefficients scientifiques ou ressources
  pour obtenir une acceptation ; ne pas réutiliser un pilote comme confirmation.
- Ne pas élargir les marges ou adapter l'arrêt aux résultats observés.
- Ne pas assimiler une étude trop petite, une variance observée nulle ou une
  suite de tests verte à une validation scientifique complète.

## Definition of Done

- [ ] ID1 Les décisions scientifiques et le budget sont explicites ; plan, critères, graines et règle d'adoption sont gelés avant confirmation.
- [ ] ID2 La confirmation réelle satisfait les critères pré-déclarés, avec rapport complet, évaluation et rejeu vérifiés.
- [ ] ID3 Tous les scénarios utilisent le protocole principal adopté ; compatibilité historique, traçabilité et non-régression sont vérifiées.
- [ ] ID4 L'audit final prouve D1–D10 et R4, les validations Nix passent et M3 est clôturé sur ces preuves.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_m3_principal_protocol.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Le premier test est à créer avec l'adoption, pas à remplacer par une découverte
vide. L'état de reprise et les blocages figurent dans l'audit final.

Reprise du 26 octobre 2026 : les contrôles existants de mesure/autosomes/suite
complète retournent 0 sous Nix (**8/164/241 tests**) ; 32 ressources de
provenance sont conformes. Un benchmark full réel, N=1450/G=6993/B=20,
scénario `reich_plus_symmetric_1pct`, graine 720000, est archivé séparément
(environ 6.70 s CPU), sans valeur confirmatoire. Les choix de portée, marges
et budget ont été demandés ; aucune réponse scientifique n'est encore
enregistrée. ID1–ID4 restent ouverts, aucun plan final ni test d'adoption
n'est inventé, M3 reste READY et aucun commit partiel n'est créé.
