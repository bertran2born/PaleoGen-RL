# I17 — Évaluer les blocs en modes rapide et adaptatif sans mesure finale prématurée

Milestone: M3
Advances: D6, D7, D9, D10 ; objectifs O3/O4
Depends on: I11–I16 ; M1 D8/D9 ouverts

## Objective

Exposer `quick` et `adaptive` pour le moteur de blocs, avec disponibilité autosomale explicite et accord du critère conjoint avec `full` sur des références fixées. Préserver les trajectoires intégrales et comptabiliser tout le travail, y compris un rejeu.

## Repository Grounding

- `reich_experiment_v2/paleogen_rl/genetics/selected.py::run_selected` simule seulement l'horizon complet avec RNG local ; aucun arrêt par absorption n'existe.
- `reich_experiment_v2/paleogen_rl/genetics/pulse.py::evaluate_block_pulse` fournit mesure finale I11 et critère conjoint ; I16 refuse les modes anticipés dans la CLI.
- `reich_experiment_v2/run_experiment.py::run_mode` distingue déjà ces trois modes pour le moteur historique, dont les règles et tirages doivent rester inchangés.
- `measure_ancestry` fournit des valeurs finales nulles en `quick`, même si l'horizon est atteint.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/ancestry.py` — disponibilité des mesures.
- `reich_experiment_v2/tests/test_pulse_modes.py` — sémantique historique de comparaison.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/selected.py` — arrêt optionnel après absorption des deux marqueurs.
- `reich_experiment_v2/paleogen_rl/genetics/pulse.py` — politique des modes et rapports de chaque passe.
- `reich_experiment_v2/run_experiment.py` — projection CLI et agrégation des coûts.
- `reich_experiment_v2/tests/test_autosomal_block_modes.py` (new) — preuves des trois modes.
- `reich_experiment_v2/tests/test_autosomal_pulse.py` — retirer uniquement le refus des deux modes désormais supportés.
- `docs/science/autosomal-pulse-protocol.md` — contrats, références préfixées et preuves.

## Required Changes

1. L'arrêt rapide est permis uniquement après une génération complète lorsque mtDNA et Y sont chacun fixés ou perdus. Il ne consomme aucun tirage et ne désactive aucune sélection. Le préfixe de trajectoire doit être identique à celui de `full` pour les mêmes entrées et graine.
2. `quick` ne produit ni ascendance finale, ni indicatrice cible, ni critère conjoint autosomal évalué. Conserver génération réelle, panel et diagnostic intermédiaire explicitement nommé, même si l'horizon est atteint.
3. `adaptive` utilise cette première passe : si P10=0, signaler l'ascendance non évaluée et un critère conjoint nul ; sinon rejouer la même graine jusqu'à l'horizon complet sans accélération de sélection. Refuser une divergence des marqueurs, un horizon incomplet ou tout échec reproductif exécuté.
4. Déclarer modes, générations, disponibilité et coûts de chaque passe et leur cumul. Versionner les nouvelles sorties anticipées sans changer le format intégral I16. Ne jamais estimer la fréquence autosomale inconditionnelle depuis les seules continuations positives.
5. Vérifier les références définies avant exécution dans le protocole : cas neutres et sélectionnés, cartes nulle/active, graines et dominances fixées. Inclure une réussite conjointe synthétique non nulle, les échecs, le rejeu CLI et la compatibilité intégrale/historique.

## Constraints and Non-goals

- Aucun changement d'observation, cible, pénalité, graine historique ou moteur de référence.
- Pas de convergence sous sélection, calibration de carte, résolution principale ni clôture globale M3.

## Definition of Done

- [x] ID1 L'arrêt rapide préserve le préfixe intégral et ne fournit aucune mesure autosomale finale.
- [x] ID2 `adaptive` et `full` concordent sur le critère conjoint et les marqueurs pour les références préfixées, y compris une réussite non nulle.
- [x] ID3 Disponibilité, générations, coûts de toutes les passes et rejeu sont vérifiés ; aucune statistique autosomale inconditionnelle n'est annoncée en adaptatif.
- [x] ID4 Les erreurs reproductives/incomplètes et divergences restent des erreurs, sans sortie de réussite.
- [x] ID5 CLI, tests autosomaux, pulse et complets réussissent sous Nix ; compatibilité et limites documentées.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_block_modes.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : commandes réussies avec **9, 63, 35 et 140 tests**.
Préfixes comparés sur 18 configurations et indisponibilité même à horizon atteint
(ID1) ; matrice préfixée de 216 configurations et 12 fixtures à critère conjoint
égal à 1 (ID2). CLI répétée/rejouée pour tous les scénarios, disponibilités et
coûts cumulés vérifiés (ID3). Erreurs d'écran/continuation, divergence et létalité
réelle CLI sans fichiers de réussite vérifiées (ID4). Après correction de la
portée des coûts d'erreur, les 9 tests ciblés et 140 complets passent de nouveau.
Le test I16 de refus des modes est adapté au comportement intentionnel ; ses
autres contrôles et les tests M2 restent intacts (ID5). Aucun moteur historique,
observation ou milestone modifié ; contrôles de whitespace sans diagnostic.
Aucun commit ni push.
