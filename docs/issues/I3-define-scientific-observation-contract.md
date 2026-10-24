# I3 — Définir et vérifier le contrat des observations scientifiques

Milestone: M1
Advances: D1, D2, D3, D9 (partiellement)
Depends on: I2 — sources scientifiques identifiées et versionnées

## Objective

Établir un contrat scientifique versionné séparant observations rapportées et statistiques de simulation. Rendre vérifiable la métadonnée indispensable à une ascendance autosomale finale, avant toute intégration ultérieure aux évaluations.

## Repository Grounding

- `docs/science/sources.json` identifie SI1 et SI3 avec leurs versions de contenu. SI1, pages 1–2, décrit l'ascendance et les paramètres démographiques ; SI3, pages 1 et 4, distingue données et échantillonnage simulé de dix mâles.
- `reich_experiment_v2/src/epi_pulse.py` calcule `p10_joint`, `joint_fixed` et `target_auto`, avec exclusion des partenaires autosomiques lorsque l'épistasie est active.
- `reich_experiment_v2/src/reich_panmictic_original.py::_stats` mesure `auto_mod` sur les copies diploïdes des loci non exclus, dans toute la population.
- `reich_experiment_v2/run_experiment.py` distingue les modes `quick`, `full` et `adaptive`, mais il n'existe pas de contrat scientifique structuré ni de validateur autonome des métadonnées autosomales.

## Change Scope

### Inspect

- `docs/milestones/M1-scientific-contract-and-provenance.md` — exigences D1–D3.
- `docs/science/sources.json` — citations et versions.
- `reich_study/media-1.pdf`, pages 1–3, et `reich_study/media-5.pdf`, pages 1–4 — preuves scientifiques locales.
- `README.md`, `reich_experiment_v2/src/epi_pulse.py` et `reich_experiment_v2/run_experiment.py` — sémantique actuelle.

### Expected change paths

- `docs/science/observations.md` (new) — contrat lisible, définitions et limites.
- `docs/science/observations.json` (new) — observations et statistiques versionnées avec citations.
- `reich_experiment_v2/science_contract.py` (new) — validateurs du contrat et d'une mesure autosomale.
- `reich_experiment_v2/tests/test_science_contract.py` (new) — cas positifs et refus observables.

## Required Changes

1. Définir séparément fixation mtDNA dans la population, fixation Y chez les mâles, événement conjoint des dix mâles sans remise et ascendance autosomale à l'horizon nominal de 50 ka. Expliciter unités, dénominateurs, formule de probabilité et hypothèses d'échantillonnage.
2. Citer précisément les sources versionnées pour chaque observation et hypothèse opérationnelle. La plage 3–7 % reste une plage rapportée, sans confiance statistique inventée. Le choix de dix mâles et l'extrapolation à la fixation populationnelle ne doivent pas être présentés comme observations directes.
3. Documenter la chronologie de référence, les tailles publiées et leur approximation dans le prototype. Préciser les jeux de huit ou six loci neutres, la sélection exclue et leurs limites de comparabilité.
4. Fournir un validateur autonome refusant une mesure finale sans génération explicite, sans loci identifiés, avec horizon incorrect, dénominateur incohérent ou valeur invalide. Il doit accepter des mesures valides de résolutions différentes, sans transformer une mesure précoce en résultat final.

## Constraints and Non-goals

- Aucune modification des moteurs, graines, paramètres, sorties historiques ou du filtre 3–7 %.
- Le validateur est un point d'entrée explicite ; la migration des sorties existantes et le score relèvent des milestones suivants.
- L'export public et la classification des rapports ne font pas partie d'I3.

## Definition of Done

- [x] ID1 Les quatre statistiques distinctes, leurs unités et leurs règles sont consignées dans un contrat versionné.
- [x] ID2 Chaque observation et hypothèse opérationnelle possède statut et citation paginée reliée à une version du catalogue I2.
- [x] ID3 Les tests refusent générations ou bases de loci absentes, horizons incorrects, loci invalides, dénominateurs incohérents et valeurs non finies/hors plage.
- [x] ID4 Les tests acceptent des mesures valides avec différents nombres de loci et vérifient les limites des modes et de l'incertitude documentées.
- [x] ID5 Les tests ciblés puis complets passent sous Nix, y compris les contrôles I1/I2 et la parité du moteur existant.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_science_contract.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (24 octobre 2026) : 10 tests ciblés, 40 tests complets réussis.
ID1/ID2 : contrat réel et citations vérifiés ; ID3/ID4 : cas négatifs,
résolutions multiples et simulation courte refusée à l'horizon 6993 ; ID5 : suite complète.
