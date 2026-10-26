# I28 — Déclarer un protocole autosomal pondéré et identifiable

Milestone: M3
Advances: D1 ; objectifs O1/O4, exigences R1/R2/R3/R4
Depends on: I19, I25, I27 ; convergence et protocole principal non établis

## Objective

Fournir un contrat JSON pondéré, explicite, immuable et identifiable par son
contenu, utilisable avec l'API pulse existante. Cette entrée précède son
exposition CLI et permet de conserver poids, justification, carte et partenaires
dans une déclaration rejouable.

## Repository Grounding

- `paleogen_rl/genetics/protocol.py` valide le protocole I19 à poids égaux,
  verrouille démographie, horizon, carte, partenaires et définition de mesure,
  puis distingue empreintes canonique et du fichier source.
- `weighted_ancestry.py::WeightedBlockPanel` valide des poids relatifs positifs
  et leur justification ; ses poids normalisés sont dérivés.
- `pulse.py::evaluate_block_pulse` accepte ce panel en full, quick et adaptive
  depuis I27. La CLI et les plans multirésolution utilisent encore I19.
- M3 D1 reste ouvert : ce contrat ne fournit aucune preuve de convergence.

## Change Scope

### Inspect

- `reich_experiment_v2/paleogen_rl/genetics/protocol.py` — validations et identité I19.
- `reich_experiment_v2/paleogen_rl/genetics/weighted_ancestry.py` et `pulse.py` — déclarations et API pondérées.
- `reich_experiment_v2/tests/test_autosomal_protocol.py` — compatibilité et rejeu existants.

### Expected change paths

- `reich_experiment_v2/paleogen_rl/genetics/weighted_protocol.py` (new) — contrat, sérialisation et chargement.
- `reich_experiment_v2/tests/test_autosomal_weighted_protocol.py` (new) — validation, identité, rejeu et compatibilité.
- `docs/science/autosomal-weighted-protocol.md` (new) — format, exemple et limites.

## Required Changes

1. Définir une version pondérée distincte réutilisant les validations I19 pour
   population, pulse, horizon, carte et partenaires. Exiger un panel pondéré
   identique à celui de la carte ; conserver tous les blocs dans la mesure.
2. Sérialiser les poids déclarés dans l'ordre des blocs et leur justification,
   sans seconde déclaration indépendante du panel ni poids normalisés imposés
   par l'utilisateur. Verrouiller mesure pondérée, dix mâles sans remise et
   cible inclusive 3–7 %. Garder `resolution_control` à `not_established`.
3. Fournir chargement JSON strict, instantanés indépendants, empreinte canonique
   et empreinte des octets du fichier. Rejeter versions croisées, clés manquantes,
   inconnues ou dupliquées, poids invalides et fausses affirmations de convergence.
   Les changements de paramètres, poids ou justification changent l'identité.
4. Vérifier le rejeu depuis un instantané JSON sans fichier source dans les trois
   modes avec sélection active et plusieurs graines. Comparer aux appels I27
   directs ; préserver contrats, sorties et archives I19.

## Constraints and Non-goals

- Ne modifier ni CLI, plans d'étude, dynamique, graines, cible ou archives.
- Aucun poids empirique ou protocole principal adopté ; un identifiant de contenu
  n'est ni une calibration ni une preuve de convergence.
- Le mode, la graine et la sélection restent des paramètres d'exécution distincts.

## Definition of Done

- [x] ID1 Le contrat pondéré versionné valide et conserve tous ses paramètres ; les entrées incohérentes sont refusées.
- [x] ID2 Instantanés immuables, sérialisation stricte et deux empreintes sont vérifiés ; changements scientifiques et de justification modifient l'identité.
- [x] ID3 Le rejeu sans source concorde exactement avec I27 dans les trois modes ; I19 reste inchangé et incompatible explicitement avec ce format.
- [x] ID4 Tests ciblés, I19, autosomaux et complets passent sous Nix ; format, exemple exécuté et limites sont documentés.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_weighted_protocol.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_protocol.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (26 octobre 2026) : les quatre commandes réussissent, respectivement
**8/7/125/202 tests**, sans échec ni test ignoré. Les tests de déclaration et de
construction vérifient ID1 ; instantanés, mutations, empreintes et chargeur
strict vérifient ID2. Le rejeu après suppression du fichier couvre
17 scénarios × 3 graines × 3 modes = **153 configurations** ; refus croisés et
suite I19 vérifient ID3. L'[exemple documenté](../science/autosomal-weighted-protocol.md)
a été exécuté sous Nix, et les quatre suites valident ID4. Structure, taille,
syntaxe et espaces vérifiés. Aucun fichier collatéral, archive ou chemin
scientifique existant modifié ; M3 D1 reste ouvert et le milestone inchangé.
