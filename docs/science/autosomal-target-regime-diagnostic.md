# Diagnostic autosomal au régime cible — I22 / M3

## Plan fixé avant résultats

Le [plan I22](autosomal-target-regime-plan.json) déclare N=1450 diploïdes,
f=0.05, fraction masculine=0.5, horizon intégral de 6993 générations,
résolutions 8/32/128 et segment abstrait L=1. Les scénarios sont `neutral`,
`reich_point` et `reich_plus_symmetric_1pct`, chacun sur les graines publiques
520000 et 520001 : **18 évaluations attendues**, sans filtrage des résultats.
Ce lot est un pilote de fonctionnement, d'écarts et de coût, pas une étude
assez puissante pour décider une équivalence numérique.

Empreinte SHA-256 des octets du plan, relevée avant exécution :
`f400cc547acae4143b352013fb68d14c625d1f888e0b60e8d919d2131f65bb10`.
La base logicielle est le commit `25040130872d09bd42ca3d9a5d10e3b924a270bf`.
Les seules additions I22 sont ce plan, son diagnostic, l'Issue, les contrôles
d'archive et le rapport généré. Ce relevé ne fournit pas de certificat temporel
indépendant. Aucun plan ni coefficient n'est ajusté après examen des résultats.

Les arrondis M2 donnent initialement **36 mâles et 36 femelles modernes**, soit
72/1450 = 0.0496551724 d'ascendance, sans changer la fraction demandée pour
forcer exactement 5 %. Les deux homologues de ces individus sont modernes sur
tous les blocs. Le recensement simulé N ne constitue pas une calibration du Ne.
L'horizon correspond au calendrier de référence ; il ne rend pas la carte ou
le mécanisme biologiquement validés.

## Mécanismes et interprétation prévus

Les conventions I18/I21 restent inchangées : probabilité de bascule
`r=-expm1(-2L/(B-1))/2`, partenaires mt/Y aux extrémités 0/1, blocs de poids
égaux et partenaires inclus dans la mesure totale. Le poids cumulé des deux
partenaires vaut 2/B : changer B modifie cette approximation de discrétisation,
pas uniquement une précision numérique à modèle physique exactement constant.
Les trois scénarios partagent un contrat I19 par résolution.

Tous les réplicats sont évalués à l'horizon full, indépendamment de l'absorption
des marqueurs. L'événement des dix mâles est calculé sans remise, séparément
de la fixation. La cible autosomale reste inclusive, 3–7 %. Les statistiques
I18 sont conservées : Wilson ponctuel 95 % pour la fréquence cible, Hoeffding
ponctuel 95 % pour les moyennes d'ascendance, P10 et événement conjoint ainsi
que les différences par graine à 128 blocs.

Avec deux graines par case, le rayon Hoeffding d'une moyenne dans [0,1] vaut
`sqrt(log(40)/4)`, soit environ 0.9603 ; celui d'une différence dans [−1,1]
vaut `sqrt(log(40))`, soit environ 1.9206 avant troncature. Ces intervalles
larges expriment une précision insuffisante. Ils ne démontrent ni convergence
ni divergence. Ils sont Monte Carlo seulement, sans correction simultanée.
Le contrôle neutre et deux scénarios sélectionnés ne remplacent pas une étude
de tous les scénarios, des dominances, des cartes ou des posterior empiriques.

## Exécution et vérification

Depuis `reich_experiment_v2/`, la commande génératrice est :

```sh
nix develop -c python study_autosomal_resolution.py \
  --plan ../docs/science/autosomal-target-regime-plan.json \
  --output ../docs/science/autosomal-target-regime-report.json
```

La destination doit être nouvelle ; pour reproduire une archive déjà présente,
choisir une destination temporaire. Le rapport conserve instantané et identités
du plan, contrats I19, configuration réalisée, cartes, état initial, réplicats,
statistiques, coûts et empreintes des fichiers d'implémentation/verrou Nix.
Les versions restent celles de la base I21. Les tests rapides d'intégrité
I22 ne rejouent pas les simulations longues à chaque découverte de tests.
Les empreintes d'implémentation sont vérifiées lors du rejeu décrit ci-dessous,
pas assimilées à l'implémentation courante de toutes les révisions futures.

Rejeu direct d'une trajectoire sélectionnée par résolution, dans l'environnement
et l'implémentation archivés, depuis `reich_experiment_v2/` :

```sh
nix develop -c python - <<'PY'
import hashlib, json
from pathlib import Path
from run_experiment import Config, run_block_full
from paleogen_rl.genetics.protocol import AutosomalProtocol
report = json.loads(Path('../docs/science/autosomal-target-regime-report.json').read_text())
for path, digest in report['implementation_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
scenario = next(s for s in report['scenarios'] if s['name'] == 'reich_point')
for row in scenario['resolutions']:
    archived = next(r for r in row['replicates'] if r['seed'] == 520000)
    contract = AutosomalProtocol.from_dict(row['autosomal_protocol'])
    result = run_block_full(Config(**row['config_parameters'], seed=520000),
                           contract.recombination_map, contract.mt_partner_block, contract.y_partner_block)
    evaluation = json.loads(result['block_report'])
    assert result['auto_mod'] == archived['ancestry']
    assert evaluation['engine_report']['work_units'] == archived['work_units']
    for key, value in evaluation['sampling'].items():
        assert archived[key] == value, key
    for key in ('target_auto', 'joint_and_target'):
        assert archived[key] == evaluation['target'][key], key
    print(row['block_count'], 'replay identical')
PY
```

## Résultats et preuves

La génération du rapport a retourné **0** le 25 octobre 2026. Le
[rapport archivé](autosomal-target-regime-report.json) contient exactement les
18 évaluations attendues, toutes à 6993 générations, sans échec ni exclusion.
Ses octets ont pour SHA-256
`99cd8cf191a92651cb413edbce10a01502257eaaf6c6b49dd64fa3a85085affd`.
L'identité canonique du plan est
`1facb762aaf4ca85da0c4f2f8c826b979307493aa2e0ac5e2d73e7b37d1d8520` ;
l'empreinte du fichier du plan concorde avec le relevé avant exécution.
Environnement relevé : Linux x86_64, Python 3.14.8, NumPy 2.5.3, PCG64.

Chaque case ci-dessous repose sur **deux** graines ; l'ascendance est une
fraction moyenne, et la colonne cible donne un effectif, pas une probabilité
historique estimée avec précision :

| Scénario | Blocs | Ascendance moyenne | Dans 3–7 % |
| --- | --- | --- | --- |
| neutral | 8 | 0.08659483 | 1/2 |
| neutral | 32 | 0.05337284 | 1/2 |
| neutral | 128 | 0.06435210 | 1/2 |
| reich_point | 8 | 0.12500000 | 0/2 |
| reich_point | 32 | 0.05055496 | 2/2 |
| reich_point | 128 | 0.06674165 | 1/2 |
| reich_plus_symmetric_1pct | 8 | 0.00000000 | 0/2 |
| reich_plus_symmetric_1pct | 32 | 0.03273168 | 2/2 |
| reich_plus_symmetric_1pct | 128 | 0.03963631 | 1/2 |

Les 18 valeurs de P10 et du critère conjoint sont nulles. Chaque moyenne
conserve l'intervalle Hoeffding **[0, 0.9603227913]** : le zéro observé ne
signifie pas une probabilité vraie nulle. De même, 2/2 dans la cible ne signifie
pas une probabilité vraie de 100 %. Les intervalles Wilson restent dans le JSON.

L'écart absolu maximal de moyenne d'ascendance par rapport à 128 blocs vaut
**0.0582583513**, soit environ 5.83 points de pourcentage ; celui de fréquence
cible vaut **0.5**, soit 50 points. Tous les intervalles de différence de ce lot
sont tronqués à [−1,1]. Ils ne permettent pas de conclure à une différence
établie ou à une équivalence. Les trajectoires de même graine utilisent des
flux RNG différents selon B ; elles ne sont pas couplées bloc par bloc.

Coûts logiques des **18 évaluations génératrices**, sans inclure le rejeu :

| Blocs | Candidats, rejets inclus | Descendants produits | Copies de blocs transmises |
| --- | --- | --- | --- |
| 8 | 60 996 218 | 60 839 100 | 975 939 488 |
| 32 | 60 997 133 | 60 839 100 | 3 903 816 512 |
| 128 | 60 990 814 | 60 839 100 | 15 613 648 384 |

Total : **182 984 165 candidats**, **182 517 300 descendants acceptés/produits**,
**466 865 rejets** et **20 493 404 384 copies transmises**. Le plus grand état
contient **371 200 entrées alléliques**, sans prétention de mesurer le pic de
mémoire du processus. Ces unités ne constituent pas un étalonnage de durée
matérielle. Le mode full et les résolutions sont déclarés dans le plan et le
rapport ; les coûts effectifs sont observés après exécution.

Les onze empreintes d'implémentation/verrou du rapport concordent avec les
fichiers locaux lors du rejeu. Les trois trajectoires `reich_point`, graine
520000, sur 8/32/128 blocs et 6993 générations ont été rejouées directement :
ascendance et nombre de copies modernes, statut/horizon, échantillonnage,
cible/critère conjoint, initialisation et coûts sont identiques aux archives.
Ces **trois simulations de vérification** sont distinctes des 18 simulations
génératrices et ne sont pas ajoutées à leurs statistiques.

Les commandes de [I22](../issues/I22-measure-target-regime-autosomal-resolution.md)
réussissent sous Nix : **3 tests ciblés**, **88 tests autosomaux** et **165 tests
complets**, sans échec ni test ignoré. Le rejeu long est exécuté une seule fois,
séparément des trois suites. Les tests d'intégrité rapides restent exécutables
sans répéter ces calculs longs.

| DoD I22 | Preuve |
| --- | --- |
| ID1 | Empreinte pré/post du plan identique ; génération réussie, 3 scénarios × 3 résolutions × 2 graines, tous les horizons vérifiés dans `test_fixed_plan_and_complete_archive`. |
| ID2 | Mesures, dénominateurs, P10 recalculée par combinaisons, intervalles, différences et coûts vérifiés ; neuf altérations contrôlées sont détectées dans `test_tampered_counts_horizons_metrics_maps_and_costs_are_detected`. |
| ID3 | Rejeu réel des trois résolutions ; empreintes d'implémentation vérifiées avant calcul, tous les champs numériques et coûts contrôlés après calcul. |
| ID4 | Résultats et limites ci-dessus ; tests ciblés, autosomaux et complets réussis, JSON strict et provenance contrôlés dans le troisième test ciblé. |

Structure et taille de l'Issue, liens locaux, espaces et `git diff --check`
sont vérifiés. Aucun moteur, observation, récompense, ancien plan, archive
précédente ou ressource tierce n'est modifié. Aucun blocage ne subsiste pour
I22. M3 reste ouvert : protocole principal, poids physiques des partenaires et
validation de convergence restent à établir avec une précision déclarée et un
budget adapté. Aucun milestone n'est modifié dans cette Issue.
