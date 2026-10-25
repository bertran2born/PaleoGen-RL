# Évaluation pulse avec blocs — I16–I17 / M3

I16 expose I15 dans `run_experiment.py` en mode **full**, sur activation explicite.
Le chemin sans carte conserve le moteur, le schéma et les statistiques historiques.
Les blocs n'ont pas encore de résolution principale ou de carte empirique validée.
Ce choix reste un paramètre déclaré par l'utilisateur, identique pour toutes les
conditions qu'il souhaite comparer. Aucun DoD global de M3 n'est coché ici.

## Carte et lancement

Un fichier JSON de carte contient exactement deux clés, sans paramètres implicites :

```json
{
  "panel": {"panel_id": "synthetic-four", "block_ids": ["a", "b", "c", "d"]},
  "switch_probabilities": [0.1, 0.1, 0.1]
}
```

La carte réutilise les contraintes I12 : B blocs uniques de poids égal, B−1
probabilités finies dans [0, 0.5]. L'ordre est celui du panel. Les partenaires
doivent être nommés explicitement, même pour le contrôle neutre ; leurs annotations
ne changent pas le dénominateur. Ils peuvent désigner le même bloc si ce choix est
explicite. Le fichier conserve une empreinte SHA-256 de ses octets exacts ; la carte
réalisée est également stockée, sans dépendre de la persistance du chemin original.

Depuis `reich_experiment_v2/`, avec ce JSON enregistré dans `/tmp/pulse-map.json` :

```sh
nix develop -c python run_experiment.py --scenario all --mode full \
  --block-map /tmp/pulse-map.json --mt-partner-block a --y-partner-block c \
  --N 40 --f 0.5 --male-frac 0.5 --gens 3 --reps 2 --seed 17 \
  --output /tmp/block-pulse.csv
```

L'exemple est synthétique et ne mesure pas une fréquence à 50 ka. Les chemins de
sortie CSV et JSON doivent être nouveaux ; les deux sont vérifiés avant simulation
et ouverts en création exclusive. Une destination explicite `.csv` est obligatoire.
I17 ajoute `quick` et `adaptive` avec la même carte et des destinations nouvelles.
Aucun arrêt anticipé du moteur historique n'est utilisé pour décider le sort des blocs.

## Initialisation et sélection

`initialise_pulse` reprend l'arrondi Python de M2 : `round(f*N*male_fraction)`
mâles modernes, `round(f*N*(1−male_fraction))` femelles modernes. Les quotas
N//2 et N−N//2 sont respectés ou l'entrée est refusée. Les modernes occupent
les premières places de chaque sexe ; ils sont modernes sur les deux homologues
de chaque bloc et portent mtDNA moderne et Y moderne chez les mâles. Les femelles
portent Y=−1. Les effectifs réalisés et la fréquence initiale sont tracés : un
arrondi à petit N peut différer de f, même à une borne. Aucun hasard n'est consommé
par cette initialisation.

Tous les scénarios nommés sont projetés vers `BlockSelection` I15. Les overrides
réciproques conservent les coefficients de base du scénario. Les graines de
simulation restent `seed+i`, appariées entre scénarios ; les tirages SI1 gardent
`seed+i+27383`, les mêmes règles d'application et l'empreinte du fichier exact,
y compris compression. Les coefficients réalisés sont soumis aux domaines I15.

L'adaptateur `run_block_full` refuse les configurations activant des mécanismes
hors I15 (X, sélection autosomale directe, drive, DMI SI3 génériques, stérilité,
cycles ou second pulse), ainsi que toute modification des champs non supportés
par rapport aux valeurs Config par défaut. Il refuse aussi un arrêt anticipé.
Les indices partenaires historiques ne remplacent pas les identifiants explicites.
Le moteur M2 reste en lecture seule ; aucune identité RNG entre moteurs sous
sélection n'est revendiquée.

## Mesures et formats

Le schéma CSV/JSON des blocs est `block-pulse-result-v1`, le modèle
`panmictic_pulse_phased_blocks_reciprocal_epistasis`. Chaque CSV conserve la
configuration d'entrée réalisée, la provenance SI1, la chronologie du contrat M1,
la carte et un `block_report` JSON versionné `block-pulse-evaluation-v1` contenant
l'initialisation, le rapport I15 complet, l'échantillonnage et la cible. Pour
rejouer, reconstruire la carte depuis ce rapport, puis fournir le Config réalisé
et les partenaires stockés dans sa sélection à `run_block_full`.

La nouvelle mesure totale I11 reste distincte du proxy neutre historique M1.
Tous les blocs, partenaires inclus, interviennent dans `auto_mod` et dans la cible
inclusive **[0.03, 0.07]**. Le moteur doit avoir réellement atteint l'horizon ; les
marqueurs absorbés ne permettent pas d'écourter les autosomes. Le champ hérité
`auto_mod_at_50ka` désigne l'horizon demandé : seul l'horizon de référence est
proche de 50 ka ; `target_age_ka` et les générations déclarent la date réelle.

Pour K mâles portant **simultanément** mtDNA/Y modernes sur Nm mâles, la probabilité
sans remise est `P10 = produit((K−i)/(Nm−i), i=0..9)` si K≥10, sinon 0. Elle ne
vaut pas le produit des fréquences marginales. La fixation est rapportée séparément.
Le critère conjoint conserve exactement `P10 * indicatrice(ascendance dans 3–7%)`.
Cette représentation modifie les trajectoires et la mesure, pas les bornes de la
cible ou la formule du critère. Les sorties historiques archivées sont inchangées.

Le résumé JSON conserve les estimations et intervalles Monte Carlo existants.
Avec un seul réplicat, les intervalles bootstrap sont `null`, sans prétendre
estimer une incertitude. Le JSON blocs est strict, sans NaN. Les coûts I15 des
candidats et transmissions sont cumulés par scénario ; la taille d'une population
est conservée séparément, sans additionner les réplicats pour prétendre mesurer
un pic mémoire. Une erreur reproductive termine la CLI avec code 1, sans écrire
de CSV/JSON de réussite ni supprimer un réplicat de l'estimation.

Les notes scientifiques signalent approximation du Ne, poids égaux, recombinaison
non calibrée et partenaires inclus ; elles ne revendiquent pas la reproduction
des probabilités intégrées du préprint. `convergence_status` annonce explicitement
que les scénarios sélectionnés n'ont pas de convergence établie. Le contrôle neutre
I14 ne justifie pas automatiquement la carte choisie ici. Les fichiers de schémas
différents ne constituent pas une comparaison autosomale homogène ; les outils
historiques de comparaison ne sont pas migrés dans cette issue.

## Vérification du 25 octobre 2026

Les quatre commandes de [I16](../issues/I16-integrate-full-block-pulse-cli.md)
ont réussi sous Nix : **11 tests ciblés, 54 autosomaux, 35 pulse et 131 complets**.
Les tests historiques, le moteur de référence et les ressources tierces n'ont
pas été modifiés. Les preuves sont dans `tests/test_autosomal_pulse.py` :

| DoD I16 | Preuves |
| --- | --- |
| ID1 | Matrice N=5/40/81, f=0/0.05/0.5/1 et fractions masculines 0/0.5/1, comparée à `_init` M2 : sexes, marqueurs, copies autosomales et quotas impossibles. |
| ID2 | Deux exécutions `--scenario all`, deux réplicats par scénario, puis rejeu de chaque ligne depuis Config et carte exportés ; overrides et posterior synthétique signé avec les graines SI1 originales. |
| ID3 | Comparaison à I15 sur graines 0/17/42, cas analytiques combinatoires P10 (dont marqueurs partiellement associés), bornes 0.03/0.07 et valeurs voisines, refus des mesures incomplètes. |
| ID4 | Schémas, empreintes, panel/dénominateur, diagnostics, coûts cumulés, notes et convergence déclarée ; JSON strict avec un seul réplicat ; refus des modes, options, cartes, destinations et Config incompatibles. |
| ID5 | Les quatre suites passent ; les assertions historiques restent intactes. |

Le test de létalité utilise un posterior synthétique de coefficient mt=1, un
pulse nul et le scénario `reich_point` : il échoue réellement à la reproduction,
sort avec le code 1 et ne produit aucun CSV/JSON. Les tests d'horizons incomplets
et certains états analytiques utilisent des fixtures contrôlées, distinctes de
cette simulation réelle. Les cartes et paramètres des tests sont synthétiques ;
aucun de leurs résultats ne constitue une validation historique.

L'exécution CLI couvrant tous les scénarios utilise exactement les valeurs de
l'exemple ci-dessus, avec carte et destinations isolées dans des répertoires
temporaires. Les métadonnées et statistiques sont identiques entre répétitions
après exclusion du chemin de sortie et des temps matériels.
I16 laissait les modes anticipés et la convergence des scénarios sélectionnés ouverts,
ainsi que M1 D8/D9. Aucun milestone n'est modifié et aucun commit/push effectué.

## Protocole des modes I17, fixé avant exécution

La matrice de référence est fixée à N=40, horizon=40, f=0/0.5/1, fraction
masculine=0.5, graines **0/17/42**, quatre blocs a/b/c/d, cartes de probabilités
**(0,0,0)** et **(0.1,0.1,0.1)**, partenaires a/c. Scénarios : **neutral,
reich_point, symmetric_1pct, reich_plus_favor_arch_1pct**, chacun avec dominances
**additive/dominant/recessive**. Les 216 configurations seront comparées entre
full, quick et adaptive sans tolérance statistique : préfixes, marqueurs et
critères conjoints doivent coïncider exactement. Cette matrice ne sera pas
modifiée après observation des résultats. Tous les scénarios nommés sont aussi
exercés en CLI sur deux réplicats (graines 17/18), N=40, f=0.5, horizon=3 et
la carte synthétique à quatre blocs ci-dessus.

Un contrôle de réussite non nulle utilise une **initialisation synthétique
contrôlée**, sans changement des observations : N=40, 20 blocs, ascendance
moderne fixée sur les deux homologues du bloc b0 chez tous les
individus, autres blocs archaïques. mtDNA/Y modernes fixés ; les blocs demeurent
donc à **5 %**, P10=1, critère conjoint=1. Recombinaison nulle/active 0.1, horizon
40, graines 0/17/42, avec ou sans DMI (mt moderne × nucléaire archaïque=0.1,
partenaire b1). La population est une fixture de test, pas un pulse historique.
Elle vérifie notamment que la sélection reste active après absorption.

`quick` s'arrête après une génération complète dès que les deux marqueurs sont
absorbés, sans aucun tirage supplémentaire ni suppression de sélection. Même
à horizon atteint, sa mesure autosomale finale et ses diagnostics partenaires
finaux restent nuls. Un diagnostic séparé conserve uniquement fréquence au
point d'arrêt et génération réelle ; il n'est pas une mesure finale.

`adaptive` fait ce même écran. Si P10=0, l'ascendance reste non évaluée et le
critère conjoint vaut zéro ; sinon il rejoue **la même graine** depuis le même
état initial à horizon complet avec toute la sélection I15. Ce rejeu ne change
donc pas les autosomes de full. Les deux passes doivent donner les mêmes
marqueurs ; un écart est une erreur. Aucune ascendance inconditionnelle n'est
estimée sur les seules continuations. Quand une continuation est sautée, sa
viabilité reproductive future n'est pas évaluée ; seul l'événement uniparental
est impossible. Tout échec d'une passe effectivement exécutée reste une erreur.

Les sorties full I16 restent en v1. Les modes anticipés utilisent
`block-pulse-result-v2` et `block-pulse-evaluation-v2`, déclarent le mode,
`screening_report`, `engine_report`, `ancestry_measurement`, la génération des
marqueurs et le diagnostic intermédiaire. Les coûts cumulés incluent l'écran et
le rejeu ; la taille d'une population est un maximum de dimensions, pas un pic
mémoire réel. En cas d'échec de continuation, le rapport d'erreur conserve ses
coûts propres dans `work_units` et le cumul avec l'écran dans `total_work_units`.
Les valeurs indisponibles sont nulles en JSON et vides en CSV.
Le format historique sans carte et ses règles RNG restent inchangés.

Pour rejouer une ligne v2, reconstruire la carte et les partenaires depuis
`engine_report`, le Config depuis `config_realized`, puis appeler
`run_block_mode(config, mode, carte, partenaire_mt, partenaire_y)`. Cet adaptateur
contrôle le mode explicitement ; `run_block_full` conserve son contrat I16.
Les options de carte, de provenance SI1 et de protection des destinations sont
les mêmes qu'en full. Le rapport distingue `marker_generations_completed` et
`auto_generations_completed` ; une continuation positive doit atteindre l'horizon
déclaré même si les marqueurs étaient absorbés dès la première génération.

## Preuves I17 du 25 octobre 2026

Les commandes de [I17](../issues/I17-evaluate-adaptive-block-pulse.md) ont réussi
sous Nix : **9 tests ciblés, 63 autosomaux, 35 pulse et 140 complets**. Après
séparation des coûts propres/cumulés d'une continuation échouée, les 9 tests
ciblés et les 140 tests complets ont été exécutés de nouveau avec succès.

| DoD I17 | Preuves dans `tests/test_autosomal_block_modes.py` |
| --- | --- |
| ID1 | `test_quick_states_equal_full_prefix_without_rng_or_selection_change` : phase, sexes, marqueurs et coûts identiques au préfixe full sur 18 configurations ; `test_quick_at_horizon_and_zero_horizon_never_expose_final_values` et matrice principale : valeurs finales et diagnostics partenaires nuls, même à horizon atteint. |
| ID2 | `test_preregistered_reference_matrix_matches_full` : égalité exacte des marqueurs et du critère conjoint sur les 216 références déclarées ; `test_synthetic_positive_joint_event_keeps_five_percent_and_all_selection` : 12 configurations synthétiques avec critère égal à 1 et coût réel de sélection après absorption. |
| ID3 | CLI de tous les scénarios répétée et chaque ligne rejouée, sans estimation autosomale inconditionnelle ; coûts des deux passes additionnés, taille d'état non cumulée ; générations d'écran et de mesure finale séparées et JSON strict à un réplicat. |
| ID4 | Fixtures d'écran incohérent, mesure rapide invalide, continuation incomplète, marqueurs divergents et échec de continuation ; ce dernier conserve coûts propres et cumulés. Deux simulations CLI réellement létales (quick/adaptive, posterior synthétique mt=1 et f=0) sortent avec code 1 sans CSV/JSON de réussite. |
| ID5 | Les quatre suites ci-dessus passent. Le seul changement intentionnel du test I16 remplace les refus quick/adaptive par un mode inconnu ; tous ses autres contrôles restent présents. Les tests et le moteur M2 restent inchangés. |

Les graines et références n'ont pas été ajustées après exécution. Les états à
5 % et les erreurs de continuation injectées sont des fixtures contrôlées,
distinctes des simulations de la matrice et des échecs létaux réels. Ces preuves
ne constituent pas une validation historique ni une étude de convergence sous
sélection. M3 n'est pas déclaré achevé ; M1 D8/D9 restent ouverts. Aucun fichier
milestone, observation, récompense ou ressource tierce modifié. Aucun commit/push.
