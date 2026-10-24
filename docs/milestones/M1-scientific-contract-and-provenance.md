# M1 — Référentiel scientifique et provenance traçable

Status: READY
Depends on: none

## Outcome

PaleoGen-RL possède un contrat scientifique versionné décrivant les observations à expliquer, les hypothèses admissibles et l'origine de chaque ressource utilisée. Une évaluation peut distinguer données empiriques, paramètres publiés, hypothèses exploratoires et sorties simulées. Aucun résultat exploratoire du prototype ne peut être présenté comme une validation du modèle historique.

## Objectives

- O1 — Les observations et statistiques cibles possèdent des définitions reproductibles, des unités, des sources et des intervalles d'incertitude explicites.
- O2 — Chaque élément provenant du préprint de Reich, de ses suppléments ou de nos extensions est identifiable par sa version et son empreinte.
- O3 — Les droits de réutilisation et les limitations de chaque ressource sont enregistrés avant toute distribution.
- O4 — Le statut scientifique des hypothèses et résultats est visible dans les sorties.

## Scope

### In scope

- Observations uniparentales, plage d'ascendance autosomale 3–7 %, chronologie et démographie du préprint.
- Registre de provenance des PDF, archives SI1–SI4, table supplémentaire et distributions utilisées.
- Distinction des résultats publiés, reproduits, approximés et exploratoires.
- Conditions de réutilisation des données et du code.

### Out of scope

- Correction des simulateurs, recherche de nouveaux mécanismes, entraînement d'agents.
- Ajout d'observations historiques non vérifiées et publication sur le Hub.

## Requirements and Invariants

- R1 — Chaque cible indique sa source, sa définition opérationnelle, son unité, son mode d'échantillonnage et sa version.
- R2 — Le contrat distingue fixation dans la population et événement « dix mâles échantillonnés portant les deux marqueurs modernes » ; ils ne sont pas synonymes.
- R3 — La définition de la proportion autosomale précise la date de mesure, le dénominateur, les loci considérés et la sélection éventuelle.
- R4 — Les paramètres reproductifs, temporels et démographiques cités par Reich sont associés aux sections sources correspondantes.
- R5 — Toute ressource externe a une empreinte SHA-256 et une politique de redistribution : autorisée, non autorisée ou non établie.
- I1 — Une ressource à licence non établie n'est pas automatiquement intégrée au paquet public.
- I2 — Une valeur exploratoire ne devient pas « biologiquement plausible » du seul fait qu'elle optimise le score.
- I3 — Les résultats de référence ne sont jamais écrasés lors d'une nouvelle exécution.

## Relevant Repository Surfaces

- `README.md` — limites scientifiques et provenance du prototype existant.
- `manifest.json` — inventaire et empreintes actuels.
- `source/mechanisms_code/mt_gap_posterior_pooled_rna.txt` — distribution issue de SI1.
- `docs/science/observations.md` (proposed) — contrat scientifique versionné.
- `docs/science/provenance.json` (proposed) — registre machine-readable.

## Definition of Done

- [x] D1 [O1] Le contrat définit séparément fixation mtDNA, fixation Y, événement des dix mâles et ascendance autosomale à 50 ka.
- [x] D2 [O1] Chaque observation possède une citation précise du document source et un statut « observation » ou « hypothèse ».
- [x] D3 [O1] Un test refuse une statistique autosomale dont la génération ou la base de loci n'est pas indiquée.
- [x] D4 [O2] Un inventaire permet de recalculer et de comparer les SHA-256 des ressources locales.
- [x] D5 [O2] Les versions SI1–SI4 et du préprint sont consignées, sans assimilation à une publication évaluée par les pairs.
- [x] D6 [O3] Une politique de redistribution explicite est présente pour chaque archive de code originale.
- [x] D7 [O3] L'export public exclut les ressources marquées « non établie » ou « non autorisée ».
- [ ] D8 [O4] Un rapport distingue « reproduction exacte », « reproduction approximative » et « résultat exploratoire ».
- [ ] D9 [O1, O2, O3, O4] Les contrôles automatisés du contrat scientifique passent sans accès réseau.

## Final Validation

```sh
python -m unittest discover -s tests -p 'test_science_contract.py'
python -m unittest discover -s tests
```

Les commandes s'exécutent depuis `reich_experiment_v2/`.
`tests/test_science_contract.py` est présent depuis I3.

Preuves partielles (I1, 24 octobre 2026) : `docs/science/provenance.json`
inventorie 32 ressources locales avec SHA-256 et politique individuelle
`not_established` motivée, dont toutes les archives présentes. Depuis
`reich_experiment_v2/`, `nix develop -c python verify_provenance.py` retourne 0
(32 ressources `ok`), les 8 tests de `test_provenance.py` et les 22 tests complets
réussissent. Voir `docs/issues/I1-verify-local-resource-provenance.md`.
Ces preuves satisfont D4/D6 ; elles ne valident ni D5 ni D7 ni l'ensemble D9.

Preuves complémentaires (I2, 24 octobre 2026) : `docs/science/sources.json`
identifie les cinq PDF après revue de leur première page et les ancre aux
empreintes I1. Le préprint est identifié v2, daté du 13 octobre 2026 ; SI1–SI4
possèdent une version de contenu par SHA-256, sans date ou révision autonome
établie. Tous portent le statut documentaire `preprint_not_peer_reviewed`.
Depuis `reich_experiment_v2/`, `nix develop -c python verify_sources.py`
retourne 0 (5 sources conformes), le contrôle I1 retourne 0 (32 ressources),
les 8 tests de `test_sources.py` et les 30 tests complets réussissent.
Voir `docs/issues/I2-identify-versioned-scientific-sources.md`. D5 est satisfait
pour les versions locales fournies ; M1 reste incomplet.

Preuves complémentaires (I3, 24 octobre 2026) :
`docs/science/observations.md` et `docs/science/observations.json` définissent
les quatre statistiques, les observations rapportées et les hypothèses de mesure,
avec citations paginées reliées aux versions I2. Le validateur autonome
`reich_experiment_v2/science_contract.py` refuse les mesures autosomales sans
génération/base de loci ou à horizon incorrect. Sous Nix, les 10 tests de
`test_science_contract.py` et les 40 tests complets passent ; ces derniers
incluent I1/I2 et les tests de parité existants. Voir
`docs/issues/I3-define-scientific-observation-contract.md`. D1/D2/D3 sont
satisfaits. D7/D8 et D9 dans son ensemble restent ouverts ; aucune migration des
sorties historiques ni modification de moteur n'a été effectuée.

Preuves complémentaires (I4, 24 octobre 2026) :
`reich_experiment_v2/export_public.py` construit un ZIP documentaire sélectionnant
explicitement les cinq documents scientifiques et les seules ressources
`authorized` à empreinte vérifiée. Le manifeste motive les exclusions ; les
ressources non inventoriées sont également exclues. Un export réel a été créé et
inspecté : cinq documents, un manifeste, aucun contenu des 32 ressources
`not_established`. Les fixtures démontrent aussi l'exclusion de `not_authorized`,
le refus des liens et destinations existantes, et la reproductibilité des octets.
Sous Nix, les 12 tests de `test_public_export.py` et les 52 tests complets passent.
Voir `docs/issues/I4-filter-public-resource-export.md` et la procédure dans
`docs/science/provenance.md`. D7 est satisfait pour cet export documentaire local ;
la distribution exécutable M10/M11 n'est pas réalisée. D8 et D9 restent ouverts.

## References

- `README.md`.
- `manifest.json`.
- Préprint Reich v2 (13 octobre 2026), SI1, SI2, SI3 et Supplementary Table 1 fournis avec l'expérience.
