# Plans explicites de diagnostic multirésolution — I21 / M3

I18 fournit un contrôle court à N=40 sur 20 générations. I21 permet de déclarer
la démographie et le lot de simulations dans un fichier avant de les exécuter,
avec les mêmes cartes synthétiques, estimateurs, scénarios et compteurs de
travail. Cette capacité prépare les études au régime cible sans adopter une
résolution principale ni affirmer leur convergence.

## Déclaration et exécution

Le format `selected-autosomal-resolution-plan-v1` exige exactement les champs
de cet exemple **synthétique**, sans valeur de référence historique :

```json
{
  "plan_version": "selected-autosomal-resolution-plan-v1",
  "plan_id": "synthetic-test",
  "population_size": 40,
  "f": 0.5,
  "male_fraction": 0.5,
  "generations": 2,
  "map_length": 0.25,
  "resolutions": [2, 3, 5],
  "seeds": [17, 73],
  "scenarios": ["neutral", "reich_plus_symmetric_1pct"]
}
```

Enregistrer cet exemple dans un fichier neuf, puis depuis
`reich_experiment_v2/`, avec une destination de rapport inexistante :

```sh
nix develop -c python study_autosomal_resolution.py \
  --plan /tmp/resolution-plan.json --output /tmp/resolution-report.json
```

N doit être un entier ≥20, l'horizon un entier positif, les fractions finies
dans [0,1], et les quotas modernes par sexe réalisables après les arrondis M2.
L'étendue est finie et positive ou nulle. Il faut au moins trois nombres de
blocs entiers ≥2 strictement croissants, des graines entières non négatives
distinctes et au moins un scénario existant sans doublon. L'identifiant doit
être non vide et sans espaces aux extrémités. Champs inconnus/manquants,
doublons de clés JSON et valeurs non finies sont refusés avant toute simulation.
Les graines et scénarios n'ont aucune valeur implicite dans un plan.

N=1450 et 6993 générations sont déclarables, mais **aucune nouvelle étude à ce
régime n'a été exécutée dans I21**. Le lot synthétique ci-dessus représente
12 évaluations intégrales ; le temps d'une étude longue dépend notamment des
réplicats, de N, des générations, des blocs et des rejets de sélection.

Sans `--plan`, la commande conserve le diagnostic I18 : N=40, f=0.05,
fraction masculine 0.5, 20 générations, 8/32/128 blocs, graines 410000–410127
et les 17 scénarios. L'API historique conserve aussi l'horizon zéro pour ses
contrôles d'initialisation. Le plan CLI exige un horizon positif, comme I19.

## Identité, cartes et rejeu

Les rapports planifiés utilisent `selected-autosomal-resolution-v2`. Ils
conservent tous les réplicats, résultats, intervalles et coûts I18, et ajoutent :

- `plan` : instantané normalisé, suffisant au rejeu dans la même implémentation ;
- `plan_sha256` : SHA-256 de son JSON UTF-8 compact à clés triées ;
- `plan_file_sha256` : SHA-256 des octets du fichier lu par la CLI, ou nul pour
  un appel direct à `run_resolution_plan`.

Fractions et étendue sont normalisées en flottants ; l'ordre des clés et le
formatage du fichier ne changent pas l'identité canonique. L'ordre des listes
reste significatif. Le plan ne contient aucun champ permettant de changer les
observations, la cible inclusive 3–7 %, les coefficients des scénarios ou les
méthodes d'intervalle.

Chaque ligne de résolution contient `autosomal_protocol` et
`autosomal_protocol_sha256`, contrat I19 validé d'identifiant
`<plan_id>:B<nombre de blocs>`. À résolution donnée, tous les scénarios partagent
ce même contrat. Les résolutions distinctes ont des contrats distincts : elles
ne sont pas présentées comme un unique panel identique. Les cartes gardent
`r=-expm1(-2L/(B-1))/2`, avec partenaires mt/Y aux deux extrémités ; leur poids
total reste 2/B. Cette approximation n'est pas une longueur biologique calibrée.

Pour rejouer après suppression du fichier source, lire le rapport puis appeler
`run_resolution_plan(report['plan'])` et comparer l'identité canonique, les
résultats et les empreintes d'implémentation. L'empreinte du fichier source est
une provenance distincte : elle n'est pas recréée depuis l'instantané. Le rapport
inclut aussi l'empreinte de `paleogen_rl/genetics/protocol.py`. Sans plan, le
format I18 reste v1 ; ses archives ne sont ni migrées ni réécrites. Une nouvelle
exécution peut avoir une empreinte de code différente des archives, même si
les valeurs numériques sont identiques.

## Limites et validation

Une identité de contenu ne prouve pas que le plan a précédé l'examen des
résultats. Pour une étude scientifique, versionner le plan et ses décisions
avant exécution, puis conserver ces révisions. I21 ne fournit pas de scellement
temporel, de marge d'équivalence ou de décision automatique de résolution.
Le statut reste `convergence_status=not_established`, et les contrats I19 restent
non validés pour la convergence. Les intervalles restent ponctuels et Monte
Carlo seulement, comme dans I18. Ni Ne réalisé, ni carte humaine, ni poids
physiques des partenaires ne sont calibrés par ce changement.

Les destinations existantes et liens pendants sont refusés. Un plan invalide
ou un échec reproductif n'écrit aucun rapport de réussite partiel. Les codes
de retour sont 0 sur succès, 2 pour une destination déjà présente ou des arguments
CLI invalides, 1 pour une erreur de lecture, de plan ou de simulation.

Validation de [I21](../issues/I21-run-declared-autosomal-resolution-plans.md),
25 octobre 2026 : **7 tests ciblés, 85 tests autosomaux et 162 tests complets**
réussissent sous Nix, sans échec ni test ignoré. Les tests I18 sont conservés.

| DoD I21 | Preuve dans `tests/test_autosomal_resolution_plan.py` |
| --- | --- |
| ID1 | Plans invalides refusés avant moteur ; horizon cible déclarable sans simulation. Quotas impossibles, non-finis, doublons, versions/champs incorrects sont refusés. |
| ID2 | Normalisation indépendante du formatage, contrats I19 communs par résolution, empreintes des fichiers et de l'implémentation vérifiées ; rejeu CLI après suppression de la source. |
| ID3 | Évaluations directes à N=20/41/60, fractions 0.2/0.1/0.5, horizons 1/3/2 et fractions masculines 0.25/0.5 ; indicateurs, initialisation, générations et coûts comparés. Destinations et échecs reproductifs contrôlés. |
| ID4 | Suites ciblée, autosomale et complète sous Nix ; format historique, contrôle neutre archivé et autres invariants I18 vérifiés par ses huit tests inchangés. |

L'exemple JSON de ce document a également été lu, exécuté sous Nix dans un
dossier temporaire puis rejoué depuis l'instantané après suppression de sa
source : **12 évaluations**, **963 candidats**, **960 descendants acceptés**,
**6430 copies de blocs transmises**, au plus **400 entrées alléliques** par
état. Le rapport rejoué est identique, à l'exception de la provenance du fichier
source qui reste distincte comme annoncé. Le statut est `not_established`.
Ces compteurs sont des unités logiques, pas un benchmark matériel.

`git diff --check`, liens locaux, structure et taille de l'Issue sont vérifiés.
Aucun moteur, paramètre de scénario, observation, résultat archivé ou ressource
tierce n'est modifié. Aucun blocage ne subsiste pour I21. M3 reste ouvert ;
ses décisions de protocole principal et sa validation au régime cible ne sont
pas résolues par ce travail. Aucun milestone n'est modifié dans cette Issue.
