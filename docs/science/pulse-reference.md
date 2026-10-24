# Vérification locale du moteur pulse — I5

Cette vérification relève de M2, commencé à la demande explicite de l'utilisateur
avant clôture de M1 D8/D9. Elle s'appuie sur les sources et le contrat I1–I3 ;
elle ne déclare ni M1 ni M2 achevés.

## Protocole fixé

`tests/test_pulse_reference.py` vérifie 108 configurations :

| Dimension | Valeurs |
| --- | --- |
| Graines | 0, 17, 42 |
| Fraction moderne initiale | 0, 0.05, 1 |
| Scénario | `neutral`, `reich_point` |
| Dominance sans pénalité | `additive`, `dominant`, `recessive` |
| Arrêt à absorption | désactivé, activé |
| Taille et horizon | N=80, 32 générations |

Les quatre pénalités de l'extension sont explicitement nulles. `reich_point`
conserve les paramètres existants `s_mt=0.0032`, `s=0.0013`, `sel_locus='Y'`.
La proportion masculine du pulse conserve sa valeur par défaut 0.5. Les petites
tailles et durées sont des configurations de test, pas une calibration historique.

Pour chaque configuration, le test exécute le moteur original local puis son
extension, chacun avec son propre RNG initialisé à la même graine. Des observateurs
temporaires de `_init` et `_step` copient les tableaux effectivement produits
(`sex`, `mt`, `Y`, `auto`, `X`) et l'état du générateur, sans tirage supplémentaire.
Les types, valeurs des tableaux, états RNG et nombres de générations doivent
coïncider exactement. Les statistiques partagées sont comparées sans tolérance.
L'arrêt précoce des cas fixés/perdus est effectivement vérifié ; les cas sans
arrêt doivent produire les 32 générations demandées.

Les indicateurs ajoutés sont vérifiés depuis la population terminale : nombre
de mâles, porteurs conjoints, fixation conjointe et probabilité des dix mâles.
Cette probabilité est recalculée par `comb(K,10)/comb(N_m,10)`, indépendamment du
produit utilisé par l'extension, avec une tolérance absolue de l'ordre de 1e-14
pour l'arrondi flottant. Un cas supplémentaire N=200, f=0.5, une génération,
graine 0, montre une probabilité positive sans fixation et distingue le calcul
sans remise de l'approximation avec remise. Le filtre autosomal 3–7 % reste inchangé.

Pour les deux scénarios et trois graines, deux exécutions identiques sont
comparées avant puis après une épistasie active, et après une erreur réelle de
dominance dans la reproduction épistatique. Le hook temporaire `_dm_penetrance`
doit être restauré, et les trajectoires de référence suivantes rester identiques.

Enfin, chaque scénario est lancé deux fois par la CLI avec N=80, 32 générations,
trois répétitions, graine de départ 0 et mode `full`, vers des fichiers temporaires
distincts. Les CSV doivent être identiques octet par octet ; les JSON sont
comparés après retrait des seuls chemins de sortie et champs `time_seconds`.
Les paramètres, graines et intervalles Monte Carlo restent dans la comparaison.

## Commandes et portée

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_pulse_reference.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

La référence est la copie locale SI3 inventoriée par I1. La parité est démontrée
pour la matrice testée, dans l'environnement exécuté ; elle n'est pas une garantie
d'identité bit à bit entre toutes les versions de NumPy ou toutes les machines.
Elle ne reproduit pas la distribution intégrée de probabilités du préprint et
ne valide pas la plausibilité biologique de l'épistasie.

L'accélération après absorption n'est pas activée dans la matrice : elle peut
consommer un autre flux RNG et modifier les autosomes individuels, comme décrit
dans `observations.md`. La sémantique complète des modes `quick`/`adaptive`,
l'enrichissement des métadonnées et l'ascendance commune de M3 restent à vérifier
séparément. Aucune graine ou sortie archivée n'est modifiée par ces tests.

Vérification du 24 octobre 2026 : les trois commandes ci-dessus réussissent sous
Nix, respectivement avec 4 tests ciblés (dont les 108 configurations), 14 tests
pulse et 56 tests complets. Aucun changement du moteur n'a été nécessaire.

## Évaluation selon le mode — I6

La CLI applique désormais la politique de mesure avec `run_mode` sans changer
le moteur, ses graines, ses paramètres ou le seuil 3–7 %. Chaque mode fournit
les mêmes champs de disponibilité finale :

| Mode / condition | `auto_evaluation_status` | `auto_mod_at_50ka` | `target_auto` | `joint_and_target` |
| --- | --- | --- | --- | --- |
| `full` | `evaluated_at_target` | mesure finale | booléen final | P10 × filtre final |
| `quick` | `not_evaluated_quick` | `NOT_EVALUATED_QUICK` | vide | vide |
| `adaptive`, P10 = 0 | `not_evaluated_event_impossible` | `NOT_EVALUATED_EVENT_IMPOSSIBLE` | vide | 0 |
| `adaptive`, P10 > 0 | `evaluated_at_target` | mesure après continuation | booléen final | P10 × filtre final |

Le nom historique `auto_mod_at_50ka` désigne l'horizon `gens_requested` ;
seule la configuration chronologique par défaut correspond à environ 50 ka.
`auto_mod` reste une mesure brute du premier passage. En `quick` et `adaptive`,
elle est aussi exposée par `auto_mod_at_early_stop` : elle n'est pas une mesure
finale utilisable sans consulter le statut. `generations_completed` conserve
la génération du premier passage, y compris lorsqu'une continuation adaptative
est exécutée. Le mode `quick` ne publie pas de mesure finale même si le premier
passage atteint l'horizon demandé : c'est une politique conservatrice explicite.

La continuation adaptative repart de la même graine avec la même configuration,
sans arrêt précoce, et conserve le contrôle de concordance P10. Son accélération
peut changer les autosomes après absorption ; aucune égalité trajectorielle
autosomalement accélérée avec `full` n'est revendiquée. Quand P10 est nul,
l'événement conjoint vaut zéro, mais l'ascendance demeure non évaluée : cela
ne signifie pas que le filtre autosomal aurait échoué.

Les JSON conservent `P_autosomal_range` uniquement en `full`, car les trajectoires
adaptatives non poursuivies ne permettent pas d'estimer cette probabilité
inconditionnelle. `P_joint_and_auto` est disponible en `full` et `adaptive`,
jamais en `quick`. Les intervalles existants mesurent seulement l'incertitude
Monte Carlo, pas l'incertitude historique.

`tests/test_pulse_modes.py` compare les trois modes sur 36 configurations réelles :
`neutral`, `reich_point`, `reich_plus_symmetric_1pct` ; graines 0/17/42 ; N=80 ;
couples (f, générations) : (0,80), (0.05,80), (1,80), (0.5,1).
Les cas extrêmes vérifient effectivement l'arrêt avant l'horizon ; les cas courts
polymorphes comprennent un événement positif sans fixation. Les marqueurs et
P10 concordent avec `full`, y compris avec épistasie active.

Des résultats contrôlés vérifient séparément les branches de disponibilité :
une mesure précoce de 5 % ne compte pas comme réussite non évaluée ; une mesure
finale hors cible remplace le filtre précoce ; une divergence P10 est refusée.
Ces fixtures sont des tests de politique, pas des résultats simulés ni des preuves
historiques. Les sorties adaptatives mixtes sont sérialisées dans les deux ordres.
Enfin, six appels CLI réels couvrent chaque mode aux deux fréquences extrêmes,
avec inspection des CSV et JSON. Ces petits horizons ne calibrent pas le modèle
historique et ne reproduisent pas les probabilités intégrées du préprint.

Commandes depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_pulse_modes.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Vérification I6 du 24 octobre 2026 : ces commandes réussissent sous Nix avec
respectivement 4, 18 et 60 tests. Les cinq DoD de l'Issue sont vérifiés ; M2
reste incomplet et son fichier milestone n'est pas modifié.

## Métadonnées rejouables — I7

Les nouvelles lignes CSV produites par `run_experiment.py` utilisent
`result_schema_version=pulse-result-v1` et identifient le moteur étendu par
`model=panmictic_pulse_reciprocal_epistasis`, y compris lorsque ses quatre
pénalités sont nulles. Ce nom identifie la famille de moteur ; le scénario
nommé et la configuration complète distinguent les simulations. Les anciennes
colonnes sont conservées ; aucun résultat archivé n'est réécrit.

`config_realized` est un objet JSON encodé dans une cellule CSV, avec tous les
champs de la dataclass `Config`, après application des paramètres CLI, overrides,
et éventuel tirage mitochondrial. On peut rejouer une ligne dans le même
environnement et avec le même code, sans consulter le scénario nommé :

```python
import csv
import json
from run_experiment import Config, run_mode

with open('result.csv', newline='') as stream:
    row = next(csv.DictReader(stream))
result = run_mode(Config(**json.loads(row['config_realized'])), row['mode'])
```

Ce rejeu conserve la réalisation de `s_mt` ; il ne retire pas une nouvelle valeur
du posterior. La graine moteur reste dans `seed` et dans la configuration ;
`s_mt_realized` reste également disponible séparément. Les versions de code et
de NumPy doivent être compatibles : le format ne promet pas un rejeu identique
sur toutes les révisions logicielles.

Les champs chronologiques sont fournis dans chaque ligne et dans `meta` du JSON
compagnon. Ils proviennent du contrat validé `science-observations-v1`, identifié
par `science_contract_version` :

| Champ | Définition |
| --- | --- |
| `target_generation` | Horizon demandé depuis le pulse, identique à `gens_requested` |
| `mixture_generations_ago` | 8741 générations avant le présent, convention SI1 |
| `years_per_generation` | 28,6 ans par génération, convention SI1 |
| `target_generations_ago` | `mixture_generations_ago - target_generation` |
| `target_age_ka` | `target_generations_ago * years_per_generation / 1000` |

Pour 6993 générations écoulées, l'âge calculé est 49,9928 ka, soit environ 50 ka.
Pour un autre horizon, cet âge change : le JSON définit désormais l'événement
à la génération demandée plutôt que de toujours l'étiqueter « 50 ka ». Ces
conversions reprennent les arrondis du modèle publié ; elles n'améliorent pas
la précision historique et ne recalibrent ni les observations ni les simulations.
Un horizon de test court reste une simulation de test. Le champ historique
`auto_mod_at_50ka` conserve son nom pour compatibilité et doit être interprété
avec la chronologie et le statut, comme décrit en I6.

`auto_generations_completed` donne la génération retournée par le passage qui
fournit la mesure autosomale finale : passage intégral en `full`, continuation
en `adaptive` positif. Le champ est vide en `quick` et en `adaptive` impossible.
`generations_completed` reste celui du premier passage. Après absorption au
premier passage d'une simulation de 80 générations, ces deux nombres peuvent
donc être respectivement 80 et 11. Le statut I6 précise toujours si la mesure
finale est évaluée ; la chronologie cible ne prouve pas à elle seule qu'elle l'est.

Les champs de provenance mitochondriale distinguent :

| `mt_selection_source` | Signification |
| --- | --- |
| `fixed` | Aucun fichier posterior fourni ; coefficient fixé par la configuration |
| `posterior_draw` | Tirage réalisé avec la graine `mt_posterior_draw_seed` |
| `posterior_not_applied` | Fichier fourni mais non appliqué, car le coefficient initial était nul |

`mt_posterior_sha256` identifie les octets effectivement chargés, commentaires
compris, lorsqu'un fichier est fourni, et reste vide sinon. La graine de tirage
est vide hors `posterior_draw` ; elle reste calculée comme auparavant par
`seed + 27383`. Pour un fichier multicolonne, la première colonne reste la
distribution utilisée. Les fichiers `.gz` et `.bz2` restent acceptés ; leur
empreinte porte sur les octets compressés du fichier fourni.
Ces métadonnées ne donnent pas un statut empirique à
un fichier arbitraire fourni en CLI ; les posteriors des tests I7 sont synthétiques.

`tests/test_pulse_metadata.py` vérifie configuration complète, rejeu des
indicateurs, overrides, graine et statut pour chaque mode, cohérence CSV/JSON
aux horizons par défaut et personnalisés, ainsi que la génération de continuation.
Des fixtures posteriors synthétiques à une et deux colonnes vérifient séparément
empreinte, coefficient réalisé, graine de tirage et cas non appliqué, y compris
pour les fichiers compressés gzip/bzip2.

Commandes depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_pulse_metadata.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Vérification I7 du 24 octobre 2026 : ces commandes réussissent sous Nix avec
respectivement 4, 22 et 64 tests, dont les contrôles gzip/bzip2. Les cinq DoD
de l'Issue sont vérifiés ; ces preuves couvrent M2 D8 pour les nouvelles sorties
CLI. Le milestone reste incomplet et n'est pas modifié.
