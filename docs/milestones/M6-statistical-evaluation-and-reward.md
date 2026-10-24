# M6 — Évaluation statistique et récompense contrainte

Status: READY
Depends on: M3, M5

## Outcome

Un évaluateur calcule la qualité prédictive à partir du contrat scientifique, avec incertitude et pénalités explicites. La récompense RL est déterministe à partir d'un lot de résultats et d'une version de protocole, mais elle ne confond jamais une forte fréquence de fixation avec une bonne explication scientifique. Les scores restent comparables entre architectures.

## Objectives

- O1 — L'évaluation produit les statistiques communes et leurs incertitudes pour chaque modèle admissible.
- O2 — Une règle de score pré-définie tient compte de plusieurs observations et contraintes, pas uniquement de la fixation mtDNA/Y.
- O3 — Les candidats hors domaine et les observations manquantes reçoivent un statut explicite non récompensé.
- O4 — Les estimations et pénalités sont auditables et testables indépendamment de l'agent.

## Scope

### In scope

- Probabilité prédictive de l'échantillon de dix mâles, fixation stricte et ascendance 3–7 %.
- Statistiques ABC ou distance observationnelle documentée, pénalité de complexité et de plausibilité.
- Intervalles de confiance Monte Carlo, budget, intervalles des valeurs observées, diagnostics de rareté.
- Calcul homogène de la récompense et version de sa définition.

### Out of scope

- Un Bayes factor exact sans vraisemblance établie ; preuve causale d'une DMI historique.
- Ajustement des poids de récompense sur le benchmark final.
- Substitution des priors biologiques par des paramètres maximisant arbitrairement le score.

## Requirements and Invariants

- R1 — Un score sépare adéquation aux observations, pénalité de complexité, violation de contraintes et incertitude Monte Carlo.
- R2 — L'absence de succès sur peu de répétitions ne signifie pas une probabilité biologique exactement nulle.
- R3 — Les pénalités et pondérations sont définies dans un protocole versionné avant optimisation et n'utilisent pas les graines finales réservées.
- R4 — Les évaluations avec autosomes non comparables ou horizon non atteint sont invalides pour le score principal.
- R5 — Les probabilités issues de moyennes de `p10_joint` utilisent des intervalles adaptés aux valeurs dans [0,1], et non automatiquement un Wilson binomial.
- I1 — Les sorties publiées de Reich ne sont pas considérées comme des observations indépendantes de leurs propres paramètres.
- I2 — Un meilleur score signifie « meilleur selon le contrat d'évaluation », jamais « histoire vraie ».
- I3 — Les indicateurs intermédiaires et contraintes rejetées restent visibles même si la récompense finale est basse.

## Relevant Repository Surfaces

- `compare_runs.py` — comparaisons Wilson et Fisher existantes.
- `run_experiment.py` — statistiques et bootstrap actuels.
- `README.md` — avertissements sur l'autosome et la plausibilité.
- `paleogen_rl/evaluation/` (proposed) — moteur de scoring commun.
- `docs/specs/reward-v1.md` (proposed) — contrat public de récompense.
- `tests/test_evaluation.py` (proposed) — contrôles statistiques.

## Definition of Done

- [ ] D1 [O1] Un lot de résultats contient, au minimum, les trois observables primaires, les échantillons effectifs et leurs incertitudes.
- [ ] D2 [O1] Les intervalles pour variables binaires et probabilités pondérées utilisent des méthodes appropriées et documentées.
- [ ] D3 [O2] Un modèle maximisant artificiellement la fixation mais violant une contrainte biologique obligatoire n'obtient pas un score admissible.
- [ ] D4 [O2] Deux modèles ayant les mêmes prédictions et paramètres de plausibilité mais des complexités différentes sont classés selon la pénalité publiée.
- [ ] D5 [O2] Une modification de la définition des observations change la version du protocole de score.
- [ ] D6 [O3] Une exécution `quick` sans ascendance finale est exclue du score scientifique complet.
- [ ] D7 [O3] Les statuts « donnée manquante », « simulation échouée » et « modèle rejeté » sont distincts.
- [ ] D8 [O4] Le calcul du score est reproductible bit à bit à partir d'un résultat sauvegardé et d'un protocole immuable.
- [ ] D9 [O4] Le rapport détaille chaque composante de score et chaque contrainte appliquée.
- [ ] D10 [O1, O2, O3, O4] Les tests de scénarios extrêmes et de scores identiques réussissent.

## Final Validation

```sh
python -m unittest discover -s tests -p 'test_evaluation.py'
python -m unittest discover -s tests
```

## References

- `compare_runs.py` et `run_experiment.py` ; SI1–SI3.
- Documents `docs/science/observations.md` et `docs/specs/model-v1.md` (proposed, dépendances M1 et M5).
