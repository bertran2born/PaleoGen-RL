# I27 — Évaluer le pulse pondéré dans les trois modes d'exécution

Milestone: M3
Advances: D1 ; exigences R1/R2/R5, invariants I1/I2
Depends on: I17, I25, I26 ; protocole principal et convergence non établis

## Objective

Intégrer explicitement le panel pondéré I25/I26 à l'API d'évaluation pulse, avec disponibilités cohérentes en full, quick et adaptive. Calculer le critère conjoint sur cette mesure identifiée, tout en conservant le chemin existant sans pondération.

## Repository Grounding

- `paleogen_rl/genetics/selected.py::run_selected` accepte depuis I26 `measurement_panel`, sans modifier populations, marqueurs, coûts ou RNG.
- `pulse.py::evaluate_block_pulse` et `_evaluate_screened` n'acheminent pas encore cet argument. La continuation adaptive appelle le chemin full et le diagnostic d'arrêt utilise une moyenne non pondérée.
- L'échantillonnage des dix mâles et la cible inclusive 3–7 % existent ; les mesures finales quick sont indisponibles et les continuations impossibles ne mesurent pas l'ascendance.
- Les consommateurs CLI et I19 utilisent les anciens formats à poids égaux.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/selected.py` et `weighted_ancestry.py` — option I26, versions et disponibilité.
- `reich_experiment_v2/tests/test_autosomal_block_modes.py` — invariants full/quick/adaptive et coûts des erreurs.
- `reich_experiment_v2/tests/test_autosomal_pulse.py` — échantillonnage, bornes et refus des horizons incomplets.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/pulse.py` — acheminement du panel, versions et diagnostic pondéré.
- `reich_experiment_v2/tests/test_autosomal_weighted_pulse.py` (new) — modes, cible, rejeu et erreurs.
- `docs/science/autosomal-weighted-pulse.md` (new) — contrat API, preuves et limites.

## Required Changes

1. Accepter un panel pondéré explicite, identique au panel de recombinaison, et le valider avant tout moteur. Acheminer les mêmes poids et leur origine dans l'écran et la continuation ; exporter des versions d'évaluation distinctes et la déclaration complète. Sans option, conserver formats et résultats actuels.
2. En full, exiger une mesure pondérée à l'horizon demandé et calculer la cible et le critère conjoint selon les formules existantes. Refuser une mesure de version/panel incohérent. Ne changer ni P10, ni seuils, ni sélection ou graines.
3. En quick, garder mesure finale et critère conjoint indisponibles, même à horizon atteint. En adaptive, conserver une ascendance non évaluée si P10=0, sinon rejouer full avec même graine et mêmes poids. Tracer un diagnostic pondéré au point d'arrêt comme intermédiaire, distinct du résultat final.
4. Vérifier accord exact full/adaptive, marqueurs et coûts inchangés, continuité sans option et poids égaux, erreurs reproductives et coûts cumulés. Inclure des cas analytiques aux bornes 3/7 % et un événement positif synthétique prouvant l'emploi des poids et le maintien de sélection après absorption.

## Constraints and Non-goals

- Aucun changement des lois reproductives, observations, seuils, récompenses existantes, archives ou graines historiques.
- Aucune intégration implicite à la CLI/I19 ; aucun poids biologique, protocole principal ou convergence adopté.
- Un diagnostic d'arrêt n'est pas une ascendance finale et les seules continuations ne donnent pas une ascendance marginale inconditionnelle.

## Definition of Done

- [x] ID1 Le panel est validé et conservé dans chaque passe, avec versions distinctes ; le chemin sans option reste compatible.
- [x] ID2 Full utilise effectivement la pondération, l'échantillonnage sans remise et la cible inclusive inchangée ; bornes et calculs directs sont vérifiés.
- [x] ID3 Quick et adaptive respectent disponibilité/horizons ; accord full/adaptive, critère positif, coûts et propagation des erreurs sont vérifiés.
- [x] ID4 Tests ciblés, modes existants, autosomaux et complets passent sous Nix ; exemple et limites documentés, archives inchangées.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_weighted_pulse.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_block_modes.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (26 octobre 2026) : les quatre commandes retournent 0 avec
**8/9/117/194 tests**. La matrice de 306 configurations, les six états de borne
et douze contrôles positifs vérifient mesures, modes et coûts. Les erreurs et
le rejeu JSON sont contrôlés ; l'[exemple documenté](../science/autosomal-weighted-pulse.md)
a été exécuté sous Nix. Structure, taille, liens, syntaxe et `git diff --check`
vérifiés. Les quatre DoD sont satisfaits ; aucun fichier collatéral, moteur,
CLI, contrat I19, cible, récompense existante ou archive modifié. L'adoption
principale et la convergence M3 restent ouvertes, sans mise à jour du milestone.
