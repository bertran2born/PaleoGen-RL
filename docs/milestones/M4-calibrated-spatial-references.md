# M4 — Modèles d'expansion géographique calibrés

Status: READY
Depends on: M1, M3

## Outcome

PaleoGen-RL dispose de références avec expansion géographique évaluées selon les mêmes observations finales que le métissage ponctuel. Les moteurs spatiaux de Reich conservent leurs hypothèses spécifiques, sans être artificiellement assimilés à un Wright-Fisher panmictique. Le système peut comparer leurs probabilités prédictives, domaines de paramètres admissibles et budgets de calcul.

## Objectives

- O1 — Les architectures géographiques de type deme et bande disposent d'adaptateurs exécutables et identifiables.
- O2 — Les sorties des moteurs sont projetées vers une même définition des observables scientifiques.
- O3 — Les calibrations démographiques et d'ascendance publiées sont traçables et testables.
- O4 — Les divergences entre modèles reflètent leurs hypothèses plutôt qu'une différence non déclarée de protocole.

## Scope

### In scope

- Import contrôlé des moteurs SI3 `spatial_sim2.py`, `spatial_sim3.py` et `bandsim.py` depuis l'archive originale.
- Mesures de Ne réalisé, ascendance et échantillonnage à horizon comparable.
- Adaptateurs deme/bande, petits tests d'intégration et provenance des paramètres.

### Out of scope

- Garantir une identité trajectoire-à-trajectoire entre démographies non équivalentes.
- Changement des lois de reproduction originales sans version de modèle distincte.
- Simulation continentale d'ampleur production sur chaque appel RL.

## Requirements and Invariants

- R1 — Chaque moteur possède un identifiant de version, ses paramètres propres et sa source d'origine.
- R2 — Les événements d'échantillonnage, de fixation et d'ascendance sont définis comme en M1 et M3, avec toute différence résiduelle signalée.
- R3 — Les contraintes de Ne, de fenêtre de mélange et de 3–7 % autosomal s'appliquent avant le classement final et ne sont pas ajustées sur les mêmes répétitions de test.
- R4 — Les paramètres sans homologue direct entre panmixie, demes et bandes restent explicitement distincts.
- R5 — Un test vérifie qu'une référence spatiale se comporte comme attendu sur une configuration documentée de SI3.
- I1 — Les moteurs et résultats de Reich originaux restent identifiables et inchangés.
- I2 — Un modèle recalibré est étiqueté « recalibré » et non « reproduction exacte ».
- I3 — Une référence non exécutable est affichée comme indisponible ; elle ne reçoit pas un score nul présenté comme échec scientifique.

## Relevant Repository Surfaces

- `source/mechanisms_code/README.md` — inventaire publié des moteurs et procédures SI3.
- `src/reich_panmictic_original.py` — référence sans expansion existante.
- `paleogen_rl/simulators/spatial.py` (proposed) — adaptateurs géographiques.
- `tests/test_spatial_baselines.py` (proposed) — contrôles des adaptateurs.

**Note de périmètre :** `cluster/spatial_sim2.py`, `cluster/spatial_sim3.py` et `band_model/bandsim.py` figurent dans l'archive SI3 originale fournie, mais **pas** dans le sous-ensemble `source/mechanisms_code/` du prototype v2. Leur import est une nouvelle capacité, non un état existant du dépôt.

## Definition of Done

- [ ] D1 [O1] Les trois moteurs spatiaux annoncés disposent d'un point d'exécution documenté ou d'une justification d'exclusion dans la matrice de référence.
- [ ] D2 [O1] Chaque exécution enregistre moteur, version, empreinte source et paramètres réalisés.
- [ ] D3 [O2] La sortie de chaque moteur contient les observables communes et leur statut de disponibilité.
- [ ] D4 [O2] Le score des dix mâles est fondé sur la même règle d'échantillonnage que les autres références.
- [ ] D5 [O3] Les contrôles de calibration publiés sont reproduits sur des configurations et tolérances documentées.
- [ ] D6 [O3] Le filtrage sur Ne et ascendance est calculé sans consulter le jeu de test final.
- [ ] D7 [O4] Un rapport côte à côte distingue clairement paramètres communs et paramètres propres aux architectures.
- [ ] D8 [O4] Le refus d'une configuration hors domaine ne provoque ni crash silencieux ni récompense scientifique artificielle.
- [ ] D9 [O1, O2, O3, O4] Les tests spatiaux et les tests communs passent.

## Final Validation

```sh
python -m unittest discover -s tests -p 'test_spatial_baselines.py'
python -m unittest discover -s tests
```

## References

- `source/mechanisms_code/README.md` (existant).
- Archive originale `SI3codebase.zip` fournie ; supplément SI3, appendices A et B.
