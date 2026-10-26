# Famille de raffinements pondérés conservatifs — I30

`build_weighted_refinement_family` dans
`paleogen_rl.genetics.weighted_refinement` construit des contrats I28 pour une
étude multirésolution ultérieure. Il n'exécute aucun moteur ni RNG et ne
prétend pas établir la convergence. Les anciens rapports et le runner d'étude
restent inchangés.

## Hypothèses de la famille

Les poids relatifs du protocole de départ définissent des cellules contiguës
sur [0,1], dans l'ordre du panel. Le bloc représente le centre de sa cellule.
Interpréter ici ces poids comme longueurs relatives est une **hypothèse
synthétique explicite**, qui ne découle pas de leur seule validation I25.
La longueur de carte `map_length=L` couvre [0,1], avec densité génétique
uniforme. Pour deux centres `x<y`, `d=L*(y-x)` et :

```text
r(d) = -expm1(-2*d)/2
```

La carte du protocole de départ doit être compatible avec cette règle,
avec tolérance absolue **1e-15** sur chaque probabilité (arrondis flottants).
Le premier protocole est conservé intégralement, avec sa carte, ses poids,
ses identifiants et son empreinte. Une carte arbitraire I28 peut être valide
sans être admissible à cette famille ; le constructeur la refuse.

Les cellules partenaires mt/Y restent intactes : mêmes identifiants, étendues,
centres et poids déclarés. Les deux rôles peuvent désigner la même cellule.
Seules les cellules sans rôle partenaire sont divisées en `k` sous-cellules
égales, chacune pesant `w/k`. Les facteurs doivent commencer par 1, être au
moins trois, strictement croissants, impairs et divisibles successivement.
Par exemple `(1,3,9)` et `(1,3,15)` donnent des cellules emboîtées et retiennent
tous les centres précédents. Il faut au moins une cellule neutre.

Les positions et frontières sont calculées par fractions rationnelles des
poids flottants déclarés, puis exportées en flottants. Une géométrie dont les
centres/frontières deviennent indiscernables en flottants est refusée, tout
comme un poids enfant non représentable. Les nouveaux identifiants associent
le bloc parent à la fraction réduite de sa position dans la cellule ; le centre
original conserve l'identifiant parent. Les collisions sont refusées.

La composition des changements d'homologue indépendants entre deux centres
conservés satisfait :

```text
r_total = (1 - produit_i(1 - 2*r_i))/2
```

La règle exponentielle conserve cette transition quand on insère des centres
intermédiaires. Elle conserve donc les lois de transmission aux positions
retenues dans ce modèle. Elle ne couple pas les flux RNG des différentes
résolutions et ne garantit aucune égalité de trajectoires par graine.

## Déclaration et rejeu

La version est `weighted-autosomal-refinement-family-v1`. La déclaration contient
le protocole de départ et son hash, les facteurs, longueur et règles de carte,
statut synthétique, statut de convergence `not_established`, puis chaque
résolution avec :

- facteur et nombre de blocs ;
- `parent_block_ids`, `block_intervals` et `block_positions`, dans l'ordre du panel ;
- contrat I28 complet et son SHA-256 canonique.

`family_sha256` identifie le JSON canonique de toute la déclaration sauf ce
champ lui-même. Ce hash n'est pas celui d'un fichier source. Les instantanés
retournés sont indépendants des entrées. La famille se reconstruit à partir du
contrat de départ et des paramètres conservés ; les contrats de chaque
résolution sont chargeables par I28 et exécutables via l'API ou la CLI I29.

Exemple autonome depuis `reich_experiment_v2/`, dans `nix develop` :

```python
from math import expm1

from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel
from paleogen_rl.genetics.weighted_protocol import WeightedAutosomalProtocol
from paleogen_rl.genetics.weighted_refinement import build_weighted_refinement_family

panel = BlockPanel('synthetic-four', ('a', 'b', 'c', 'd'))
positions = (1/16, 5/16, 11/16, 15/16)
length = 1.
switches = tuple(-expm1(-2*(length*(b-a)))/2 for a, b in zip(positions, positions[1:]))
base = WeightedAutosomalProtocol(
    'synthetic-refinement-base', 40, 4, .5, .5, RecombinationMap(panel, switches),
    'a', 'd', WeightedBlockPanel(panel, (1, 3, 3, 1), 'synthetic relative lengths'))
family = build_weighted_refinement_family(
    base, family_id='synthetic-family', map_length=length, refinement_factors=(1, 3, 9))
for row in family['resolutions']:
    protocol = WeightedAutosomalProtocol.from_dict(row['autosomal_protocol'])
    ids = protocol.measurement_panel.panel.block_ids
    weights = protocol.measurement_panel.normalized_weights
    print(row['refinement_factor'], row['block_count'],
          weights[ids.index('a')]+weights[ids.index('d')])
```

Les partenaires de cet exemple conservent ensemble 1/4 du poids représenté,
au lieu de diminuer avec le nombre de blocs. Ce choix est un contrôle synthétique,
pas une proposition de longueur génomique biologiquement plausible.

## Portée de la validation

Les contrôles de conservation utilisent une tolérance absolue **1e-14** pour
poids, mesure et transitions composées ; les centres conservés et frontières
communes sont comparés exactement dans les fixtures. Ces tolérances numériques
ne sont pas des marges d'équivalence statistique. Les états dupliqués sont des
contrôles de mesure, pas des résultats de simulation de générations successives.

La géométrie ne raffine ni la taille ni la structure interne des partenaires :
chaque cellule sélectionnée reste un bloc fini sans recombinaison interne.
Cette famille permet de tester le raffinement **neutre conditionnel à cette
architecture fixe**. Elle ne prouve pas la convergence d'une représentation
où les régions sélectionnées changeraient aussi de taille ou de complexité.
Le protocole principal M3, les critères statistiques pré-enregistrés et l'étude
confirmatoire restent ouverts. Aucune cible, observation, sélection ou archive
n'est modifiée par ce constructeur.

Preuves du 26 octobre 2026 : sous Nix, **8 tests ciblés, 139 tests autosomaux
et 216 tests complets** réussissent, sans échec ni test ignoré. Les tests couvrent
partenaires extrêmes/intérieurs/partagés, facteurs 1/3/9 et 1/3/15, cartes de
longueur 0/0.1/2, composition des transitions, états dupliqués, identifiants
en collision, géométries non représentables, cartes incompatibles, instantanés,
empreintes et reconstruction JSON. La construction est exécutée avec moteur
et RNG interdits par mocks. Les contrats produits sont ensuite évalués réellement
sur 54 appels (3 résolutions × cartes 0/1 × graines 0/17/42 × trois modes),
avec sélection uniparentale et pénalités réciproques actives ; l'accord
full/adaptive et l'indisponibilité quick sont vérifiés à chaque résolution.

L'exemple a été exécuté : lignes `(1,4,0.25)`, `(3,8,0.25)` et `(9,20,0.25)`.
Environnement observé : Linux x86_64, Python 3.14.8, NumPy 2.5.3. Ce sont des
preuves de construction et d'intégration, sans étude statistique de convergence.
