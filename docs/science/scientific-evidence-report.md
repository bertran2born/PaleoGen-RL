# Rapport de qualification scientifique — I20 / M1

Date : 25 octobre 2026. Base inspectée :
`6c6f18e17bdb2ffcf3676095e2636351e369a76d`, complétée uniquement par les
documents I20. Ce rapport qualifie les preuves locales ; il ne produit aucune
nouvelle estimation historique. Les notes I1–I19 décrivent leur état daté et
ne sont pas réécrites rétroactivement.

## Trois catégories et leur portée

| Catégorie | Objet effectivement présent | Preuve et limite |
| --- | --- | --- |
| **Reproduction exacte locale** | Trajectoires du moteur panmictique local et de son extension lorsque les quatre pénalités sont nulles. | `tests/test_pulse_reference.py::test_zero_penalty_pathwise_parity_matrix` compare populations, états RNG et statistiques communes sur 108 configurations. Exactitude dans cette matrice et cet environnement, sans extrapolation à tous les paramètres. |
| **Reproduction approximative** | Le scénario `reich_point` représente une référence sélectionnée simplifiée, sans expansion, avec coefficients ponctuels ; l'option posterior peut tirer `s_mt` dans le fichier fourni. | `run_experiment.py::SCENARIOS` et `scientific_context`, [contrat](observations.md), [audit M2](m2-audit.md). Ce rapprochement du modèle publié ne démontre pas la reproduction de ses probabilités intégrées ; le Y reste fixé et N n'est pas un Ne calibré. |
| **Résultat exploratoire** | Simulations neutres, sélectionnées et épistatiques, pilotes archivés, diagnostics autosomaux et exemple synthétique I19. | README, `tests/test_pulse_scientific_context.py`, [protocole I19](autosomal-evaluation-protocol.md). Ces sorties explorent des hypothèses ; elles ne prouvent ni plausibilité biologique des coûts ni histoire démographique réelle. |

Ces catégories portent sur des objets différents : une parité exacte de code
peut étayer une simulation qui reste scientifiquement exploratoire. Le terme
« reproduction approximative » décrit ici la correspondance du modèle simplifié,
pas une estimation vérifiée de l'erreur par rapport au préprint. **Aucune
reproduction exacte des probabilités intégrées publiées n'est démontrée.**

La matrice exacte utilise N=80, 32 générations, graines 0/17/42, fréquences
initiales 0/0.05/1, scénarios neutre/sélectionné, trois dominances et arrêt
anticipé activé/désactivé. Les observateurs ne tirent aucun nombre aléatoire
supplémentaire. L'accélération après absorption n'est pas une garantie d'identité
des autosomes avec une exécution sans accélération. La parité est une preuve
d'implémentation, distincte de la calibration démographique et des données.

## Observations, prédictions et incertitudes

Le [contrat versionné](observations.json), expliqué dans
[observations.md](observations.md), sépare les observations **rapportées** par
les documents fournis des hypothèses opérationnelles de simulation. Les citations
paginales sont reliées aux versions de contenu du [catalogue](sources.json).
Ce rapport n'ajoute pas de recherche bibliographique ni de vérification externe
des affirmations du préprint fourni, identifié v2 du 13 octobre 2026 et non
évalué par les pairs dans ce catalogue local.

Les lignées uniparentales échantillonnées ne démontrent pas une fixation dans
toute la population ancienne. La fixation mtDNA, la fixation Y et la probabilité
que dix mâles portent simultanément les deux marqueurs restent distinctes.
Cette dernière est calculée sans remise par `(K)_10/(N_m)_10`, et non par un
produit de fréquences marginales. Les dix mâles constituent un plan simulé,
pas un nouvel échantillon empirique commun établi par le contrat.

La plage autosomale rapportée 3–7 % n'est pas un intervalle historique à 95 %.
La cofixation intégrée inférieure à 2–3 % citée dans SI1 est une prédiction de
modèle, pas une observation indépendante. Les intervalles des simulations
quantifient uniquement l'incertitude Monte Carlo ; un zéro dans un petit lot
ne démontre pas une probabilité biologique nulle.

La CLI conserve `scientific_status=exploratory_simulation`,
`published_result_reproduction=not_demonstrated` et
`uncertainty_scope=monte_carlo_only`. Les tests de contexte vérifient les trois
modes et les paramètres effectifs après overrides, y compris l'absence
d'authentification SI1 implicite d'un fichier chargé. Les archives anciennes
ne reçoivent pas rétroactivement ces métadonnées.

## Limites autosomales et comparaisons

Le proxy historique à huit loci, ou six après exclusion des partenaires par
défaut d'une épistasie active, présente discrétisation et dénominateurs différents.
Une mesure valide isolément n'est donc pas nécessairement comparable entre
architectures. Le mode quick ne fournit aucune ascendance finale admissible ;
adaptive ne mesure pas l'ascendance marginale sur toutes les trajectoires.
L'horizon réellement atteint reste nécessaire même en full.

Les blocs phasés I11–I19 incluent les partenaires dans la mesure totale à poids
égaux et tracent carte, résolution et protocole. Cela ne calibre ni une carte
humaine ni le poids physique des partenaires. I19 exige encore un statut de
convergence `not_established` ; son exemple N=40, trois générations, quatre
blocs et pulse 50 % est synthétique. Il ne résout pas le choix du protocole
principal au régime N=1450 / 6993 générations. M3 reste ouvert et aucune
référence spatiale calibrée n'est établie par cet audit M1.

## Preuves des neuf critères M1

Les chemins de tests ci-dessous sont relatifs à `reich_experiment_v2/tests/`.
Les contrôles relus sont exécutés à nouveau pour I20 ; les anciens statuts ne
servent pas seuls de preuve.

| DoD M1 | Preuve inspectée et vérification |
| --- | --- |
| D1 | `observations.json` et `test_science_contract.py::test_four_distinct_statistics_and_reference_parameters` : quatre définitions, unités et chronologie séparées. |
| D2 | Citations, pages, versions et statuts dans le contrat ; `test_status_citation_and_uncertainty_rejected` refuse statuts, citations et bornes incohérents. La lecture scientifique initiale des pages reste celle documentée dans I3. |
| D3 | `test_missing_generation_or_basis_rejected`, `test_wrong_generation_status_value_population_or_denominator_rejected` et simulation courte refusée comme mesure à 50 ka. |
| D4 | `test_provenance.py::test_real_registry_coverage_integrity_and_policies` recalcule indépendamment les SHA-256 et compare la couverture des ressources ; cas manquant/modifié/non inventorié testés séparément. |
| D5 | `test_sources.py::test_real_catalog_and_citation_evidence` contrôle cinq PDF, parenté et versions locales ; dates autonomes SI1–SI4 non établies, sans assimilation à une publication évaluée. |
| D6 | Registre de 32 ressources, toutes `not_established` avec justification ; contrôle réel D4 et `verify_provenance.validate_registry` exigent une politique explicite. Aucun droit nouveau n'est déduit d'une empreinte. |
| D7 | `test_public_export.py::test_only_authorized_resources_and_explicit_documents_included` couvre autorisé/non établi/non autorisé/non inventorié ; `test_real_repository_export_and_cli_from_other_directory` inspecte le ZIP réel : cinq documents, manifeste et 32 exclusions. |
| D8 | Les catégories, preuves et limites du présent rapport ; contexte des nouvelles sorties vérifié par `test_pulse_scientific_context.py`. |
| D9 | Les quatre suites M1 passent dans un espace réseau isolé, y compris leurs sous-processus CLI ; commandes et résultats ci-dessous. |

D7 concerne uniquement l'export documentaire local I4. Sa sélection de cinq
documents n'est pas étendue au présent rapport. Ce paquet n'est pas une
distribution exécutable v0.1 ; les obligations M10/M11 restent indépendantes.

## Vérification reproductible

Depuis `reich_experiment_v2/`, après disponibilité locale de l'environnement
Nix verrouillé, les commandes suivantes isolent les tests et leurs descendants
dans un espace réseau sans interface extérieure :

```sh
nix develop -c unshare --user --map-root-user --net python -c 'import socket; print(socket.if_nameindex())'
nix develop -c unshare --user --map-root-user --net python -m unittest discover -s tests -p 'test_science_contract.py'
nix develop -c unshare --user --map-root-user --net python -m unittest discover -s tests -p 'test_provenance.py'
nix develop -c unshare --user --map-root-user --net python -m unittest discover -s tests -p 'test_sources.py'
nix develop -c unshare --user --map-root-user --net python -m unittest discover -s tests -p 'test_public_export.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Le diagnostic d'isolation exécuté retourne `[(1, 'lo')]`. L'espace réseau est
créé **après** l'entrée dans Nix : cette preuve porte sur l'exécution des
contrôles, pas sur une première installation sans réseau. Elle nécessite Linux,
`unshare` et la disponibilité des espaces de noms utilisateur ; un refus de
création doit rester un échec de validation hors réseau. Les ressources locales
de référence sont présentes, sans téléchargement implicite ni redistribution.

Résultats exécutés pour I20 : les six commandes de test retournent le code 0,
sans échec ni test ignoré. Les quatre suites isolées comptent respectivement
**10, 8, 8 et 12 tests**, soit **38 contrôles M1**. Les non-régressions comptent
**35 tests pulse** et **155 tests complets**. Ces derniers incluent aussi les
contrôles autosomaux existants ; leur succès ne clôture pas les critères
scientifiques encore ouverts de M3.

Environnement relevé par
`nix develop -c python -c 'import platform, sys, numpy; print(platform.machine()); print(sys.version.split()[0]); print(numpy.__version__)'` :
Linux x86_64, Python **3.14.8**, NumPy **2.5.3**. L'entrée nixpkgs du
`reich_experiment_v2/flake.lock` est
`02c087f3fe673c9e317f206a627cb6b910336dbe`.

Inspection documentaire : liens locaux existants, structure I20 conforme,
taille inférieure à 800 mots et aucun espace terminal. `git diff --check`
réussit. Les seuls changements I20 sont l'Issue, ce rapport et la mise à jour
M1 ; tests, moteurs, observations, registres, ressources et résultats archivés
restent inchangés. Les neuf DoD M1 sont vérifiés dans le périmètre ci-dessus.
Aucun blocage ne subsiste pour I20 ; les limites de calibration, de résolution
et de redistribution décrites ici ne sont pas levées par la clôture de M1.
