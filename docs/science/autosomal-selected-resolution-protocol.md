# Sensibilité à la résolution sous sélection — I18 / M3

## Plan fixé avant toute exécution

Le diagnostic utilise **tous les 17 scénarios nommés** présents dans
`run_experiment.SCENARIOS`, avec leurs paramètres inchangés et dominance additive.
Il s'agit de simulations synthétiques de contrôle, sans posterior SI1, pas d'une
reproduction du préprint. N=40, f=0.05, fraction masculine=0.5, horizon intégral
**20 générations**, résolutions **8, 32, 128**, graines **410000 à 410127**
incluses, appariées entre scénarios/résolutions. Ces graines reprennent le lot
public I14 pour son contrôle neutre ; aucune graine ni archive n'est modifiée.
Chaque résolution représente au départ exactement un mâle et une femelle
modernes, homozygotes sur tous les blocs (indices 0 et 20).

Les blocs sont ordonnés aux positions `i/(B−1)` sur un segment abstrait de
longueur **L=1**. Comme I14, la probabilité par frontière vaut
`r=-expm1(-2*L/(B−1))/2` ; la parité de recombinaison entre extrémités reste
`(1-exp(-2L))/2` à chaque résolution. Les partenaires sont toujours le premier
bloc (mtDNA, position 0) et le dernier (Y, position 1), même au contrôle neutre.
Leurs identifiants et la carte complète figurent dans chaque résultat.

Ces positions aux extrémités sont des choix synthétiques explicites. Elles ne
reproduisent pas les loci 0/1 indépendants du moteur historique ni une carte
humaine. Le panel est de poids égaux ; le poids d'un bloc partenaire vaut 1/B,
et le poids cumulé des deux partenaires 2/B. Le raffinement réduit donc aussi
la portion du panel portant directement le marqueur sélectionné. C'est une
approximation du modèle de blocs à quantifier, sans lui attribuer une longueur
biologique fixe. Garder l'indice 1 comme second partenaire aurait déplacé sa
position avec B ; le présent diagnostic évite cette modification implicite.

## Statistiques et erreurs fixées

Chaque réplicat est évalué par `run_block_full` I16/I17 : mesure totale I11,
événement des dix mâles sans remise et cible inclusive inchangée **3–7 %**.
Tous les réplicats sont conservés, y compris ceux où P10 ou le critère conjoint
est nul ; aucun conditionnement aux marqueurs ou à l'ascendance n'est effectué.
Les annotations n'excluent pas les partenaires du dénominateur commun.

Par scénario/résolution : moyenne d'ascendance, fréquence cible (avec effectif),
moyenne de P10 et moyenne du critère conjoint. Réutiliser les bornes I14 :
Wilson bilatéral 95 % pour la fréquence cible, Hoeffding ponctuel 95 % pour les
autres moyennes dans [0,1], rayon `sqrt(log(40)/(2n))`. Pour chaque résolution
autre que la plus fine, calculer les différences par graine « résolution moins
plus fine » pour ces quatre métriques, avec Hoeffding dans [−1,1], rayon
`sqrt(2*log(40)/n)`. L'appariement n'exige pas l'indépendance entre résolutions ;
l'hypothèse d'indépendance concerne les graines distinctes. Les flux RNG changent
avec B et ne donnent pas des trajectoires couplées bloc par bloc.

Les intervalles sont ponctuels, sans correction pour toutes les comparaisons,
et représentent seulement l'incertitude Monte Carlo. Une estimation jointe nulle
garde une borne supérieure positive. Aucune marge d'équivalence, règle de
sélection de résolution ou affirmation de convergence n'est déduite des résultats.
La faible taille, le petit nombre de graines et l'horizon de test ne permettent
pas de choisir une résolution pour 6 993 générations et N=1 450.

Un échec reproductif ou une erreur d'évaluation interrompt l'étude, sans supprimer
le réplicat ni écrire un rapport de réussite partiel. L'export est en création
exclusive et refuse aussi les liens symboliques pendants vers une sortie.

## Provenance, coûts et rejeu

Le rapport conserve paramètres demandés/réalisés, initialisation et ses empreintes,
version du moteur et de la mesure, NumPy/PCG64, cartes et résultats individuels.
Les SHA-256 des fichiers d'implémentation utilisés et du verrou Nix identifient
l'environnement local, même sans commit. Aucune source tierce n'est copiée dans
ce rapport. Le format est `selected-autosomal-resolution-v1`, le mode est `full`.

Les compteurs I15 incluent tous les candidats et copies transmis, rejets compris,
et sont additionnés par résolution/scénario et sur toute l'étude. La taille d'un
état est un maximum, pas un cumul ni un pic mémoire mesuré. Aucun benchmark de
temps matériel n'est revendiqué.

Commande depuis `reich_experiment_v2/` (destination nouvelle obligatoire) :

```sh
nix develop -c python study_autosomal_resolution.py \
  --output ../docs/science/autosomal-selected-resolution-report.json
```

Pour rejouer : utiliser une nouvelle destination dans le même environnement et
comparer les valeurs JSON complètes, empreintes d'implémentation comprises.
L'API accepte des résolutions, graines et sous-ensembles de scénarios explicites
pour les tests ; la commande applique le plan ci-dessus. Ne pas mélanger les
comparaisons à positions partenaires différentes comme si seule B changeait.

## Résultats exécutés le 25 octobre 2026

Le [rapport archivé](autosomal-selected-resolution-report.json) contient les
6 528 évaluations attendues, sans suppression de réplicat et sans échec.
NumPy=2.5.3, PCG64 ; les dix fichiers d'implémentation/verrou possèdent leurs
empreintes. Une seconde exécution CLI complète vers une destination temporaire
a reproduit le JSON **octet pour octet**, y compris ces empreintes.

Extrait des effectifs dans la cible finale 3–7 %, sur 128 graines par case
(les 17 scénarios et leurs intervalles sont présents dans le JSON) :

| Scénario | 8 blocs | 32 blocs | 128 blocs |
| --- | --- | --- | --- |
| neutral | 24 | 27 | 28 |
| reich_point | 31 | 26 | 31 |
| reich_plus_symmetric_1pct | 33 | 24 | 25 |
| reich_plus_favor_mod_1pct | 35 | 25 | 27 |
| reich_plus_favor_arch_1pct | 27 | 20 | 33 |

Sur toutes les comparaisons à 128 blocs, l'écart absolu maximal de moyenne
d'ascendance vaut **0.0114342**, soit environ 1.14 point de pourcentage ; celui
de probabilité cible vaut **0.1015625**, soit environ 10.16 points. Le rayon
préfixé des intervalles d'écart est **0.2400807** : ils ne démontrent ni une
équivalence ni une différence statistiquement établie. Aucune résolution
principale n'est retenue.

Les 51 estimations moyennes du critère conjoint sont nulles sur ce lot court.
Chacune conserve cependant un intervalle de Hoeffding **[0, 0.12004035]**.
Cela ne prouve pas que la probabilité vraie est nulle, ni que les résolutions
sont équivalentes pour cet événement rare. Aucun paramètre, graine ou borne
n'a été changé pour obtenir ces résultats.

Travail total : **5 238 034 candidats**, **5 222 400 descendants acceptés et
produits**, **586 652 080 copies de blocs transmises**. Les 15 634 rejets restent
comptabilisés. La plus grande population contient 10 240 entrées alléliques,
sans prétention de mesurer le pic réel de mémoire. Le contrôle neutre retrouve
les moyennes I14 aux trois résolutions ; le test de continuité compare aussi
directement les copies et la carte d'une graine archivée.

## Vérification de l'issue

Les quatre suites de [I18](../issues/I18-report-selected-autosomal-resolution.md)
passent sous Nix : **8 tests ciblés, 71 autosomaux, 35 pulse, 148 complets**.

| DoD I18 | Preuve |
| --- | --- |
| ID1 | Plan préfixé puis export des 17 scénarios sur 8/32/128 blocs ; cartes, positions et poids des partenaires déclarés. |
| ID2 | `test_each_replicate_replays_directly_with_the_realised_selection`, cartes à étendue constante, statistiques et différences analytiques, coûts et état initial à horizon nul. |
| ID3 | Tests de JSON strict, empreintes, répétabilité, entrées invalides, erreurs injectées et refus d'écrasement ; rejeu CLI intégral identique octet pour octet. |
| ID4 | Résultats, limites et bilan M3 consignés dans ce document, avec convergence explicitement non établie. |
| ID5 | Les quatre suites Nix réussissent, sans modification des assertions ni des implémentations précédentes. |

Les échecs d'évaluation du test CLI sont injectés pour vérifier la propagation
et l'absence de rapport incomplet ; l'étude réelle n'a rencontré aucun échec.
Les assertions statistiques suivent les bornes I14 inchangées, sans ajustement
aux résultats. Aucun fichier préexistant, ressource tierce ou milestone modifié,
et aucun commit/push effectué.

## État de M3 après I18

Les critères ci-dessous décrivent la **couverture technique constatée**, pas
une mise à jour des cases du milestone ni une validation historique globale.

| DoD M3 | Couverture et limites |
| --- | --- |
| D1 | Tous les scénarios CLI avec carte explicite utilisent le même panel et dénominateur (I16/I17). La CLI sans carte conserve le proxy historique ; le protocole autosomal principal de v0.1 n'est pas encore adopté. |
| D2 | Annotations partenaires sans sélection : définition, dénominateur et trajectoires inchangés, vérifiés par I11/I15. |
| D3 | Ségrégation mendélienne vérifiée par I12, graines et tolérances pré-enregistrées. |
| D4 | Invariants à recombinaison nulle/active vérifiés par I12/I13/I15, y compris états absorbants et transmission parentale. |
| D5 | Contrôle neutre à espérance 5 % vérifié par I13 sur 1 024 graines pour chacune des deux cartes. |
| D6 | Aucun résultat autosomal final en quick : I11/I17, même à horizon atteint. |
| D7 | Accord exact adaptive/full sur les 216 références I17 et 12 contrôles synthétiques à critère positif ; périmètre de graines/cartes documenté. |
| D8 | Rapports à trois résolutions livrés : neutre I14 puis tous les scénarios nommés sous sélection I18. La convergence au protocole historique cible n'est pas établie. |
| D9 | Modes, cartes, coûts logiques et rejets sont tracés par évaluation et dans les études. La résolution et la carte principales restent à fixer ; aucun coût matériel calibré revendiqué. |
| D10 | Les 71 tests autosomaux passent, avec scénarios épistatiques actifs, trois dominances dans I15/I17 et trois résolutions dans I18. |

Le reste du travail M3 porte principalement sur l'adoption d'un protocole
autosomal de référence (carte, résolution, positions/poids partenaires), sa
validation de résolution avec précision numérique déclarée au régime visé
N=1 450 et 6 993 générations, puis l'audit d'acceptation qui relie chaque
évaluation comparable à ce protocole. Un lot synthétique court ne lève pas
ces décisions. Les modèles restent exploratoires ; une calibration humaine
n'est pas démontrée. La dépendance transitive M1 D8/D9 demeure non clôturée
dans les documents d'acceptation de M2. Le milestone M3 reste inchangé.
