# I2 — Identifier les versions locales du préprint et de SI1–SI4

Milestone: M1
Advances: D5, D9 (partiellement)
Depends on: I1 — inventaire des ressources et vérification des empreintes

## Objective

Rendre les cinq documents scientifiques principaux citables par identifiant stable, avec une version locale vérifiable et une preuve d'identification. Ce catalogue prépare les citations du futur contrat des observations, sans assimiler le préprint à une publication évaluée par les pairs.

## Repository Grounding

- `docs/science/provenance.json` contient les empreintes des PDF mais aucune identité bibliographique structurée.
- `docs/science/provenance.md` laisse explicitement ouverte la correspondance entre les fichiers `media-*` et SI1–SI4.
- La première page de `reich_study/2026.03.11.711219v2.full.pdf` indique le DOI, la date du 13 octobre 2026 et l'absence de certification par les pairs.
- Les premières pages de `media-1.pdf`, `media-3.pdf`, `media-5.pdf` et `media-7.pdf` portent respectivement les titres « Supplementary Information section 1 » à « section 4 ». Elles ne donnent pas de version autonome datée.

## Change Scope

### Inspect

- `docs/milestones/M1-scientific-contract-and-provenance.md` — critère D5.
- `docs/science/provenance.json` et `reich_experiment_v2/verify_provenance.py` — ancrage aux empreintes existantes.
- Les cinq PDF identifiés ci-dessus, page 1 — preuves bibliographiques locales.
- `reich_experiment_v2/tests/test_provenance.py` — conventions de tests et fixtures.

### Expected change paths

- `docs/science/sources.json` (new) — catalogue versionné des cinq documents.
- `docs/science/provenance.md` — correspondances vérifiées, limites et commande.
- `reich_experiment_v2/verify_sources.py` (new) — validation du catalogue et de son ancrage local.
- `reich_experiment_v2/tests/test_sources.py` (new) — contrôles positifs et négatifs.

## Required Changes

1. Définir des identifiants distincts pour le préprint et SI1–SI4. Consigner chemin, titre, SHA-256, version de contenu et preuve d'identification avec numéro de page. Relier chaque supplément au préprint en distinguant cette association d'une version autonome.
2. Consigner le DOI et la date affichée du préprint, ainsi que la version v2 indiquée dans le nom local et le manifeste. Pour les suppléments, employer une version de contenu fondée sur leur SHA-256 et signaler l'absence de date autonome établie.
3. Fournir un contrôle hors réseau, en lecture seule, avec code non nul pour catalogue invalide, identité manquante ou dupliquée, lien de parenté invalide, empreinte divergente de l'inventaire ou fichier local modifié/absent.
4. Documenter les preuves consultées et les limites : identification locale, absence de certification éditoriale indépendante, aucune déduction de droits supplémentaires.

## Constraints and Non-goals

- Aucun changement aux ressources originales, aux empreintes I1 ou aux politiques de redistribution.
- Ne pas introduire de dépendance PDF pour exécuter les contrôles : la lecture bibliographique est une revue initiale ; les empreintes en figent les documents.
- L'interprétation scientifique des observations et l'identification des archives de code restent hors périmètre.

## Definition of Done

- [x] ID1 Les cinq identités possèdent titre, fichier, empreinte, version et preuve paginée ; les associations SI1–SI4 correspondent aux premières pages lues.
- [x] ID2 Le catalogue distingue version v2 datée du préprint et versions par empreinte des suppléments, sans prétention d'évaluation par les pairs.
- [x] ID3 Les tests refusent identités manquantes/dupliquées, parenté ou version invalide, empreinte divergente et ressources absentes/modifiées.
- [x] ID4 La commande réelle, les tests ciblés et la suite complète passent sous Nix ; les 32 ressources I1 restent conformes.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_sources.py'
nix develop -c python verify_sources.py
nix develop -c python verify_provenance.py
nix develop -c python -m unittest discover -s tests
```

Preuves du 24 octobre 2026 : ID1, revue des premières pages avec `pdftotext` ;
ID2/ID3, 8 tests ciblés réussis ; ID4, vérificateurs avec codes 0
(5 sources, 32 ressources conformes) et suite complète : 30 tests réussis.
