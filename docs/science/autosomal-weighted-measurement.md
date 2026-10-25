# Mesure autosomale à poids déclarés — I25 / M3

Les diagnostics I18/I22 conservent des partenaires aux extrémités du panel,
mais leur poids total vaut 2/B dans la mesure I11. Augmenter B modifie donc
aussi le poids représenté par ces blocs. Une étude de convergence doit pouvoir
distinguer cette modification du modèle d'une simple subdivision de mesure.

I25 fournit une primitive pondérée séparée, dont les poids sont une hypothèse
explicite du caller. Elle permet de tester une subdivision conservative sur
des états donnés. Elle ne choisit aucune longueur biologique ni résolution.

## Déclaration et formule

`paleogen_rl.genetics.weighted_ancestry` expose `WeightedBlockPanel` et
`measure_weighted_ancestry`. Le panel pondéré contient un `BlockPanel` I11,
un poids relatif par bloc et `weight_basis`, une explication obligatoire de
leur origine. Les poids doivent être strictement positifs, finis et
représentables comme flottants ; booléens, poids nuls, valeurs manquantes et
rapports de poids dont la normalisation produit un zéro sont refusés.
Les listes fournies sont copiées en tuples immuables. La justification fournie
n'est pas authentifiée et ne constitue pas une preuve de calibration empirique.

Pour C[i,b] copies modernes (0/1/2) chez N individus et des poids w[b] :

```text
fraction_b = somme_i C[i,b] / (2*N)
A = somme_b (w[b] * fraction_b) / somme_b w[b]
```

Tous les blocs contribuent, partenaires inclus. Leur annotation ne modifie
jamais la mesure ou les poids. Les poids sont relatifs : les multiplier par
une même constante positive conserve A, à la précision flottante près.
Le calcul commence par une mise à l'échelle par le plus grand poids, puis une
normalisation ; il évite ainsi le débordement d'une somme de poids bruts finis.
Les poids déclarés et les poids normalisés effectivement utilisés sont exportés.

## Format et disponibilité

Le format `weighted-autosomal-block-measurement-v1` et l'observable
`total_weighted_diploid_block_ancestry` sont distincts d'I11. Les champs
`modern_ancestry_weight` et `weight_denominator` décrivent respectivement la
somme des fréquences pondérées et la somme des poids normalisés. Le premier
est une masse d'ascendance relative, **pas un nombre de copies alléliques**.
Le dénominateur peut différer légèrement de 1 par arrondi flottant.

N, générations, statut et panel sont explicites. Les comptes bruts sont
conservés séparément comme diagnostics :
`unweighted_modern_allele_copies` et `unweighted_allele_copy_denominator=2*N*B`.
Ce dénominateur brut ne doit pas servir à recalculer A pondéré.
Chaque partenaire conserve son nombre de copies, son dénominateur 2*N et sa
fréquence ; `relative_panel_weight` et `weighted_ancestry_contribution`
précisent son poids et sa contribution au total.

La validation des comptes et des générations réutilise I11. En full/adaptive,
l'état doit atteindre exactement l'horizon déclaré. En quick, même à horizon
atteint, valeur finale, masse moderne, compte brut moderne et diagnostics
partenaires restent nuls en JSON. Le panel, ses poids et les dénominateurs
restent disponibles comme métadonnées. La primitive ne calcule aucun événement
3–7 %, score, intervalle, sélection ou trajectoire.

## Raffinement analytique conservatif

Considérons deux blocs partenaires de poids 2 chacun et un bloc intermédiaire
de poids 4. On peut découper ce dernier en deux blocs de poids 2, puis quatre
de poids 1. Pour chaque individu, les sous-blocs reçoivent ici **les mêmes
comptes d'ascendance que le bloc initial**. Les partenaires gardent chacun un
quart du poids total aux trois résolutions :

| Blocs | Poids déclarés dans l'ordre | Poids total des partenaires |
| --- | --- | --- |
| 3 | 2, 4, 2 | 1/2 |
| 4 | 2, 2, 2, 2 | 1/2 |
| 6 | 2, 1, 1, 1, 1, 2 | 1/2 |

Exemple purement synthétique depuis `reich_experiment_v2/` :

```python
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel, measure_weighted_ancestry

panel = WeightedBlockPanel(BlockPanel('synthetic-example', ('mt', 'middle', 'y')),
                           (2, 4, 2), 'synthetic analytical fixture; no empirical calibration')
result = measure_weighted_ancestry([[2, 0, 2], [1, 0, 1]], panel,
                                  generation=7, target_generation=7, mode='full',
                                  partner_block_ids=('mt', 'y'))
assert result['value'] == 0.375
assert all(p['relative_panel_weight'] == 0.25 for p in result['partner_diagnostics'])
```

Les trois panels donnent exactement 0.375 sur cette fixture, contre
0.5/0.375/0.25 avec la mesure à poids égaux. Ces nombres illustrent les deux
définitions ; aucune des valeurs n'est un résultat historique ni un score
optimisé. Les tests vérifient aussi des ascendances intermédiaires non nulles
et la correspondance avec I11 lorsque tous les poids sont égaux.

## Portée scientifique et vérification

L'invariance d'une mesure sur des états subdivisés n'est pas une convergence
de simulations. Il reste à définir une famille cohérente de cartes, transmissions
et partenaires sélectionnés, puis à l'intégrer à des contrats versionnés et
à vérifier ses trajectoires avec une précision déclarée. Des poids constants
dans le calcul ne prouvent pas à eux seuls que la dynamique représente le
même modèle biologique entre résolutions.

Les moteurs, CLI, mesure I11, contrats I19, cibles et archives restent inchangés.
Cette primitive n'est pas utilisée par les évaluations ou récompenses actuelles.
Son origine déclarée et ses exemples synthétiques ne valident aucun poids humain.
Le protocole principal et la convergence M3 restent ouverts.

Validation de [I25](../issues/I25-measure-explicitly-weighted-autosomal-panels.md),
25 octobre 2026 : **8 tests ciblés, 103 tests autosomaux et 180 tests complets**
réussissent sous Nix, sans échec ni test ignoré. L'exemple Python ci-dessus a
également été extrait du document et exécuté sous Nix : valeur 0.375 et poids
partenaires [0.25,0.25].

| DoD I25 | Preuve dans `tests/test_autosomal_weighted_ancestry.py` |
| --- | --- |
| ID1 | Immuabilité, copie des listes, reconstruction JSON et justification obligatoire ; poids booléens/non finis/non positifs, dimensions et rapports non représentables refusés. |
| ID2 | Cas 0/1/2 copies et matrice mixte, poids égaux comparés à I11, échelles de 1e-200 à 8e307, annotations inchangées, trois panels conservatifs à plusieurs ascendances intermédiaires. |
| ID3 | Version et observable distinctes, unités et diagnostics séparés, JSON strict, quick indisponible même à horizon atteint et générations full/adaptive contrôlées. |
| ID4 | Les trois suites passent ; exemple et limites documentés, seuls les quatre fichiers I25 sont ajoutés. |

`git diff --check`, structure/taille de l'Issue, liens locaux et espaces sont
vérifiés. Les fichiers existants I11 et I19 ne sont pas modifiés ; le rapport
I22 conserve son SHA-256
`99cd8cf191a92651cb413edbce10a01502257eaaf6c6b49dd64fa3a85085affd`.
Aucun blocage ne subsiste pour I25. Le milestone n'est pas modifié : sa métrique
principale D1 et la convergence restent ouvertes, car l'intégration à une famille
de simulations comparable et son acceptation scientifique ne sont pas réalisées.
