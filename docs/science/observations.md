# Contrat scientifique — science-observations-v1

`observations.json` est le contrat structuré, schéma 1. Il distingue des
observations **rapportées dans le préprint fourni** et des hypothèses de mesure
du simulateur. Les citations donnent identifiant I2, version de contenu SHA-256,
page PDF et section. Elles ne constituent pas une vérification indépendante des
articles primaires cités par Reich. Le préprint n'est pas évalué par les pairs.

## Observations et incertitude

SI3, page 1, « Motivation », paragraphes 1–3, rapporte des lignées mtDNA et Y
apparentées aux humains modernes chez les Neandertaliens échantillonnés. Ce
constat ne démontre pas leur fixation dans toute la population ancienne et ne
définit pas un échantillon empirique commun de dix mâles.

SI1, page 1, « Motivation », et SI3, page 1, « Motivation », rapportent environ
3–7 % d'ascendance apparentée aux humains modernes sur les autosomes. C'est une
plage rapportée, pas un intervalle de confiance à 95 % établi par ce contrat.
Les champs `confidence_level` restent nuls : aucune incertitude historique
chiffrée supplémentaire n'est inventée. Les intervalles calculés sur les
réplicats concernent uniquement l'incertitude Monte Carlo. Le résultat intégré
de cofixation inférieur à 2–3 % dans SI1 est une prédiction de modèle, pas une
observation indépendante à expliquer.

## Quatre statistiques distinctes

Ces définitions opérationnelles portent le statut `hypothesis` ; les observations
ci-dessus portent le statut `observation`.

| Identifiant | Définition à la génération cible | Unité et dénominateur |
| --- | --- | --- |
| `mt_fixation` | `mt_mod == 1` dans toute la population | Booléen ; N copies mtDNA, femmes et hommes |
| `y_fixation` | `Y_mod == 1` chez tous les mâles ; non défini sans mâles | Booléen ; N_m copies Y |
| `ten_male_joint` | Chacun des dix mâles tirés porte simultanément les deux marqueurs modernes | Probabilité ; échantillon sans remise parmi N_m mâles |
| `final_autosomal_ancestry` | Somme des copies modernes aux loci inclus divisée par `2*N*L` | Fraction [0,1] ; tous les individus, L loci diploïdes de poids égal |

SI3, page 1, distingue données échantillonnées et fixation théorique. SI3, page 4,
« Scenario 1 », protocole précédant les résultats, décrit le tirage simulé de dix
mâles et le critère autosomal. Leur utilisation ici est une hypothèse de mesure,
pas une nouvelle observation historique.

Pour K mâles portant **les deux** marqueurs et N_m mâles au total,
`P10 = (K)_10 / (N_m)_10`, où `(x)_10 = x(x-1)…(x-9)`. Si K ou N_m est inférieur
à dix, le prototype retourne zéro ; N_m inférieur à dix signifie aussi que le
plan d'échantillonnage demandé est irréalisable. On ne remplace pas cette formule
par un produit des fréquences marginales ou par un tirage avec remise. Une
probabilité P10 positive n'implique aucune fixation. Les deux fixations conjointes
correspondent au champ existant `joint_fixed`. Moyennée sur les répétitions, P10
est une probabilité prédictive simulée ; elle n'est pas un décompte d'observations.

## Chronologie et démographie de référence

SI1, page 2, « Methods », fixe 28,6 ans/génération, le mélange à 8741 générations
avant le présent (~250 ka) et l'échantillonnage à 1748 (~50 ka), soit **6993
générations écoulées**. Les âges calendaires sont arrondis. Changer `--gens`
ne conserve pas automatiquement l'étiquette « 50 ka ».

La même page indique les tailles effectives uniparentales 7000 (moderne), 2250
(archaïque) et 725 (post-mélange). Elle précise que son analyse de fixation
arrondit cette dernière à 750. SI1, page 1, donne environ 1450 diploïdes comme
moyenne harmonique post-mélange. Le prototype fixe son **recensement** à N=1450,
un pulse f=0,05 et une fraction masculine de 0,5 : ces choix ne constituent pas
une calibration du Ne réalisé. L'égalité des tailles efficaces par sexe est une
hypothèse de SI1, page 2, pas une observation. Les valeurs sont des hypothèses de
modélisation publiées, enregistrées dans `reference_parameters` avec leurs unités.

## Base autosomale et disponibilité

Le proxy actuel vient de `_stats` dans `src/reich_panmictic_original.py`. Sans
sélection autosomale ni DMI, il utilise les huit loci 0–7. Avec les quatre
pénalités réciproques actives et les partenaires par défaut 0 et 1, il utilise
les six loci 2–7. Les autres exclusions de sélection/DMI dépendent de la
configuration réelle. Il faut donc déclarer les loci inclus, exclus et sélectionnés,
pas seulement un nombre de loci. La sélection mtDNA/Y peut influencer les
trajectoires ; « neutre » décrit ici les loci mesurés directement.

La cible reste **inclusive** : `0.03 <= A <= 0.07`. Le proxy à quelques loci
présente un artefact de discrétisation et n'est pas une reconstruction génomique.
Valider séparément des mesures sur six et huit loci ne les rend pas comparables
scientifiquement : la standardisation et la convergence relèvent de M3.

- `full` demande l'horizon complet pour toutes les trajectoires ; une interruption
  du moteur doit encore être exclue par la vérification de génération.
- `quick` ne fournit pas de mesure autosomale finale admissible. Son arrêt précoce
  ne peut pas être réétiqueté comme la génération cible.
- `adaptive` ne poursuit que les trajectoires pour lesquelles l'événement des dix
  mâles demeure possible. Les autres ascendances autosomales sont non évaluées. Leur
  contribution à l'événement conjoint est nulle, mais leur ascendance n'est pas zéro.
  La fréquence autosomale marginale de toutes les trajectoires n'est pas estimable
  à partir de ces seules continuations.

La persistance des états mtDNA/Y après absorption suppose notamment l'absence de
nouveau pulse ou mutation ; l'accélération du prototype après absorption peut
changer les tirages autosomaux individuels. Ce contrat n'étend pas ces garanties.

## Validation explicite des mesures

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_science_contract.py'
```

`science_contract.load_contract()` valide les citations et le schéma sans réseau.
`validate_autosomal_statistic(measurement, expected_generation=6993)` accepte
seulement une mesure `evaluated` avec une valeur finie dans [0,1], une génération
entière égale à l'horizon demandé, un effectif diploïde positif, une base de loci
explicite et un dénominateur cohérent. Exemple de métadonnées pour le proxy à six
loci, avec valeur illustrative **synthétique**, sans simulation historique :

```json
{
  "status": "evaluated", "value": 0.05, "generation": 6993,
  "diploid_individuals": 1450, "allele_copy_denominator": 17400,
  "locus_basis": {
    "kind": "neutral_proxy", "weighting": "equal_diploid_copies",
    "total_loci": 8, "included_loci": [2, 3, 4, 5, 6, 7],
    "excluded_loci": [0, 1], "selected_loci": [0, 1]
  }
}
```

Les listes incluse/exclue doivent partitionner les loci, sans doublon ; tout locus
déclaré sélectionné est exclu de ce proxy neutre. Les autres représentations
génomiques ne sont pas couvertes par ce validateur. Celui-ci vérifie les déclarations,
sans prouver que le moteur a effectivement atteint l'horizon ou mesurer la valeur
à sa place. Les sorties historiques ne possédant pas ces métadonnées ne deviennent
pas conformes automatiquement ; leur migration reste hors d'I3.

Tout changement des observations, des bornes ou de la sémantique nécessite une
nouvelle version du contrat, revue indépendamment des performances des candidats.
