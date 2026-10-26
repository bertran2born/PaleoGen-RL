# I31 — Exécuter des études sur les familles pondérées conservatrices

Milestone: M3
Advances: D1, D8, D9 ; objectifs O1/O4, exigences R1/R3/R4
Depends on: I29, I30 ; convergence et protocole principal non établis

## Objective

Exécuter une étude full sur une famille I30 déclarée, avec aperçu des coûts,
résultats pondérés rejouables et écarts entre résolutions. Cette étape rend
possible une comparaison contrôlée sans changer les poids des partenaires.

## Repository Grounding

- `weighted_refinement.py` construit des protocoles I28 emboîtés et identifiés,
  mais ne produit aucune étude ou statistique entre résolutions.
- `run_experiment.py::run_block_full` accepte les panels pondérés depuis I29.
- `study_autosomal_resolution.py` fournit agrégation des métriques, écarts
  appariés et coûts, mais ses études restent à poids égaux et partenaires `2/B`.
- Les intervalles existants sont ponctuels et Monte Carlo ; ils ne démontrent
  aucune équivalence statistique ou convergence dans le régime historique.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/weighted_refinement.py` et `weighted_protocol.py` — construction et rejeu.
- `reich_experiment_v2/study_autosomal_resolution.py` et `tests/test_autosomal_resolution_plan.py` — rapports et validations.

### Expected change paths

- `reich_experiment_v2/study_weighted_autosomal_resolution.py` (new) — plan strict, aperçu et exécution CLI/API.
- `reich_experiment_v2/tests/test_autosomal_weighted_study.py` (new) — résultats, provenance, coûts, erreurs et rejeu.
- `docs/science/autosomal-weighted-study.md` (new) — format, exemple et limites.

## Required Changes

1. Définir un plan JSON versionné déclarant protocole de départ I28,
   paramètres de famille I30, graines distinctes et scénarios existants.
   Valider tout avant simulation ; refuser champs manquants, inconnus,
   dupliqués ou non finis. Conserver instantané, identité canonique et
   empreinte des octets du fichier source.
2. Exécuter toutes les combinaisons scénario/résolution/graine en full avec
   les contrats produits par I30, sans modifier les scénarios. Conserver
   paramètres réalisés, contrats, rapports I27, mesures pondérées et provenance
   d'implémentation nécessaire au rejeu. Rapporter moyennes, incertitudes
   ponctuelles et différences appariées avec la résolution la plus fine.
3. Fournir un aperçu sans moteur ni RNG : mode, nombre d'évaluations,
   descendants attendus à achèvement, minima de candidats/transmissions et
   taille d'un état. Rapporter ensuite les coûts réels agrégés, rejets inclus.
4. Exposer plan/aperçu/exécution dans une CLI à destination inexistante.
   Les erreurs reproductives ne produisent aucun rapport de réussite.
   Garder les statuts exploratoire et convergence non établie ; ne pas
   transformer des intervalles ponctuels en acceptation d'équivalence.

## Constraints and Non-goals

- Préserver runners historiques, contrats, moteurs, graines, observations,
  cible et archives ; aucun posterior ajouté ou paramètre ajusté aux résultats.
- Pas de seuil d'équivalence ou protocole principal choisi, ni de longue étude
  confirmatoire lancée. Les partenaires restent des cellules finies intactes.
- Une graine commune n'implique pas de trajectoires ou flux RNG identiques
  entre résolutions. Les coûts logiques ne bornent pas le temps ou pic mémoire.

## Definition of Done

- [x] ID1 Plan strict, famille, versions, identités et instantanés sont vérifiés ; erreurs refusées avant simulation.
- [x] ID2 Réplicats et rejeu concordent avec l'API I27/I29 ; métriques, différences et provenance sont vérifiées sur plusieurs scénarios/graines.
- [x] ID3 Aperçu sans simulation et coûts réels sont cohérents ; CLI sans écrasement et échecs sans rapport sont vérifiés.
- [x] ID4 Tests ciblés, autosomaux et complets réussissent sous Nix ; exemple exécuté et limites documentées.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_weighted_study.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (26 octobre 2026) : les trois commandes réussissent avec
**6/145/222 tests**, sans échec ni test ignoré. ID1 : erreurs pré-moteur,
normalisation indépendante, empreintes canonique/fichier, reconstruction JSON.
ID2 : 153 réplicats (17 scénarios × 3 résolutions × graines 17/18/19)
comparés à I27, métriques et écarts recalculés, hashes d'implémentation vérifiés.
ID3 : aperçu sans RNG/moteur, minima comparés au travail réel, CLI full/preview,
refus de destinations existantes/invalides et échec reproductif injecté sans
rapport. ID4 : suites complètes et [exemple CLI exécuté](../science/autosomal-weighted-study.md),
18 évaluations et 2160 descendants à N=40/G=3. Le régime N=1450/G=6993 est
seulement prévu sans simulation. Structure, taille, syntaxe et espaces
vérifiés ; aucun fichier collatéral, moteur, archive ou ressource modifié.
M3 D1 et la convergence restent ouverts, sans mise à jour du milestone.
