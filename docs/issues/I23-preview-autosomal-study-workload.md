# I23 — Annoncer le coût d'un plan autosomal avant simulation

Milestone: M3
Advances: D9, D10 ; objectif O4
Depends on: I21, I22 ; convergence et protocole principal non établis

## Objective

Permettre d'inspecter le coût logique d'un plan multirésolution avant de lancer ses simulations. Distinguer travail minimal, taille d'un état et précision ponctuelle prévue des compteurs réellement observés après exécution.

## Repository Grounding

- `reich_experiment_v2/study_autosomal_resolution.py` valide les plans I21, mais sa CLI ne propose qu'une exécution intégrale vers une nouvelle destination JSON.
- I22 a produit 18 évaluations et plus de vingt milliards de copies de blocs transmises ; ses deux graines par case ne permettent pas une décision de convergence.
- `selected.py::run_selected` compte candidats, descendants et copies ; la sélection peut rejeter des candidats. N × générations donne le nombre de descendants d'une trajectoire intégrale achevée.
- Les intervalles I18 utilisent des bornes Hoeffding ponctuelles à 95 % pour moyennes et différences ; la fréquence cible utilise Wilson et dépend des résultats.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/selected.py` — sens des compteurs et des rejets.
- `reich_experiment_v2/paleogen_rl/genetics/resolution.py` — méthodes d'intervalle existantes.
- `reich_experiment_v2/tests/test_autosomal_resolution_plan.py` — validation, CLI et protection des sorties.
- `docs/science/autosomal-target-regime-plan.json` et son diagnostic — plan réel à inspecter sans le relancer.

### Expected change paths

- `reich_experiment_v2/study_autosomal_resolution.py` — aperçu déterministe sans appel au moteur.
- `reich_experiment_v2/tests/test_autosomal_workload_preview.py` (new) — calculs, absence de simulation et CLI.
- `docs/science/autosomal-workload-preview.md` (new) — commandes, unités, résultats vérifiés et limites.

## Required Changes

1. Ajouter un aperçu pour un plan explicite I21, validé intégralement avant calcul. Exporter instantané normalisé, identité canonique et empreinte du fichier lorsqu'il provient de la CLI, sous un format distinct des résultats de simulation.
2. Annoncer par résolution et au total le nombre d'évaluations, descendants/acceptations nécessaires à l'achèvement, minima de candidats et de copies transmises, et taille maximale d'un état en entrées alléliques. Les rejets, échecs, allocations temporaires et durées ne doivent pas être convertis en prévisions matérielles non justifiées.
3. Donner le nombre de graines par case et les rayons Hoeffding ponctuels non tronqués correspondant aux moyennes et différences existantes. Indiquer que Wilson dépend des résultats ; ne produire ni estimation d'événement, ni décision d'équivalence ou de convergence.
4. Exposer un mode CLI explicite d'aperçu avec destination nouvelle. Refuser son emploi sans plan, préserver les protections d'écrasement et le comportement sans aperçu. Vérifier l'absence de tout appel de simulation et comparer les prévisions aux coûts de petits runs réels ainsi qu'à l'archive I22.

## Constraints and Non-goals

- Aucun moteur, observation, scénario, estimateur, ancien plan ou résultat archivé modifié.
- Aucun budget de temps/mémoire matérielle, aucune nouvelle graine ou étude longue, aucune résolution principale choisie.
- Un minimum annoncé ne constitue pas un plafond de calcul ni une garantie d'achèvement.

## Definition of Done

- [x] ID1 L'aperçu valide et identifie le plan sans appeler les moteurs ; ses résultats sont déterministes et indépendants du formatage du fichier.
- [x] ID2 Les coûts par résolution et totaux sont exacts pour un run neutre achevé et bornent ceux des runs sélectionnés ; les unités et hypothèses sont explicites.
- [x] ID3 Les rayons correspondent aux formules I18, sans prédiction d'événement ni convergence ; la CLI protège entrées et destinations.
- [x] ID4 Tests ciblés, autosomaux et complets réussissent sous Nix ; l'aperçu I22 et ses limites sont documentés, archives inchangées.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_workload_preview.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : les trois commandes retournent 0 avec **7/95/172
tests**. Les tests interdisent moteur/RNG pour l'aperçu, comparent les comptes
aux petites simulations réelles et à I22, et contrôlent précision et CLI.
L'[aperçu I22 documenté](../science/autosomal-workload-preview.md) a été exécuté
sans relancer ses simulations ; les empreintes de son plan et de son archive
sont inchangées. Structure, taille, liens et `git diff --check` vérifiés.
Les quatre DoD sont satisfaits. Aucun fichier collatéral ni milestone modifié ;
la convergence et le protocole principal M3 restent non établis.
