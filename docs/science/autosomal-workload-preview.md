# Aperçu de coût des études autosomales — I23 / M3

Le runner I21 peut inspecter un plan avant toute simulation. Cette capacité
répond au coût du pilote I22 sans utiliser ses résultats pour choisir un
paramètre scientifique. Aucun plan, scénario, intervalle ou moteur n'est modifié
par l'aperçu.

## Commande et identité

Depuis `reich_experiment_v2/`, avec une destination **nouvelle** :

```sh
nix develop -c python study_autosomal_resolution.py --preview \
  --plan ../docs/science/autosomal-target-regime-plan.json \
  --output /tmp/paleogen-i23-preview.json
```

`--preview` exige `--plan`. Sans cette option, les chemins d'exécution I18/I21
restent inchangés. Le plan est entièrement validé par I21, y compris ses quotas,
graines et scénarios, avant tout calcul d'aperçu. Une destination existante,
y compris le fichier plan lui-même ou un lien pendant, est refusée avec code 2.
Une erreur de lecture ou de plan retourne 1 ; un succès retourne 0. La commande
ne déclenche aucune simulation ni aucun tirage aléatoire.

Le JSON porte `preview_version=selected-autosomal-workload-preview-v1`,
`scientific_status=planning_only`, `simulation_performed=false`, `mode=full`
et `convergence_status=not_established`. Son instantané `plan` et son
`plan_sha256` suivent la normalisation I21. La CLI ajoute l'empreinte des octets
du fichier dans `plan_file_sha256`. L'API
`preview_resolution_plan(plan)` laisse cette dernière à nul. Deux mises en forme
d'un même plan ont la même identité canonique et les mêmes comptes.

## Unités et hypothèses

Pour S scénarios, R graines, N individus, G générations et B blocs, une
résolution comporte S×R évaluations. Si toutes les trajectoires intégrales
aboutissent, elles produisent exactement S×R×N×G descendants et autant de
candidats acceptés. Le minimum de candidats générés est égal à ce nombre ; le
minimum de copies de blocs transmises vaut 2×B×S×R×N×G. Un rejet de sélection
augmente ces deux derniers comptes. L'aperçu n'essaie pas d'estimer les rejets
depuis des résultats pilotes.

Les sorties distinguent explicitement `*_on_completion` et
`*_lower_bound_on_completion`. Ce sont des comptes conditionnels à l'achèvement,
pas un plafond de calcul ni une garantie de réussite. Un échec précoce peut
arrêter le moteur avant ces comptes ; un lot réussi avec sélection peut les
dépasser pour les candidats et copies. Le travail de tentatives échouées reste
affaire des rapports réellement exécutés.

`state_allele_entries=2×N×B` décrit un seul tableau d'ascendance de population.
Le total annonce le maximum entre résolutions, sans additionner les états.
Les allocations temporaires, marqueurs, indices et copies de travail ne sont
pas inclus : ce nombre n'est pas une limite de mémoire du processus. Les
comptes ne prédisent aucune durée matérielle.

## Précision annoncée

La section `precision` dépend seulement du nombre n de graines par case. Elle
reprend les formules I18 : rayon Hoeffding ponctuel 95 %
`sqrt(log(40)/(2n))` pour les moyennes dans [0,1], et
`sqrt(2log(40)/n)` pour les différences appariées dans [−1,1]. Les rayons sont
**non tronqués** : à petit n ils peuvent dépasser l'étendue de la variable.
L'intervalle final sera tronqué après observation de sa moyenne, comme dans I18.

Les graines distinctes sont supposées définir des répétitions indépendantes.
L'appariement des résolutions n'exige pas des flux RNG identiques entre elles.
La confiance est ponctuelle, sans correction simultanée pour les multiples
scénarios, résolutions ou métriques. La fréquence dans 3–7 % garde Wilson,
dont les bornes dépendent des résultats : l'aperçu ne les invente pas.
Ces rayons ne constituent ni une estimation de probabilité, ni un seuil de
convergence, ni une marge d'équivalence. Aucun choix scientifique n'en découle
automatiquement.

## Aperçu réel du plan I22

La commande ci-dessus a retourné 0 le 25 octobre 2026 dans une destination
temporaire ; les simulations longues I22 n'ont pas été relancées. Elle conserve
l'identité canonique I22
`1facb762aaf4ca85da0c4f2f8c826b979307493aa2e0ac5e2d73e7b37d1d8520`.

| Blocs | Évaluations | Descendants si achevé | Copies transmises, minimum | Entrées alléliques d'un état |
| --- | --- | --- | --- | --- |
| 8 | 6 | 60 839 100 | 973 425 600 | 23 200 |
| 32 | 6 | 60 839 100 | 3 893 702 400 | 92 800 |
| 128 | 6 | 60 839 100 | 15 574 809 600 | 371 200 |

Au total : **18 évaluations**, **182 517 300 descendants/acceptations**, au
moins **182 517 300 candidats** et **20 441 937 600 copies transmises**.
L'archive I22 donne exactement ce nombre de descendants, mais **182 984 165
candidats** et **20 493 404 384 copies** après rejets. Elle respecte donc ces
minima. La prévision et l'observation gardent leurs significations distinctes.

Pour les deux graines par case I22, les rayons prévus valent
**0.9603227913** pour les moyennes et **1.9206455826** pour les différences.
Ils rendent visible l'insuffisance de précision de ce pilote avant un nouveau
calcul. Le choix du prochain lot, de sa marge d'équivalence éventuelle et de la
résolution principale reste à établir séparément, sans changer les observations.

## Vérification

Les commandes de [I23](../issues/I23-preview-autosomal-study-workload.md),
exécutées le 25 octobre 2026 sous Nix, retournent 0 avec **7 tests ciblés,
95 tests autosomaux et 172 tests complets**, sans échec ni test ignoré.

| DoD I23 | Preuve dans `tests/test_autosomal_workload_preview.py` |
| --- | --- |
| ID1 | Moteur, runner et RNG interdits par les tests d'aperçu ; répétabilité, instantané indépendant et identité insensible au formatage vérifiés. |
| ID2 | Comparaisons aux petits runs neutres/sélectionnés réels à trois résolutions et aux comptes de l'archive I22 ; totaux et maximum de taille d'état contrôlés. |
| ID3 | Rayons non tronqués, mise à l'échelle en racine de n et correspondance avec I22 ; appels CLI réels, provenance fichier, absence de plan, plans invalides et destinations protégées. |
| ID4 | Les trois suites passent ; commande d'aperçu I22 exécutée, unités et limites documentées. |

`git diff --check`, liens locaux et structure/taille de l'Issue sont vérifiés.
Les SHA-256 du plan I22
`f400cc547acae4143b352013fb68d14c625d1f888e0b60e8d919d2131f65bb10`
et de son rapport
`99cd8cf191a92651cb413edbce10a01502257eaaf6c6b49dd64fa3a85085affd`
restent inchangés. Aucun moteur, observation, scénario, estimateur, ancien plan
ou résultat archivé n'est modifié. Aucun blocage ne subsiste pour I23.
Les coûts effectifs des futurs lots, le protocole principal et la convergence
restent à établir ; aucun milestone n'est modifié ou déclaré achevé.
