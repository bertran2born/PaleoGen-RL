# I4 — Filtrer les ressources de l'export public selon leurs droits

Milestone: M1
Advances: D7, D9 (partiellement)
Depends on: I1, I2, I3 — inventaire, sources et contrat scientifique

## Objective

Produire une archive locale du contrat scientifique appliquant les politiques du registre. Seuls les contenus externes explicitement autorisés et conformes à leur empreinte sont exportables ; les documents restent exportables seuls.

## Repository Grounding

- `docs/science/provenance.json` inventorie 32 ressources, toutes `not_established`, avec empreintes et justifications individuelles.
- `reich_experiment_v2/verify_provenance.py` fournit la validation du registre et la découverte des ressources, mais ne construit aucun paquet.
- Les cinq documents de `docs/science/` décrivent provenance, sources et observations. Ils peuvent être sélectionnés explicitement sans parcourir les fichiers personnels ni copier les simulateurs.
- M1 D7 reste ouvert ; la distribution exécutable et la publication effective relèvent de M10/M11.

## Change Scope

### Inspect

- `docs/milestones/M1-scientific-contract-and-provenance.md` — invariants de redistribution.
- `reich_experiment_v2/verify_provenance.py` — schéma, statuts et périmètre externe.
- `reich_experiment_v2/science_contract.py` — validation du contrat et des citations.
- `reich_experiment_v2/tests/test_provenance.py` — conventions de fixtures.

### Expected change paths

- `reich_experiment_v2/export_public.py` (new) — sélection, filtrage et création de l'archive avec manifeste.
- `reich_experiment_v2/tests/test_public_export.py` (new) — inspection du contenu exporté et des erreurs.
- `docs/science/provenance.md` — commande, politique d'export et limites.

## Required Changes

1. Exporter les cinq fichiers précis du contrat sous `docs/science/`, puis uniquement les ressources `authorized` du registre. Inclure un manifeste versionné listant chemins, empreintes incluses et motifs d'exclusion ; `not_established`, `not_authorized` et ressources externes non inventoriées sont exclues.
2. Valider registre et contrat avant production. Refuser une ressource autorisée absente, modifiée ou accessible via un lien symbolique, ainsi que les liens dans les documents sélectionnés. Les contenus exclus ne doivent pas être ouverts pour copie ; leur absence n'empêche pas l'export documentaire.
3. Fournir une commande hors réseau avec destination explicite et code de sortie déterministe. Ne pas écraser une destination existante ni écrire dans les répertoires des ressources originales ; ne laisser aucune archive présentée comme réussie après un échec de validation.
4. Produire un contenu reproductible à entrées identiques, sans métadonnées temporelles variables ni chemins absolus de machine. Ne pas inclure par balayage global fichiers personnels, caches, résultats ou code tiers hors sélection.

## Constraints and Non-goals

- Aucun changement des autorisations, empreintes de référence, données scientifiques ou simulateurs.
- Tester les autorisations avec des fixtures synthétiques, sans autoriser de ressource réelle.
- L'installation complète, la licence globale et la publication distante restent hors périmètre.

## Definition of Done

- [x] ID1 L'archive réelle contient les cinq documents et le manifeste, sans contenu des 32 ressources à droits non établis.
- [x] ID2 Des fixtures prouvent inclusion des seuls contenus autorisés et exclusion motivée des deux autres statuts et des ressources non inventoriées.
- [x] ID3 Registre invalide, contenu autorisé absent/modifié, liens symboliques et destination existante sont refusés sans écrasement ; une ressource exclue absente est tolérée.
- [x] ID4 Deux exports identiques ont le même SHA-256 ; les tests confirment absence de fichiers hors sélection et concordance des empreintes du manifeste avec les octets exportés.
- [x] ID5 Les tests ciblés et complets passent sous Nix, y compris les contrôles I1–I3 ; un export réel est créé et inspecté localement.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_public_export.py'
nix develop -c python -m unittest discover -s tests
nix develop -c python export_public.py --output <nouveau-chemin-local.zip>
```

Preuves (24 octobre 2026) : 12 tests ciblés et 52 tests complets réussis.
Export réel inspecté : code 0, cinq documents, un manifeste, 32 exclusions.
Les tests couvrent individuellement ID1–ID5, dont reproductibilité et refus sans écrasement.
