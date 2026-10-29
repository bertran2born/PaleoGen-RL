# I36 — Refuser les graines réutilisées avant une étude autosomale

Milestone: M3
Advances: D1, D8, D9 ; objectifs O1/O4, Scientific Acceptance exigence 5
Depends on: I31–I34 ; clôture I35 bloquée par architecture, marges et budget ouverts

## Objective

Rendre vérifiable la séparation des graines d'une future étude et d'un historique
déclaré de dimensionnement, sélection, exploration ou ingénierie. Refuser toute
réutilisation avant simulation, sans adopter de protocole scientifique principal.

## Repository Grounding

- `study_weighted_autosomal_resolution.py` valide les graines distinctes dans
  chaque plan, mais ne les compare à aucun historique externe.
- Ses API d'aperçu/exécution et sa CLI conservent plan, réplicats et empreintes ;
  elles offrent une surface commune pour contrôler cette séparation.
- M3 exige désormais des données confirmatoires indépendantes du dimensionnement
  et de la sélection. L'audit provisoire I35 exclut aussi sa graine d'ingénierie.
- M1 est vérifié par I20 ; les dix critères techniques de M2 sont couverts par
  I10 et les tests pulse. Le statut documentaire M2 reste antérieur à I20.
- Les marges, l'architecture finale et le budget manquent encore : une garde
  technique sur les graines est réalisable sans les inventer.

## Change Scope

### Inspect

- `docs/milestones/M3-comparable-autosomal-ancestry.md` — indépendance et portée.
- `reich_experiment_v2/paleogen_rl/genetics/protocol.py` et `weighted_protocol.py` — conventions de validation et JSON.
- `reich_experiment_v2/tests/test_autosomal_weighted_study.py` — rejeu et compatibilité CLI.

### Expected change paths

- `reich_experiment_v2/autosomal_seed_history.py` (new) — historique versionné, validation et audit déterministe.
- `reich_experiment_v2/study_weighted_autosomal_resolution.py` — contrôle optionnel avant aperçu/exécution et archivage.
- `reich_experiment_v2/tests/test_autosomal_seed_history.py` (new) — collisions, entrées invalides, CLI et non-régression.
- `docs/science/autosomal-seed-separation.md` (new) — contrat, utilisation et limites.

## Required Changes

1. Définir un historique versionné non vide : sources identifiées, usage antérieur,
   empreinte documentaire et graines entières distinctes par source. Refuser
   champs inconnus/manquants, identifiants dupliqués et JSON ambigu/non fini.
2. Auditer les intersections avec les graines candidates, conserver toutes les
   sources de conflit et produire des instantanés et empreintes reproductibles,
   sans RNG ni simulation. Un partage entre sources historiques est permis.
3. Ajouter un historique optionnel aux deux API I31 et à la CLI. Lorsqu'il est
   fourni, une collision ou entrée invalide interdit tout appel moteur et toute
   publication de rapport. Un succès archive historique, identités et plan lié.
4. Préserver les parcours sans historique, les statistiques et le rejeu. Distinguer
   explicitement disjonction déclarée, indépendance statistique et confirmation.

## Constraints and Non-goals

- Aucun choix de nouvelles graines scientifiques, seuil, architecture ou budget.
- Aucun inventaire exhaustif implicite : les empreintes déclarées ne prouvent
  ni authenticité, ni exhaustivité, ni antériorité de l'historique.
- Aucun résultat d'équivalence, adoption principale ou clôture M3 ; les archives
  existantes et modifications préexistantes restent hors du commit de cette Issue.

## Definition of Done

- [x] ID1 Historique strict, chargement JSON, identités et instantanés indépendants sont vérifiés.
- [x] ID2 L'audit détecte toutes les collisions, y compris entre usages/scénarios différents, sans moteur ni RNG.
- [x] ID3 API et CLI refusent conflits/entrées invalides avant simulation ; les sorties acceptées conservent l'audit lié au plan et les empreintes de fichier.
- [x] ID4 Les évaluations avec/sans historique concordent ; rejeu, refus d'écrasement et méthodes d'équivalence existantes restent valides.
- [x] ID5 Documentation et limites concordent avec le comportement ; tests ciblés, autosomaux et complets réussissent sous Nix.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_seed_history.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves du 29 octobre 2026 : **10 tests ciblés, 174 tests autosomaux et 251 tests
complets** réussissent sous Nix, sans échec ni test ignoré. ID1 : entrées invalides,
JSON dupliqué/non fini, empreintes fichier/contenu et instantanés sont contrôlés.
ID2 : toutes les sources de conflit sont vérifiées, avec moteur/RNG interdits.
ID3 : chaque usage antérieur bloque les API ; CLI refusée sans sortie sur conflit,
historique invalide ou absent du disque ; empreintes et lien au plan vérifiés.
ID4 : études réelles courtes sur deux scénarios et trois résolutions, rejeu exact,
égalité avec/sans audit, évaluation I32 et refus d'écrasement réussissent.
ID5 : exemple documentaire exécuté sans moteur/RNG ; suites I31–I34 inchangées.
Le contrôle de provenance vérifie **32 ressources conformes**. Structure, taille
et espaces sont vérifiés. Aucun chemin collatéral modifié ; M3 reste ouvert,
sans confirmation scientifique ni protocole principal adopté.
