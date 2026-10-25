# Sensibilité à la résolution — protocole I14 / M3

## Plan fixé avant exécution

Cette étude synthétique réutilise le contrôle neutre I13, sans sélection ni
marqueurs uniparentaux. N=40 diploïdes, 20 mâles puis 20 femelles ; individus
0 et 20 modernes sur les deux homologues de tous les blocs, autres copies
archaïques. Chaque sexe commence donc à 5 %. Horizon : 20 générations intégrales,
y compris les états absorbants. Résolutions : **8, 32, 128** blocs de poids égal.
Graines : **410000 à 410127 incluses**, toutes conservées à chaque résolution.
Les mêmes graines ne garantissent pas des trajectoires couplées : les dimensions
changent la consommation RNG. Aucune graine I13 ou M2 n'est remplacée.

La carte représente un segment abstrait d'étendue L=1, avec B points ordonnés
espacés de d=L/(B−1). Chaque frontière bascule indépendamment avec
`r = (1 − exp(−2d))/2`. Cette définition synthétique conserve la probabilité
de parité impaire entre extrémités : `(1 − (1−2r)^(B−1))/2 = (1−exp(−2L))/2`.
Elle se raffine sans augmenter arbitrairement l'étendue de recombinaison.
Elle n'est pas une carte humaine calibrée ; blocs de poids égal et points aux
extrémités restent une approximation de discrétisation. L=0 permet le contrôle
sans recombinaison. Le rapport conserve toutes les probabilités I12.

## Statistiques fixées

La cible inclusive est toujours **[0.03, 0.07]**, sur la moyenne diploïde totale
I11 à l'horizon final. Aucun conditionnement ni filtrage des réplicats.
Par résolution : moyenne d'ascendance, effectif dans la cible, fréquence et
intervalle de Wilson bilatéral 95 % (z=1.959963984540054). La moyenne reçoit une
borne de Hoeffding bilatérale 95 %, rayon `sqrt(log(40)/(2n))`, tronquée à [0,1].
Pour chaque résolution autre que la plus fine : différences « résolution moins
plus fine » des moyennes et des indicatrices de cible, par graine. Chaque
différence est dans [−1,1] ; rayon de Hoeffding `sqrt(2*log(40)/n)`, tronqué à
[−1,1]. Les répétitions sont indépendantes entre graines, sans supposer
l'indépendance entre résolutions pour une même graine. Intervalles ponctuels,
sans garantie simultanée ni incertitude historique ; ils peuvent être larges.

Il n'existe aucun seuil d'acceptation de convergence dans cette étude. Des écarts
faibles ou des intervalles contenant zéro ne démontrent pas l'équivalence.
Aucune résolution principale ne sera choisie à partir de ces résultats.

## Sortie, coûts et rejeu

`python -m paleogen_rl.genetics.resolution --output CHEMIN` produit un JSON strict
en création exclusive. Aucun écrasement autorisé. L'API `run_resolution_study`
permet des configurations de test explicites ; le lancement CLI applique le
plan ci-dessus. Le JSON versionne le protocole, les briques I11/I12/I13, NumPy
et le générateur RNG. Chaque résolution contient carte, empreintes de l'état
initial, dénominateur, valeurs et nombres de copies finaux par graine.
Le plan d'initialisation suffit à reconstruire cet état synthétique.

Les unités I13 sont cumulées sur tous les réplicats : descendants produits et
copies transmises. Les entrées d'état indiquent la taille d'une population à
une résolution ; le maximum entre résolutions est déclaré séparément du cumul
de travail. Les simulations sont séquentielles, sans conservation des populations
finales ; les résumés des réplicats occupent O(n*nombre_de_résolutions). Aucun
temps matériel ni pic réel d'allocation ne sont revendiqués.

Pour rejouer le rapport archivé, relancer la commande de l'issue avec une
**nouvelle destination**, puis comparer les JSON dans le même environnement Nix.
Une identité numérique universelle entre versions de NumPy n'est pas garantie.
Cette étude avance M3 D8/D9 dans le périmètre neutre uniquement ; l'intégration
des DMI, des modes pulse et la résolution principale restent ouvertes. M1 D8/D9
restent ouverts également. Aucun DoD global de milestone n'est modifié.

## Résultats exécutés le 25 octobre 2026

Le [rapport JSON](autosomal-resolution-report.json) a été généré sous Nix avec
NumPy 2.5.3 et PCG64, puis une seconde exécution indépendante du calcul a
reproduit exactement toutes ses valeurs JSON.

| Blocs | Ascendance moyenne | Dans 3–7 % | Probabilité, IC Wilson 95 % | Copies transmises | Entrées d'état |
| --- | --- | --- | --- | --- | --- |
| 8 | 0.046155 | 24/128 | 0.187500 [0.129361, 0.263849] | 1 638 400 | 640 |
| 32 | 0.046686 | 27/128 | 0.210938 [0.149213, 0.289507] | 6 553 600 | 2 560 |
| 128 | 0.045050 | 28/128 | 0.218750 [0.155905, 0.297984] | 26 214 400 | 10 240 |

Chaque résolution produit 102 400 descendants ; le total est 307 200 descendants
et 34 406 400 copies transmises. Les coûts augmentent linéairement avec B dans
ces unités logiques. L'étude ne mesure pas le coût matériel réel.

Par rapport à 128 blocs, les écarts moyens d'ascendance valent +0.001105 (8)
et +0.001636 (32). Les écarts de probabilité cible valent −0.031250 et
−0.0078125, avec intervalles de Hoeffding respectifs [−0.271331, 0.208831]
et [−0.247893, 0.232268]. Le JSON fournit aussi les bornes sur les moyennes.
Cette incertitude large ne démontre aucune convergence, même si les estimations
ponctuelles sont proches. Ni les paramètres ni les graines ni les bornes n'ont
été adaptés après lecture des résultats.

## Vérification

Depuis `reich_experiment_v2/`, les commandes Nix de
[l'issue I14](../issues/I14-report-neutral-autosomal-resolution.md) ont réussi :
7 tests ciblés, 32 autosomaux, 35 pulse et 109 complets. Les tests vérifient
la parité de recombinaison entre extrémités, chaque réplicat face à I13, les
statistiques analytiques (dont les bornes inclusives), les coûts, les erreurs,
le JSON strict et le refus d'écrasement. Les tests et moteurs antérieurs restent
inchangés. L'archive a également été comparée au résultat intégral d'une seconde
exécution sous Nix, avec égalité de toutes les valeurs JSON.
