# M9 — Benchmark indépendant et conclusions auditables

Status: READY
Depends on: M4, M6, M8

## Outcome

PaleoGen-RL produit des évaluations hors recherche permettant de comparer des modèles proposés par un agent aux références panmictiques et géographiques. La sélection est gelée avant le test final. Une amélioration du score d'entraînement ne peut pas être présentée comme une amélioration scientifique sans succès sur le protocole de validation indépendant.

## Objectives

- O1 — Les candidats sélectionnés sont évalués sur des graines indépendantes et des paramètres de référence pré-enregistrés.
- O2 — Les modèles sans expansion et avec expansion sont comparés sur les mêmes observables finales et contraintes scientifiques.
- O3 — Les rapports distinguent optimisation, validation, incertitude Monte Carlo et limites de la vraisemblance.
- O4 — La procédure de sélection d'un candidat est reproductible sans l'historique d'un agent.

## Scope

### In scope

- Découpage entre exploration, sélection, validation et test final ; budget de confirmation.
- Benchmarks incluant contrôle neutre, pulse sélectionné, modèles géographiques et candidats retenus.
- Comparaison de probabilités prédictives, score agrégé, contrôle a posteriori et courbes de sensibilité.
- Rapport CSV/JSON lisible par machine et synthèse humaine avec limitations explicites.

### Out of scope

- Déclaration de réfutation du préprint, preuve d'une DMI historique, inférence d'un unique mécanisme vrai.
- Validation des candidats sur les mêmes graines utilisées pour leur découverte.
- Choix rétroactif des priors, des poids ou de la cible d'ascendance.

## Requirements and Invariants

- R1 — Le protocole final fixe observables, paramètres admissibles, règles de classement et budget avant d'évaluer les candidats finalistes.
- R2 — Les graines de test final ne sont pas accessibles depuis l'observation ni la récompense de M7.
- R3 — Chaque architecture de référence conserve ses mécanismes et sa calibration propres ; seule la projection des sorties sur les observables est commune.
- R4 — Les rapports donnent le nombre d'essais et la politique de sélection pour prévenir le biais du « meilleur parmi beaucoup ».
- R5 — Toute comparaison de probabilités rares reporte taille d'échantillon, estimateur, intervalle et incertitude de différence.
- I1 — Un résultat nul sur un faible nombre de répétitions ne devient pas une probabilité nulle.
- I2 — Le score ne remplace pas les observations détaillées ni la comparaison des hypothèses biologiques.
- I3 — Une architecture non évaluée faute de ressources demeure « non évaluée ».

## Relevant Repository Surfaces

- `results/reference_500.csv` et `results/epistasis_500.csv` — exemples exploratoires présents dans v2, non jeu de test final.
- `compare_runs.py` — statistiques exploratoires actuelles.
- `manifest.json` — contexte de provenance actuel.
- `paleogen_rl/benchmark/` (proposed) — protocole et évaluations tenues à l'écart.
- `docs/benchmarks/` (proposed) — rapports reproductibles.
- `tests/test_benchmark_protocol.py` (proposed) — garanties de séparation.

## Definition of Done

- [ ] D1 [O1] Le jeu de test possède une liste de graines fixées par version, absente de l'état exposé pendant les épisodes.
- [ ] D2 [O1] Aucun candidat n'est sélectionné ou modifié à partir de ses performances sur le jeu de test final.
- [ ] D3 [O2] Les résultats incluent au moins une référence pulse et une référence spatiale calibrée, ou déclarent explicitement le benchmark scientifique incomplet.
- [ ] D4 [O2] Les mêmes définitions d'échantillonnage mtDNA/Y et d'ascendance finale s'appliquent à tous les résultats comparables.
- [ ] D5 [O2] Toute incompatibilité de calibration apparaît comme contrainte non satisfaite, et non comme score chiffré trompeur.
- [ ] D6 [O3] Le rapport sépare performance d'exploration et performance sur données finales indépendantes.
- [ ] D7 [O3] Chaque résultat rare possède son effectif et un intervalle de confiance adapté.
- [ ] D8 [O3] Les limites de l'approximation autosomale, des priors et du calcul du score sont consignées.
- [ ] D9 [O4] Un utilisateur peut régénérer le classement depuis les artefacts d'évaluation et le protocole versionné.
- [ ] D10 [O1, O2, O3, O4] Les tests de fuite de graines et de traçabilité des rapports réussissent.

## Final Validation

```sh
python -m unittest discover -s tests -p 'test_benchmark_protocol.py'
python -m unittest discover -s tests
```

## References

- `README.md`, avertissements et résultats pilotes.
- `compare_runs.py` ; contrat M1 ; définitions M3 et M6 ; moteurs M4.
