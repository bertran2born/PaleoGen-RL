# I16 — Évaluer les scénarios pulse avec les blocs en mode intégral

Milestone: M3
Advances: D1, D2, D9, D10 (CLI intégrale), D6 (refus des modes anticipés) ; objectifs O1/O3/O4
Depends on: I11–I15 ; M2 techniquement validé, M1 D8/D9 ouverts

## Objective

Rendre le moteur I15 accessible depuis la CLI pour tous les scénarios nommés, avec une carte explicite commune et une mesure totale finale. Conserver le chemin historique et distinguer les nouveaux résultats par leur schéma, sans imposer une résolution principale non validée.

## Repository Grounding

- `reich_experiment_v2/paleogen_rl/genetics/selected.py::run_selected` accepte blocs phasés, mtDNA/Y, carte et sélection ; il attend un état initial explicite.
- `reich_experiment_v2/run_experiment.py` définit les scénarios, tirages SI1, graines appariées et sorties CSV/JSON, mais appelle seulement le moteur historique.
- `reich_experiment_v2/src/reich_panmictic_original.py::_init` initialise des individus entièrement modernes, avec effectifs par sexe arrondis et contrôle des quotas ; cette source reste en lecture seule.
- I14 ne valide aucune résolution principale ni convergence sous sélection. I15 ne fournit encore ni initialisation pulse ni événement conjoint.

## Change Scope

### Inspect

- `reich_experiment_v2/run_experiment.py` et `tests/test_pulse_metadata.py` — CLI, provenance et rejeu existants.
- `reich_experiment_v2/paleogen_rl/genetics/selected.py` et `inheritance.py` — moteur et carte.
- `reich_experiment_v2/src/reich_panmictic_original.py::_init` — initialisation de référence, lecture seule.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/pulse.py` (new) — initialisation, projection finale et lecture de carte.
- `reich_experiment_v2/run_experiment.py` — activation explicite du moteur blocs et sorties distinctes.
- `reich_experiment_v2/tests/test_autosomal_pulse.py` (new) — tests analytiques, CLI, rejeu et compatibilité.
- `docs/science/autosomal-pulse-protocol.md` (new) — contrat d'utilisation et preuves.

## Required Changes

1. Initialiser un pulse phasé selon les effectifs et règles M2 : quotas par sexe, individus modernes homozygotes sur tous les blocs, mtDNA et Y associés. Déclarer paramètres demandés et effectifs réalisés ; refuser un pulse excédant un quota.
2. Activer les blocs via une carte JSON et des partenaires explicitement fournis. Supporter tous les scénarios nommés, overrides réciproques et tirages SI1 existants, avec mêmes graines de simulation et de posterior. Les mécanismes Config non supportés doivent être refusés, jamais ignorés.
3. Évaluer uniquement `full` dans cette issue ; refuser `quick`/`adaptive` avec blocs avant simulation. Calculer exactement la probabilité des dix mâles sans remise, la cible inclusive 3–7 % et leur produit à l'horizon final I15. Ne pas modifier la cible ou le calcul historique.
4. Versionner séparément modèle et résultats blocs ; enregistrer configuration réalisée, carte et empreinte, initialisation, horizon, mesure totale, diagnostics partenaires, coûts et absence de convergence sélectionnée établie. Conserver les avertissements scientifiques adaptés à cette nouvelle mesure.
5. Exiger une destination explicite pour les blocs et refuser l'écrasement CSV/JSON. Les erreurs reproductives ne produisent aucun résultat de réussite. Sans carte, conserver les trajectoires, statistiques et schémas historiques.

## Constraints and Non-goals

- Aucun changement de moteur historique, ressources tierces, observations, graines antérieures ou récompenses.
- Pas de calibration empirique, résolution par défaut, modes anticipés ni clôture globale M3.

## Definition of Done

- [x] ID1 L'initialisation concorde avec M2 pour les pulses valides, biaisés et arrondis ; les quotas impossibles sont refusés.
- [x] ID2 Tous les scénarios CLI blocs utilisent le même panel/dénominateur ; sélection réalisée, overrides et posterior sont rejouables.
- [x] ID3 Les statistiques finales concordent avec des cas analytiques et I15 ; aucune évaluation précoce n'est acceptée.
- [x] ID4 Les sorties versionnées tracent carte, mesure, coûts et limites ; destinations existantes et configurations incompatibles sont refusées.
- [x] ID5 Les tests ciblés, autosomaux, pulse et complets passent sous Nix sans modification des assertions historiques.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_pulse.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : les quatre commandes retournent 0 avec **11, 54,
35 et 131 tests**. La matrice d'initialisation vérifie ID1. Deux exécutions CLI
de tous les scénarios et le rejeu de chaque ligne, plus overrides et posterior
synthétique, vérifient ID2. Les cas combinatoires, bornes inclusives, états I15
et refus d'horizons incomplets vérifient ID3. Métadonnées, coûts, JSON strict,
destinations et configurations invalides, modes interdits et échec reproductif
réel vérifient ID4. Les suites historiques inchangées et le protocole complètent
ID5. Contrôles de whitespace sans diagnostic. Aucun moteur historique, observation
ou milestone modifié ; I14/I15 conservées. Aucun commit ni push.
