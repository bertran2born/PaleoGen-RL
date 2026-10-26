# Contrat d'entrée autosomal pondéré — I28

Ce contrat permet de déclarer et de rejouer la mesure explicite I25/I27.
Il prépare M3 O1/O4 et D1 ; aucune convergence ou adoption de métrique
principale n'est établie. Les poids de l'exemple sont synthétiques.

`paleogen_rl.genetics.weighted_protocol.WeightedAutosomalProtocol` hérite des
contraintes de population, pulse, horizon, carte et partenaires d'I19. Son
champ supplémentaire `measurement_panel` est un `WeightedBlockPanel` dont
l'identité et l'ordre des blocs doivent correspondre exactement à la carte.
Les objets sont immuables ; `to_dict()` fournit un instantané indépendant.

La déclaration JSON reprend les champs I19 avec ces différences explicites :

| Champ | Valeur ou définition |
| --- | --- |
| `protocol_version` | `weighted-autosomal-evaluation-protocol-v1` |
| `measurement.measurement_version` | `weighted-autosomal-block-measurement-v1` |
| `measurement.observable` | `total_weighted_diploid_block_ancestry` |
| `measurement.weighting` | `explicit_relative_block_weights` |
| `measurement_weights.block_weights` | Un poids relatif positif fini par bloc, dans l'ordre de la carte |
| `measurement_weights.weight_basis` | Justification explicite, chaîne non vide sans espaces périphériques |

Les champs partagés sont `protocol_id`, `population_size`, `generations`,
`pulse` (`f`, `male_fraction`), `recombination_map` (`panel`,
`switch_probabilities`), `partners` (`mt`, `y`), `measurement` et
`resolution_control`. Le panel est déclaré une seule fois dans la carte.
Les poids normalisés sont calculés par I25 ; ils ne sont pas acceptés en entrée.
La mesure conserve tous les blocs, y compris les partenaires sélectionnés.

Population >=20, horizon >=1, arrondis du pulse par sexe, carte et partenaires
restent soumis aux validations I19. La définition impose toujours dix mâles
sans remise et la cible inclusive `[0.03, 0.07]`. `resolution_control` doit être
exactement `{"status": "not_established"}`. Les modes, graines et paramètres
de sélection sont des paramètres d'exécution séparés, à conserver avec les
résultats I27 pour un rejeu complet.

`canonical_json` trie les clés sans espaces, en UTF-8 ; `sha256` identifie
cette déclaration canonique. Les poids déclarés et leur justification font
partie de l'identité. Ainsi, multiplier tous les poids par une constante
change l'empreinte de déclaration même si la mesure normalisée est identique.
L'identité ne normalise pas la formulation de la justification.

`load_weighted_autosomal_protocol(path)` retourne le contrat et le SHA-256 des
octets du fichier : une autre indentation change ce second hash, sans changer
le hash canonique. Le chargeur refuse clés inconnues, manquantes ou dupliquées,
constantes JSON non finies, poids invalides et revendications de convergence.
Les erreurs de déclaration lèvent `ValueError` ; les erreurs de lecture restent
des erreurs système. Les chargeurs I19 et I28 refusent leurs versions croisées,
y compris lorsque tous les poids I28 sont égaux.

Exemple exécutable depuis `reich_experiment_v2/`, dans `nix develop` :

```python
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from paleogen_rl.genetics.ancestry import BlockPanel
from paleogen_rl.genetics.inheritance import RecombinationMap
from paleogen_rl.genetics.pulse import evaluate_block_pulse
from paleogen_rl.genetics.selected import BlockSelection
from paleogen_rl.genetics.weighted_ancestry import WeightedBlockPanel
from paleogen_rl.genetics.weighted_protocol import (
    WeightedAutosomalProtocol, load_weighted_autosomal_protocol,
)

panel = BlockPanel('synthetic-three', ('mt', 'middle', 'y'))
protocol = WeightedAutosomalProtocol(
    protocol_id='synthetic-weighted-v1', population_size=40, generations=4,
    f=.5, male_fraction=.5, recombination_map=RecombinationMap(panel, (.1, .1)),
    mt_partner_block='mt', y_partner_block='y',
    measurement_panel=WeightedBlockPanel(panel, (2, 4, 2), 'synthetic relative lengths'))
with TemporaryDirectory() as directory:
    path = Path(directory)/'protocol.json'
    path.write_text(protocol.canonical_json, encoding='utf-8')
    loaded, source_sha256 = load_weighted_autosomal_protocol(path)
    snapshot = json.loads(loaded.canonical_json)
    path.unlink()
    restored = WeightedAutosomalProtocol.from_dict(snapshot)
assert restored.sha256 == protocol.sha256 == source_sha256

selection = BlockSelection(
    mt_partner_block=restored.mt_partner_block, y_partner_block=restored.y_partner_block,
    mt_arch_nuc_mod=.01)
for mode in ('full', 'quick', 'adaptive'):
    result = evaluate_block_pulse(
        population_size=restored.population_size, f=restored.f,
        male_fraction=restored.male_fraction, generations=restored.generations,
        recombination_map=restored.recombination_map,
        measurement_panel=restored.measurement_panel, selection=selection, seed=17, mode=mode)
    print(mode, result['target'])
```

Le contrat ne modifie pas les disponibilités I27 : quick laisse le critère
final indisponible ; adaptive sans événement possible n'évalue pas l'ascendance
finale. Un diagnostic au point d'arrêt reste intermédiaire. Ni une même
empreinte, ni une mesure identique après raffinement ne prouvent la convergence
de la dynamique. Les poids ne donnent pas automatiquement une carte de
recombinaison ou une architecture sélectionnée cohérente entre résolutions.

La CLI et les études multirésolution restent sur le contrat I19 ; elles
n'acceptent pas encore ce nouveau format. Aucun fichier historique n'est migré.

Preuves du 26 octobre 2026 : sous Nix, les suites
`test_autosomal_weighted_protocol.py`, `test_autosomal_protocol.py`,
`test_autosomal*.py` et la suite complète réussissent avec respectivement
**8, 7, 125 et 202 tests**, sans échec ni test ignoré. Les huit tests ciblés
couvrent instantanés, immutabilité, identités canonique/fichier, sensibilité à
tous les paramètres, erreurs de déclaration/construction, JSON strict, refus
croisés I19/I28 et rejeu exact sans source sur **153 configurations**
(17 scénarios × graines 0/17/42 × trois modes). Les scénarios comprennent les
sélections uniparentales et les quatre coûts réciproques existants.

L'exemple ci-dessus a été exécuté : full donne `target_auto=False` et un
critère conjoint nul ; quick laisse les deux champs indisponibles ; adaptive
laisse `target_auto` indisponible et donne un critère conjoint nul. Ces sorties
sont celles d'une fixture synthétique, sans interprétation historique.
Environnement observé : Linux x86_64, Python 3.14.8, NumPy 2.5.3 ; SHA-256 de
`reich_experiment_v2/flake.lock` :
`a52bdf3a3b9a069175d3af298234c3cf7adeba54540833eed6ad902e9ccc0a64`.
