# M8 — Méthodes de recherche de référence à budget égal

Status: READY
Depends on: M7

## Outcome

PaleoGen-RL peut mesurer si un agent apprend réellement à explorer les architectures génétiques mieux que des stratégies simples. Le benchmark dispose au minimum d'une politique aléatoire et d'une méthode d'optimisation paramétrique, toutes deux soumises au même validateur, au même espace de modèles et au même budget de simulations. Une méthode RL pourra être ajoutée ultérieurement sans modifier la définition du succès.

## Objectives

- O1 — Une recherche aléatoire reproductible établit une performance de référence sur les architectures et paramètres autorisés.
- O2 — Un optimiseur paramétrique classique utilise le même environnement et la même fonction de récompense.
- O3 — Les comparaisons comptabilisent le coût effectif, l'incertitude et la diversité des modèles explorés.
- O4 — Les découvertes sont archivées comme candidats distincts et non seulement comme leur meilleur score observé.

## Scope

### In scope

- Baselines de recherche aléatoire et optimisation numérique conditionnelle à une architecture.
- Budget fixé par générations simulées ou unité de coût documentée, et non seulement nombre d'appels.
- Traçabilité des propositions, invalidations, résultats et meilleurs candidats admissibles.
- Graines de recherche multiples et expériences reproductibles.

### Out of scope

- Entraînement LLM/PPO/GRPO, évolution de code source et optimisation de paramètres non admissibles.
- Déclaration de supériorité scientifique sur la base du meilleur score d'entraînement.

## Requirements and Invariants

- R1 — Chaque algorithme interagit par le contrat d'environnement de M7, sans accès caché aux moteurs.
- R2 — L'optimiseur classique peut explorer des paramètres continus d'une architecture fixée ; sa portée distincte de la découverte d'architectures est explicitée.
- R3 — Une configuration expérimentale déclare le nombre de propositions, le budget total, les graines et la version du protocole.
- R4 — Tous les candidats évalués restent disponibles, y compris ceux rejetés ou peu performants.
- R5 — Un rapport compare les méthodes en fonction du budget consommé et fournit des intervalles d'incertitude entre répétitions indépendantes.
- I1 — Aucun algorithme n'accède aux données de test final durant la recherche.
- I2 — Aucun candidat hors domaine n'est retenu uniquement grâce à sa récompense élevée.
- I3 — L'algorithme de recherche ne change pas le calcul du score pour lui-même.

## Relevant Repository Surfaces

- `run_experiment.py` — tirages et statistiques Monte Carlo actuels.
- `compare_runs.py` — comparaison statistique existante, non équivalente à un benchmark de recherche.
- `paleogen_rl/search/` (proposed) — méthodes de recherche.
- `paleogen_rl/envs/` (proposed) — interface unique de M7.
- `tests/test_search_baselines.py` (proposed) — tests d'équité et de reproductibilité.

## Definition of Done

- [ ] D1 [O1] La baseline aléatoire termine des épisodes valides pour au moins deux architectures distinctes.
- [ ] D2 [O1] Deux exécutions à graine égale ont le même journal de propositions et de coûts.
- [ ] D3 [O2] Un optimiseur paramétrique termine sur une architecture fixée sans contournement du validateur.
- [ ] D4 [O2] Le rapport précise que l'optimiseur paramétrique n'est pas un découvreur d'architectures général.
- [ ] D5 [O3] Les budgets sont calculés avec la même unité documentée pour les deux méthodes.
- [ ] D6 [O3] Une méthode dépassant le budget est arrêtée et son résultat conservé avec le statut adéquat.
- [ ] D7 [O3] Les résultats comparent au moins cinq graines indépendantes sur un problème déterministe de test.
- [ ] D8 [O4] Le catalogue contient tous les candidats essayés et leur identité canonique.
- [ ] D9 [O4] Un candidat déclaré « meilleur » référence l'évaluation et la version du protocole qui justifient son rang.
- [ ] D10 [O1, O2, O3, O4] Les tests de budget, de répétabilité et de contrôle d'accès aux données finales passent.

## Final Validation

```sh
python -m unittest discover -s tests -p 'test_search_baselines.py'
python -m unittest discover -s tests
```

## References

- `run_experiment.py` ; `compare_runs.py`.
- Contrat d'environnement livré par M7 ; définition de score M6.
