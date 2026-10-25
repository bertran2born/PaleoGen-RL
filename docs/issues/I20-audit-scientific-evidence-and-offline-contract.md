# I20 — Qualifier les preuves scientifiques et vérifier le contrat hors réseau

Milestone: M1
Advances: D8, D9 ; objectifs O1–O4
Depends on: I1–I4, preuves locales de parité I5/I10 et contexte scientifique I8

## Objective

Fournir le rapport scientifique général manquant de M1, distinguant reproduction exacte locale, reproduction approximative et résultats exploratoires. Vérifier les contrôles du contrat scientifique sans accès réseau avant de mettre à jour ses critères d'acceptation.

## Repository Grounding

- M1 D8/D9 restent ouverts ; les preuves I1–I4 couvrent déjà provenance, sources, observations et export documentaire.
- `tests/test_pulse_reference.py` compare populations, statistiques communes et états RNG sur 108 configurations sans pénalité ; cette parité locale ne reproduit pas les probabilités intégrées du préprint.
- `run_experiment.py::scientific_context` qualifie les sorties de simulations exploratoires et signale les approximations, mais ne fournit pas le rapport général demandé par M1.
- Le protocole autosomal I19 conserve `resolution_control_status=not_established` ; son exemple synthétique ne constitue pas une résolution historique validée.

## Change Scope

### Inspect

- `docs/milestones/M1-scientific-contract-and-provenance.md` — exigences et neuf critères.
- `docs/science/observations.md`, `provenance.md`, `m2-audit.md` — définitions, provenance et portée des preuves existantes.
- `reich_experiment_v2/tests/test_science_contract.py`, `test_provenance.py`, `test_sources.py`, `test_public_export.py` — contrôles effectifs M1.
- `reich_experiment_v2/tests/test_pulse_reference.py` et `run_experiment.py` — portée de la parité et qualification des sorties.

### Expected change paths

- `docs/science/scientific-evidence-report.md` (new) — catégories, preuves et validation reproductible.
- `docs/milestones/M1-scientific-contract-and-provenance.md` — critères vérifiés et lien vers le rapport.

## Required Changes

1. Définir les trois catégories et classer les preuves présentes en précisant ce qui est exactement reproduit, approximé ou non démontré. Relier chaque affirmation aux fichiers et contrôles existants.
2. Distinguer observations rapportées, prédictions publiées, simulations et incertitude Monte Carlo ; rappeler les limites de calibration, d'ascendance et de plausibilité sans nouvelle inférence historique.
3. Relier les neuf DoD M1 à des preuves consultables. Exécuter les quatre suites M1 dans un espace réseau isolé, puis les non-régressions pulse et la suite complète sous Nix. Documenter commandes, environnement, résultats réels et limites d'installation.
4. Cocher D8/D9 seulement après vérification ; toute clôture M1 exige également la confirmation des sept critères précédents. Conserver les notes antérieures comme preuves historiques datées.

## Constraints and Non-goals

- Aucun changement de moteur, cible, récompense, paramètre, graine ou archive.
- Aucune reproduction nouvelle des probabilités intégrées ou calibration spatiale ; aucune clôture automatique des milestones dépendants.
- L'export documentaire I4 reste inchangé ; ce rapport n'étend pas sa sélection ni les droits de redistribution.

## Definition of Done

- [x] ID1 Le rapport distingue les trois catégories avec preuves locales et limites explicites.
- [x] ID2 Les neuf critères M1 possèdent une correspondance vérifiable ; aucune simulation n'est qualifiée de preuve historique.
- [x] ID3 Les quatre suites M1 passent sous Nix sans réseau ; procédure et résultats sont consignés.
- [x] ID4 Les suites pulse et complète passent sous Nix ; seuls les critères effectivement vérifiés sont cochés.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c unshare --user --map-root-user --net python -m unittest discover -s tests -p 'test_science_contract.py'
nix develop -c unshare --user --map-root-user --net python -m unittest discover -s tests -p 'test_provenance.py'
nix develop -c unshare --user --map-root-user --net python -m unittest discover -s tests -p 'test_sources.py'
nix develop -c unshare --user --map-root-user --net python -m unittest discover -s tests -p 'test_public_export.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : le
[rapport](../science/scientific-evidence-report.md) satisfait ID1/ID2 par sa
classification bornée et son tableau D1–D9. Les quatre commandes isolées
retournent 0, avec 10/8/8/12 tests (ID3) ; le diagnostic réseau n'affiche que
`lo`. Les suites pulse et complète retournent 0 avec 35/155 tests (ID4).
Liens locaux, structure, taille et espaces vérifiés ; `git diff --check` réussit.
M1 est clôturé après confirmation de ses neuf critères. Aucun fichier collatéral,
moteur, résultat archivé ou ressource tierce modifié ; aucun blocage I20.
