# Audit de clôture M3 — I35, en cours

État au 26 octobre 2026, base `03bcb232d6caf64dc30bc6261ba6c5f76a6f1789`.
**M3 n'est pas clôturé.** I35 formalise les conditions de la dernière étape,
sans certifier à l'avance qu'une confirmation réussira.

## Décisions encore nécessaires

| Décision | État constaté | Effet sur la clôture |
| --- | --- | --- |
| Architecture principale | Aucun protocole adopté ; I30/I33 restent synthétiques | Impossible de fixer le panel principal D1 |
| Portée scientifique | Validation conditionnelle d'une famille ou architecture biologiquement justifiée non tranchée | Les poids partenaires 0.25 ne deviennent pas empiriques |
| Quatre marges absolues | Aucune valeur scientifique adoptée | Impossible de définir l'acceptation avant résultats |
| Précision et risque | Les exemples ne sont pas une décision confirmatoire | Impossible de fixer l'effectif et la garantie |
| Budget de calcul | Non déclaré | Aucun engagement massif de CPU ne peut être planifié raisonnablement |
| Confirmation et adoption | Non réalisées | D1 et l'acceptation scientifique restent ouverts |

Une demande de clôture ne fournit pas les valeurs manquantes. Les choisir
pour rendre les tests ou les simulations acceptés changerait le sens de
l'évaluation. L'Issue attend des décisions explicites, sans changer observations,
seuils cibles ou coefficients existants.

## Proposition de périmètre à trancher

Une clôture **conditionnelle à un modèle synthétique** pourrait retenir une
famille conservatrice I30, en maintenant visibles l'absence de calibration
humaine et les cellules partenaires finies. La famille de coût I33 fournit un
exemple exécutable (4/8/20 blocs, poids `(1,3,3,1)`, L=1), pas une architecture
recommandée biologiquement. Ses 25 % de poids partenaires ne sont pas justifiés
par les observations 3–7 %.

Une clôture portant sur une représentation biologiquement justifiée demande
d'abord une justification indépendante de la carte et des poids. Aucun résultat
de simulation du dépôt ne fournit cette justification par lui-même.

Dans les deux cas, le plan final doit préciser les 17 scénarios, N=1450 et
6993 générations si le régime cible actuel est retenu, les marges absolues
pour ascendance/probabilité cible/P10/critère conjoint, le risque simultané,
le rayon demandé, l'effectif fixe, de nouvelles graines et une règle d'adoption.
Les arrondis du pulse et les paramètres de scénario restent inchangés.

## Conditions d'acceptation

Le gel précède les résultats confirmatoires. Les sorties réelles doivent
conserver plan, critères, implémentation, environnement, tous les réplicats
et leurs coûts. Les comparaisons ne peuvent pas être arrêtées ou sélectionnées
selon leurs scores. Les échecs ou une précision insuffisante sont des résultats
à conserver, pas des motifs pour retoucher les critères.

L'adoption vient après satisfaction de la règle fixée. Elle doit porter sur
une définition identique de la métrique principale pour tous les scénarios,
avec un chemin historique explicite conservant les anciennes références.
La portée d'une équivalence dans une famille finie doit rester distincte
d'une convergence universelle, d'une calibration humaine ou d'une validation
de l'hypothèse historique.

L'[audit technique I24](m3-audit.md) reste une preuve datée de D2–D10 dans son
périmètre ; il n'est pas réécrit comme preuve de confirmation. Les validations
actuelles sont consignées ci-dessous après exécution. Aucun plan final ni
critère numérique n'est inventé pour combler les décisions ouvertes.

## Vérifications de reprise

Depuis `reich_experiment_v2/`, les commandes suivantes réussissent le
26 octobre 2026 sous Nix :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_ancestry.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Résultats réels : **8/164/241 tests**, sans échec ni test ignoré. Le contrôle
`verify_provenance.verify` confirme **32 ressources conformes**, aucun fichier
manquant ou modifié. Cela maintient les garanties techniques précédentes ;
aucune confirmation scientifique nouvelle n'est déduite de ces tests.

| Critère | État de clôture |
| --- | --- |
| D1 — Protocole principal commun | Ouvert : adoption absente, chemin par défaut historique |
| D2–D5 — Mesure, transmission, recombinaison, contrôle neutre | Garanties techniques maintenues par les assertions réexécutées, dans leur périmètre |
| D6–D7 — Quick et accord adaptive/full | Garanties techniques maintenues, sans preuve de convergence entre résolutions |
| D8 — Rapport multirésolution | Rapports historiques présents ; confirmation pondérée au régime cible encore absente |
| D9 — Coûts et mode | Prévisions et compteurs disponibles ; budget final non adopté |
| D10 — Tests autosomaux | 164 tests autosomaux réussis |
| R4 et acceptation scientifique globale | Ouverts : aucun résultat confirmatoire sous critères adoptés |

## Mesure d'ingénierie indépendante

Un seul réplicat full a été exécuté pour éclairer le budget, sous la base
logicielle indiquée : scénario `reich_plus_symmetric_1pct`, N=1450, f=0.05,
fraction masculine=0.5, G=6993, 20 blocs de la famille de coût I33,
graine **720000**, sans posterior. Il ne réutilise aucune des graines
620000–620002 du gabarit de coût. Cette graine d'ingénierie est à exclure
de la future confirmation.

Le [rapport complet](m3-engineering-benchmark.json) conserve configuration,
contrat, évaluation, versions et empreintes d'implémentation. Son SHA-256 est
`5eda09c4332f0a74f6def5236afed2a22b65e19ea9ddcced76f99867685f955a`.
Le temps observé de la seule évaluation est **6.747539304 s écoulées** et
**6.701541569 s CPU**. Il produit **10139850 descendants**, propose
**10179937 candidats**, transmet **407197480 copies de blocs** et utilise
un état de **58000 entrées alléliques**. Horizon, statut et identités de coûts
ont été vérifiés directement dans le rapport. Ces mesures ne prédisent pas
le coût de tous les scénarios/résolutions, les rejets futurs ou le pic mémoire.

Le résultat est une mesure d'ingénierie, **pas une confirmation, un choix de
marges ou une preuve de convergence**. Les résultats génétiques sont conservés
pour le rejeu ; ils ne sont pas utilisés pour adapter les critères.

Pour situer la taille du calcul, les prévisions I34 donnent pour le seul
gabarit de coût, K=136 et α=0.05 :

| Rayon absolu de calcul | Effectif/cellule si variance observée nulle | Effectif/cellule suffisant par l'étendue | Évaluations totales dans le premier cas |
| --- | ---: | ---: | ---: |
| 0.01 (1 point) | 4339 | 194473 | 221289 |
| 0.001 (0.1 point) | 43377 | 18676014 | 2212227 |

Ces rayons ne sont pas des marges scientifiques adoptées. Le premier cas
est conditionnel, pas une garantie de précision ; les scénarios réellement
observés peuvent demander une étude plus précise. Les effectifs restent
ceux de la méthode I34, pas une impossibilité universelle d'autres méthodes.

## État de l'Issue de clôture

I35 reste non résolue : aucune décision finale sur la portée, les marges et
le budget n'est encore enregistrée. Ses quatre DoD restent décochés.
Le test `test_m3_principal_protocol.py` n'est pas encore créé ; aucune
découverte vide n'a été annoncée comme validation. Aucun défaut d'implémentation
n'est inféré des décisions manquantes, aucun marqueur d'acceptation n'est
forcé, et aucun commit partiel n'est créé.
