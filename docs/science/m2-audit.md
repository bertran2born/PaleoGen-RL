# Audit technique M2 — I10

Date : 24 octobre 2026. Périmètre : code de simulation et tests I5–I9 sur la
révision de base `9712c2e89c5484baf50150372d0edf6fb299f79a`, complétés par les
tests de fitness Y d'I10. Aucun moteur, paramètre scientifique ou résultat
archivé n'est modifié par cet audit.

La validation technique des critères ci-dessous est distincte de la clôture
globale de M2 : sa dépendance M1 reste ouverte sur D8/D9. Les sources locales
nécessaires sont présentes ; aucune acquisition ou redistribution n'est réalisée.

## Correspondance des dix critères

Les chemins de test ci-dessous se trouvent dans `reich_experiment_v2/tests/`.
Les méthodes nommées permettent de retrouver l'assertion et sa configuration
sans déduire une preuve du seul statut d'une Issue.

| Critère | Preuve vérifiée dans le code des tests | Portée |
| --- | --- | --- |
| D1 — Reproductibilité | `test_pulse_reference.py::test_cli_repeated_seeded_outputs` et `test_repeatability_after_active_epistasis_and_error` | Deux CLI par scénario neutre/sélectionné, CSV identiques ; JSON identiques hors destination et durée. Répétabilité du moteur avant/après épistasie et erreur. |
| D2 — Fréquences neutres | `test_pulse_reference.py::test_zero_penalty_pathwise_parity_matrix` | Fréquences initiales 0, 0.05 et 1 ; états initiaux et générations réellement simulées. |
| D3 — Parité sans pénalité | Même matrice I5, plus `test_pulse.py::test_selected_reference_matches_original` | Populations, états RNG et statistiques partagées comparés au moteur original local, pour les paramètres testés. |
| D4 — Coûts Y mâles | `test_pulse_y_fitness.py::test_each_y_direction_requires_male_sex_independently_of_sentinel` et `test_y_survival_composes_with_mt_without_changing_female_fitness` | Deux directions, trois génotypes, trois dominances ; garde par sexe testée indépendamment de Y=-1. Inspection de l'application à la viabilité reproductive, décrite ci-dessous. |
| D5 — Quick indisponible | `test_pulse_modes.py::test_cli_mode_outputs`, `test_controlled_early_ancestry_and_continuation` | Statut et sentinelle explicites, filtre final et événement conjoint vides. I9 refuse les passages reproductivement échoués. |
| D6 — Événement adaptatif/intégral | `test_pulse_modes.py::test_real_seeded_mode_matrix` | Même P10, fréquences mtDNA/Y et fixation sur 36 configurations, dont absorption, polymorphisme et épistasie active. |
| D7 — Pas de fausse réussite | `test_pulse_modes.py::test_controlled_early_ancestry_and_continuation`, `test_mixed_adaptive_csv_in_both_orders` ; `test_pulse_termination.py::test_all_modes_reject_failure_even_when_event_is_impossible` | Mesure précoce dans 3–7 % non comptée comme succès final ; événement impossible nul avec ascendance non évaluée ; échec reproductif refusé. |
| D8 — Métadonnées par ligne | `test_pulse_metadata.py::test_cli_replay_all_modes_with_overrides`, `test_cli_default_horizon_has_model_age_near_50ka`, `test_posterior_provenance_and_replay`, `test_final_measurement_generation_is_not_first_pass` | Modèle, graine, configuration complète rejouable, chronologie, statut et génération finale ; provenance des tirages, y compris fichiers compressés. |
| D9 — Approximations signalées | `test_pulse_scientific_context.py::test_cli_context_in_all_modes_and_reference_scenarios`, `test_overrides_determine_epistasis_instead_of_scenario_name`, `test_posterior_is_not_implicitly_authenticated` | CSV et JSON qualifient la simulation, la reproduction publiée non démontrée, les approximations et l'incertitude Monte Carlo ; activation selon les coefficients. |
| D10 — Tests réussis | Commandes pulse et complète dans la section de validation | Comprend les tests I5–I9, les preuves de fitness I10 et les contrôles scientifiques/provenance présents. |

## Nature des preuves

La matrice I5 exécute réellement le moteur original et son extension sur 108
configurations : N=80, 32 générations, graines 0/17/42, fréquences 0/0.05/1,
neutre/sélectionné, trois dominances et arrêt activé/désactivé. Les observateurs
copient populations et états RNG sans tirage supplémentaire. La preuve concerne
ces configurations et l'environnement exécuté, pas toute configuration possible.

La matrice réelle I6 utilise N=80, trois scénarios, graines 0/17/42 et les couples
(fraction, horizon) (0,80), (0.05,80), (1,80), (0.5,1). Le cas court polymorphe
permet un événement positif sans fixation. I5 recalcule aussi P10 par
`comb(K,10)/comb(N_m,10)` depuis la population finale et distingue l'approximation
avec remise. Ces contrôles étayent R1/R2/R5 et I2.

Pour D4, les tables de pénétrance I10 sont indépendantes de `_nuclear_carrier`.
La matrice isolée couvre 216 combinaisons, avec partenaire Y aux loci 1 et 5.
La composition mitochondriale/Y couvre 324 combinaisons. Les valeurs Y 0/1 sur
entrées féminines sont des entrées adversariales de fonction, pas des génotypes
biologiques proposés pour les femelles. Elles empêchent la sentinelle de masquer
une régression du filtre mâle. Les tests vérifient aussi que les entrées de la
matrice isolée ne sont pas modifiées.

L'inspection de `src/epi_pulse.py::run_extended` confirme que le hook de
pénétrance passe par `_epistasis_loss` et est restauré en sortie. Dans
`src/reich_panmictic_original.py::_breed`, la viabilité `w` est multipliée par
`1 - _dm_penetrance(...)` avant le tirage d'acceptation. C'est une inspection
statique de l'application à la fitness, distincte des tableaux synthétiques.
I5 vérifie la restauration du hook sur exécution réelle et sur erreur.

Les tests de branche I6 utilisent explicitement des résultats contrôlés pour
isoler la politique de disponibilité ; les tests CLI et matrices réelles les
complètent. I9 emploie une interruption contrôlée après plusieurs générations,
une population synthétique incompatible avec les vraies fonctions de reproduction,
et des sous-processus sans remplacement de fonction pour une sélection létale
synthétique. Aucune de ces fixtures n'est une observation historique.

Les générations du premier passage, la chronologie cible et la génération finale
autosomale sont distinctes dans les sorties I7/I9. La continuation intégrale doit
atteindre l'horizon ; un échec n'est ni remplacé par zéro ni exclu silencieusement
d'une synthèse. Ces vérifications étayent R3/R4 et I1. Les champs scientifiques
I8 qualifient les intervalles comme Monte Carlo seulement, conformément à I3.

## Validation exécutée

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_pulse_y_fitness.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Les trois commandes ont été exécutées dans cet audit et retournent le code 0 :
respectivement **2 tests ciblés**, **35 tests pulse** et **77 tests complets**.
Les succès ne sont pas déduits des anciennes notes d'Issue. Les dix DoD
techniques sont vérifiés dans les périmètres indiqués ci-dessus.

Environnement observé : x86_64 Linux, Python 3.14.8, NumPy 2.5.3 ; entrée
nixpkgs verrouillée sur `02c087f3fe673c9e317f206a627cb6b910336dbe` dans
`reich_experiment_v2/flake.lock`. La commande de diagnostic exécutée est :

```sh
nix develop -c python -c 'import platform, sys, numpy; print(platform.machine()); print(sys.version.split()[0]); print(numpy.__version__)'
```

`git diff --check` retourne également 0. Les anciens tests et leurs assertions
sont conservés. La modification du milestone coche les dix critères avec un
lien vers ce rapport et garde explicitement la dépendance M1 ouverte.

## Limites et dépendance ouverte

La parité locale ne reproduit pas les probabilités intégrées du préprint.
L'accélération après absorption peut changer le flux RNG et les autosomes
individuels ; l'audit n'exige pas leur identité avec le passage sans accélération.
Les petits N/horizons des tests ne constituent pas une calibration historique.
Le recensement/Ne, le proxy à quelques loci et la base différente avec épistasie
restent des approximations explicitement signalées ; la comparabilité autosomale
relève de M3. Les nouveaux champs n'enrichissent pas rétroactivement les archives.

M1 D8 demande encore un rapport général séparant reproduction exacte,
approximative et résultat exploratoire. M1 D9 demande la validation globale du
contrat sans accès réseau. Leur clôture ne découle pas de cet audit technique
M2 ; le milestone conserve `Depends on: M1` et ne passe pas au statut achevé.

Références : [milestone M2](../milestones/M2-pulse-reference-parity.md),
[milestone M1](../milestones/M1-scientific-contract-and-provenance.md),
[protocole pulse et Issues I5–I9](pulse-reference.md),
[Issue I10](../issues/I10-audit-pulse-milestone-acceptance.md).
