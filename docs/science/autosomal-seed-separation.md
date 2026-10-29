# Séparation déclarée des graines autosomales — I36

M3 demande une confirmation indépendante du dimensionnement et de la sélection.
I36 ajoute un contrôle préalable des graines pour les études pondérées I31.
Ce contrôle vérifie la disjonction avec un historique **déclaré** ; il ne suffit
pas à établir l'indépendance des données ou l'acceptation scientifique de M3.

## Historique versionné

`autosomal_seed_history.validate_seed_history` exige exactement :

| Champ | Contenu |
| --- | --- |
| `history_version` | `autosomal-seed-history-v1` |
| `history_id` | Chaîne non vide sans espaces périphériques |
| `sources` | Liste non vide des sources à exclure |

Chaque source contient exactement `source_id` (unique dans l'historique),
`purpose`, `source_sha256` et `seeds`. `purpose` vaut `sizing`, `selection`,
`exploration` ou `engineering`. L'empreinte est un SHA-256 minuscule à 64 caractères
identifiant le document de référence ; les graines sont des entiers distincts,
non négatifs, dans une liste non vide. Les booléens et nombres flottants sont
refusés. Une graine peut apparaître dans plusieurs sources historiques : tous
les conflits doivent rester visibles. La séparation s'applique globalement,
même si l'ancien usage concernait un autre scénario ou une autre résolution.

Le chargeur JSON refuse champs dupliqués, inconnus ou manquants et constantes
non finies. Il retourne un instantané normalisé indépendant et l'empreinte des
octets du fichier. L'audit conserve aussi l'empreinte du contenu canonique,
indépendante de l'indentation. L'ordre déclaré des sources et graines est conservé
et participe à cette identité ; les intersections sont triées numériquement.

## API et contrôle avant simulation

`audit_seed_separation(seeds, history)` retourne un audit
`autosomal-seed-separation-v1`, l'historique complet, les graines candidates,
leurs empreintes, le nombre de graines historiques distinctes et chaque source
de collision. Il n'utilise aucun RNG ni moteur et ne lit aucun fichier source.
Son statut est `overlap_detected` ou `disjoint_from_declared_history`.

Les API `preview_weighted_resolution_plan` et `run_weighted_resolution_plan`
acceptent l'argument nommé optionnel `seed_history`. Lorsqu'il est fourni,
l'audit précède les simulations ; une collision ou un historique invalide
produit une `ValueError`. Un succès ajoute `seed_audit`, lié au `plan_sha256`
normalisé exact, au rapport et à l'aperçu conservé dans une étude full.
L'historique reste rejouable depuis l'instantané sans fichier d'entrée.

Sans cet argument, les sorties ne comportent aucun champ d'audit ajouté et
conservent leur sémantique exploratoire. Les statistiques, paramètres, graines,
poids et dynamiques sont inchangés. Les études enregistrent également
l'empreinte du nouveau module de contrôle parmi leurs sources d'implémentation.

Exemple **synthétique** minimal, depuis `reich_experiment_v2/` dans `nix develop` :

```python
import hashlib
from autosomal_seed_history import HISTORY_VERSION, audit_seed_separation

history = dict(history_version=HISTORY_VERSION, history_id='synthetic-example', sources=[
    dict(source_id='synthetic-sizing', purpose='sizing',
         source_sha256=hashlib.sha256(b'synthetic-sizing-document').hexdigest(), seeds=[11, 12]),
    dict(source_id='synthetic-selection', purpose='selection',
         source_sha256=hashlib.sha256(b'synthetic-selection-document').hexdigest(), seeds=[12, 13]),
])
collision = audit_seed_separation([12, 20], history)
assert collision['status'] == 'overlap_detected'
assert [row['seeds'] for row in collision['collisions']] == [[12], [12]]
separated = audit_seed_separation([20, 21], history)
assert separated['status'] == 'disjoint_from_declared_history'
assert separated['excluded_seed_count'] == 3
assert separated['statistical_independence_established'] is False
```

## CLI

Avec un plan I31 et un historique explicites, depuis `reich_experiment_v2/` :

```sh
nix develop -c python study_weighted_autosomal_resolution.py \
  --plan /tmp/weighted-plan.json --seed-history /tmp/seed-history.json \
  --preview --output /tmp/weighted-preview.json
nix develop -c python study_weighted_autosomal_resolution.py \
  --plan /tmp/weighted-plan.json --seed-history /tmp/seed-history.json \
  --output /tmp/weighted-study.json
```

La CLI archive `history_file_sha256` en plus des empreintes canoniques ; l'API
sans fichier laisse ce champ à `None`. Une collision, un fichier historique
illisible ou invalide retourne 1 sans appel moteur et sans publier de rapport.
Les destinations existantes et liens symboliques restent refusés, sans écrasement.

## Limites scientifiques

L'utilisateur doit déclarer toutes les données qui ont influencé dimensionnement,
architecture, paramètres ou choix de méthode, ainsi que les benchmarks observés.
Le contrôle ne découvre pas automatiquement les archives, n'authentifie pas les
empreintes documentaires et ne garantit ni exhaustivité ni antériorité.
Il ne détecte pas des trajectoires identiques obtenues par un autre procédé.
Des graines distinctes ne démontrent pas à elles seules l'indépendance statistique
des flux RNG ou l'absence d'autres formes de sélection des données.

Un historique tronqué ou faux peut donc laisser passer des données réutilisées.
Le statut reste limité aux sources déclarées ; `confirmation_status` reste
`not_established` et `statistical_independence_established` reste faux. Le statut
scientifique exploratoire des études et `convergence_status=not_established`
ne changent pas. Ce mécanisme ne gèle ni marges, ni budget, ni règle d'adoption,
et ne clôture pas M3. Les échecs et sorties non concluantes restent soumis aux
exigences de conservation de M3 ; cette Issue ne change pas la gestion des
échecs reproductifs d'I31.
