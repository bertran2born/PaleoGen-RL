# I29 — Exécuter les protocoles autosomaux pondérés depuis la CLI

Milestone: M3
Advances: D1, D6, D7, D9 ; objectifs O1/O3/O4
Depends on: I19, I27, I28 ; protocole principal et convergence non établis

## Objective

Rendre le contrat pondéré I28 exécutable par `run_experiment.py`, avec des
sorties identifiées et rejouables dans les trois modes. Conserver les chemins
historiques et I19 par défaut, sans adoption implicite d'une nouvelle métrique.

## Repository Grounding

- `weighted_protocol.py` fournit déclaration stricte, poids explicites,
  justification et empreintes canonique/fichier ; il n'est pas chargé par la CLI.
- `pulse.py::evaluate_block_pulse` accepte `measurement_panel`, avec cible
  inchangée, quick indisponible et continuation adaptive identifiée.
- Les adaptateurs `run_block_full`, `run_block_mode` et `_run_block` ne
  transmettent pas encore cette option. La CLI exporte déjà paramètres réalisés,
  contrat I19, provenance du posterior, coûts et rapports complets.
- `scientific_context` décrit actuellement les blocs comme également pondérés.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/weighted_protocol.py` et `pulse.py` — formats et disponibilité.
- `reich_experiment_v2/tests/test_autosomal_protocol.py` et `test_autosomal_block_modes.py` — conflits, sorties et compatibilité.

### Expected change paths

- `reich_experiment_v2/run_experiment.py` — option, adaptateurs, sorties et contexte scientifique.
- `reich_experiment_v2/tests/test_autosomal_weighted_cli.py` (new) — intégration, rejeu, refus et non-régression.
- `docs/science/autosomal-weighted-cli.md` (new) — usage, formats et limites.

## Required Changes

1. Ajouter une entrée CLI explicite pour I28, exclusive avec I19 et les options
   carte/partenaires. Verrouiller N, horizon et pulse comme I19 ; accepter leurs
   valeurs explicites identiques. Refuser contrats invalides, sorties existantes
   ou manquantes et conflits avant tout moteur.
2. Acheminer le panel pondéré aux adaptateurs puis à I27 dans les trois modes.
   Conserver scénarios, graines appariées, posterior et substitutions de coûts,
   sans changer dynamique, seuils ou échantillonnage.
3. Identifier les sorties pondérées par une version distincte ; conserver dans
   chaque ligne et les métadonnées JSON le contrat complet et ses deux empreintes.
   Exposer mesures, disponibilité, diagnostics intermédiaires et coûts I27.
   Adapter les notes scientifiques pour déclarer les poids et leur statut
   exploratoire, sans affirmer calibration ou convergence.
4. Vérifier les résultats CLI contre I27 et leur rejeu sans fichier source,
   sur tous les scénarios, plusieurs graines et les trois modes. Vérifier
   bornes de disponibilité, résumés, provenance du posterior, erreurs reproductives
   sans sorties de succès et non-régression des formats existants.

## Constraints and Non-goals

- Aucun changement des contrats I19/I28, moteurs, archives, observations ou récompenses.
- Aucun protocole principal, poids empiriques ou raffinement multirésolution adopté.
- L'ascendance d'arrêt reste intermédiaire ; adaptive ne fournit pas une
  distribution autosomale marginale sur toutes les trajectoires.

## Definition of Done

- [x] ID1 La CLI charge exclusivement I28 sur demande, verrouille ses paramètres et refuse les conflits avant simulation.
- [x] ID2 Les trois modes concordent avec I27 ; chaque sortie conserve version, contrat, poids, provenance, disponibilité et coûts vérifiables.
- [x] ID3 Le rejeu sans source, les scénarios sélectionnés, posterior, substitutions et erreurs reproductives sont vérifiés ; chemins existants préservés.
- [x] ID4 Tests ciblés, I19, autosomaux et complets passent sous Nix ; exemple CLI exécuté et limites documentées.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_weighted_cli.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_protocol.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves finales (26 octobre 2026) : les quatre commandes réussissent sous Nix
avec **6/7/131/208 tests**, sans échec ni test ignoré.
ID1 est couvert par refus pré-moteur
et sorties préservées ; ID2/ID3 par 17 scénarios × 3 graines (17–19) × 3 modes,
comparaison directe I27, rejeu sans source, posterior, substitutions, états
absorbés et erreurs reproductives réelles. L'[exemple CLI](../science/autosomal-weighted-cli.md)
est exécuté ; structure, taille, syntaxe et `git diff --check` vérifiés.

ID4 est satisfait après résolution du blocage local initial (3 échecs de
provenance/sources, 31 ressources absentes). Les 14 fichiers `reich_study/`
étaient présents et conformes lors de la reprise ; les 17 fichiers absents
de `source/` ont été restaurés depuis `/home/mathieu/reich_experiment/`, après
vérification de leurs SHA-256. Le moteur ignoré avait aussi été restauré à
l'identique depuis cette copie locale. `verify_provenance.py` et
`verify_sources.py` retournent 0 ; les **32 ressources** correspondent au
registre. Aucun fichier existant remplacé, contenu tiers édité, test affaibli
ou registre modifié. Les ressources restent ignorées par Git ; seuls les
quatre fichiers de l'Issue sont à committer. M3 D1 et la convergence restent
ouverts ; le milestone est inchangé.
