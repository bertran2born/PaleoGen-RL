# Contrôle de dérive neutre — protocole I13 / M3

## Paramètres fixés avant exécution

Ce protocole est écrit avant la première exécution du contrôle statistique I13.
Les graines, effectifs, cartes et bornes ci-dessous ne seront pas ajustés pour
faire passer les résultats. Les états sont synthétiques et n'ont pas de statut
d'observation historique ou de calibration génomique humaine.

- Population : **40 diploïdes**, dont **20 mâles et 20 femelles**.
- Panel : **8 blocs** de poids égaux, dans l'ordre déclaré I11.
- État initial : tous les blocs sont homozygotes archaïques, sauf chez **un mâle
  et une femelle**, homozygotes modernes à tous les blocs. Avec mâles aux indices
  0–19 et femelles 20–39, les individus modernes sont **0 et 20**.
- Ascendance initiale totale et dans chaque sexe : **0.05 exactement**.
- Horizon : **20 générations** sans sélection, mutation ou migration.
- Cartes : fractions de changement d'homologue **0** puis **0.25** à chacune des
  sept frontières. Ce sont deux modèles synthétiques, pas une carte empirique.
- Réplicats : **1024**, graines entières **310000 à 311023 incluses**, pour
  chacune des deux cartes ; aucun réplicat n'est filtré après simulation.

## Espérance et intervalle Monte Carlo préfixé

Chaque descendant reçoit un gamète d'une mère uniforme parmi les femelles et
d'un père uniforme parmi les mâles. Pour N pair avec quotas égaux, l'espérance
conditionnelle de l'ascendance de la génération suivante égale la moyenne de
toute la population courante. La transmission I12 ne crée ni ne favorise un
allèle. L'espérance finale de ce contrôle est donc **mu=0.05** pour les deux
cartes. Cela ne suppose pas une indépendance des blocs dans un individu.

Pour la fraction finale A d'un réplicat, `0 <= A <= 1` et sous l'hypothèse nulle
`Var(A) <= mu*(1-mu) = 0.0475`. Une borne de Bernstein pour la moyenne de R
réplicats indépendants et une union sur K cartes donne l'intervalle préfixé :

```text
R = 1024 ; K = 2 ; alpha = 0.01
t = log(2*K/alpha)
epsilon = sqrt(2*0.0475*t/R) + 2*t/(3*R)
intervalle = [moyenne_observee - epsilon, moyenne_observee + epsilon] intersecte [0,1]
```

La demi-largeur est environ **0.0275**. Le test exige que **0.05 appartienne à
l'intervalle pour chaque carte**. Cette borne conservatrice contrôle le risque
de faux rejet de la famille par alpha, sous les hypothèses indiquées. Elle
permet notamment de détecter une implémentation qui retournerait toujours zéro ;
elle ne constitue pas un test de forte puissance contre tout biais faible.
Les cartes peuvent partager leurs graines : l'union des bornes ne requiert pas
leur indépendance entre elles. L'indépendance supposée concerne les réplicats
d'une même carte. Aucun intervalle historique n'est inféré.

## Hypothèses du simulateur neutre

L'état initial est fourni explicitement ; aucun pulse, phase ou sex-ratio n'est
reconstruit depuis les huit loci du moteur M2. Les quotas sont ceux de M2 :
`N//2` mâles puis `N-N//2` femelles parmi les descendants. Les sexes initiaux
doivent avoir ces effectifs, dans un ordre quelconque. Le choix de parents est
uniforme dans chaque sexe, indépendamment pour chaque descendant. La transmission
réutilise I12, un gamète par parent, avec état phasé conservé.

Pour N impair, les deux groupes n'ont pas la même taille. L'espérance d'un
descendant est alors la moyenne **des deux fréquences par sexe**, qui peut
différer de la fréquence globale pondérée par leurs effectifs. Le contrôle de
martingale ci-dessus utilise donc délibérément un N pair ; il n'affirme pas la
même formule pour n'importe quel déséquilibre de sexes.

La simulation poursuit toutes les générations, même après fixation/perte des
blocs. Il n'y a pas de marqueurs mtDNA/Y, d'absorption uniparentale, de sélection
ou d'évaluation adaptative. Les annotations de blocs partenaires sont seulement
des diagnostics de mesure I11 et ne changent pas la reproduction.

## API, rapport et provenance

`paleogen_rl.genetics.neutral.run_neutral(haplotypes, sex, *, recombination_map,
generations, seed, partner_block_ids=())` retourne un `NeutralRun` contenant
les tableaux finaux `haplotypes`, `sex` et un dictionnaire `report` sérialisable
en JSON strict. Les tableaux retournés appartiennent au résultat, sans modifier
ni partager le stockage des états initiaux. L'horizon et la graine sont des
entiers Python non négatifs ; l'horizon zéro mesure l'état initial et ne produit
aucun descendant. Les sexes doivent être binaires, de longueur N et compatibles
avec les quotas ; les autres déclarations sont validées par I11/I12.

Le simulateur crée un générateur local avec la graine déclarée, après validation
des entrées. À chaque génération, il tire d'abord tous les indices maternels,
puis tous les indices paternels, avec remise et sans poids, et appelle la
transmission I12. Les sexes de la descendance sont ordonnés mâles puis femelles.
Cette règle préserve la loi de reproduction séparée par sexe, sans revendiquer
l'identité du flux RNG avec M2 ou entre toutes les versions de NumPy. Le RNG
global n'est pas utilisé et les annotations partenaires ne déclenchent pas de
tirages supplémentaires.

Le format du rapport est `neutral-autosomal-block-simulation-v1` :

| Champ | Contenu |
| --- | --- |
| `model`, `scientific_status`, `mode` | Modèle neutre à sexes séparés, simulation, mode intégral `full` uniquement |
| `seed`, `numpy_version`, `rng_bit_generator` | Provenance du hasard local et de l'environnement numérique |
| `population_size`, `male_n`, `female_n` | Taille fixe et quotas |
| `generations_requested`, `generations_completed`, `termination_reason` | Horizon réellement produit, sans absorption anticipée |
| `recombination_map` | Déclaration I12 avec panel et probabilités |
| `initial_haplotypes_sha256`, `initial_sex_sha256` | Empreintes de l'état initial canonique |
| `initial_measurement`, `final_measurement` | Mesures I11 séparées, à l'horizon zéro et à l'horizon demandé |
| `work_units` | Descendants produits, copies de blocs transmises, nombre d'entrées du tableau d'état |

Les empreintes utilisent les octets en ordre C des tableaux binaires normalisés
en `uint8`. Les dimensions et l'ordre du panel figurent dans le rapport ; deux
phases différentes de mêmes comptes diploïdes possèdent des empreintes différentes.
Un hash n'encode pas le tableau : pour rejouer, le caller doit conserver les
états initiaux et vérifier leurs empreintes, puis réutiliser la carte, la graine,
l'horizon et un environnement compatible. Aucun fichier de résultat n'est écrit
ou écrasé automatiquement par l'API.

Les unités de travail valent `N*generations` descendants, `2*N*B*generations`
copies transmises et `2*N*B` entrées d'état. Elles décrivent le travail logique,
pas un temps matériel mesuré ni l'ensemble des allocations temporaires. Le
temps croît en O((generations+1)*N*B), la mémoire de travail en O(N*B), sans historique
complet conservé. Aucun gain par arrêt anticipé n'est revendiqué.

Exemple synthétique exécutable depuis `reich_experiment_v2/` sous Nix :

```python
import numpy as np
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.neutral import run_neutral

panel = BlockPanel('synthetic-two-blocks', ('a', 'b'))
mapping = RecombinationMap(panel, (0.25,))
initial = np.ones((4, 2, 2), dtype=np.uint8)
result = run_neutral(initial, [1, 1, 0, 0], recombination_map=mapping,
                     generations=5, seed=17)
assert result.report['generations_completed'] == 5
assert result.report['final_measurement']['value'] == 1.0
assert result.report['work_units']['block_copy_transmissions'] == 80
```

Ce modèle neutre n'implémente aucun événement mtDNA/Y ni `quick`/`adaptive`.
La mesure finale n'est pas étiquetée « 50 ka » pour un horizon de test. Aucun
filtre 3–7 % n'est utilisé pour retenir ou supprimer les réplicats du contrôle.

## Vérification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_neutral.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Vérification du 25 octobre 2026 : les quatre commandes retournent 0 avec
respectivement **8 tests ciblés, 25 tests autosomaux, 35 tests pulse et 102 tests
complets**. La moyenne théorique de 0.05 appartient aux intervalles préfixés
des deux cartes sur les 1024 graines déclarées ; le protocole n'a pas été ajusté
aux résultats. Les cinq DoD d'I13 sont vérifiés et les tests antérieurs sont
inchangés. `git diff --check` réussit.

Ce contrôle ne valide ni les scénarios épistatiques, ni la convergence en
résolution, ni la calibration du Ne réalisé. L'intégration aux scénarios et
modes CLI reste ouverte, ainsi que M3. Aucun fichier milestone n'est modifié.

Références : [M3](../milestones/M3-comparable-autosomal-ancestry.md),
[mesure I11](autosomal-block-measurement.md),
[transmission I12](autosomal-inheritance-protocol.md),
[Issue I13](../issues/I13-validate-neutral-autosomal-drift.md).
