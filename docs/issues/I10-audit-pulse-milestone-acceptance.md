# I10 — Auditer les dix critères techniques du milestone pulse

Milestone: M2
Advances: D4, D10 ; consolidation D1–D9, objectifs O1–O4
Depends on: I5–I9 ; M1 D8/D9 ouverts, audit de M2 explicitement demandé

## Objective

Établir un audit reproductible des dix DoD techniques de M2 et synchroniser le milestone avec les preuves réellement vérifiées. Distinguer cette validation technique de la clôture globale dépendante de M1.

## Repository Grounding

- `docs/milestones/M2-pulse-reference-parity.md` ne coche que D1–D3 et décrit encore les modes et sorties comme travaux restants, alors qu’I6–I9 fournissent leur implémentation et leurs tests.
- `reich_experiment_v2/tests/test_pulse.py::test_y_penalty_male_only` couvre les deux directions sur des homozygotes, mais sa seule femelle porte `Y=-1`. Cette entrée ne distingue pas à elle seule le masque de sexe d’une exclusion due à la valeur de Y.
- `reich_experiment_v2/src/epi_pulse.py::_epistasis_loss` applique explicitement un masque mâle et trois dominances ; le moteur original multiplie la viabilité par la survie épistatique.
- Les suites I5–I9 vérifient trajectoires, modes, rejeu, contexte scientifique et échecs reproductifs. M1 D8/D9 restent non cochés dans leur milestone.

## Change Scope

### Inspect

- `docs/milestones/M2-pulse-reference-parity.md` et `docs/milestones/M1-scientific-contract-and-provenance.md` — critères et dépendance.
- `reich_experiment_v2/src/epi_pulse.py` et `reich_experiment_v2/src/reich_panmictic_original.py` — fitness et application reproductive, en lecture seule.
- `reich_experiment_v2/tests/test_pulse*.py` — preuves exécutables existantes, sans duplication des matrices I5–I9.

### Expected change paths

- `reich_experiment_v2/tests/test_pulse_y_fitness.py` (new) — preuve ciblée D4 indépendante de la sentinelle Y féminine.
- `docs/science/m2-audit.md` (new) — correspondance D1–D10, vérifications et limites.
- `docs/milestones/M2-pulse-reference-parity.md` — critères vérifiés et état réel de la dépendance.

## Required Changes

1. Vérifier isolément les deux pénalités Y sur les trois génotypes nucléaires et trois dominances, pour les mâles et femelles. Inclure les valeurs Y 0/1 sur entrées féminines synthétiques afin que le masque de sexe soit testé indépendamment de la sentinelle, sans les présenter comme populations biologiques.
2. Vérifier que les termes Y laissent inchangée la composante mitochondriale des femelles et se composent multiplicativement avec celle des mâles. Ne pas changer les règles de fitness.
3. Relier chaque critère D1–D10 à des symboles de test existants ou ajoutés, consigner les commandes exécutées, leurs résultats et la portée des configurations testées.
4. Actualiser les cases de M2 seulement après vérification de tous ses critères. Conserver sa dépendance M1, signaler D8/D9 ouverts dans M1 et ne pas annoncer une clôture globale ou validation historique.

## Constraints and Non-goals

- Aucun changement des moteurs, paramètres, graines, observations, sorties archivées ou assertions existantes.
- Aucun travail M1/M3 ajouté ; aucune reproduction des probabilités intégrées du préprint revendiquée.
- L’audit doit distinguer preuves par simulation réelle, fixtures contrôlées et inspection statique.

## Definition of Done

- [x] ID1 La matrice Y distingue explicitement sexe et sentinelle, dans les deux directions et trois dominances.
- [x] ID2 La composition mitochondriale/Y respecte les survies multiplicatives, sans coût Y féminin.
- [x] ID3 Le rapport relie chacun des dix DoD à une preuve identifiable et décrit ses limites.
- [x] ID4 Les tests ciblés, pulse et complets passent sous Nix ; les cases M2 reflètent ces preuves sans déclarer M1 achevé.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_pulse_y_fitness.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (24 octobre 2026) : les trois commandes retournent 0 avec respectivement
2, 35 et 77 tests. `test_pulse_y_fitness.py` vérifie ID1 sur 216 combinaisons
(deux loci partenaires) et ID2 sur 324 combinaisons. Le tableau D1–D10 de
`docs/science/m2-audit.md` identifie tests, nature des preuves et limites (ID3).
Le milestone coche ses dix critères techniques et conserve `Depends on: M1`
avec clôture globale en attente de M1 D8/D9 (ID4). `git diff --check` réussit.
Les anciens tests, moteurs, paramètres, graines et archives sont inchangés ;
aucun changement collatéral hors des chemins annoncés.
