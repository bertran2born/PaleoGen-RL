# I7 — Enregistrer les métadonnées rejouables de chaque résultat pulse

Milestone: M2
Advances: D8 ; objectif O4, invariant I1
Depends on: I3, I5, I6 ; M1 D8/D9 ouverts, poursuite de M2 explicitement demandée

## Objective

Permettre de rejouer chaque ligne CSV avec les paramètres effectivement simulés, sans reconstruire implicitement un scénario nommé. Associer explicitement le résultat à son modèle, sa chronologie cible et la disponibilité de la mesure autosomale finale.

## Repository Grounding

- `reich_experiment_v2/run_experiment.py` exporte scénario, graine, horizon demandé et `s_mt_realized`, mais pas la totalité de `Config`. Les scénarios et overrides sont partiellement décrits dans le JSON compagnon.
- Le posterior mitochondrial remplace `s_mt` par un tirage reproductible utilisant une graine décalée de 27383 ; son contenu n’est pas identifié dans les résultats.
- Depuis I6, `run_mode` exporte `auto_evaluation_status`, mais `generations_completed` décrit seulement le premier passage, même après continuation adaptative.
- `docs/science/observations.json` fixe 28,6 ans/génération, 8741 générations avant le présent pour le pulse et 6993 générations jusqu’à l’échantillonnage nominal. La définition JSON actuelle annonce toujours 50 ka, même avec `--gens` personnalisé.

## Change Scope

### Inspect

- `docs/milestones/M2-pulse-reference-parity.md` — contenu requis par ligne résultat.
- `reich_experiment_v2/src/epi_pulse.py` et `reich_experiment_v2/src/reich_panmictic_original.py` — champs de configuration et générations retournées, en lecture seule.
- `reich_experiment_v2/science_contract.py` — chargement du contrat chronologique validé.
- `reich_experiment_v2/tests/test_pulse_modes.py` — disponibilité des mesures à préserver.

### Expected change paths

- `reich_experiment_v2/run_experiment.py` — métadonnées CSV versionnées et contexte JSON cohérent.
- `reich_experiment_v2/tests/test_pulse_metadata.py` (new) — rejeu, chronologie, provenance des tirages et générations des mesures.
- `docs/science/pulse-reference.md` — contrat des nouveaux champs et preuves I7.

## Required Changes

1. Chaque ligne doit identifier le modèle et la version du format, sérialiser tous les champs réalisés de `Config`, conserver la graine et le statut I6, et fournir la génération cible et son âge calculé avec les paramètres du contrat scientifique identifié.
2. Distinguer la génération de mesure autosomale finale de celle du premier passage ; laisser cette génération finale indisponible quand la mesure ne l’est pas.
3. Pour les tirages mitochondriaux, enregistrer l’empreinte SHA-256 des octets chargés et la graine de tirage, ainsi que le coefficient réalisé. Distinguer les coefficients fixes et le cas où un posterior fourni n’est pas appliqué.
4. Le JSON compagnon doit identifier le même format et la même chronologie ; sa définition ne doit plus attribuer systématiquement les sorties personnalisées à 50 ka. Vérifier le rejeu depuis la configuration CSV et la stabilité des indicateurs existants.

## Constraints and Non-goals

- Conserver les colonnes existantes et les lois de simulation, graines, distributions et seuils.
- Ne pas migrer les archives ni modifier les ressources tierces ou les moteurs.
- La date calculée reste une convention du modèle ; ne pas revendiquer une précision historique accrue, ni clôturer M1/M2.

## Definition of Done

- [x] ID1 Les lignes des trois modes contiennent une configuration complète rejouable et les identifiants du modèle, format et contrat.
- [x] ID2 Les horizons par défaut/personnalisés ont une chronologie cohérente dans CSV et JSON, sans étiquette universelle 50 ka.
- [x] ID3 La génération autosomale finale distingue continuation et premier passage ; elle est vide si non évaluée.
- [x] ID4 Un posterior synthétique vérifie empreinte, graine de tirage, coefficient réalisé et distinction du cas non appliqué.
- [x] ID5 Les indicateurs rejoués concordent ; les tests ciblés, pulse et complets réussissent sous Nix sans affaiblir les tests existants.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_pulse_metadata.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (24 octobre 2026) : les trois commandes réussissent sous Nix avec
respectivement 4, 22 et 64 tests. Dans `test_pulse_metadata.py`,
`test_cli_replay_all_modes_with_overrides` vérifie ID1 et le rejeu ID5 ;
`test_cli_default_horizon_has_model_age_near_50ka` complète ID2 ;
`test_final_measurement_generation_is_not_first_pass` vérifie ID3 ;
`test_posterior_provenance_and_replay` vérifie ID4 et le rejeu, y compris gzip/bzip2.
La suite complète conserve les tests précédents de parité, de modes et de contrat
scientifique. `git diff --check` réussit. Aucun moteur, ressource tierce ou résultat
archivé modifié ; aucun changement collatéral hors des chemins annoncés.
M2 D8 dispose désormais de preuves pour les nouvelles sorties CLI ; aucun
milestone n'est modifié ou déclaré achevé. M1 D8/D9 restent ouverts.
