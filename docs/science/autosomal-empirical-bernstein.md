# Équivalence par Bernstein empirique à effectif fixé — I34

I34 ajoute une option de précision sensible à la variance dans
`weighted_autosomal_equivalence.py`. La méthode Hoeffding v1 et les archives
I32/I33 restent inchangées. Aucune marge, architecture ou résolution principale
n'est adoptée ; M3 reste ouvert.

## Source et adaptation

Source primaire : Andreas Maurer et Massimiliano Pontil, *Empirical Bernstein
Bounds and Sample Variance Penalization*, COLT 2009,
[théorème 4, page 2](https://www.cs.mcgill.ca/~colt2009/papers/012.pdf)
([notice arXiv](https://arxiv.org/abs/0907.3740)). Le théorème donne une borne
unilatérale dépendant de la variance empirique pour des variables i.i.d. dans
[0,1], à effectif fixé n≥2. Aucun code ou PDF tiers n'est ajouté au dépôt.

L'adaptation utilisée ici part des différences appariées D dans [-1,1]. On
applique le théorème à `(D+1)/2` et à son complément, avec risque `alpha/(2K)`
par queue pour K comparaisons, puis on revient à l'échelle de D. Cela donne :

```text
L = log(4*K/alpha)
m = somme(D_i)/n
S² = somme((D_i-m)²)/(n-1)
r = sqrt(2*S²*L/n) + 14*L/(3*(n-1))
intervalle = [max(-1,m-r), min(1,m+r)]
```

L'union sur les deux queues et les K comparaisons donne une couverture
simultanée au moins `1-alpha`. Les comparaisons peuvent être dépendantes ;
les réplicats doivent être indépendants et de même loi pour cette application.
La variance est celle des **différences**, pas celle de chaque résolution
prise séparément. Son calcul centré en deux passes évite la soustraction de
deux grands moments presque égaux.

Une variance observée nulle conserve le terme positif `14*L/(3*(n-1))`.
Elle ne prouve ni variance vraie nulle ni différence vraie exactement nulle.
Cette option peut donner une borne plus étroite à faible variance, mais peut
aussi être moins précise que Hoeffding pour d'autres données.

## Contrat explicite et compatibilité

Les critères v1 continuent à exiger exactement les champs I32 et à produire
les mêmes formats/résultats. L'option exige :

- `criteria_version = weighted-autosomal-equivalence-criteria-v2` ;
- `method = empirical_bernstein_maurer_pontil_2009` ;
- les mêmes identifiant, hash du plan, alpha, quatre marges et rayon maximal ;
- au moins deux graines dans le plan lié.

Les critères et leur méthode doivent être fixés avant résultats. Il est
interdit de sélectionner après coup la méthode qui conclut, ou de prendre
le minimum non corrigé entre Bernstein et Hoeffding. Les identités et les
limites d'authentification/pré-enregistrement I32 restent applicables.
Le chargeur JSON existant accepte cette version explicite sans migration v1.

## Prévision sans données

`preview_weighted_equivalence` conserve le schéma v1 pour Hoeffding.
En v2, `precision_satisfied`, `required_replicates_per_cell` et
`simultaneous_radius_unclipped` valent `None` : la variance reste inconnue.
Il annonce séparément :

- rayon et effectif conditionnels à une variance **observée** nulle ;
- rayon et effectif suffisants par l'étendue, via `S² <= n/(n-1)` ;
- `precision_guaranteed_from_range`, qui vérifie cette seconde borne ;
- `sample_size_must_be_fixed=true` et `precision_is_outcome_dependent=true`.

Le rayon pessimiste est `sqrt(2*L/(n-1))+14*L/(3*(n-1))`. L'effectif suffisant
est trouvé sans simulation ni liste de graines supplémentaire, par recherche
entière sur cette borne monotone. Le scénario de variance nulle ne garantit
pas la précision observée ; le scénario pessimiste peut demander davantage
de répétitions que la méthode v1. Aucune durée matérielle n'est prédite.

## Évaluation

`empirical_bernstein_interval(values, comparisons=K, alpha=...)` fournit moyenne,
variance sans biais, effectif, budget logarithmique, rayon non tronqué et
intervalle. Il refuse valeurs non finies/hors [-1,1], booléens et effectif <2.

`assess_weighted_equivalence` réutilise les vérifications du rapport I31 et
recalcule les différences. La v2 exporte, pour chaque comparaison,
`sample_variance`, `radius_unclipped` et `precision_satisfied`. La précision
globale exige le respect du rayon maximal pour **toutes** les comparaisons.
Le maximum des rayons observés est exporté séparément dans la prévision
enrichie ; un rayon prédit sous variance nulle n'est jamais utilisé à sa place.

Les décisions strictes I32 sont conservées : différence détectée, équivalence
soutenue, résultat non concluant ou précision insuffisante. La sortie porte
`weighted-autosomal-equivalence-assessment-v2`, et la convergence globale reste
`not_established`, même si l'équivalence est soutenue dans la famille finie.

**Pas d'arrêt optionnel** : ces bornes valent à un effectif fixé avant résultats.
Observer plusieurs fois les intervalles puis arrêter quand ils conviennent
nécessiterait une autre garantie statistique, absente d'I34. Le nombre de
réplicats ne peut pas être adapté aux mêmes observations pour conserver la
couverture annoncée sans correction.

## Exemple de prévision, sans simulation

Depuis `reich_experiment_v2/`, dans `nix develop` :

```python
from pathlib import Path
from study_weighted_autosomal_resolution import load_weighted_resolution_plan
from weighted_autosomal_equivalence import (
    CRITERIA_VERSION, BERNSTEIN_CRITERIA_VERSION, BERNSTEIN_METHOD, METRICS,
    preview_weighted_equivalence, empirical_bernstein_interval,
)
from paleogen_rl.genetics.protocol import _canonical
import hashlib

plan, _ = load_weighted_resolution_plan(Path('../docs/science/m3-confirmation-budget-plan.json'))
criteria = dict(criteria_version=BERNSTEIN_CRITERIA_VERSION, method=BERNSTEIN_METHOD,
    criteria_id='cost-comparison-only', study_plan_sha256=hashlib.sha256(_canonical(plan).encode()).hexdigest(),
    alpha=.05, margins={metric: .02 for metric in METRICS}, max_interval_radius=.01)
forecast = preview_weighted_equivalence(criteria, plan)
old = dict(criteria, criteria_version=CRITERIA_VERSION)
del old['method']
hoeffding = preview_weighted_equivalence(old, plan)
print(forecast['comparisons'], forecast['zero_variance_required_replicates_per_cell'],
      forecast['worst_case_sufficient_replicates_per_cell'], hoeffding['required_replicates_per_cell'])
print(forecast['precision_satisfied'])
interval = empirical_bernstein_interval([0.]*5000, comparisons=136, alpha=.05)
print(round(interval['radius_unclipped'], 6))
```

Les marges et le rayon ci-dessus sont une **illustration de coût**, sans
adoption scientifique. Les 5000 différences nulles sont un vecteur analytique,
pas des résultats simulés. Le gabarit I33 n'est pas exécuté ; une véritable
confirmation exigerait un nouveau plan avec toutes ses graines et des
critères liés à sa nouvelle empreinte, gelés avant données.

## Preuves de validation

Le 26 octobre 2026, **8 tests ciblés, 164 tests autosomaux et 241 tests complets**
réussissent sous Nix, sans échec ni test ignoré. Les contrôles vérifient formule,
deux queues, variance sans biais, changement d'échelle, constantes et stabilité.
L'énumération de tous les effectifs possibles de 18 lois binomiales (n=30/100/1000,
plusieurs probabilités et budgets de comparaison) vérifie leur couverture
numérique ; elle complète la dérivation, sans être une preuve pour toutes les lois.

Le contrôle absorbant I31 réel utilise N=40/G=1/f=0, 160 graines et trois
résolutions (480 évaluations full). Les marges de test ne sont pas scientifiques.
Des observations synthétiques contrôlées vérifient qu'une variance plus élevée
peut empêcher la précision demandée, sans changer les marges. Le chargeur,
les refus, la prévision sans RNG/moteur et la compatibilité numérique exacte
des sept aperçus I33 sont vérifiés ; les archives restent inchangées.

L'exemple a produit `136 4339 194473 172031`, puis `None` et `0.008677`.
La première valeur d'effectif est conditionnelle à une variance observée nulle ;
la seconde garantit le rayon par l'étendue, la troisième est la prévision
Hoeffding antérieure. `None` confirme l'absence de promesse de précision observée.
Environnement relevé : Linux x86_64, Python 3.14.8, NumPy 2.5.3.
