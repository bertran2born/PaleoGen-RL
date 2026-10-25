# Contrat autosomal versionné — I19 / M3

I18 n'établit pas de résolution principale convergente au régime historique.
I19 fournit un contrat réutilisable pour figer les paramètres effectivement
choisis et identifier les évaluations qui emploient ce même contrat. Il n'adopte
aucune carte ou résolution comme référence scientifique par défaut.

## Déclaration et identité

Le format `autosomal-evaluation-protocol-v1` exige exactement :

| Champ | Rôle |
| --- | --- |
| `protocol_id` | Nom explicite, non vide et sans espaces aux extrémités. |
| `population_size`, `generations` | N ≥ 20, horizon ≥ 1, entiers. |
| `pulse` | Fractions `f` et `male_fraction` dans [0,1], quotas M2 réalisables après arrondi. |
| `recombination_map` | Panel ordonné et probabilités I12 explicitement déclarés. |
| `partners` | Identifiants mt/Y présents dans le panel. |
| `measurement` | Mesure totale I11 de poids égaux, dix mâles sans remise, cible inclusive [0.03,0.07]. |
| `resolution_control` | Statut obligatoire `not_established`. |

La clé `protocol_version` doit correspondre à la version ci-dessus. Champs
inconnus/manquants et clés JSON dupliquées sont refusés. La cible, les règles
d'échantillonnage et le dénominateur ne peuvent pas être modifiés par ce fichier.
Les annotations ne suppriment jamais un partenaire de la mesure totale.
L'objet `AutosomalProtocol` est immuable ; les listes d'entrée ne sont pas
conservées par référence dans son panel/carte. Son instantané est un objet JSON
indépendant.

Le SHA-256 canonique porte sur le contenu normalisé, encodé UTF-8, clés triées
et séparateurs JSON compacts. Les fractions et probabilités sont normalisées en
flottants. L'ordre des blocs reste significatif ; l'ordre des clés et les espaces
du fichier ne le sont pas. Modifier le nom, la carte, les partenaires, N,
l'horizon ou le pulse change l'identité. Le SHA-256 des octets du fichier source
est conservé séparément et peut donc différer entre deux mises en forme d'un
même contrat.

## Utilisation CLI

L'[exemple fourni](autosomal-protocol-synthetic.json) représente N=40, trois
générations, quatre blocs et un pulse de 50 %. Ces choix sont **synthétiques**,
sans statut de protocole principal v0.1 ni validation à 50 ka.

Depuis `reich_experiment_v2/`, avec une destination nouvelle :

```sh
nix develop -c python run_experiment.py --scenario all --mode adaptive \
  --autosomal-protocol ../docs/science/autosomal-protocol-synthetic.json \
  --reps 2 --seed 17 --output /tmp/protocol-example.csv
```

Les trois modes sont disponibles et conservent leurs règles I16/I17. Le contrat
fournit N, horizon et fractions ; les options correspondantes peuvent répéter
ces valeurs mais toute contradiction est refusée avant simulation. Le fichier
protocole est exclusif avec les options séparées de carte/partenaires. Une
destination explicite `.csv` nouvelle reste obligatoire, avec refus de l'écrasement
du CSV ou de son JSON compagnon.

Les graines de simulation et de posterior, le nombre de réplicats, les scénarios
et coûts réciproques restent des paramètres d'évaluation distincts du contrat.
Ils demeurent tracés dans chaque résultat. Les modes ne modifient pas l'identité
du contrat : la disponibilité de l'ascendance finale continue d'être déclarée
séparément et reste nulle en quick, même à horizon atteint.

## Sorties et rejeu

Une exécution avec contrat utilise le schéma `block-pulse-result-v3`. Les rapports
numériques internes I16/I17 ne changent pas et restent rejouables ; les nouvelles
colonnes externes et métadonnées JSON lient le résultat au contrat :

- `autosomal_protocol_id`, `autosomal_protocol_version` ;
- `autosomal_protocol_sha256` : empreinte du contenu normalisé ;
- `autosomal_protocol_file_sha256` : empreinte du fichier lu ;
- `autosomal_protocol` : instantané canonique dans chaque ligne CSV, objet natif
  dans les métadonnées JSON ;
- `resolution_control_status=not_established`.

Le JSON conserve aussi le chemin source à titre descriptif. Avec cette entrée,
il n'existe pas de fichier de carte séparé : `block_map_sha256` est vide ; la
carte est protégée par l'empreinte du protocole et conservée dans les instantanés.
Les sorties sans contrat restent respectivement dans leurs schémas historiques,
blocs full v1 ou blocs anticipés v2, sans colonnes de contrat ajoutées.

Pour rejouer sans fichier d'origine : charger `AutosomalProtocol.from_dict` avec
l'instantané, vérifier son `sha256`, reconstruire le Config depuis
`config_realized`, puis appeler `run_block_mode` avec le mode et la carte/les
partenaires du contrat. La chronologie M1 et les graines demeurent dans la ligne.
L'identité commune est une identité du contrat de mesure et de démographie ; elle
ne remplace pas la comparaison des paramètres réalisés, versions de moteur,
graines et statuts de disponibilité.

## Limites

La validation de structure ne valide ni convergence numérique, ni carte humaine,
ni plausibilité des coûts. Un utilisateur ne peut pas déclarer `validated` ou
`converged` pour promouvoir son fichier en preuve : ces états sont refusés. Une
future acceptation de résolution devra vérifier des contrôles distincts avant
d'introduire un autre statut. Aucun résultat I18 n'est réécrit ou réinterprété.

Ce contrat est un préalable à l'adoption d'un protocole principal ; son exemple
ne résout pas le choix de carte, de résolution ou de poids physiques des
partenaires. Les évaluations longues et leur précision Monte Carlo restent à
pré-enregistrer puis vérifier au régime visé. M3 reste ouvert, ainsi que la
dépendance transitive M1 D8/D9. Aucun milestone n'est modifié dans cette issue.

## Vérification du 25 octobre 2026

Les commandes de [I19](../issues/I19-bind-versioned-autosomal-protocol.md) ont
réussi sous Nix : **7 tests ciblés, 78 autosomaux, 35 pulse et 155 complets**.
Les tests précédents et les moteurs n'ont pas été modifiés. Le changement des
valeurs par défaut internes d'argparse permet de détecter les options explicites
contradictoires ; les valeurs historiques sont restaurées avant exécution quand
aucun contrat n'est fourni, ce que couvre aussi la suite de non-régression.

| DoD I19 | Preuve dans `tests/test_autosomal_protocol.py` |
| --- | --- |
| ID1 | Aller-retour, instantanés indépendants, immuabilité, quotas, champs inconnus/manquants, clés dupliquées, cible/échantillonnage modifiés et fausses validations refusés. |
| ID2 | Trois formats JSON ont la même empreinte canonique et trois empreintes de fichier distinctes ; chaque paramètre verrouillé modifié change l'identité. Rejeu depuis les lignes après suppression du fichier temporaire source. |
| ID3 | Tous les scénarios, deux graines et les trois modes : mêmes résultats et rapports numériques que le chemin à carte explicite, même identité de protocole pour toutes les lignes. |
| ID4 | Schéma v3, instantané et empreintes vérifiés dans CSV/JSON ; conflits explicites et destinations existantes refusés avant tout moteur ; options répétant les valeurs et posterior/overrides restent acceptés. |
| ID5 | Les quatre suites Nix passent ; l'exemple fourni est copié à l'identique et exécuté en répertoire temporaire, sans téléchargement ni modification des observations. |

Le contrat peut représenter N=1 450 / 6 993 générations, mais **aucune nouvelle
étude longue ni validation de convergence** n'a été exécutée dans I19. Le statut
reste non établi, y compris pour ce régime. Les archives I14/I18 conservent leurs
empreintes et leur contexte d'implémentation au moment de leur production ; elles
ne sont pas réécrites pour suivre les modifications ultérieures de la CLI.
Les cinq DoD de l'issue sont vérifiés ; M3 n'est pas déclaré achevé.
Aucun commit ni push effectué.
