# I19 — Lier les évaluations à un protocole autosomal versionné

Milestone: M3
Advances: D1, D9, D10 ; exigences R1/R3/R4 et invariant I3
Depends on: I16–I18 ; résolution principale non validée, M1 D8/D9 ouverts

## Objective

Permettre aux évaluations comparables de réutiliser un contrat autosomal explicite, identifié par son contenu et exporté avec chaque résultat. Verrouiller les paramètres de mesure sans choisir une résolution principale que le diagnostic I18 ne justifie pas.

## Repository Grounding

- `reich_experiment_v2/run_experiment.py` accepte une carte et deux partenaires séparés ; N, horizon et pulse restent des options indépendantes. Les sorties n'ont pas d'identité commune de protocole autosomal.
- `paleogen_rl/genetics/pulse.py` distingue déjà résultats intégrals v1 et anticipés v2, avec disponibilité explicite.
- I18 conserve des cartes et résultats multirésolution, mais ne démontre ni convergence ni calibration au régime N=1 450 / 6 993 générations.
- La mesure I11 inclut les partenaires dans le total ; sa version et le critère dix mâles / 3–7 % existent et restent inchangés.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/ancestry.py`, `inheritance.py`, `pulse.py` — mesure, carte et formats.
- `reich_experiment_v2/tests/test_autosomal_pulse.py` et `test_autosomal_block_modes.py` — rejeu et compatibilité CLI.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/protocol.py` (new) — validation, instantané et identité canonique.
- `reich_experiment_v2/run_experiment.py` — entrée protocole et traçabilité des évaluations.
- `reich_experiment_v2/tests/test_autosomal_protocol.py` (new) — validation et intégration des trois modes.
- `docs/science/autosomal-evaluation-protocol.md` (new) — contrat et limites.
- `docs/science/autosomal-protocol-synthetic.json` (new) — exemple synthétique exécutable, sans statut de référence validée.

## Required Changes

1. Définir un protocole versionné explicite : identité lisible, N, horizon, pulse, panel/carte, partenaires, mesure totale I11, échantillonnage dix mâles et cible inclusive 3–7 %. Refuser champs inconnus/manquants, doublons JSON et valeurs incohérentes, y compris quotas impossibles.
2. Calculer un SHA-256 canonique du contenu normalisé, indépendant de l'ordre des clés et du formatage JSON ; conserver aussi l'empreinte des octets du fichier. L'instantané doit suffire à reconstruire le protocole sans le chemin original.
3. Ajouter une entrée CLI protocole pour tous les scénarios/modes. Elle fournit les paramètres verrouillés ; refuser une valeur explicite contradictoire et les options concurrentes de carte/partenaires avant toute simulation. Les coefficients génétiques, graines, posterior et disponibilités gardent leur sémantique existante.
4. Exporter protocole, version, identité et statut de contrôle de résolution dans chaque ligne et le JSON récapitulatif, avec schéma distinct. La convergence reste `not_established` : un champ utilisateur ne peut pas la promouvoir en validation. Ne pas modifier les sorties sans protocole ni les archives I18.
5. Vérifier identité, refus des conflits, rejeu depuis instantané, tous les scénarios et modes, continuité numérique avec la carte explicite et tests de non-régression. Documenter que l'identité commune ne prouve ni convergence, ni validité d'une mesure indisponible, ni équivalence scientifique complète.

## Constraints and Non-goals

- Aucun moteur, observation, cible, récompense, graine historique ou ressource tierce modifié.
- Aucun choix automatique de carte/résolution ni promotion du protocole synthétique en référence v0.1 ; étude longue et clôture M3 hors périmètre.

## Definition of Done

- [x] ID1 Le protocole validé fixe carte, mesure, partenaires et paramètres ; déclarations invalides et convergence falsifiée sont refusées.
- [x] ID2 Identité canonique stable, sensible aux changements du contrat, et rejeu sans fichier original vérifiés.
- [x] ID3 Tous les scénarios/modes partagent le protocole fourni ; résultats numériques identiques au chemin carte explicite.
- [x] ID4 Conflits CLI refusés avant simulation ; instantané, empreintes et statut apparaissent dans CSV/JSON sous schéma distinct.
- [x] ID5 Tests ciblés, autosomaux, pulse et complets passent sous Nix ; exemple et limites documentés.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_protocol.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests -p 'test_pulse*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : les quatre commandes retournent 0 avec **7, 78,
35 et 155 tests**. Validation stricte, immuabilité et statuts refusés couvrent
ID1 ; variantes de format, modifications des paramètres et rejeu après suppression
du fichier temporaire couvrent ID2. Tous les scénarios sont comparés à la carte
explicite et rejoués dans les trois modes (ID3). Métadonnées, conflits avant
simulation, posterior et overrides vérifient ID4. Les suites précédentes restent
inchangées et passent, l'exemple synthétique est exécuté par les tests (ID5).
Contrôles de whitespace sans diagnostic. Aucun moteur, observation, archive
I18 ou milestone modifié. Aucun commit ni push.
