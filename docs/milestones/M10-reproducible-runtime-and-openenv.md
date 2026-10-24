# M10 — Exécution reproductible sur NixOS et interface OpenEnv

Status: READY
Depends on: M7, M9

## Outcome

PaleoGen-RL v0.1 peut être installé, testé et exécuté localement sous NixOS à partir d'une révision identifiée. Un utilisateur peut lancer un épisode, obtenir un rapport d'évaluation et exposer le même environnement via l'interface standard OpenEnv, sans changer la sémantique scientifique. Les versions, graines, ressources externes et coûts du calcul sont enregistrés avec chaque sortie.

## Objectives

- O1 — Un environnement Nix verrouillé fournit les dépendances requises sans installation manuelle non documentée.
- O2 — Une interface CLI stable donne accès à la vérification, à l'épisode de démonstration et à l'évaluation.
- O3 — Un adaptateur OpenEnv expose les mêmes actions, observations et récompenses que l'environnement local.
- O4 — L'installation peut être validée indépendamment des archives originales dont la redistribution n'est pas établie.

## Scope

### In scope

- Gestion des dépendances Nix, interface CLI v0.1, exécution hors réseau d'un épisode de test.
- Adaptateur client/serveur OpenEnv, cas de test à budget réduit et format de sortie versionné.
- Rapport sur les dépendances locales manquantes et sur les ressources à obtenir légalement.
- Manifestes de version, empreintes des ressources et graine d'exécution.

### Out of scope

- Déploiement distribué, entraînement GPU ou cluster, publication automatique.
- Embarquement non autorisé des ZIP originaux, garanties d'identité bit-à-bit entre toutes les architectures matérielles.

## Requirements and Invariants

- R1 — L'environnement Nix publie un `flake.lock` avec les dépendances résolues et compatible avec `x86_64-linux`.
- R2 — La CLI distingue diagnostic de ressources, exécution d'épisode et évaluation scientifique avec codes de retour explicites.
- R3 — Les modes locaux et OpenEnv invoquent le même validateur de modèles et le même calcul de récompense.
- R4 — Une absence d'archive non redistribuable donne un diagnostic actionnable sans téléchargement implicite ni sortie présentée comme succès.
- R5 — Chaque exécution exporte version logicielle, identité du modèle, protocole de score, graine et statut.
- I1 — Le service OpenEnv n'expose pas de primitive d'exécution de code arbitraire.
- I2 — Le protocole de récompense est identique quel que soit le transport.
- I3 — Aucun identifiant de compte, jeton Hub ou secret ne figure dans les journaux ou paquets.

## Relevant Repository Surfaces

- `flake.nix` — environnement Nix actuel, non verrouillé dans l'archive v2.
- `requirements.txt` — dépendances Python actuelles.
- `manifest.json` — traçabilité initiale.
- `paleogen_rl/__main__.py` (proposed) — CLI publique.
- `paleogen_rl/openenv/` (proposed) — adaptateur protocolaire.
- `tests/test_runtime.py` (proposed) — tests d'installation et parité transport.
- `flake.lock` (proposed) — versions des entrées Nix.

## Definition of Done

- [ ] D1 [O1] `nix develop -c python -m unittest discover -s tests` réussit sur `x86_64-linux` avec les ressources autorisées installées.
- [ ] D2 [O1] Le dépôt versionne `flake.lock` et documente toute entrée nécessitant un accès réseau lors de l'installation initiale.
- [ ] D3 [O2] `python -m paleogen_rl --help` affiche les commandes publiques et sort avec le code 0.
- [ ] D4 [O2] Un mode diagnostic signale les ressources requises absentes sans déclencher de simulation.
- [ ] D5 [O2] Un épisode de test produit un résultat JSON versionné et un code de retour déterministe.
- [ ] D6 [O3] Un client OpenEnv peut appeler `reset`, `step` et `state` pour un épisode isolé.
- [ ] D7 [O3] Les observations et récompenses numériques obtenues localement et par OpenEnv concordent pour la même configuration.
- [ ] D8 [O4] Le mode démonstration sans archive originale fonctionne sur un scénario de test clairement étiqueté « synthétique ».
- [ ] D9 [O4] Aucune archive de Reich à droits indéterminés n'est incluse dans le paquet public par défaut.
- [ ] D10 [O1, O2, O3, O4] La suite d'installation, d'interface et de reproductibilité réussit.

## Final Validation

```sh
nix develop -c python -m unittest discover -s tests
nix develop -c python -m paleogen_rl --help
nix develop -c python -m unittest discover -s tests -p 'test_runtime.py'
```

## References

- `flake.nix` et `requirements.txt`.
- OpenEnv, documentation d'intégration : https://github.com/huggingface/OpenEnv/blob/main/docs/source/getting_started/environment-builder.md
