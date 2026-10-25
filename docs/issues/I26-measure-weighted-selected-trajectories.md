# I26 — Mesurer les trajectoires sélectionnées avec un panel pondéré explicite

Milestone: M3
Advances: D1 ; exigences R1/R2/R5, invariants I1/I2
Depends on: I15, I17, I25 ; protocole principal et convergence non établis

## Objective

Rendre la mesure pondérée I25 utilisable sur les états initial et final du moteur sélectionné, sans modifier sa dynamique. Garantir la traçabilité de l'option et l'identité des trajectoires avec le chemin à poids égaux pour une même configuration reproductive.

## Repository Grounding

- `paleogen_rl/genetics/selected.py::run_selected` produit états, marqueurs, rapports et coûts ; ses mesures initiale/finale appellent exclusivement I11 à poids égaux.
- I25 expose `WeightedBlockPanel` et `measure_weighted_ancestry` avec poids positifs, justification, observable distincte et disponibilité conforme aux modes.
- Le moteur accepte un arrêt sur absorption des marqueurs ; sa mesure finale quick reste indisponible, même à horizon atteint.
- Les adaptateurs pulse et CLI actuels reposent sur le format I11 ; aucune intégration pondérée ne doit y être implicite.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/weighted_ancestry.py` — validation, unités et disponibilité I25.
- `reich_experiment_v2/tests/test_autosomal_selected.py` — sélection, reproductibilité et rapports d'échec existants.
- `reich_experiment_v2/paleogen_rl/genetics/pulse.py` — consommateurs du rapport historique à préserver.
- `docs/science/autosomal-weighted-measurement.md` — portée scientifique de la pondération.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/selected.py` — choix explicite de mesure et métadonnées distinctes.
- `reich_experiment_v2/tests/test_autosomal_weighted_selected.py` (new) — identité des trajectoires, rapports, erreurs et rejeu.
- `docs/science/autosomal-weighted-simulation.md` (new) — API, preuves et limites.

## Required Changes

1. Accepter optionnellement un panel pondéré dont le panel ordonné est exactement celui de la carte de recombinaison. Refuser type ou identité incompatibles avant toute création du RNG. L'absence de l'option conserve les champs et le comportement existants.
2. Avec l'option, appliquer I25 aux états initial et final et exporter les poids, leur origine, la version de mesure et une version de rapport explicite. Les marqueurs, sélection, transmission, graines et compteurs ne dépendent pas des poids.
3. Conserver l'indisponibilité quick, l'horizon intégral et les erreurs reproductives. Un échec ne fournit jamais de mesure finale ; son rapport conserve configuration pondérée et coûts partiels.
4. Prouver l'identité des populations, marqueurs, coûts et états RNG finaux avec/sans pondération pour les scénarios nommés et dominances existantes. Vérifier les mesures par calcul direct sur les états, les poids égaux, la répétabilité et le rejeu depuis la configuration exportée.

## Constraints and Non-goals

- Ne pas modifier les lois de reproduction/sélection, moteur M2, cibles, scores, observations ou archives.
- Ne pas intégrer implicitement cette option à pulse, la CLI ou I19 ; ces consommateurs gardent leurs contrats actuels.
- Aucun panel principal, poids biologique, carte physique ou convergence adopté. L'égalité de trajectoires à carte fixée n'est pas une convergence entre résolutions.

## Definition of Done

- [x] ID1 Le panel pondéré est accepté explicitement et les incompatibilités sont refusées avant RNG ; le rapport sans option conserve son contrat.
- [x] ID2 Les comparaisons réelles vérifient populations, marqueurs, coûts et RNG identiques pour les scénarios et dominances testés.
- [x] ID3 Mesures initiale/finale, versions, poids et rejeu sont cohérents ; quick et échecs ne divulguent aucune mesure finale admissible.
- [x] ID4 Tests ciblés, sélection existante, autosomaux et complets réussissent sous Nix ; les limites sont documentées.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_weighted_selected.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_selected.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : les quatre commandes retournent 0 avec
**6/11/109/186 tests**. Les 102 comparaisons couvrent les 17 scénarios, trois
dominances et deux cartes, avec états RNG et coûts identiques. Mesures,
rejeu, quick et erreurs sont vérifiés ; l'[exemple documenté](../science/autosomal-weighted-simulation.md)
a aussi été exécuté sous Nix. Structure, taille, liens et `git diff --check`
vérifiés. Les quatre DoD sont satisfaits, sans fichier collatéral, changement
de dynamique, cible, score, adaptateur ou archive. L'adoption principale et la
convergence M3 restent ouvertes ; aucun milestone n'est modifié.
