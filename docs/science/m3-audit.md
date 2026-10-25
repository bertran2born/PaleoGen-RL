# Audit d'acceptation technique partielle M3 — I24

Date : 25 octobre 2026. Base inspectée :
`1f5fa629f56df6e9639dda715ad408aab24370d6`. I24 ajoute uniquement cet audit,
son Issue et la mise à jour documentaire M3. Les conclusions ci-dessous reposent
sur les assertions relues puis réexécutées, et sur les artefacts présents ; elles
ne sont pas déduites des cases des Issues précédentes.

## Correspondance des dix critères

Les fichiers de tests cités sont sous `reich_experiment_v2/tests/`.
Les critères vérifiés décrivent la portée des mécanismes et des contrôles
actuels, sans extrapolation à tous les paramètres ou à une calibration humaine.

| Critère M3 | Conclusion et preuve inspectée | Portée et limite |
| --- | --- | --- |
| D1 — Métrique principale commune | **Ouvert.** `test_autosomal_protocol.py::test_all_scenarios_and_modes_match_explicit_map_and_replay_without_source` vérifie le contrat partagé quand il est fourni. `run_experiment.py` conserve le moteur/proxy historique sans carte ni protocole. | Une capacité explicite à partager un panel n'est pas l'adoption d'un protocole principal v0.1. Carte, résolution et validation de convergence restent non établies. |
| D2 — Partenaires sans sélection | **Vérifié.** `test_autosomal_ancestry.py::test_partner_annotations_never_change_total_or_panel` et `test_autosomal_selected.py::test_zero_selection_matches_i13_with_and_without_partner_annotations`. | Numérateur, dénominateur, panel, observable et trajectoires neutres restent identiques avec/sans annotations dans les configurations testées. |
| D3 — Ségrégation | **Vérifié.** `test_autosomal_inheritance.py::test_mendelian_segregation_preregistered_tolerances` et `test_boundary_switch_frequencies_preregistered_tolerances`. | Parents hétérozygotes, proportions 0/1/2 et transitions ; effectifs, graines et tolérances fixés dans le protocole I12, explicités ci-dessous. |
| D4 — Invariants de recombinaison | **Vérifié.** `test_zero_recombination_transmits_whole_parental_homologues`, `test_active_recombination_never_creates_an_allele_or_changes_parent_origin` et `test_absorbing_ancestries_survive_five_generations_at_zero_and_active_recombination` dans le même fichier. `test_autosomal_selected.py::test_parents_markers_and_gametes_are_consistent_for_each_proposal` couvre les propositions sélectionnées. | Origines parentales, absence de création d'allèles et états absorbants ; aucune invariance de la moyenne sous sélection n'est revendiquée. |
| D5 — Dérive neutre | **Vérifié.** `test_autosomal_neutral.py::test_neutral_mean_in_preregistered_bernstein_intervals`. | Deux cartes, 1024 graines chacune, N=40 et 20 générations ; contrôle de l'espérance 0.05 avec borne préfixée, pas calibration du Ne ou validation au régime historique. |
| D6 — Quick indisponible | **Vérifié.** `test_autosomal_ancestry.py::test_quick_has_no_final_value_even_at_target` et `test_autosomal_block_modes.py::test_quick_at_horizon_and_zero_horizon_never_expose_final_values`, plus la matrice des modes. | Valeur finale, copies modernes et diagnostics finaux indisponibles, même à horizon atteint ; le diagnostic d'arrêt reste distinct. |
| D7 — Adaptive/full | **Vérifié.** `test_autosomal_block_modes.py::test_preregistered_reference_matrix_matches_full` et `test_synthetic_positive_joint_event_keeps_five_percent_and_all_selection`. | Égalité exacte sur 216 références et 12 contrôles synthétiques positifs ; aucune équivalence numérique entre résolutions déduite de cet accord entre modes. |
| D8 — Rapport multirésolution | **Vérifié.** Archives I14, I18 et I22 sur 8/32/128 blocs ; contrôles dans `test_autosomal_selected_resolution.py` et `test_autosomal_target_regime.py`. | Le rapport compare les résolutions et leurs écarts ; ce critère documentaire ne démontre pas la convergence demandée par le périmètre scientifique global. |
| D9 — Coût et mode | **Vérifié dans les configurations explicites de blocs.** `test_autosomal_workload_preview.py` vérifie prévisions, unités et comparaison aux coûts réels ; `test_autosomal_block_modes.py::test_cli_all_scenarios_replay_repeatability_and_costs` vérifie les modes anticipés. | Aperçu full avant exécution, compteurs effectifs des modes exécutés, rejets et cumuls inclus. Aucun temps matériel ni pic mémoire garanti ; pas de prévision d'arrêt anticipé. |
| D10 — Tests autosomaux | **Vérifié.** Les 95 tests autosomaux et 172 tests complets réussissent sous Nix dans I24. `test_autosomal_selected.py::test_named_scenarios_keep_the_same_measurement_panel` couvre les scénarios nommés, des pénalités actives et trois dominances. | Le succès d'une suite vérifie ses assertions ; il ne fournit pas une validation historique. |

## Mesure et transmission vérifiées

L'inspection de `paleogen_rl/genetics/ancestry.py::measure_ancestry` confirme
que tous les blocs contribuent au total, partenaires inclus : somme des copies
modernes divisée par `2*N*B`. Les diagnostics des partenaires sont séparés,
sans retrait de colonnes. `test_named_scenarios_keep_the_same_measurement_panel`
dans `test_autosomal_selected.py` vérifie les 17 scénarios, les trois dominances
et deux cartes sur un panel fixé. Ce test complète D2 ; il ne lève pas D1.

Le test sans sélection compare au moteur neutre I13 les états et mesures sur
N=5/40, B=2/8, probabilités 0/0.25, graines 0/17/42 et cinq générations, avec
et sans partenaires. La transmission I12 reçoit les parents et le RNG du caller ;
les choix de parents par sexe sont vérifiés dans les moteurs neutre et sélectionné.
Ces garanties portent sur les lois et états contrôlés, pas sur une identité RNG
avec le moteur historique M2 sous sélection.

Le [protocole I12](autosomal-inheritance-protocol.md) et son code de test fixent
les graines 104729/130363/155921 et 20000 descendants par graine. Les proportions
mendéliennes attendues sont 0.25/0.5/0.25, et 0.5 pour chaque contribution
parentale. La tolérance est `sqrt(log(2*K/0.001)/(2*20000))`, K=15 pour cette
famille. Les transitions utilisent la carte (0,0.2,0.5), K=18 ; à probabilité
nulle, aucun changement n'est autorisé. Les deux familles gardent leurs seuils.

Le [protocole neutre I13](autosomal-neutral-protocol.md) utilise les graines
310000–311023, N=40, huit blocs et 20 générations, pour chaque carte uniforme
0 ou 0.25. La fraction initiale est exactement 0.05 dans chaque sexe. Avec
`t=log(4/0.01)` et n=1024, le rayon préfixé est
`sqrt(2*0.05*0.95*t/n)+2*t/(3*n)` ; l'intervalle autour de la moyenne doit
contenir 0.05. Aucun réplicat n'est conditionné à une réussite autosomale ou
uniparentale, et les seuils ne sont pas ajustés après observation.

## Modes, horizons et nature des preuves

Le [protocole I17](autosomal-pulse-protocol.md) définit 216 configurations :
quatre scénarios, trois dominances, deux cartes (0 et 0.1), trois graines
0/17/42 et trois fractions 0/0.5/1, sur N=40 et 40 générations. Les tests
comparent le critère conjoint et les marqueurs exactement ; les continuations
positives rejoignent l'ascendance full à l'horizon. En adaptive, un événement
impossible donne un critère conjoint nul et une ascendance non évaluée,
sans lui attribuer une fréquence autosomale nulle.

Les douze contrôles positifs utilisent une initialisation **synthétique
contrôlée**, avec 5 % sur un panel de vingt blocs et marqueurs modernes fixés,
pour vérifier que la continuation conserve la sélection et le critère positif.
Ils ne sont pas des observations historiques. Les erreurs injectées vérifient
le refus des écrans incohérents et horizons incomplets ; les tests CLI de
sélection létale provoquent aussi de véritables échecs reproductifs sans sorties
de réussite. Ces catégories de preuve restent distinctes.

## Archives, coût et convergence

Inspection des JSON présents : I14 contient 384 évaluations neutres ; I18
contient 6528 évaluations des 17 scénarios, sur 128 graines par case ; I22
contient 18 évaluations de trois scénarios sur deux graines par case. Les trois
rapports comparent 8/32/128 blocs. I14/I18 utilisent N=40 et 20 générations ;
I22 utilise N=1450 et 6993 générations. Les coûts et écarts sont conservés,
y compris les résultats nuls. Les tests d'intégrité I22 recalculent mesures,
échantillonnage et agrégats et détectent les altérations contrôlées.

I24 ne relance pas les études longues. Le [rejeu de trois trajectoires I22](autosomal-target-regime-diagnostic.md)
est une preuve datée d'I22 ; son intégrité documentaire et numérique est
contrôlée ici, sans prétendre que les empreintes d'implémentation de l'archive
doivent correspondre aux modifications ultérieures du runner I23.

L'[aperçu I23](autosomal-workload-preview.md) annonce full, résolutions, nombre
d'évaluations, travail minimal conditionnel à l'achèvement et taille d'un état.
Les coûts sélectionnés observés peuvent dépasser les minima à cause des rejets.
Les coûts quick/adaptive effectivement exécutés incluent écran et continuation ;
la taille d'un état est un maximum, pas une somme ni un pic mémoire mesuré.
Ces preuves satisfont le suivi logique des coûts, pas une calibration matérielle.

Les cartes sont synthétiques ; les poids des partenaires changent avec B,
selon 2/B. Le raffinement ne représente donc pas uniquement une erreur numérique
à poids physique sélectionné constant. Les différences par graine n'impliquent
pas un couplage bloc par bloc des flux RNG. Les intervalles I18/I22 sont
ponctuels et Monte Carlo seulement. Avec deux graines, I22 est insuffisant
pour une équivalence et ne justifie pas de sélectionner 128 blocs comme référence.

## Conditions restant ouvertes

M3 conserve D1 et son statut global ouverts. Les progrès techniques ne
dispensent pas de fixer une carte, les positions/poids partenaires et une
résolution principale, puis d'en établir la validation à précision déclarée
dans le régime visé. Les marges éventuelles, répétitions et règles d'acceptation
doivent être fixées avant leur étude de confirmation ; les observations et
la cible ne doivent pas être adaptées aux scores.

R4, qui demande les résultats du contrôle de convergence dans les évaluations,
reste un point d'acceptation scientifique : les sorties déclarent actuellement
un statut non établi. Le cochement de D8 pour l'existence du rapport ne change
pas ce statut. Le chemin historique de compatibilité continue d'utiliser un
proxy différent ; un fichier I19 synthétique n'est pas un protocole principal.

M1 est clos depuis I20. M2 porte ses dix critères techniques vérifiés et reste
documentairement READY ; sa dépendance et son statut ne sont pas modifiés par
I24. La poursuite M3 est explicitement demandée dans cette session. Cet audit
ne clôture ni M2 ni M3 et ne requalifie pas leurs anciens rapports datés.

## Validation I24

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_inheritance.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_neutral.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_block_modes.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_ancestry.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Les quatre commandes ciblées ont retourné 0 : **9 tests de transmission,
8 tests neutres, 9 tests des modes et 8 tests de mesure**. Les suites
autosomale et complète retournent également 0 : **95 et 172 tests**, sans échec
ni test ignoré. Les graines, familles et seuils préfixés restent inchangés.
La validation ciblée de mesure et les deux suites satisfont les commandes
d'acceptation du milestone. Les autres commandes ciblées isolent ses contrôles
statistiques et son accord entre modes.

Environnement relevé avec
`nix develop -c python -c 'import platform, sys, numpy; print(platform.machine()); print(sys.version.split()[0]); print(numpy.__version__)'` :
Linux x86_64, Python 3.14.8, NumPy 2.5.3. Le SHA-256 du verrou local
`reich_experiment_v2/flake.lock` est
`a52bdf3a3b9a069175d3af298234c3cf7adeba54540833eed6ad902e9ccc0a64`.

Les SHA-256 du plan et du rapport I22 restent ceux de leur diagnostic :
`f400cc547acae4143b352013fb68d14c625d1f888e0b60e8d919d2131f65bb10`
et `99cd8cf191a92651cb413edbce10a01502257eaaf6c6b49dd64fa3a85085affd`.
`git diff --check`, liens locaux et structure/taille de l'Issue sont vérifiés.
Les seuls fichiers I24 sont l'Issue, le présent rapport et le milestone ;
aucun moteur, test, seuil, paramètre, observation, archive ou ressource tierce
n'est modifié. Aucun blocage ne subsiste pour cet audit.

Les quatre DoD d'[I24](../issues/I24-audit-autosomal-milestone-acceptance.md)
sont vérifiés : correspondance des dix critères, validation réelle, mise à jour
partielle et décisions restantes explicites. Le milestone coche D2–D10 et
conserve D1, R4 et son statut global ouverts. Cela acte les preuves acquises
sans choisir de résolution ni annoncer une convergence non démontrée.
