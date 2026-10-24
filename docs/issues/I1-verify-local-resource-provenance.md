# I1 — Inventorier et vérifier la provenance des ressources locales

Milestone: M1
Advances: D4, D6, D9 (partiellement)
Depends on: aucune ; ressources locales déjà présentes

## Objective

Fournir un inventaire versionné permettant de vérifier hors réseau les empreintes des ressources externes locales et de connaître leur politique de redistribution. Cette étape fonde la traçabilité de M1 avant la rédaction du contrat des observations ; elle ne valide ni leur interprétation scientifique ni leurs droits d'utilisation.

## Repository Grounding

- `reich_experiment_v2/manifest.json` décrit le prototype et conserve seulement deux empreintes de code ; il n'inventorie pas les ressources locales individuellement.
- `reich_study/` contient le préprint, des suppléments aux noms `media-*` et deux archives du prototype, sans registre de redistribution.
- `reich_experiment_v2/source/` contient le sous-ensemble de code tiers et la distribution mitochondriale utilisée par `run_experiment.py`.
- `reich_experiment_v2/src/reich_panmictic_original.py` est une copie de référence distincte de ce sous-ensemble. Les seuls tests actuels sont `test_pulse.py` et `test_v2.py`.

## Change Scope

### Inspect

- `docs/milestones/M1-scientific-contract-and-provenance.md` — exigences de traçabilité.
- `reich_experiment_v2/manifest.json` — provenance historique existante.
- `reich_experiment_v2/source/mechanisms_code/README.md` — description originale des ressources.
- `reich_experiment_v2/tests/test_v2.py` — conventions de validation.

### Expected change paths

- `docs/science/provenance.json` (new) — inventaire avec empreintes et politiques individuelles.
- `docs/science/provenance.md` (new) — périmètre, limites et utilisation du contrôle.
- `reich_experiment_v2/verify_provenance.py` (new) — contrôle local en lecture seule.
- `reich_experiment_v2/tests/test_provenance.py` (new) — tests du registre et des diagnostics.

## Required Changes

1. Recenser tous les fichiers de `reich_study/`, de `reich_experiment_v2/source/` (hors caches Python), ainsi que la copie du moteur original. Chaque entrée possède un chemin relatif à la racine, un SHA-256 et une politique de redistribution motivée ; aucun droit non vérifié ne doit être présumé acquis.
2. Fournir une commande hors réseau qui recalcule les empreintes, signale séparément fichiers absents, modifiés et non inventoriés, et retourne un code non nul en cas d'écart ou de registre invalide. Elle ne doit jamais réécrire le registre pour faire disparaître un écart.
3. Valider le format versionné, les chemins uniques, les empreintes et les statuts de redistribution. Les chemins doivent désigner des ressources du périmètre déclaré.
4. Documenter la différence entre intégrité locale, identité scientifique et autorisation de redistribution, ainsi que la procédure de revue avant mise à jour des empreintes.

## Constraints and Non-goals

- Conserver le manifeste historique, les ressources originales et les sorties de simulation inchangés.
- Ne pas déduire la correspondance SI1–SI4 des seuls noms `media-*` ; leur identification et versionnement détaillés relèvent d'une autre Issue.
- Ne pas construire l'export public ni déclarer M1 achevé dans cette étape.

## Definition of Done

- [x] ID1 Le registre couvre exactement le périmètre local documenté avec des SHA-256 recalculables.
- [x] ID2 Chaque ressource, y compris chaque archive originale, possède une politique explicite et motivée, sans autorisation inventée.
- [x] ID3 Le vérificateur distingue absence, modification et ajout non inventorié ; les tests couvrent ces trois écarts sur des ressources temporaires.
- [x] ID4 Les registres invalides (version, doublons, empreinte, politique ou chemin) sont refusés par les tests.
- [x] ID5 La commande réelle et les tests ciblés puis complets réussissent sous Nix sans modification des ressources vérifiées.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_provenance.py'
nix develop -c python verify_provenance.py
nix develop -c python -m unittest discover -s tests
```

Vérifié le 24 octobre 2026 : 8 tests ciblés et 22 tests complets réussis ;
commande réelle : code 0, 32 ressources `ok`. ID1/ID2 : test du registre réel ;
ID3/ID4 : fixtures d'écarts et de registres invalides ; ID5 : commandes ci-dessus
et contrôles de lecture seule.
