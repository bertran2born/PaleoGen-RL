# I25 — Mesurer l'ascendance sur des blocs de poids explicitement déclarés

Milestone: M3
Advances: D1 ; objectifs O1/O4, exigences R1/R2
Depends on: I11, I24 ; protocole principal et convergence non établis

## Objective

Fournir une primitive versionnée de mesure pondérée permettant de raffiner un panel sans modifier mécaniquement le poids des partenaires. Vérifier l'invariance de la mesure lors d'un découpage conservant les poids et les ascendances, préalable à une famille de résolutions comparable.

## Repository Grounding

- `paleogen_rl/genetics/ancestry.py::measure_ancestry` attribue le même poids à chaque bloc, partenaires inclus ; son dénominateur est 2×N×B.
- Les diagnostics I18/I22 fixent les positions partenaires mais leur poids total varie selon 2/B. Leur raffinement modifie donc aussi la représentation du modèle sélectionné.
- Le contrat I19 exige la mesure I11 à poids égaux. Il ne faut pas lui attribuer implicitement une nouvelle observable ou modifier ses archives.
- Aucun module de mesure à poids de blocs explicites n'est présent dans `paleogen_rl/genetics/`.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/ancestry.py` — validation, annotations et disponibilité de la mesure I11.
- `reich_experiment_v2/tests/test_autosomal_ancestry.py` — cas analytiques et invariants existants.
- `reich_experiment_v2/paleogen_rl/genetics/protocol.py` — contraintes du contrat historique à préserver.
- `docs/science/autosomal-selected-resolution-protocol.md` — confondant 2/B et limites du diagnostic.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/weighted_ancestry.py` (new) — déclaration immuable et mesure pondérée distincte.
- `reich_experiment_v2/tests/test_autosomal_weighted_ancestry.py` (new) — formules, raffinement, annotations et refus d'entrées invalides.
- `docs/science/autosomal-weighted-measurement.md` (new) — contrat, exemple de raffinement et limites.

## Required Changes

1. Déclarer un poids relatif strictement positif et fini par bloc, avec une justification explicite de son origine. Refuser poids manquants, booléens, non finis, non positifs ou normalisation numériquement non représentable ; copier les entrées pour préserver l'immuabilité.
2. Calculer A = somme des poids multipliés par les fréquences diploïdes modernes par bloc, divisée par la somme des poids. Inclure tous les partenaires ; exporter poids déclarés/effectifs, N, numérateur et dénominateur pondérés clairement distingués des comptes bruts.
3. Utiliser une version et une observable distinctes d'I11. Conserver les règles de génération et de disponibilité : pas de valeur finale en quick, horizon exact requis en full/adaptive. Les annotations partenaires ne doivent changer ni poids ni mesure totale.
4. Vérifier cas analytiques 0/1/2 copies, compatibilité numérique avec I11 à poids égaux, invariance à une échelle commune des poids et au découpage conservatif d'un bloc. Démontrer sur trois panels synthétiques que les partenaires peuvent conserver leur poids lors du raffinement.

## Constraints and Non-goals

- Aucun moteur, CLI, contrat I19, observation, cible, récompense ou archive existante modifié.
- Aucun poids humain validé, panel principal ou marge d'équivalence adopté ; la primitive ne prouve pas une convergence des trajectoires.
- Aucun poids nul pour exclure silencieusement un partenaire ou optimiser une réussite.

## Definition of Done

- [x] ID1 Le panel pondéré est immuable, ses poids et leur origine sont explicites ; les déclarations invalides sont refusées.
- [x] ID2 Formule, échelle commune, annotations, égalité des poids et trois panels de raffinement conservatif sont vérifiés analytiquement.
- [x] ID3 Version, unités, diagnostics et disponibilité sont explicites et sérialisables en JSON strict ; I11/I19 restent inchangés.
- [x] ID4 Tests ciblés, autosomaux et complets passent sous Nix ; le document distingue invariance de mesure, hypothèse de poids et convergence non démontrée.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_weighted_ancestry.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : les trois commandes retournent 0 avec **8/103/180
tests**. Les contrôles analytiques relient chaque DoD aux assertions décrites
dans le [contrat](../science/autosomal-weighted-measurement.md). Son exemple
Python a aussi été exécuté sous Nix, avec valeur 0.375 et poids partenaires
0.25/0.25. Structure, taille, liens et `git diff --check` vérifiés. Aucun fichier
préexistant, moteur, cible, score, contrat I19, archive ou milestone modifié.
Les quatre DoD sont satisfaits ; adoption principale, intégration des poids
aux simulations et convergence M3 restent à établir.
