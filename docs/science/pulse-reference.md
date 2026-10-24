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
