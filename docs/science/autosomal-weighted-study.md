# Études de résolution pondérée — I31

`study_weighted_autosomal_resolution.py` exécute en **full** une famille
conservatrice I30 pour des scénarios et graines explicitement déclarés.
Il conserve les partenaires comme cellules finies intactes et compare le
raffinement des cellules neutres. Les études historiques I18/I21 restent
inchangées. Aucun poids, carte ou protocole principal biologique n'est adopté.

## Plan et identité

Le plan impose exactement ces champs :

| Champ | Contenu |
| --- | --- |
| `plan_version` | `weighted-autosomal-resolution-plan-v1` |
| `plan_id` | Identifiant non vide sans espaces périphériques |
| `family` | `base_protocol` I28, `family_id`, `map_length`, `refinement_factors` I30 |
| `seeds` | Liste non vide d'entiers distincts non négatifs |
| `scenarios` | Liste non vide de noms existants distincts dans `SCENARIOS` |

Les contraintes I28/I30 sont vérifiées avant toute simulation. Les champs
manquants, inconnus ou dupliqués et constantes JSON non finies sont refusés.
`validate_weighted_resolution_plan` retourne un instantané indépendant normalisé.
`load_weighted_resolution_plan` retourne cet instantané et l'empreinte SHA-256
des octets du fichier. `plan_sha256` identifie le JSON canonique de l'instantané,
indépendamment de l'indentation ; `plan_file_sha256` identifie le fichier source.
L'API sans fichier laisse ce dernier champ à `None`.

## Aperçu et exécution

Depuis `reich_experiment_v2/`, avec un plan enregistré :

```sh
nix develop -c python study_weighted_autosomal_resolution.py \
  --plan /tmp/weighted-plan.json --preview --output /tmp/weighted-preview.json
nix develop -c python study_weighted_autosomal_resolution.py \
  --plan /tmp/weighted-plan.json --output /tmp/weighted-study.json
```

Les destinations doivent être absentes et leur dossier parent déjà présent.
La CLI refuse aussi les liens symboliques, même pendants, comme destinations.
Une erreur reproductive donne un code de retour 1 avec scénario, nombre de
blocs et graine ; aucun fichier de rapport n'est alors publié.

`preview_weighted_resolution_plan` n'utilise ni moteur ni RNG. La version
`weighted-autosomal-resolution-preview-v1` annonce `planning_only` et
`simulation_performed=false`, la famille complète et les coûts par résolution :
nombre d'évaluations, descendants et candidats acceptés à achèvement,
minima de candidats/transmissions et nombre d'entrées alléliques d'un état.
Les totaux additionnent le travail et prennent le maximum des tailles d'état.
Les rejets peuvent augmenter le travail réel ; un échec peut interrompre une
simulation avant ces nombres conditionnels à son achèvement. Il ne s'agit
pas de bornes de temps matériel ni de pic mémoire.

`run_weighted_resolution_plan` évalue les mêmes graines dans chaque scénario
et résolution, via l'adaptateur I29 et la mesure I27. Le rapport versionné
`weighted-autosomal-resolution-study-v1` conserve plan et famille complets,
identifiants/empreintes I28, versions Python/NumPy, RNG et SHA-256 des fichiers
d'implémentation et de `flake.lock`. Les paramètres réalisés et le rapport I27
complet sont conservés par réplicat : mesure pondérée, diagnostics, génération,
sélection, état initial identifié, P10 exact, cible et coûts. Le plan, la famille
et ces paramètres suffisent au rejeu sans le fichier d'entrée ; la reproduction
exige aussi les versions d'implémentation et d'environnement enregistrées.

Les quatre métriques sont ascendance pondérée, probabilité de cible 3–7 %,
moyenne de P10 et critère conjoint. Les mêmes agrégateurs que dans les études
existantes fournissent intervalles Hoeffding/Wilson **ponctuels**, à 95 %.
Les écarts avec la résolution la plus fine sont appariés par graine et conservent
leurs intervalles bornés. L'appariement ne signifie pas que les flux RNG ou
trajectoires sont identiques entre résolutions. Les coûts réels incluent tous
les candidats rejetés ; l'aperçu est conservé pour comparaison.

## Exemple synthétique exécutable

Dans `nix develop`, depuis `reich_experiment_v2/` :

```python
import json
from math import expm1
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel
from paleogen_rl.genetics.weighted_protocol import WeightedAutosomalProtocol
from study_weighted_autosomal_resolution import PLAN_VERSION

panel = BlockPanel('synthetic-four', ('a', 'b', 'c', 'd'))
positions = (1/16, 5/16, 11/16, 15/16)
length = .25
switches = tuple(-expm1(-2*(length*(b-a)))/2 for a, b in zip(positions, positions[1:]))
base = WeightedAutosomalProtocol(
    'synthetic-study-base', 40, 3, .05, .5, RecombinationMap(panel, switches),
    'a', 'd', WeightedBlockPanel(panel, (1, 3, 3, 1), 'synthetic relative lengths'))
plan = dict(plan_version=PLAN_VERSION, plan_id='synthetic-study',
            family=dict(base_protocol=base.to_dict(), family_id='synthetic-family',
                        map_length=length, refinement_factors=[1, 3, 9]),
            seeds=[17, 18, 19], scenarios=['neutral', 'reich_plus_symmetric_1pct'])
with TemporaryDirectory() as directory:
    source = Path(directory)/'plan.json'
    source.write_text(json.dumps(plan), encoding='utf-8')
    for preview in (True, False):
        output = Path(directory)/f'{preview}.json'
        subprocess.run([sys.executable, 'study_weighted_autosomal_resolution.py',
                        '--plan', str(source), '--output', str(output),
                        *(['--preview'] if preview else [])], check=True)
        report = json.loads(output.read_text())
        print(report['convergence_status'],
              report['total_workload']['evaluations'] if preview else
              report['total_work_units']['offspring_generated'])
```

L'exemple utilise N=40 et trois générations, sans prétention historique.
Le régime N=1450/G=6993 est déclarable et son coût peut être prévu sans
simulation ; aucune longue étude à ce régime n'est exécutée par I31.

Le statut de convergence reste **`not_established`**. Les intervalles ne sont
ni simultanés sur toutes les comparaisons, ni une validation d'équivalence,
ni une incertitude historique. Les graines doivent représenter des réplicats
indépendants pour les bornes annoncées. Choisir les marges scientifiques et
la précision confirmatoire avant une étude dédiée reste nécessaire. La
résolution la plus fine sert de référence interne ; elle n'est pas adoptée
comme protocole principal M3. Le raffinement interne des partenaires reste
hors du périmètre de la famille I30.

Validation du 26 octobre 2026 : **6 tests ciblés, 145 tests autosomaux et
222 tests complets** passent sous Nix, sans échec ni test ignoré. Les tests
comparent 153 réplicats (17 scénarios × 3 résolutions × graines 17/18/19)
à l'API I27, recalculent mesures, métriques, écarts appariés et intervalles
bornés, vérifient provenance et rejeu du plan sans son fichier source.
Ils contrôlent aussi les coûts prévus/réels, absence de moteur/RNG pendant
l'aperçu, JSON strict, sorties préservées et échec reproductif injecté sans
rapport. Ce dernier est un test contrôlé de propagation d'erreur, distinct des
échecs reproductifs réels déjà vérifiés en I29. L'aperçu N=1450/G=6993 est
testé sans exécution de cette longue étude.

L'exemple ci-dessus a produit `not_established 18` pour l'aperçu et
`not_established 2160` pour l'étude. Il démontre le fonctionnement du runner,
sans conclusion de convergence. Environnement observé : Linux x86_64,
Python 3.14.8 et NumPy 2.5.3.
