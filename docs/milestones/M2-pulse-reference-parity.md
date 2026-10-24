# M2 — Modèle de métissage ponctuel reproductible

Status: READY
Depends on: M1

## Outcome

Le modèle panmictique sans expansion fournit une référence stable à toutes les recherches de PaleoGen-RL. Ses règles d'hérédité, de sélection et d'échantillonnage correspondent aux implémentations vérifiées du prototype, et la parité avec le moteur d'origine peut être démontrée pour les scénarios sans extension. Les résultats publiés par Reich sont distingués des estimations du moteur simplifié.

## Objectives

- O1 — Le scénario neutre et le scénario sélectionné sont reproductibles à paramètres et graines fixés.
- O2 — Les extensions épistatiques conservent exactement les trajectoires de référence quand leurs coefficients sont nuls.
- O3 — Les trois modes d'exécution possèdent des sémantiques statistiques non ambiguës.
- O4 — Les sorties contiennent les informations nécessaires pour refaire les tests et calculer l'incertitude Monte Carlo.

## Scope

### In scope

- Modèle Wright-Fisher panmictique, hérédité mtDNA, Y, X et autosomes.
- Épistasie réciproque à quatre pénalités et règles de dominance existantes.
- Modes `quick`, `full` et `adaptive`, échantillon de dix mâles et paramètres SI1.
- Sémantique des graines et transparence des approximations de taille effective.

### Out of scope

- Nouveaux moteurs géographiques, représentation génomique définitive, optimisation des paramètres.
- Inférence de nouvelles distributions biologiques à partir des données anciennes.

## Requirements and Invariants

- R1 — Un moteur de référence et un adaptateur fournissent les mêmes statistiques observables pour les mêmes paramètres acceptés.
- R2 — Le modèle sans épistasie conserve le comportement du moteur Reich original, y compris les tirages sous les scénarios de parité.
- R3 — `quick` n'annonce aucune mesure de proportion autosomale finale après arrêt anticipé.
- R4 — `adaptive` poursuit à l'horizon final toute trajectoire où l'événement des dix mâles demeure possible ; les autres reçoivent « non évalué » sur l'autosome.
- R5 — L'estimation de la probabilité des dix mâles emploie l'échantillonnage sans remise, et non une approximation avec remise.
- I1 — La génération d'échantillonnage reste explicitement associée à chaque statistique.
- I2 — L'absence de fixation d'un marqueur est distinguée de sa présence chez dix mâles.
- I3 — Les intervalles de confiance Monte Carlo ne sont pas décrits comme des intervalles d'incertitude historique.

## Relevant Repository Surfaces

- `src/reich_panmictic_original.py` — copie locale du moteur SI3.
- `src/epi_pulse.py` — extension épistatique existante.
- `run_experiment.py` — scénarios et modes d'exécution.
- `tests/test_pulse.py` et `tests/test_v2.py` — contrôles actuels de transmission et de parité.
- `source/mechanisms_code/cluster/panmictic_sim.py` — source locale de référence.
- `tests/test_pulse_reference.py` (proposed) — contrats supplémentaires.

## Definition of Done

- [x] D1 [O1] Deux exécutions du même scénario avec les mêmes graines produisent les mêmes indicateurs, hors métadonnées temporelles.
- [x] D2 [O1] Les cas neutres couvrent les fréquences initiales nulles, totales et intermédiaires.
- [x] D3 [O2] Zéro pénalité épistatique redonne les sorties du moteur original, pour les scénarios sélectionnés et neutres testés.
- [ ] D4 [O2] Chaque terme Y agit uniquement sur la fitness des mâles ; les tests couvrent les deux directions.
- [ ] D5 [O3] Le mode `quick` marque explicitement la proportion autosomale finale comme indisponible.
- [ ] D6 [O3] `adaptive` et `full` produisent le même événement mtDNA/Y pour chaque graine de référence vérifiée.
- [ ] D7 [O3] Une trajectoire arrêtée prématurément sans événement possible n'est jamais comptée comme réussite autosomale.
- [ ] D8 [O4] Chaque ligne résultat contient le modèle, la graine, la date cible, les paramètres réalisés et le statut d'évaluation.
- [ ] D9 [O4] Les écarts entre simulation et résultats publiés sont signalés comme écarts d'approximations.
- [ ] D10 [O1, O2, O3, O4] Tous les tests du moteur panmictique réussissent.

## Final Validation

```sh
python -m unittest discover -s tests -p 'test_pulse*.py'
python -m unittest discover -s tests
```

Preuves partielles (I5, 24 octobre 2026) :
`tests/test_pulse_reference.py` compare populations et états RNG sur 108
configurations fixées (N=80, 32 générations ; graines 0/17/42 ; fréquences
0/0.05/1 ; neutre/sélectionné ; trois dominances ; arrêt activé/désactivé).
Les tests vérifient aussi les indicateurs supplémentaires, la répétabilité après
épistasie active et sur erreur, et deux exécutions CLI de chaque scénario.
Depuis `reich_experiment_v2/`, les commandes Nix ciblée, pulse et complète
réussissent avec respectivement 4, 14 et 56 tests. Voir
`docs/issues/I5-verify-seeded-pulse-reference-trajectories.md` et
`docs/science/pulse-reference.md`. D1/D2/D3 sont satisfaits dans ce périmètre.
M2 a été commencé sur demande explicite avant clôture de M1 D8/D9 : sa dépendance
reste ouverte. M2 n'est pas déclaré achevé, et D10 reste ouvert pour la validation
globale après les travaux restants sur les modes et sorties.

## References

- `README.md`, sections « Modèle et observations » et « Vérification avant une conclusion scientifique ».
- SI1 et SI3 fournis par l'utilisateur ; `source/mechanisms_code/README.md`.
