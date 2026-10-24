# Mesure autosomale sur panel fixe — I11 / M3

## Portée

I11 fournit une primitive de mesure, pas un simulateur de génomes. Elle prépare
une définition commune indépendante de l'activation des DMI. Le moteur M2, ses
tirages, sa CLI, ses statistiques et ses critères 3–7 % ne sont pas modifiés.
La nouvelle primitive n'est donc pas encore la métrique principale des scénarios.

M3 démarre à la demande explicite de l'utilisateur après la validation des dix
DoD techniques de M2 par I10. La dépendance transitive M1 D8/D9 reste ouverte.
Aucun DoD global de M3 n'est déclaré satisfait par cette seule brique.

## Définition opérationnelle

Le module `reich_experiment_v2/paleogen_rl/genetics/ancestry.py` expose
`BlockPanel` et `measure_ancestry`. Le format porte la version
`autosomal-block-measurement-v1` et l'observable
`total_diploid_block_ancestry`.

Un panel déclare un identifiant et un ordre fixe de B blocs. Chaque colonne
du tableau d'entrée correspond à un identifiant, chaque ligne à un individu
diploïde. L'entrée `C[i,b]` compte 0, 1 ou 2 copies modernes. Pour N individus :

```text
modern_allele_copies = somme de C[i,b] sur tous les individus et tous les blocs
allele_copy_denominator = 2 * N * B
value = modern_allele_copies / allele_copy_denominator
```

Chaque bloc reçoit le même poids : c'est une hypothèse explicite de la mesure,
pas une calibration empirique des longueurs génomiques. Il n'existe aucun nombre
de blocs par défaut ni résolution « suffisante » dans I11. `panel_id` est une
déclaration du caller ; la définition complète et son ordre figurent dans chaque
résultat. Réutiliser un nom ne rend pas deux listes de blocs identiques.

`BlockPanel` est immuable et copie une liste d'identifiants fournie en tuple.
Les identifiants doivent être uniques, non vides et sans espaces aux extrémités.
Le tableau doit être rectangulaire, entier, non vide, de largeur B ; les valeurs
hors 0–2, flottantes, booléennes, manquantes ou masquées sont refusées. Les
générations doivent être des entiers Python non négatifs, avec génération de
l'état au plus égale à l'horizon demandé. Les incohérences lèvent `ValueError`.
Les entrées ne sont pas modifiées par la mesure.

## Partenaires et dénominateur commun

`partner_block_ids` annote zéro ou plusieurs blocs du panel. Les références
inconnues ou dupliquées sont refusées ; les partenaires sont rendus dans l'ordre
du panel. Leur déclaration ne supprime jamais une colonne du total et ne change
ni son poids, ni son numérateur, ni son dénominateur.

Pour chaque partenaire, `partner_diagnostics` fournit séparément son identifiant,
son nombre de copies modernes, son dénominateur `2*N` et sa fraction. Ces données
permettent de suivre des blocs contenant des partenaires sélectionnés sans
rebaptiser la moyenne des seuls blocs restants « ascendance totale ».
La désignation d'un partenaire n'applique aucune sélection et n'identifie pas
un gène réel ; l'éventuel mécanisme de sélection appartient au futur simulateur.

Cette mesure totale est distincte du `neutral_proxy` de M1, qui exclut les loci
sélectionnés. Son format est distinct et ne passe pas implicitement pour une
mesure conforme à `validate_autosomal_statistic`. Le contrat historique et les
observations ne sont ni réécrits ni remplacés. La coexistence des diagnostics
historiques et de la future métrique principale devra être explicite lors de
l'intégration ultérieure.

## Génération et disponibilité

Le résultat est un dictionnaire sérialisable en JSON strict :

| Champ | Contenu |
| --- | --- |
| `measurement_version`, `observable` | Version et définition propres à cette mesure |
| `panel` | `panel_id`, `block_ids` ordonnés, `block_count`, `weighting=equal_diploid_copies` |
| `generation`, `target_generation`, `mode` | État fourni, horizon demandé et politique d'évaluation |
| `status` | `evaluated_at_target` ou `not_evaluated_quick` |
| `diploid_individuals`, `allele_copy_denominator` | Taille et dénominateur fixe du panel |
| `modern_allele_copies`, `value` | Total et fraction finaux, ou `null` si non évalués |
| `partner_block_ids`, `partner_diagnostics` | Déclaration et diagnostics séparés, diagnostics `null` si non évalués |

En `full` et `adaptive`, la génération fournie doit être exactement l'horizon
demandé ; tout état antérieur ou postérieur est refusé. Le caller reste
responsable de fournir une population réellement produite à cette génération et
de vérifier les échecs reproductifs : cette fonction ne peut pas établir la
provenance d'un tableau ni attester le succès d'un moteur.

En `quick`, les valeurs finales et les diagnostics partenaires restent `null`,
même si l'état fourni atteint l'horizon. Le panel, la taille, le dénominateur et
les générations restent disponibles comme métadonnées. Ils ne prouvent pas
qu'une mesure finale a été effectuée. Aucun intervalle de confiance, événement
conjoint ou décision 3–7 % n'est calculé par cette primitive.

## Exemple synthétique exécutable

Depuis `reich_experiment_v2/`, dans l'environnement Nix :

```python
from paleogen_rl.genetics.ancestry import BlockPanel, measure_ancestry

panel = BlockPanel('synthetic-example', ('a', 'b', 'c'))
result = measure_ancestry(
    [[2, 0, 1], [0, 1, 0]], panel,
    generation=7, target_generation=7, mode='full', partner_block_ids=('a',),
)
assert result['modern_allele_copies'] == 4
assert result['allele_copy_denominator'] == 12
assert result['value'] == 1 / 3
assert result['partner_diagnostics'][0]['value'] == 0.5
```

Ces nombres illustrent une formule sur des données synthétiques ; ils ne sont
ni une simulation historique ni une observation empirique.

## Vérification et travail restant

`tests/test_autosomal_ancestry.py` vérifie les cas analytiques 0/1/2 copies pour
N=1/3/20 et B=1/8/32, une matrice mixte, l'invariance aux annotations, les
diagnostics partenaires, l'immuabilité du panel, les trois modes, les erreurs
d'entrée et le passage JSON strict sans valeur non finie. Les résolutions de
test ne constituent pas une étude de convergence.

Commandes depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_ancestry.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Vérification du 24 octobre 2026 : les trois commandes retournent 0 avec
respectivement **8 tests autosomaux, 35 tests pulse et 85 tests complets**.
Les cinq DoD d'I11 sont vérifiés ; les tests et implémentations M2 sont inchangés.
Le fichier milestone M3 et ses cases restent inchangés, car ces preuves ne
suffisent pas à satisfaire ses critères globaux.

M3 requiert encore la génération et transmission de blocs, un modèle de
recombinaison traçable, les contrôles statistiques pré-enregistrés de ségrégation
et dérive, puis l'étude d'au moins trois résolutions avec leurs coûts. Ni la
résolution principale ni la carte de recombinaison ne sont décidées par cette
mesure. L'intégration cohérente à tous les scénarios et aux modes CLI, avec preuve
adaptative/intégrale du critère conjoint, reste à réaliser. Appliquer simplement
cette fonction aux huit loci historiques ne résout pas leur discrétisation.

Références : [M3](../milestones/M3-comparable-autosomal-ancestry.md),
[contrat historique](observations.md), [audit technique M2](m2-audit.md),
[Issue I11](../issues/I11-define-fixed-autosomal-block-measurement.md).
