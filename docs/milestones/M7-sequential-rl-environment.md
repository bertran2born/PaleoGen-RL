# M7 — Environnement séquentiel d'exploration compatible RL

Status: READY
Depends on: M5, M6

## Outcome

Un agent peut explorer les modèles évolutifs au moyen d'une interface séquentielle documentée, sans modifier les moteurs, les observations ou le protocole d'évaluation. Chaque épisode expose les actions légales, les résultats des simulations précédentes et le budget résiduel, puis fournit une récompense vérifiable. L'environnement est utilisable localement par une politique aléatoire sans nécessiter l'entraînement d'un réseau neuronal.

## Objectives

- O1 — Le protocole d'épisode possède des règles définies pour initialisation, observation, action, transition, récompense et terminaison.
- O2 — Les actions structurées permettent d'ajouter, retirer ou ajuster les mécanismes et de demander des évaluations.
- O3 — Un agent ne peut ni accéder aux graines réservées du benchmark final ni exécuter du code arbitraire.
- O4 — Les traces d'épisode peuvent être rejouées et auditées.

## Scope

### In scope

- Interface Gymnasium (`reset`, `step`) pour politiques locales ; états et observations sérialisables.
- Actions structurées, validation, coûts de calcul, budget maximal par épisode et limite de transitions.
- Retour des statistiques, incertitudes et raisons de refus.
- Réinitialisation déterministe et journal de décisions.

### Out of scope

- Entraînement PPO/GRPO, langage naturel libre générant du code, orchestration distante en cluster.
- Modification de la définition de récompense à l'intérieur d'un épisode.

## Requirements and Invariants

- R1 — `reset(seed)` fixe l'état initial et un flux de hasard propre à l'épisode, séparé des graines d'évaluation finales.
- R2 — `step(action)` produit observation, récompense et indicateurs d'arrêt conformes au contrat Gymnasium.
- R3 — Une action illégale retourne une erreur normalisée et ne modifie pas les références, les observations ni les résultats validés.
- R4 — L'épuisement du budget termine ou tronque l'épisode selon une règle documentée.
- R5 — L'observation donne un récapitulatif des candidats précédents, de leurs incertitudes et des unités de calcul consommées.
- I1 — Les actions modifient seulement les spécifications candidates et les demandes de simulation.
- I2 — Un épisode ne consulte pas le jeu de validation finale pour choisir une action ou une récompense.
- I3 — Toute simulation coûteuse est comptabilisée, qu'elle réussisse ou non.

## Relevant Repository Surfaces

- `run_experiment.py` — exécution actuelle à scénario fixé.
- `src/epi_pulse.py` — mécanique de reproduction existante.
- `paleogen_rl/envs/` (proposed) — contrat et interface Gymnasium.
- `paleogen_rl/models/` (proposed) — modèles candidats de M5.
- `paleogen_rl/evaluation/` (proposed) — score commun de M6.
- `tests/test_environment.py` (proposed) — tests d'épisode.

## Definition of Done

- [ ] D1 [O1] Une politique aléatoire peut terminer un épisode complet sans interface interactive ni service externe.
- [ ] D2 [O1] L'observation initiale ne comporte aucun résultat de simulation encore non exécutée.
- [ ] D3 [O2] Les actions « modifier modèle », « évaluer modèle » et « terminer » disposent de schémas documentés.
- [ ] D4 [O2] Une demande d'évaluation légale modifie le budget et ajoute un résultat traçable à l'observation.
- [ ] D5 [O3] Le validateur refuse une proposition de code Python et une référence à un fichier hors périmètre.
- [ ] D6 [O3] Aucune action ne permet de modifier le protocole d'observation, les graines finales ou le calcul de récompense.
- [ ] D7 [O3] La limite de calcul reste applicable après erreurs et évaluations invalides.
- [ ] D8 [O4] Rejouer un journal avec la même version et la même graine redonne les mêmes observations numériques.
- [ ] D9 [O4] Chaque étape conserve l'identité du candidat, les statistiques retournées et le coût consommé.
- [ ] D10 [O1, O2, O3, O4] Les tests de conformité à l'API et de limites d'épisode réussissent.

## Final Validation

```sh
python -m unittest discover -s tests -p 'test_environment.py'
python -m unittest discover -s tests
```

## References

- `run_experiment.py` ; spécifications M5 et M6.
- Guide OpenEnv : https://github.com/huggingface/OpenEnv/blob/main/docs/source/guides/concepts.md
