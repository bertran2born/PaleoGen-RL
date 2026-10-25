# Transmission phasée de blocs — protocole I12 / M3

## Hypothèses et portée

Ce protocole est écrit avant la première exécution des tests I12. Ses graines,
effectifs et seuils ne seront pas ajustés aux résultats pour les faire passer.
Il ne décrit pas des données observées ou une calibration génomique humaine.

Un état contient N individus, deux homologues et B blocs ordonnés du panel I11.
Chaque valeur binaire représente une copie moderne (1) ou archaïque (0).
La dimension des homologues d'un descendant place la contribution maternelle en
position 0 et paternelle en position 1. Il s'agit d'une représentation phasée ;
les comptes diploïdes 0/1/2 ne suffisent pas à la reconstruire sans ambiguïté.

La carte déclare B-1 probabilités de changement d'homologue entre blocs adjacents,
dans [0,0.5]. Un gamète démarre équiprobablement sur l'un des deux homologues,
puis change selon des Bernoulli indépendantes aux frontières. Le modèle discret
ne représente ni recombinaison intrabloc ni positions physiques ou interférence.
Une probabilité est une fraction de changement entre deux blocs, pas un nombre
de crossovers ni un taux par base. La valeur 0 conserve l'homologue entier ;
0.5 rend le choix d'homologue indépendant de la position précédente.

Le caller fournit pour chaque descendant un indice de mère et un indice de père.
Il reste responsable du sexe, du choix des parents et de la sélection. Le module
ne simule pas les marqueurs mtDNA/Y/X, ne change pas leurs transmissions validées
en M2 et n'est pas encore intégré à la reproduction du prototype. Aucun nombre
de blocs ou carte empirique par défaut n'est introduit.

## API et traçabilité

`paleogen_rl.genetics.inheritance` expose :

- `RecombinationMap(panel, switch_probabilities)` : carte immuable sur un
  `BlockPanel` I11, sans probabilité implicite. Une liste fournie est copiée en
  tuple de nombres finis ; B=1 requiert une liste vide de frontières.
- `inherit_diploid(haplotypes, *, mothers, fathers, recombination_map, rng)` :
  tableaux parentaux N×2×B et deux vecteurs d'indices de même longueur ; résultat
  descendants×2×B, dtype `uint8`, sans partage de mémoire avec les parents.
- `copy_counts(haplotypes)` : somme des deux homologues en comptes diploïdes
  0/1/2 directement utilisables par `measure_ancestry` d'I11.

Les indicateurs d'allèles peuvent être booléens ou entiers binaires. Les valeurs
flottantes, non binaires ou masquées sont refusées. Les indices doivent être
entiers, non négatifs et dans la population parentale. Aucun parent n'est choisi
silencieusement : la taille de la descendance vient des vecteurs fournis.
Le caller doit associer le bon ordre de colonnes au panel ; le contenu d'un
tableau nu ne permet pas d'en prouver l'identité ou la provenance.

`to_dict()` sérialise le modèle sous `autosomal-block-inheritance-v1`, avec
l'identité et l'ordre du panel, les probabilités par frontière, le démarrage
équiprobable, l'absence de recombinaison intrabloc et l'ordre maternel/paternel.
Cette déclaration permet de reconstruire la carte ; elle ne lui confère pas
le statut de carte empirique. Les sorties du moteur M2 ne sont pas réétiquetées.

Le générateur `numpy.random.Generator` est fourni par le caller. Les gamètes
maternels sont tirés avant les gamètes paternels ; pour chacun sont tirés les
homologues initiaux puis les uniformes de toutes les frontières. Pour B>1,
ces uniformes sont tirés même aux probabilités nulles. Aucun RNG global ni
nouveau générateur interne n'est utilisé. La validation de toutes les entrées
précède ces tirages. L'identité du flux entre versions de NumPy ou avec le
moteur M2 n'est pas revendiquée : cette primitive conserve les lois parentales,
mais n'est pas un adaptateur assurant la parité de trajectoires M2.

La transmission croît en O(descendants×B) et la validation parcourt l'état
parental en O(parents×B). Les tableaux temporaires occupent au plus
O((parents+descendants)×B), en plus de l'état parental fourni. Cela décrit la
primitive ; ce n'est pas un benchmark de coûts sur des résolutions génomiques
ou un choix de résolution principale M3.

Exemple purement synthétique, depuis `reich_experiment_v2/` sous Nix :

```python
import numpy as np
from paleogen_rl.genetics.ancestry import BlockPanel, measure_ancestry
from paleogen_rl.genetics.inheritance import RecombinationMap, inherit_diploid, copy_counts

panel = BlockPanel('synthetic-two-blocks', ('a', 'b'))
mapping = RecombinationMap(panel, (0.2,))
parents = np.array([[[0, 0], [0, 0]], [[1, 1], [1, 1]]], dtype=np.uint8)
children = inherit_diploid(parents, mothers=[0], fathers=[1],
                           recombination_map=mapping, rng=np.random.default_rng(17))
result = measure_ancestry(copy_counts(children), panel,
                          generation=1, target_generation=1, mode='full')
assert result['value'] == 0.5
```

## Protocole statistique fixé

Pour chaque test statistique : graines **104729, 130363, 155921**, chacune avec
**20 000 descendants** de deux parents hétérozygotes distincts. Les tirages des
deux gamètes et des descendants sont indépendants selon le modèle défini.

La tolérance absolue pour une proportion est
`epsilon = sqrt(log(2*K/alpha)/(2*n))`, avec **alpha=0.001**, **n=20000** et K
le nombre total de comparaisons de la famille. C'est une borne de Hoeffding et
une union des K tests, sans supposer leur indépendance entre eux. Elle porte
sur l'erreur Monte Carlo de cette validation synthétique, pas sur l'histoire.

- **Ségrégation mendélienne** : un bloc, hétérozygote × hétérozygote ; proportions
  de copies modernes 0/1/2 attendues **0.25/0.5/0.25**, chaque contribution
  parentale moderne attendue **0.5**. Cinq comparaisons par graine, **K=15**,
  epsilon d'environ **0.0161**.
- **Changements d'homologue** : quatre blocs, homologues entièrement 0 et
  entièrement 1 chez chaque parent, carte **(0, 0.2, 0.5)**. Les transitions
  observées entre allèles révèlent le changement d'homologue. Trois frontières
  × deux contributions × trois graines : **K=18**, epsilon d'environ **0.0162**.
  La frontière de probabilité nulle doit en outre ne montrer aucun changement.

Ces familles fixent une probabilité de faux rejet au plus 0.001 chacune selon
les hypothèses du modèle. Les graines sont publiques et réservées aux tests,
sans prétention de benchmark final indépendant ou d'inférence historique.

## Invariants déterministes et reproductibilité

- Parents homozygotes opposés : chaque descendant reçoit exactement la copie
  maternelle en position 0 et paternelle en position 1 ; inverser les parents
  inverse ces positions sans changer les comptes diploïdes.
- À probabilité de changement nulle, chaque gamète correspond à un homologue
  entier du parent désigné, y compris pour des homologues mosaïques.
- Les états entièrement archaïques ou modernes restent absorbants sur cinq
  générations pour cartes nulles et actives. La projection 0/1/2 produit la
  mesure I11 attendue à la génération finale déclarée.
- Aucun allèle ne peut être créé : à chaque bloc, la contribution du descendant
  appartient à l'un des homologues du parent désigné.
- Générateur et configuration identiques donnent les mêmes descendants et
  l'état RNG final identique. Les états parentaux et indices ne sont pas modifiés.
- Les dimensions, valeurs binaires, probabilités et indices invalides sont
  refusés avant le premier tirage ; l'état du générateur demeure inchangé.

## Vérification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_inheritance.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Vérification du 25 octobre 2026 : les quatre commandes retournent 0 avec
respectivement **9 tests ciblés, 17 tests autosomaux, 35 tests pulse et 94 tests
complets**. Les deux familles statistiques passent avec les graines, effectifs
et tolérances définis avant leur première exécution, sans ajustement du protocole.
Les cinq DoD d'I12 sont vérifiés ; les suites, moteurs et paramètres M2 sont
inchangés. `git diff --check` réussit.

La dérive neutre en population, la convergence entre résolutions, les coûts
mesurés et l'intégration aux scénarios et modes restent des travaux ultérieurs.
Une validation de transmission ne démontre pas leur satisfaction et ne clôture
pas M3. Aucun fichier milestone n'est modifié dans cette Issue.

Références : [M3](../milestones/M3-comparable-autosomal-ancestry.md),
[mesure I11](autosomal-block-measurement.md),
[Issue I12](../issues/I12-transmit-phased-autosomal-blocks.md).
