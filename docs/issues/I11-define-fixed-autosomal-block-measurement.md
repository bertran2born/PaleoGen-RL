# I11 — Définir une mesure autosomale sur un panel fixe de blocs diploïdes

Milestone: M3
Advances: D1, D2, D6 (prérequis partiels) ; objectifs O1/O3
Depends on: I10, M2 techniquement vérifié ; démarrage explicite de M3, dépendance transitive M1 D8/D9 ouverte

## Objective

Fournir une primitive de mesure autosomale dont la définition et le dénominateur restent identiques lorsqu’on désigne des blocs partenaires DMI. Séparer cette mesure des statistiques historiques et refuser toute attribution finale à un état précoce.

## Repository Grounding

- `reich_experiment_v2/src/epi_pulse.py` exclut les deux partenaires autosomaux dès qu’une pénalité réciproque est active ; `_stats` mesure alors six loci au lieu de huit par défaut.
- `docs/science/observations.md` documente cette non-comparabilité et l’artefact de discrétisation. Son contrat `neutral_proxy` ne décrit pas une ascendance totale incluant des blocs sélectionnés.
- `docs/milestones/M3-comparable-autosomal-ancestry.md` propose `paleogen_rl/genetics/` et `tests/test_autosomal_ancestry.py`, absents du prototype.
- I10 vérifie les dix critères techniques de M2 ; sa clôture globale reste dépendante de M1. Aucun moteur de blocs recombinants ni protocole de convergence n’est encore présent.

## Change Scope

### Inspect

- `docs/milestones/M3-comparable-autosomal-ancestry.md` — définition commune, disponibilité et limites.
- `reich_experiment_v2/src/epi_pulse.py` et `reich_experiment_v2/src/reich_panmictic_original.py` — proxy et exclusions actuels, en lecture seule.
- `reich_experiment_v2/science_contract.py` — contrat historique à ne pas réinterpréter.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/ancestry.py` (new) — panel explicite et mesure indépendante des mécanismes.
- `reich_experiment_v2/paleogen_rl/__init__.py` et `reich_experiment_v2/paleogen_rl/genetics/__init__.py` (new, mécaniques) — accès au module.
- `reich_experiment_v2/tests/test_autosomal_ancestry.py` (new) — cas analytiques, validation et invariance aux annotations partenaires.
- `docs/science/autosomal-block-measurement.md` (new) — définition opérationnelle, version et limites.

## Required Changes

1. Définir un panel immuable de blocs identifiés et de poids égaux. Une matrice individus × blocs fournit le nombre entier de copies modernes diploïdes, entre 0 et 2. La mesure totale utilise tous les blocs déclarés et le dénominateur `2*N*B`.
2. Enregistrer les blocs partenaires comme annotations et fournir leur diagnostic séparé ; leur désignation ne retire jamais de bloc de la mesure principale. Valider identifiants uniques, dimensions, valeurs et références partenaires.
3. Retourner des métadonnées JSON sérialisables et versionnées : définition du panel, population, dénominateur, génération de l’état, horizon, mode et disponibilité. En `quick`, laisser valeur finale et diagnostic final indisponibles ; en `full`/`adaptive`, refuser une génération différente de l’horizon.
4. Vérifier des cas analytiques homozygotes/hétérozygotes et mixtes, plusieurs tailles de panels, les annotations partenaires et les entrées invalides. Conserver toutes les sorties et trajectoires M2.

## Constraints and Non-goals

- Ne pas intégrer cette primitive au score ou à la CLI dans cette Issue ; ne pas changer le contrat historique `neutral_proxy`.
- Aucun moteur de reproduction/recombinaison nouveau, choix de résolution principale ou preuve de convergence. Les blocs de test sont synthétiques, sans calibration génomique.
- Ne modifier ni observations, bornes 3–7 %, ressources tierces ou archives ; ne pas cocher les DoD globaux de M3 pour ce seul prérequis.

## Definition of Done

- [x] ID1 Les cas analytiques valident la mesure totale et son dénominateur pour plusieurs panels explicites.
- [x] ID2 Désigner des partenaires conserve panel, valeur et dénominateur ; le diagnostic partenaire est distinct.
- [x] ID3 `quick` ne fournit aucune mesure finale et les modes évalués refusent les états hors horizon.
- [x] ID4 Les entrées incohérentes sont refusées et les métadonnées se sérialisent sans valeur non finie.
- [x] ID5 Les tests ciblés, de parité pulse et complets réussissent sous Nix ; les limites et la non-intégration sont documentées.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_ancestry.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (24 octobre 2026) : les commandes retournent 0 avec respectivement
8, 35 et 85 tests. Dans `test_autosomal_ancestry.py`, les cas homozygotes,
hétérozygotes et mixtes vérifient ID1 ; les annotations et diagnostics vérifient
ID2 ; les tests de modes/horizon vérifient ID3 ; les erreurs, valeurs masquées
et aller-retour JSON strict vérifient ID4. Les suites pulse et complète préservent
les preuves M2 (ID5). `docs/science/autosomal-block-measurement.md` documente
l'API, le format distinct du proxy historique et les limites. Aucun moteur,
score, observation, ancienne assertion ou fichier milestone n'est modifié ;
aucun changement collatéral hors des chemins annoncés. M3 reste incomplet.
