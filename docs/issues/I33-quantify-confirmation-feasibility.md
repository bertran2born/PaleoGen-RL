# I33 — Chiffrer la faisabilité de la confirmation avant de fixer ses critères

Milestone: M3
Advances: D1, D9 ; objectif O4, exigence R4
Depends on: I30, I31, I32 ; marges et budget confirmatoires non adoptés

## Objective

Produire un dossier reproductible reliant précision simultanée et coût logique
au régime N=1450/G=6993, sans lancer les simulations. Ce chiffrage prépare
le choix scientifique des marges et du budget, encore ouvert après I32.

## Repository Grounding

- I31 prévoit le travail full conditionnel à l'achèvement, pour un plan explicite.
- I32 prévoit l'effectif requis par cellule avec une borne simultanée sur
  tous les scénarios, métriques et résolutions ; ses marges d'exemple sont
  uniquement techniques, non adoptées pour M3.
- I30 fournit une famille synthétique à poids partenaires constants ; aucun
  protocole principal biologique n'est établi par cette famille.
- I22 documente un pilote à l'horizon cible, mais ses résolutions changent
  aussi le poids sélectionné ; ses résultats ne fixent pas les nouvelles marges.

## Change Scope

### Inspect

- `reich_experiment_v2/weighted_autosomal_equivalence.py` — risque et effectif simultanés.
- `reich_experiment_v2/study_weighted_autosomal_resolution.py` — coûts prévus.
- `docs/science/autosomal-target-regime-diagnostic.md` — contexte et limites du pilote.

### Expected change paths

- `docs/science/m3-confirmation-budget-plan.json` (new) — gabarit I31 de chiffrage, sans adoption scientifique.
- `docs/science/m3-confirmation-budget.json` (new, generated) — précision, effectifs, coûts et provenance.
- `docs/science/m3-confirmation-budget.md` (new) — reproduction, résultats et décisions restantes.
- `reich_experiment_v2/tests/test_autosomal_confirmation_budget.py` (new) — intégrité et calculs indépendants.

## Required Changes

1. Déclarer un gabarit de chiffrage au régime cible, avec pulse et arrondis
   existants, les 17 scénarios, une famille I30 déjà validée et un petit lot
   de graines réservé à la prévision. Identifier explicitement son caractère
   synthétique ; ne pas le présenter comme plan confirmatoire approuvé.
2. Archiver une analyse de sensibilité à plusieurs rayons de précision, avec
   risque global déclaré. Pour chaque rayon, utiliser I32 pour prévoir l'effectif
   nécessaire sur toutes les comparaisons et I31 pour extrapoler les coûts
   minimaux à cet effectif, sans matérialiser d'immenses listes de graines.
   Distinguer précision, marge d'équivalence et probabilité de réussite.
3. Conserver gabarit complet, empreintes canonique/fichier, critères techniques
   de calcul, versions et empreintes d'implémentation. Fournir une reproduction
   exécutable utilisant les APIs existantes, à destination nouvelle, sans
   ajouter de nouvel outil générique ni appeler moteur/RNG.
4. Documenter les minima conditionnels, rejets non prévus, taille d'un état et
   absence de borne de temps matériel. Présenter les décisions nécessaires
   avant gel d'un vrai plan : architecture, marges justifiées, précision,
   risque, budget et graines confirmatoires. Une extension des graines exige
   une nouvelle identité de plan/critères.

## Constraints and Non-goals

- Aucun changement des méthodes statistiques, runners, moteurs, observations,
  cible, graines ou archives historiques.
- Aucune étude confirmatoire exécutée, marge scientifique adoptée ou conclusion
  de convergence. Les poids et facteurs du gabarit sont des hypothèses de coût.
- Ne pas élargir les marges selon des scores observés pour rendre le calcul
  faisable ; ce dossier ne contient aucun résultat simulé.

## Definition of Done

- [x] ID1 Gabarit valide et archive identifiée couvrent le régime cible et les 17 scénarios, avec statuts de planification explicites.
- [x] ID2 Effectifs et coûts sont vérifiés indépendamment sur tous les rayons ; aucun moteur/RNG ni liste de graines géante n'est utilisé.
- [x] ID3 Reproduction sans écrasement, provenance et limites sont vérifiées ; décisions scientifiques restantes documentées.
- [x] ID4 Tests ciblés, autosomaux et complets réussissent sous Nix ; dossier et conclusions chiffrées sont cohérents.

## Verification

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_confirmation_budget.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Preuves (26 octobre 2026) : les commandes réussissent avec **3/156/233 tests**,
sans échec ni test ignoré. ID1 : empreintes du gabarit/rapport, régime cible,
17 scénarios et famille 4/8/20 vérifiés. ID2 : effectif minimal et coûts entiers
recalculés indépendamment pour sept rayons, sans grande liste de graines.
ID3 : [reproduction documentée](../science/m3-confirmation-budget.md) exécutée
sous Nix, puis dans les tests avec moteur/RNG interdits et destination existante
préservée. ID4 : suites complètes et table cohérente ; un rayon de 1 point
demande 172031 réplicats par cellule, soit 8773581 évaluations full avec I32.
Structure, taille, syntaxe, JSON strict et espaces vérifiés. Aucun moteur,
runner, observation, archive historique ou ressource modifié ; M3 reste ouvert.
