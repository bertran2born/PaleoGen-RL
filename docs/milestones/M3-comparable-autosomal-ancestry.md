# M3 — Ascendance autosomale comparable et validée

Status: READY
Depends on: M2

## Outcome

PaleoGen-RL mesure l'ascendance autosomale finale avec une représentation adaptée aux comparaisons entre modèles, sans l'artefact connu des huit loci sentinelles du prototype. La même observable est calculée pour les mécanismes neutres et épistatiques, y compris lorsque des loci sont soumis à sélection. Les résultats permettent de tester la plage de 3–7 % sans confondre erreur de discrétisation et sélection biologique.

## Objectives

- O1 — L'ascendance autosomale possède une définition commune indépendante du nombre de loci partenaires d'une architecture.
- O2 — Les mécanismes de ségrégation, recombinaison et dérive satisfont des contrôles statistiques pré-enregistrés.
- O3 — L'évaluation finale ne dépend jamais d'une fréquence autosomale mesurée à un arrêt anticipé.
- O4 — Les coûts et approximations de la représentation autosomale sont quantifiés.

## Scope

### In scope

- Blocs d'ascendance neutres représentatifs, recombinaison et contributions diploïdes.
- Ascendance génomique totale, avec séparation explicite des loci sélectionnés et du proxy neutre.
- Validations analytiques, contrôle d'échelle et convergence en nombre de blocs.
- Continuité avec la statistique précédente uniquement pour les tests de diagnostic.

### Out of scope

- Simulation nucléotidique de génomes humains complets et inférence généalogique ARG.
- Attribution de mécanismes biologiques à des variants réels sans donnée indépendante.

## Requirements and Invariants

- R1 — Le score principal se fonde sur une mesure d'ascendance identique pour tous les candidats, quelles que soient les DMI activées.
- R2 — Les loci participant à une DMI sont suivis séparément ; leur activation ne modifie pas silencieusement le dénominateur de l'ascendance.
- R3 — Le mécanisme de recombinaison est défini, paramétré et traçable au niveau des blocs représentés.
- R4 — Le nombre de blocs et les résultats du contrôle de convergence sont déclarés dans chaque évaluation.
- R5 — La cible 3–7 % est évaluée uniquement à la génération finale, même lorsque mtDNA/Y ont déjà été fixés.
- I1 — Le flux de reproduction conserve les règles maternelle et paternelle validées en M2.
- I2 — La fréquence autosomale calculée à une génération intermédiaire n'est jamais présentée comme fréquence à 50 ka.
- I3 — Les comparaisons à paramètres identiques utilisent le même schéma de mesure autosomale.

## Relevant Repository Surfaces

- `src/reich_panmictic_original.py` — hérédité autosomale actuelle.
- `src/epi_pulse.py` — exclusion actuelle des loci partenaires du proxy neutre.
- `compute_autosomal_limit.py` — diagnostic théorique de la discrétisation.
- `plot_autosomal_sensitivity.py` — visualisation du diagnostic.
- `paleogen_rl/genetics/` (proposed) — représentation et mesure communes.
- `tests/test_autosomal_ancestry.py` (proposed) — vérifications de la nouvelle observable.

## Definition of Done

- [ ] D1 [O1] Tous les scénarios existants utilisent le même nombre et la même définition de blocs autosomiques pour la métrique principale.
- [ ] D2 [O1] Activer les loci partenaires sans sélection ne change pas la définition de l'observable autosomale.
- [ ] D3 [O2] Les tests de ségrégation valident les proportions mendéliennes avec les tolérances chiffrées dans le protocole de test.
- [ ] D4 [O2] À recombinaison nulle et à recombinaison active, les trajectoires satisfont les invariants d'ascendance attendus.
- [ ] D5 [O2] Un contrôle neutre reproduit la moyenne théorique attendue sur un lot de graines préfixé, dans son intervalle de confiance pré-enregistré.
- [ ] D6 [O3] `quick` ne produit aucune valeur prétendument finale pour cette nouvelle statistique.
- [ ] D7 [O3] `adaptive` et `full` concordent sur le critère conjoint sur un jeu de références et de graines fixé.
- [ ] D8 [O4] Un rapport compare au moins trois résolutions croissantes et donne les écarts de la métrique cible.
- [ ] D9 [O4] La configuration annonce explicitement le coût des résolutions et le mode choisi.
- [ ] D10 [O1, O2, O3, O4] Les tests autosomiques réussissent, indépendamment des scénarios épistatiques activés.

## Final Validation

```sh
python -m unittest discover -s tests -p 'test_autosomal_ancestry.py'
python -m unittest discover -s tests
```

`tests/test_autosomal_ancestry.py` est une surface proposée, absente du prototype actuel.

## References

- `README.md`, sections « Vérification avant une conclusion scientifique » et « Mise à jour v2 ».
- `compute_autosomal_limit.py` ; SI3, définitions d'ascendance des modèles.
