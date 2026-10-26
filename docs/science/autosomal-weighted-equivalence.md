# Critères déclarés d'équivalence — I32

`weighted_autosomal_equivalence.py` ajoute une évaluation séparée des rapports
I31, sans modifier études, moteurs ou observations. Il ne fournit **aucune marge
scientifique par défaut** et ne clôture pas M3. Le choix des marges et de la
précision d'une étude confirmatoire reste ouvert.

## Déclaration liée au plan

Les critères JSON contiennent exactement :

| Champ | Définition |
| --- | --- |
| `criteria_version` | `weighted-autosomal-equivalence-criteria-v1` |
| `criteria_id` | Identifiant non vide sans espaces périphériques |
| `study_plan_sha256` | SHA-256 canonique du plan I31 normalisé, graines incluses |
| `alpha` | Risque global strictement entre 0 et 1 |
| `margins` | Marges explicites dans `(0,1]` pour les quatre métriques ci-dessous |
| `max_interval_radius` | Rayon demandé positif, au plus égal à chaque marge |

Les métriques obligatoires sont `ancestry`, `target_probability`, `p10_joint`
et `joint_and_target`. Les marges sont des différences absolues de proportions,
pas des pourcentages relatifs. Le chargeur refuse booléens, nombres non finis,
clés inconnues/manquantes/dupliquées et liens à un autre plan. Les précisions
non représentables par l'arithmétique de prévision sont refusées.

`validate_weighted_equivalence_criteria(criteria, plan)` normalise et retourne
un instantané indépendant. `load_weighted_equivalence_criteria(path, plan)`
retourne cet instantané et le SHA-256 des octets du fichier. Le hash canonique
des critères, dans les résultats, est indépendant de leur indentation.

Ces critères doivent être fixés **avant** les résultats confirmatoires.
L'empreinte lie leur contenu à celui du plan ; elle ne prouve pas leur date
de création. Une procédure extérieure de gel/versionnement avant exécution
reste nécessaire. I32 n'adopte ni critères empiriques, ni protocole principal.

## Précision simultanée

Pour S scénarios, R résolutions et les quatre métriques, le nombre de
comparaisons avec la plus fine est `K=S*(R-1)*4`. Pour chaque comparaison,
la différence appariée par graine est bornée dans `[-1,1]`.

La borne bilatérale de Hoeffding donne
`P(|moyenne-espérance| >= r) <= 2*exp(-n*r*r/2)`.
La somme de ces bornes pour K comparaisons donne le rayon commun :

```text
C = 2 * (log(2*K) - log(alpha))
r = sqrt(C/n)
n_requis = ceil(C / max_interval_radius²)
```

Les intervalles, tronqués à `[-1,1]`, couvrent simultanément les espérances
des écarts avec probabilité au moins `1-alpha`, sous l'hypothèse de réplicats
indépendants. Les comparaisons peuvent dépendre entre elles ; la borne par
somme n'exige pas leur indépendance. Une graine partagée définit un appariement,
pas un flux RNG identique entre résolutions. Le rayon est conservateur.

`preview_weighted_equivalence(criteria, plan)` annonce K, rayon non tronqué,
effectif requis par cellule et satisfaction de la précision, sans moteur ni RNG.
L'effectif est arrondi vers le haut avec vérification numérique de la borne.
La précision demandée est vérifiée sur le rayon non tronqué ; la troncature
ne peut pas rendre artificiellement une étude plus précise.

## Évaluation des résultats

`assess_weighted_equivalence(criteria, report)` exige un rapport full I31 et
vérifie plan/famille, résolutions, graines, horizons, configurations/scénarios,
carte, sélection et observations pondérées finales. Les valeurs sont finies,
la cible inclusive 3–7 % et le produit P10 × cible sont cohérents. La masse
pondérée et son dénominateur doivent reproduire l'ascendance à `1e-14` près,
tolérance numérique distincte des marges scientifiques.

Les agrégats et intervalles ponctuels en cache ne participent pas à la décision :
les différences sont recalculées depuis les réplicats. Pour une marge δ :

- intervalle entièrement au-delà de +δ ou de −δ : `difference_detected` ;
- sinon, précision demandée non atteinte : `inconclusive_precision` ;
- sinon, intervalle strictement dans `(−δ,+δ)` : `equivalence_supported` ;
- sinon : `inconclusive`.

Toucher une frontière ne suffit pas à soutenir une équivalence ou une différence.
Une différence détectée peut être concluante même si le rayon demandé n'est
pas atteint. L'équivalence globale exige le soutien de **toutes** les
comparaisons et prend le statut `equivalence_supported_within_declared_family`.
Une seule différence détectée donne `difference_detected` ; les autres cas
restent non concluants. Un zéro observé n'est pas une preuve d'équivalence
quand l'incertitude est trop grande, ni une preuve de probabilité vraie nulle.

La sortie `weighted-autosomal-equivalence-assessment-v1` conserve critères,
hashes des critères/plan/rapport/famille, prévision et chaque comparaison.
`convergence_status` reste **`not_established`**, quel que soit le résultat.
Le résultat porte sur les espérances des quatre métriques dans la famille
finie déclarée ; il ne prouve ni convergence au-delà de sa plus fine résolution,
ni équivalence de toutes les distributions, ni plausibilité historique.
Les cellules partenaires restent celles du modèle I30.

Le contrôle vérifie la cohérence des champs utilisés. Il n'authentifie pas
l'exécution, ne refait pas la simulation, et ne détecte pas une falsification
coordonnée de tous les champs. Les ressources et implémentations enregistrées
doivent être contrôlées pour un audit et un rejeu complets.

## Exemple technique exécutable

Dans `nix develop`, depuis `reich_experiment_v2/` :

```python
import hashlib
from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.protocol import _canonical
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel
from paleogen_rl.genetics.weighted_protocol import WeightedAutosomalProtocol
from study_weighted_autosomal_resolution import PLAN_VERSION, run_weighted_resolution_plan
from weighted_autosomal_equivalence import (
    CRITERIA_VERSION, METRICS, preview_weighted_equivalence, assess_weighted_equivalence,
)

panel = BlockPanel('synthetic-four', ('a', 'b', 'c', 'd'))
base = WeightedAutosomalProtocol(
    'absorbing-control', 40, 1, 0., .5, RecombinationMap(panel, (0., 0., 0.)),
    'a', 'd', WeightedBlockPanel(panel, (1, 3, 3, 1), 'synthetic control'))
plan = dict(plan_version=PLAN_VERSION, plan_id='technical-control', seeds=[0, 1, 2],
            scenarios=['neutral'], family=dict(base_protocol=base.to_dict(),
            family_id='control-family', map_length=0., refinement_factors=[1, 3, 9]))
criteria = dict(criteria_version=CRITERIA_VERSION, criteria_id='technical-test-only',
    study_plan_sha256=hashlib.sha256(_canonical(plan).encode()).hexdigest(), alpha=.05,
    margins={metric: .4 for metric in METRICS}, max_interval_radius=.2)
preview = preview_weighted_equivalence(criteria, plan)
print(preview['comparisons'], preview['required_replicates_per_cell'])
report = run_weighted_resolution_plan(plan)
assessment = assess_weighted_equivalence(criteria, report)
print(assessment['status'], assessment['convergence_status'])
```

Les marges de 0.4 et le rayon de 0.2 sont des **fixtures techniques**, pas des
seuils proposés pour M3. Le pulse nul est un contrôle absorbant. Même avec des
différences observées nulles, trois graines ne satisfont pas ces critères.
Cet exemple n'est pas une étude confirmatoire au régime historique.

Validation du 26 octobre 2026 : **8 tests ciblés, 153 tests autosomaux et
230 tests complets** passent sous Nix, sans échec ni test ignoré. Les tests
vérifient les deux empreintes, liens au plan, calcul analytique du rayon,
effectif minimal, multiplicité, prévision sans RNG/moteur et frontières strictes.
Un contrôle absorbant I31 réellement simulé (N=40, G=1, f=0, 320 graines,
trois résolutions, soit 960 évaluations full) soutient uniquement sa famille
déclarée sous les marges de test ; le petit contrôle à trois graines reste
non concluant. Des champs d'observation synthétiques contrôlés, distincts de
trajectoires simulées, vérifient les statuts de différence et d'incertitude.
Les rapports incomplets, plans/panels/configurations altérés, valeurs invalides,
horizons ou échantillons incohérents sont refusés. Les agrégats en cache ne
changent pas les comparaisons recalculées.

L'exemple a produit `8 289` puis `inconclusive_precision not_established`.
Environnement observé : Linux x86_64, Python 3.14.8, NumPy 2.5.3.
Aucune de ces fixtures n'adopte des marges pour la science M3.
