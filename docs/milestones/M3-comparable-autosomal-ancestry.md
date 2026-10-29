# M3 — Ascendance autosomale comparable et validée

Status: READY
Depends on: M2

Acceptation technique partielle I24 : D2–D10 vérifiés dans le périmètre de
l'[audit](../science/m3-audit.md). D1 et l'acceptation scientifique globale
restent ouverts : protocole principal et convergence non établis.

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

- `src/reich_panmictic_original.py` et `src/epi_pulse.py` — chemin historique de compatibilité, avec proxy neutre distinct.
- `compute_autosomal_limit.py` — diagnostic théorique de la discrétisation.
- `plot_autosomal_sensitivity.py` — visualisation du diagnostic.
- `paleogen_rl/genetics/ancestry.py` et `inheritance.py` — mesure totale et transmission phasée sur carte déclarée.
- `paleogen_rl/genetics/neutral.py`, `selected.py` et `pulse.py` — dérive, sélection et évaluation des trois modes.
- `paleogen_rl/genetics/protocol.py` — contrats de mesure explicites et identifiés.
- `run_experiment.py` — activation des blocs par carte/protocole, chemin historique préservé par défaut.
- `study_autosomal_resolution.py` — études multirésolution et aperçu de coût avant simulation.
- `tests/test_autosomal_ancestry.py`, `test_autosomal_inheritance.py`, `test_autosomal_neutral.py` — contrôles analytiques et statistiques.
- `tests/test_autosomal_selected.py`, `test_autosomal_block_modes.py`, `test_autosomal_protocol.py` — scénarios, modes et identité de mesure.
- `docs/science/m3-audit.md` — correspondance des critères et limites d'acceptation.

## Scientific Acceptance — M3

La clôture de M3 exige, outre la validation technique des mécanismes autosomiques,
une confirmation indépendante de la stabilité numérique de la métrique principale
entre les résolutions retenues.

**Portée scientifique**

- Une validation conditionnelle sur une famille synthétique est admissible, à
  condition que son architecture, ses hypothèses et ses limitations soient explicites.
- Une équivalence dans une famille finie de résolutions ne constitue ni une preuve
  de convergence universelle, ni une calibration du génome humain, ni une validation
  historique.
- Les poids des loci partenaires doivent être conservés selon les règles du
  raffinement retenu, sans modification silencieuse du dénominateur de l'ascendance.

**Exigences de confirmation**

1. L'architecture principale, les résolutions et les observables sont définies avant
   la confirmation.
2. Les quatre marges d'équivalence, le risque statistique simultané, la précision
   requise, la méthode d'inférence, les effectifs, les graines et le budget sont
   fixés dans un protocole versionné.
3. L'équivalence est évaluée à partir des intervalles simultanés des différences
   entre résolutions, et non de la seule absence de différence statistiquement
   significative.
4. Les événements rares font l'objet d'une justification explicite des marges et
   de leur portée scientifique.
5. Les données confirmatoires sont indépendantes de celles ayant servi au
   dimensionnement et à la sélection des paramètres.
6. Les résultats non concluants et les échecs sont conservés sans modification
   rétroactive des critères.

**Règle de clôture**

M3 ne peut être déclaré `COMPLETE` que si les critères confirmatoires préalablement
définis sont satisfaits et si le protocole autosomal principal est effectivement
adopté pour les 17 scénarios, avec préservation explicite du chemin historique.

Le rapport final doit identifier précisément la famille de modèles et les
résolutions pour lesquelles cette validation est établie.

## Definition of Done

- [ ] D1 [O1] Tous les scénarios existants utilisent le même nombre et la même définition de blocs autosomiques pour la métrique principale.
- [x] D2 [O1] Activer les loci partenaires sans sélection ne change pas la définition de l'observable autosomale.
- [x] D3 [O2] Les tests de ségrégation valident les proportions mendéliennes avec les tolérances chiffrées dans le protocole de test.
- [x] D4 [O2] À recombinaison nulle et à recombinaison active, les trajectoires satisfont les invariants d'ascendance attendus.
- [x] D5 [O2] Un contrôle neutre reproduit la moyenne théorique attendue sur un lot de graines préfixé, dans son intervalle de confiance pré-enregistré.
- [x] D6 [O3] `quick` ne produit aucune valeur prétendument finale pour cette nouvelle statistique.
- [x] D7 [O3] `adaptive` et `full` concordent sur le critère conjoint sur un jeu de références et de graines fixé.
- [x] D8 [O4] Un rapport compare au moins trois résolutions croissantes et donne les écarts de la métrique cible.
- [x] D9 [O4] La configuration annonce explicitement le coût des résolutions et le mode choisi.
- [x] D10 [O1, O2, O3, O4] Les tests autosomiques réussissent, indépendamment des scénarios épistatiques activés.

## Final Validation

```sh
nix develop -c python -m unittest discover -s tests -p 'test_autosomal_ancestry.py'
nix develop -c python -m unittest discover -s tests -p 'test_autosomal*.py'
nix develop -c python -m unittest discover -s tests
```

Les commandes s'exécutent depuis `reich_experiment_v2/`.

Preuves I24 (25 octobre 2026) : les trois commandes ci-dessus réussissent
sous Nix avec **8 tests de mesure, 95 tests autosomaux et 172 tests complets**.
Les contrôles isolés de transmission, dérive neutre et modes réussissent aussi
avec **9/8/9 tests**. L'[audit D1–D10](../science/m3-audit.md) donne assertions,
graines, seuils, types de preuves et limites. Les scénarios sélectionnés sont
couverts, et les archives I14/I18/I22 fournissent les rapports à trois résolutions.
D8 valide l'existence du diagnostic, sans prouver la convergence R4.
D9 est vérifié pour les configurations explicites de blocs : aperçu full et
coûts effectifs des modes, en unités logiques, sans borne de temps matériel
ou de pic mémoire. Le chemin par défaut conserve le proxy historique ; aucun
protocole principal convergent n'est adopté. D1 reste décoché et le statut
reste READY. Aucune ancienne preuve datée, simulation ou observation n'est
modifiée par cette mise à jour documentaire.

## References

- `README.md`, sections « Vérification avant une conclusion scientifique » et « Mise à jour v2 ».
- `compute_autosomal_limit.py` ; SI3, définitions d'ascendance des modèles.
