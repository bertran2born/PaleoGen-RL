# Exécution CLI des protocoles pondérés — I29

`run_experiment.py --weighted-autosomal-protocol <contrat.json>` exécute un
[contrat I28](autosomal-weighted-protocol.md) dans les modes full, quick ou
adaptive. Cette option conserve les poids déclarés et leur justification.
Elle est exclusive avec `--autosomal-protocol`, `--block-map` et les options
de partenaires ; N, horizon et pulse viennent du contrat. Des valeurs explicites
identiques sont acceptées, les valeurs contradictoires sont refusées avant
simulation. Un fichier de sortie `.csv` explicite et inexistant est obligatoire ;
le fichier JSON associé doit aussi être absent.

Depuis `reich_experiment_v2/`, pour un contrat I28 déjà enregistré :

```sh
nix develop -c python run_experiment.py \
  --weighted-autosomal-protocol /tmp/weighted-protocol.json \
  --scenario reich_plus_symmetric_1pct --mode adaptive \
  --reps 3 --seed 17 --output /tmp/weighted-adaptive.csv
```

Les scénarios, graines appariées entre scénarios, posterior mitochondrial et
substitutions des quatre coûts conservent leurs règles actuelles. La provenance
du posterior, sa graine de tirage et les paramètres réalisés restent exportés.
Les poids ne modifient ni la reproduction, ni l'échantillonnage des dix mâles,
ni les bornes inclusives 3–7 %.

Les sorties pondérées annoncent `result_schema_version` =
`weighted-block-pulse-result-v1`. Les colonnes de contrat existantes sont
réutilisées avec une version explicite : `autosomal_protocol_version` =
`weighted-autosomal-evaluation-protocol-v1`, `autosomal_protocol_id`,
`autosomal_protocol` (JSON canonique), `autosomal_protocol_sha256` et
`autosomal_protocol_file_sha256`. Les mêmes informations se trouvent dans
`meta` du JSON, avec le chemin source. Le premier hash identifie le contenu
canonique, le second les octets originaux. Le contrat contient carte, partenaires,
poids relatifs et justification ; le rapport contient aussi les poids normalisés.
`resolution_control_status` reste `not_established`.

`config_realized`, mode, graine et contrat conservés dans chaque ligne permettent
le rejeu sans fichier source. `block_report` est le rapport I27 complet :
mesures initiale/finale, sélection, disponibilité, diagnostics et coûts logiques.
Les résumés JSON donnent les moyennes et coûts agrégés avec les règles existantes.
Les notes scientifiques déclarent des poids explicites et leur absence de
calibration dans cette exécution.

En full, `auto_mod_at_50ka` contient la mesure à l'horizon demandé par le
contrat ; la chronologie exportée précise cet horizon, qui n'est 50 ka que pour
les paramètres temporels correspondants. En quick, cette colonne,
`target_auto` et `joint_and_target` sont vides. `auto_mod` et
`auto_mod_at_early_stop` sont alors des diagnostics intermédiaires pondérés.
En adaptive, l'ascendance finale reste vide si P10=0 et le critère conjoint vaut
zéro ; sinon la même graine est rejouée jusqu'à l'horizon avec les mêmes poids.
Les résumés adaptive ne prétendent pas estimer la probabilité autosomale
marginale sur toutes les trajectoires.

Exemple autonome, à exécuter dans `nix develop` depuis `reich_experiment_v2/` :

```python
import csv
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel
from paleogen_rl.genetics.weighted_protocol import WeightedAutosomalProtocol

panel = BlockPanel('synthetic-three', ('mt', 'middle', 'y'))
protocol = WeightedAutosomalProtocol(
    protocol_id='synthetic-cli-v1', population_size=40, generations=4,
    f=.5, male_fraction=.5, recombination_map=RecombinationMap(panel, (.1, .1)),
    mt_partner_block='mt', y_partner_block='y',
    measurement_panel=WeightedBlockPanel(panel, (2, 4, 2), 'synthetic relative lengths'))
with TemporaryDirectory() as directory:
    source = Path(directory)/'protocol.json'
    source.write_text(protocol.canonical_json, encoding='utf-8')
    for mode in ('full', 'quick', 'adaptive'):
        output = Path(directory)/f'{mode}.csv'
        subprocess.run([
            sys.executable, 'run_experiment.py', '--weighted-autosomal-protocol', str(source),
            '--scenario', 'neutral', '--mode', mode, '--reps', '2', '--seed', '17',
            '--output', str(output)], check=True, capture_output=True, text=True)
        with output.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        print(mode, len(rows), rows[0]['result_schema_version'], rows[0]['auto_evaluation_status'])
```

Cet exemple est synthétique et ne justifie aucun choix de poids biologiques.
Les contrats I19 et les sorties historiques gardent leurs formats ; aucun
protocole principal n'est adopté. Le raffinement des cartes, des poids et des
partenaires entre résolutions et la démonstration de convergence M3 restent
ouverts. Une erreur reproductive interrompt l'exécution sans publier de fichiers
CSV/JSON de succès.

Validation finale du 26 octobre 2026 : **6 tests CLI**, **7 tests I19**,
**131 tests autosomaux** et **208 tests complets** réussissent sous Nix,
sans échec ni test ignoré. Les tests CLI couvrent
17 scénarios × graines 17/18/19 × trois modes, soit 153 résultats comparés
à l'API I27 et rejoués sans leur fichier source. Ils contrôlent aussi posterior,
substitutions, coûts, refus pré-moteur, disponibilités full/quick/adaptive,
résumés à un réplicat et erreurs reproductives réelles sans fichier de succès.
L'exemple autonome ci-dessus a produit deux lignes par mode, version
`weighted-block-pulse-result-v1`, avec les statuts `evaluated_at_target`,
`not_evaluated_quick` et `not_evaluated_event_impossible` respectivement.

La validation globale était initialement bloquée par trois échecs
(deux contrôles de provenance et un de sources), dus à 31 ressources locales
inventoriées absentes. Ce blocage est résolu : les 14 fichiers de
`reich_study/` étaient présents et conformes à la reprise ; les 17 fichiers
absents de `source/` ont été restaurés depuis les copies locales conformes
sous `/home/mathieu/reich_experiment/`, sans remplacer de fichier existant.
Les **32 ressources** correspondent maintenant au registre ;
`verify_provenance.py` et `verify_sources.py` retournent tous deux 0 sous Nix.
Le moteur tiers requis pour les tests CLI a été restauré localement, sans
suivi Git, depuis la copie disponible sous `/home/mathieu/reich_experiment/` ;
ses octets correspondent au SHA-256 enregistré
`95f854cb0a8eeef33810168a487d5b998a90f4f69f9d873508a1f67407deb641`.
Aucun contenu tiers existant ou registre n'a été modifié. Les ressources
restaurées restent ignorées et ne sont pas incluses dans le commit I29.

Environnement observé : Linux x86_64, Python 3.14.8, NumPy 2.5.3 ; SHA-256 de
`reich_experiment_v2/flake.lock` inchangé :
`a52bdf3a3b9a069175d3af298234c3cf7adeba54540833eed6ad902e9ccc0a64`.
