# M5 — Description canonique des modèles candidats

Status: READY
Depends on: M2, M4

## Outcome

Les modèles candidats de PaleoGen-RL sont décrits par des documents déclaratifs vérifiables, indépendants d'un script Python généré par l'agent. Une proposition précise sa démographie, ses mécanismes génétiques, les paramètres libres et les contraintes qui la rendent admissible. Deux documents équivalents désignent le même modèle canonique et peuvent être évalués, comparés ou archivés.

## Objectives

- O1 — Un schéma versionné représente les mécanismes panmictiques et géographiques pris en charge en v0.1.
- O2 — Les invariants biologiques, domaines des paramètres et prérequis des mécanismes sont vérifiés avant la simulation.
- O3 — Les modèles possèdent une identité canonique stable, insensible aux détails de sérialisation sans effet sémantique.
- O4 — L'espace de recherche autorise des combinaisons de mécanismes sans exécuter de code arbitraire soumis par un agent.

## Scope

### In scope

- Types de démographie, pulse, expansion, effet sexuel, épistasie à quatre directions et dominance.
- Coefficients de sélection, tailles de population, bornes, distributions a priori et champs de provenance.
- Sérialisation JSON, validation de schéma, normalisation et empreinte stable.
- Rejet explicite des modèles hors domaine ou incompatibles avec un moteur.

### Out of scope

- Langage de programmation général, mutations de code source, exécution dynamique d'expressions.
- Modèles démographiques non représentables par les moteurs disponibles.
- Démonstration empirique de plausibilité d'un mécanisme simplement parce qu'il est syntaxiquement valide.

## Requirements and Invariants

- R1 — Le document modèle sépare architecture discrète, paramètres numériques et distributions de paramètres incertains.
- R2 — Chaque mécanisme annonce ses loci partenaires, son sexe d'effet, la direction des pénalités et sa dominance lorsqu'applicables.
- R3 — Un mécanisme ne peut être combiné à un moteur qui ne le supporte pas sans rejet explicite.
- R4 — La validation signale séparément erreur de syntaxe, contradiction biologique codifiée et paramètre insuffisamment justifié.
- R5 — Les domaines de paramètres sont associés à des sources ou à l'étiquette « exploratoire » ; un intervalle exploratoire n'est pas traité comme un prior informatif validé.
- I1 — Les règles de transmission uniparentale demeurent inchangées par le document candidat.
- I2 — La définition des observations et leur origine ne font pas partie de l'espace d'actions modifiable.
- I3 — Aucun champ du document ne donne accès au système de fichiers, au réseau ni à un interpréteur.

## Relevant Repository Surfaces

- `src/epi_pulse.py` — paramètres actuels d'épistasie et de dominance.
- `src/reich_panmictic_original.py` — configuration et mécanismes préexistants.
- `run_experiment.py` — scénarios nommés actuels et overrides.
- `paleogen_rl/models/` (proposed) — schéma, validation et identité canonique.
- `docs/specs/model-v1.md` (proposed) — spécification normative du format.
- `tests/test_model_spec.py` (proposed) — cas valides, invalides et invariants.

## Definition of Done

- [ ] D1 [O1] Les scénarios `reich_point` et `reich_plus_favor_mod_0p3pct` ont chacun une représentation canonique convertible sans perte de paramètres.
- [ ] D2 [O1] Un modèle géographique de référence peut être décrit sans convertir ses paramètres spécifiques en paramètres panmictiques fictifs.
- [ ] D3 [O2] Les valeurs hors domaine, indices de loci invalides et mécanismes incompatibles sont rejetés avant exécution.
- [ ] D4 [O2] Une pénalité égale à zéro est distinguée d'un mécanisme absent si cette différence reste sémantiquement significative.
- [ ] D5 [O3] Deux sérialisations équivalentes produisent la même empreinte canonique.
- [ ] D6 [O3] Une modification de coefficient ou d'architecture produit une identité distincte.
- [ ] D7 [O4] Les documents modèles ne peuvent ni importer des modules ni soumettre du code arbitraire.
- [ ] D8 [O4] Les erreurs de validation décrivent le champ fautif avec un code stable.
- [ ] D9 [O1, O2, O3, O4] Les modèles historiques connus passent les tests de migration, et les modèles volontairement invalides échouent.

## Final Validation

```sh
python -m unittest discover -s tests -p 'test_model_spec.py'
python -m unittest discover -s tests
```

## References

- `README.md`, sections « Paramètres d'épistasie » et « Mise à jour v2 ».
- Contrat scientifique livré en M1 ; suppléments SI1 et SI3.
