# I21 — Exécuter un plan déclaré de diagnostic multirésolution autosomal

Milestone: M3
Advances: D8, D9, D10 ; objectifs O4/O1, invariant I3
Depends on: I18, I19 ; M1 clos par I20, protocole principal M3 non adopté

## Objective

Permettre de préparer puis rejouer un diagnostic sélectionné à population et horizon explicites depuis un plan versionné. Lever la restriction actuelle au petit contrôle I18 sans transformer une déclaration de plan en preuve de convergence.

## Repository Grounding

- `reich_experiment_v2/study_autosomal_resolution.py` fixe N=40, f=0.05 et fraction masculine=0.5 ; son API accepte horizon, cartes, scénarios et graines, mais sa CLI n'accepte que la destination.
- I18 archive un diagnostic à 20 générations ; il ne valide pas la résolution à N=1450 / 6993 générations.
- `paleogen_rl/genetics/protocol.py::AutosomalProtocol` fournit validation, instantané et empreinte des contrats de mesure I19, avec convergence non établie.
- Les statistiques et coûts I18 sont disponibles pour toutes les résolutions et doivent rester inchangés.

## Change Scope

### Inspect

- `docs/science/autosomal-selected-resolution-protocol.md` — plan historique et limites.
- `reich_experiment_v2/paleogen_rl/genetics/protocol.py` et `pulse.py` — validation des paramètres, initialisation et rejeu.
- `reich_experiment_v2/tests/test_autosomal_selected_resolution.py` — contrôles existants à conserver.

### Expected change paths

- `reich_experiment_v2/study_autosomal_resolution.py` — entrée plan, démographie explicite et provenance.
- `reich_experiment_v2/tests/test_autosomal_resolution_plan.py` (new) — validation préalable et intégration réelle.
- `docs/science/autosomal-resolution-plan.md` (new) — format, exemple synthétique et preuves.

## Required Changes

1. Accepter un plan JSON versionné avec identifiant, population, horizon positif, fractions du pulse, étendue de carte, au moins trois résolutions croissantes, graines distinctes et scénarios nommés explicites. Refuser champs inconnus/manquants, doublons JSON, non-finis et déclarations invalides avant simulation.
2. Conserver la carte uniforme I18 à étendue constante et partenaires aux extrémités. Chaque résolution doit exporter un contrat I19 valide et son identité ; tous les scénarios partagent ces contrats. Ne modifier ni les statistiques ni les paramètres des scénarios.
3. Exporter l'instantané du plan, son identité canonique et l'empreinte de son fichier, sous une version distincte du rapport. L'instantané suffit au rejeu sans fichier source. Préserver le fonctionnement sans plan, les valeurs historiques par défaut et les archives I18.
4. Vérifier des populations, fractions et horizons différents par comparaison avec les évaluations directes, la répétabilité, les coûts, le rejet préalable et les protections de destination. Documenter que le plan ne garantit ni antériorité temporelle, ni convergence, ni calibration historique.

## Constraints and Non-goals

- Aucun moteur, observation, cible, récompense, archive ou graine historique modifié.
- Pas de résolution par défaut scientifique, étude historique longue ou clôture M3 ; le statut de convergence reste non établi.
- Pas d'évolution des estimateurs ou d'acceptation statistique dans cette Issue.

## Definition of Done

- [x] ID1 Les plans invalides échouent avant toute simulation ; les entrées valides fixent tous les paramètres déclarés.
- [x] ID2 Les contrats I19, instantané et empreintes sont exportés ; rejeu et indépendance du formatage sont vérifiés.
- [x] ID3 Les résultats et coûts correspondent aux évaluations directes pour plusieurs démographies ; les erreurs et écrasements sont refusés.
- [x] ID4 Les suites ciblée, autosomale et complète passent sous Nix, y compris les tests I18 inchangés ; limites documentées.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_resolution_plan.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (25 octobre 2026) : les trois commandes retournent 0 avec **7, 85
et 162 tests**. Le [document de format](../science/autosomal-resolution-plan.md)
relie chaque DoD aux tests et consigne le rejeu réel de son exemple : 12
évaluations identiques après suppression du fichier source. Les comparaisons
directes couvrent trois populations et horizons ; les erreurs sont refusées
avant écriture. Structure, taille, liens et `git diff --check` vérifiés.
Aucun fichier collatéral ou milestone modifié. Les quatre DoD sont satisfaits,
sans étude longue nouvelle, choix de résolution principale ni clôture de M3.
