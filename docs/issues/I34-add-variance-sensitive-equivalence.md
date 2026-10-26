# I34 — Ajouter une équivalence simultanée sensible à la variance

Milestone: M3
Advances: D1, D8, D9 ; objectif O4, exigence R4
Depends on: I32, I33 ; marges et protocole principal non adoptés

## Objective

Ajouter une méthode explicite de Bernstein empirique à effectif fixé pour
évaluer les différences de résolution. Cette option doit exploiter une faible
variance sans changer les marges, les observations ou la méthode historique.

## Repository Grounding

- `weighted_autosomal_equivalence.py` valide des critères v1 et calcule des
  intervalles simultanés Hoeffding indépendants de la variance.
- Le dossier I33 chiffre leur coût élevé au régime cible, sans simulation
  ni adoption de seuil scientifique.
- L'évaluateur I32 vérifie les rapports I31 et recalcule les différences depuis
  les réplicats ; ses règles de décision peuvent être conservées.
- Maurer–Pontil (COLT 2009), théorème 4, donne une borne empirique unilatérale
  pour des observations indépendantes bornées ; son adaptation bilatérale
  simultanée doit être explicitée et vérifiée.

## Change Scope

### Inspect

- `reich_experiment_v2/weighted_autosomal_equivalence.py` — critères, intégrité et décisions.
- `reich_experiment_v2/tests/test_autosomal_weighted_equivalence.py` — contrôles analytiques et I31.
- `docs/science/m3-confirmation-budget.md` — coût et limites de la méthode actuelle.

### Expected change paths

- `reich_experiment_v2/weighted_autosomal_equivalence.py` — option versionnée, prévision et intervalles par comparaison.
- `reich_experiment_v2/tests/test_autosomal_empirical_bernstein.py` (new) — formule, couverture discrète, intégration et compatibilité.
- `docs/science/autosomal-empirical-bernstein.md` (new) — source primaire, dérivation, API et limites.

## Required Changes

1. Exiger une nouvelle version de critères avec une méthode explicite ; conserver
   exactement entrées, formats et résultats v1. Garder le lien au plan, le
   risque global, les marges et le rayon maximal comme entrées pré-déclarées.
2. Pour chaque différence dans [-1,1], utiliser la variance empirique sans biais
   et le théorème 4 à deux queues, avec union sur toutes les comparaisons.
   Refuser moins de deux réplicats. Exporter moyenne, variance, rayon brut et
   intervalle tronqué ; conserver les règles de décision strictes d'I32.
3. Avant simulation, distinguer rayon/effectif sous variance observée nulle et
   garantie conservatrice par l'étendue. Ne pas promettre une précision réelle
   sans connaître les données. Après évaluation, vérifier le rayon réellement
   obtenu pour chaque comparaison et pour la conclusion globale.
4. Vérifier calculs indépendants, cas constants/non constants, frontières,
   couverture par énumération de lois discrètes, entrée invalide, intégration
   I31 et compatibilité v1/I33. Documenter la dérivation et la portée à
   effectif fixé ; aucun choix opportuniste de méthode ni arrêt optionnel.

## Constraints and Non-goals

- Aucun changement des moteurs, plans I31, observations, cible ou archives.
- Ne pas prendre le minimum non corrigé de deux bornes après résultats.
- Une variance observée nulle ne prouve pas une variance vraie nulle ; conserver
  le terme résiduel. Une méthode plus précise n'adopte aucune marge scientifique.
- Pas de simulation longue, arrêt séquentiel, protocole principal ou conclusion
  de convergence M3.

## Definition of Done

- [x] ID1 La méthode exige des critères explicites identifiés ; la v1 reste compatible et les entrées invalides sont refusées.
- [x] ID2 Formule, variance et correction simultanée sont vérifiées, avec couverture discrète et cas limites.
- [x] ID3 Prévisions conditionnelle/pire cas et précision observée sont distinctes ; l'intégration I31 et les statuts sont vérifiés.
- [x] ID4 Tests ciblés, autosomaux et complets passent sous Nix ; source primaire, exemple exécuté et limites documentés.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_empirical_bernstein.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (26 octobre 2026) : **8/164/241 tests** réussissent sous Nix,
sans échec ni test ignoré. ID1 : version/méthode explicites, chargeur,
entrées invalides et aperçus v1 exactement identiques à I33. ID2 :
calcul indépendant, changement d'échelle, variance sans biais, constantes,
stabilité et énumération de 18 lois binomiales (n=30/100/1000).
ID3 : effectifs conditionnel/pessimiste vérifiés, contrôle absorbant I31 réel
à 160 graines × 3 résolutions, précision par comparaison et observations
synthétiques non constantes. ID4 : source primaire et [exemple exécuté](../science/autosomal-empirical-bernstein.md),
136 comparaisons, effectifs 4339/194473 contre 172031 pour Hoeffding.
Structure, taille, syntaxe et espaces vérifiés ; aucun runner, moteur,
observation, archive ou ressource modifié. M3 et ses marges restent ouverts.
