# I24 — Établir l'acceptation technique partielle de M3 sur preuves vérifiées

Milestone: M3
Advances: D2–D10 ; objectifs O1–O4
Depends on: I11–I23 ; adoption principale et convergence non établies

## Objective

Relier les critères M3 aux assertions exécutables et aux artefacts réellement présents, puis mettre à jour uniquement les critères vérifiés. Distinguer l'acceptation technique des blocs de l'adoption d'un protocole principal dont la convergence reste à démontrer.

## Repository Grounding

- M3 conserve dix cases ouvertes et présente encore les modules/tests autosomaux comme proposés ou absents.
- Les tests I11–I19 couvrent mesure, transmission, dérive, sélection et modes ; I22 archive un pilote au régime cible et I23 annonce les coûts avant simulation.
- `run_experiment.py` conserve le proxy historique sans carte/protocole ; un contrat I19 fourni lie les scénarios au même panel mais n'est pas une référence principale adoptée.
- I22 n'a que deux graines par case et conserve la convergence non établie. Le succès des tests ne transforme pas ce pilote en preuve d'équivalence.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/ancestry.py`, `inheritance.py`, `selected.py`, `pulse.py` — mesure, transmission, sélection et disponibilité.
- `reich_experiment_v2/tests/test_autosomal_ancestry.py`, `test_autosomal_inheritance.py`, `test_autosomal_neutral.py` — critères analytiques/statistiques préfixés.
- `reich_experiment_v2/tests/test_autosomal_selected.py`, `test_autosomal_block_modes.py`, `test_autosomal_protocol.py`, `test_autosomal_workload_preview.py` — annotations, modes, contrats et coûts.
- `docs/science/autosomal-target-regime-diagnostic.md` et les protocoles I12/I13/I17 — portée des preuves et limites.

### Expected change paths

- `docs/science/m3-audit.md` (new) — correspondance D1–D10, validation et conditions restant ouvertes.
- `docs/milestones/M3-comparable-autosomal-ancestry.md` — surfaces existantes, cases vérifiées et lien vers l'audit.

## Required Changes

1. Auditer chacun des dix critères à partir des fichiers et assertions présents. Nommer les tests, paramètres, graines et tolérances qui constituent les preuves ; ne pas déduire l'acceptation des statuts d'Issues.
2. Vérifier annotations sans sélection, ségrégation, invariants de recombinaison, contrôle neutre, indisponibilité quick, accord adaptive/full, diagnostics multirésolution et coûts. Relancer les contrôles ciblés, la suite autosomale et la suite complète sous Nix.
3. Distinguer tests de primitives, simulations réelles, fixtures contrôlées et archives datées. Consigner les limites des petits lots, cartes synthétiques, poids partenaires 2/B, incertitudes ponctuelles et coûts logiques ; ne modifier aucune hypothèse pour obtenir une acceptation.
4. Mettre à jour les surfaces obsolètes et les cases dont les critères sont vérifiés. Garder D1 ouvert si la métrique principale commune n'est pas adoptée ; conserver le statut global M3 ouvert et expliciter les décisions scientifiques restantes.

## Constraints and Non-goals

- Aucun moteur, test, observation, récompense, graine, protocole ou résultat archivé modifié.
- Aucune nouvelle étude longue, marge d'équivalence, résolution principale ou calibration biologique décidée par cet audit.
- Conserver les anciennes notes scientifiques comme preuves historiques datées, sans les réécrire rétroactivement.

## Definition of Done

- [x] ID1 Un tableau D1–D10 relie chaque conclusion à des preuves vérifiables et leur portée.
- [x] ID2 Les contrôles ciblés, autosomaux et complets réussissent sous Nix ; leurs résultats réels figurent dans l'audit.
- [x] ID3 Le milestone référence les surfaces existantes et seules les cases démontrées sont cochées ; D1 et le statut global restent ouverts.
- [x] ID4 Les décisions restantes et limites sont explicites, sans changement scientifique ou fichier collatéral.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_inheritance.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_neutral.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_block_modes.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_ancestry.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : les six commandes retournent 0 avec
**9/8/9/8/95/172 tests**. L'[audit](../science/m3-audit.md) relie les dix critères
aux assertions inspectées et consigne leurs limites (ID1/ID2). M3 référence les
surfaces existantes, coche D2–D10 et conserve D1 et READY (ID3). Les décisions
de protocole/convergence restent explicites, sans relance longue, changement
scientifique ni fichier collatéral (ID4). Structure, taille, liens et
`git diff --check` vérifiés ; les quatre DoD de l'Issue sont satisfaits.
