# M11 — Publication Hugging Face et reproductibilité externe

Status: DRAFT
Depends on: M9, M10

## Outcome

PaleoGen-RL v0.1 permet à un tiers d'exécuter l'environnement OpenEnv et de reproduire un benchmark de démonstration. Le dépôt distingue vérification, exploration et ressources externes. La publication ne présume pas de droits sur les archives originales de Reich.

## Objectives

- O1 — La distribution publique contient une carte d'environnement RL complète avec licence, provenance et limites scientifiques.
- O2 — Le paquet public exécute au moins un épisode standard sans accès à des données non autorisées.
- O3 — Un tiers dispose des contrats nécessaires pour comparer une politique aux baselines.
- O4 — Chaque version référence code, dépendances et tests de reproduction.

## Scope

### In scope

- Dépôt Hugging Face de type dataset avec tags `rl-environment` et `openenv` lorsque la compatibilité est vérifiée.
- Carte descriptive, exemples d'appel, politique d'accès aux ressources originales et rapport de benchmark.
- Audit d'absence de secrets, fichiers sensibles et composants interdits de redistribution.
- Documentation d'un déploiement OpenEnv de démonstration, distinct du dépôt de données.

### Out of scope

- Entraînement et publication de poids d'un agent RL performant.
- Affirmation qu'un modèle découvert remplace ou réfute le modèle de Reich.
- Publication des fichiers SI1–SI4 ou de leurs codes sans droit vérifié.

## Requirements and Invariants

- R1 — Le dépôt de données déclare sa compatibilité réelle par métadonnées ; les tags ne remplacent pas un environnement exécutable.
- R2 — La carte décrit observations, actions, budget, récompense, métriques de test et restrictions de licence.
- R3 — Le dépôt public sépare code original, extension scientifique, résultats synthétiques et résultats empiriques.
- R4 — Toute dépendance non redistribuable dispose d'une procédure d'import documentée ou d'une alternative de démonstration.
- R5 — Chaque release est identifiable par une version sémantique et une empreinte des artefacts scientifiques.
- I1 — Les graines finales réservées du benchmark ne sont pas révélées dans le matériel de recherche de l'agent si leur confidentialité fait partie du protocole.
- I2 — Un score de simulation n'est jamais présenté comme preuve historique.
- I3 — La publication ne modifie ni les contrats d'actions ni les calculs de récompense validés en M7 et M6.

## Relevant Repository Surfaces

- `README.md` — limitations et attribution du prototype.
- `manifest.json` — inventaire actuel, à étendre.
- `flake.nix` — environnement de développement.
- `docs/releases/v0.1.md` (proposed) — contrat de livraison et historique.
- `hub/README.md` (proposed) — carte du dataset RL.
- `tests/test_release.py` (proposed) — audit du paquet.

## Definition of Done

- [ ] D1 [O1] Une carte de dataset contient les tags de compatibilité vérifiés et la version de protocole.
- [ ] D2 [O1] Les limitations scientifiques, les observables et la licence de chaque composant sont publiques.
- [ ] D3 [O2] Un test externe installe l'environnement et exécute un épisode de démonstration avec le même résultat que le test local.
- [ ] D4 [O2] Les ressources de Reich à droits non établis sont absentes de la distribution publique.
- [ ] D5 [O2] L'audit ne trouve aucun jeton, identifiant secret ou chemin personnel dans les fichiers distribués.
- [ ] D6 [O3] L'API d'environnement, le schéma d'actions et les métriques de benchmark sont documentés.
- [ ] D7 [O3] Une baseline aléatoire est exécutable par un utilisateur extérieur avec budget d'exemple fini.
- [ ] D8 [O4] Une release référence code, ressources et dépendances.
- [ ] D9 [O4] La carte pointe vers un rapport de résultats qui inclut la provenance et les limites.
- [ ] D10 [O1, O2, O3, O4] Les tests de contenu du paquet et le test d'installation externe réussissent avant la publication effective.

## Final Validation

```sh
python -m unittest discover -s tests -p 'test_release.py'
python -m unittest discover -s tests
nix develop -c python -m paleogen_rl --help
```

## References

- `README.md` ; `manifest.json` ; contrats scientifiques M1 et M9.
- https://huggingface.co/docs/hub/datasets-cards
- https://github.com/huggingface/OpenEnv/blob/main/docs/source/guides/concepts.md

## Open Decisions

- Définir le détenteur, le nom du dépôt et la licence de la contribution originale PaleoGen-RL.
- Établir la permission de redistribuer séparément les scripts de Reich ou retenir une distribution publique excluant ces scripts.
