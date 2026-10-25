# I15 — Simuler les blocs autosomaux sous sélection réciproque

Milestone: M3
Advances: D1, D2, D4, D9, D10 (moteur intégral, prérequis d'intégration) ; objectifs O1/O2/O4
Depends on: I11–I14 ; M2 techniquement validé, M1 D8/D9 ouverts

## Objective

Simuler à horizon intégral des blocs phasés avec transmission mtDNA/Y et sélection de viabilité réciproque. Fournir une mesure totale commune aux conditions neutres et sélectionnées, préalable nécessaire à l'intégration des scénarios et modes CLI.

## Repository Grounding

- `reich_experiment_v2/paleogen_rl/genetics/neutral.py::run_neutral` transmet les blocs I12 mais ne représente ni marqueurs uniparentaux ni sélection.
- `reich_experiment_v2/src/epi_pulse.py::_epistasis_loss` définit quatre coûts multiplicatifs et trois dominances ; les termes Y sont limités aux mâles.
- `reich_experiment_v2/src/reich_panmictic_original.py::_breed` tire uniformément les parents par sexe et rejette les descendants selon leur viabilité ; `_step` impose les quotas N//2 mâles puis femelles.
- Les scénarios nommés de `reich_experiment_v2/run_experiment.py` combinent sélection mt/Y et ces quatre coûts ; leur métrique principale utilise encore les autosomes historiques.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/ancestry.py`, `inheritance.py`, `neutral.py` — contrats I11–I13.
- `reich_experiment_v2/src/epi_pulse.py` et `src/reich_panmictic_original.py` — sémantique de viabilité, en lecture seule.
- `reich_experiment_v2/run_experiment.py` — paramètres des scénarios existants, sans changement CLI.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/selected.py` (new) — moteur intégral, configuration et rapport.
- `reich_experiment_v2/tests/test_autosomal_selected.py` (new) — héritage, sélection, invariants et échecs.
- `docs/science/autosomal-selection-protocol.md` (new) — protocole, contrats, preuves et limites.

## Required Changes

1. Accepter un état initial explicite (blocs, sexes, mtDNA, Y), carte I12, partenaires identifiés dans le panel, sélection mt/Y signée et quatre coûts réciproques. Appliquer les règles M2 de viabilité aux descendants, sans copie du moteur historique ni modification de ses globals.
2. Produire toutes les générations, avec mère/père des groupes de sexes respectifs, mtDNA maternel, Y paternel chez les fils et sentinelle féminine. Conserver les quotas M2 et réutiliser la transmission I12. À coefficients nuls, retrouver exactement les trajectoires autosomales I13 avec les mêmes entrées et graine, y compris lorsque les partenaires sont annotés.
3. Mesurer tous les blocs I11, partenaires compris, avec diagnostics séparés. Tracer configuration, carte, horizon, graines, empreintes initiales et coûts réels des propositions, y compris rejetées. Un épuisement borné des tentatives lève une erreur traçable sans mesure finale évaluée.
4. Vérifier analytiquement et contre M2 les viabilités ; tester un cas de sélection de descendants avec proportions pré-enregistrées, la transmission liée aux marqueurs, les configurations des scénarios nommés, le rejeu et les entrées invalides.

## Constraints and Non-goals

- Aucun changement de moteur historique, proxy existant, observations, récompenses ou graines antérieures.
- Pas d'initialisation historique implicite, sélection X/autosome directe, drive, DMI SI3 génériques, second pulse ou démographie variable.
- Pas de CLI ni modes anticipés, choix de résolution, calibration biologique ou clôture globale M3.

## Definition of Done

- [x] ID1 Les viabilités signées mt/Y et réciproques concordent avec les formules et la référence sur les trois dominances.
- [x] ID2 Transmission parentale, quotas et phase sont vérifiés ; le contrôle de sélection préfixé passe.
- [x] ID3 À coefficients nuls, trajectoires I13 et mesure totale sont préservées avec/sans partenaires.
- [x] ID4 Tous les scénarios nommés sont exercés sur ce moteur ; leur mesure conserve panel et dénominateur.
- [x] ID5 Rapports JSON, répétabilité, coûts et erreurs avant RNG sont vérifiés ; les échecs reproductifs ne produisent aucune mesure finale évaluée.
- [x] ID6 Tests ciblés, autosomaux, pulse et complets réussissent sous Nix ; limites documentées.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_selected.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : les quatre commandes retournent 0 avec **11, 43,
35 et 120 tests**. Les matrices analytique/M2 et isolée vérifient ID1 ; suivi
des parents et contrôle statistique préfixé vérifient ID2. La parité I13 couvre
48 configurations, chacune avec/sans partenaires (ID3). Les scénarios nommés
passent avec trois dominances et deux cartes (ID4). Rejeu depuis métadonnées,
JSON strict, coûts, invalidations et deux échecs contrôlés vérifient ID5.
Le protocole détaille les limites ; son exemple a été exécuté sous Nix (ID6).
Contrôles de whitespace réussis. Aucun fichier antérieur, moteur historique,
milestone, score ou observation modifié ; I14 conservée. Aucun commit ni push.
