# Expérience : métissage ponctuel, épistasie réciproque et ascendance néandertalienne

**État : prototype de simulation exploratoire ; il ne constitue pas une réfutation du préprint.**

## 1. Origine et nouveauté

Ce projet utilise le code de **David Reich**, *Hypothesis: A modern human range expansion ~300,000 years ago had a critical role in Neandertal origins*, préprint bioRxiv **v2 daté du 13 octobre 2026**, et particulièrement `SI3codebase.zip` → `mechanisms_code/cluster/panmictic_sim.py` (copié sans modification sous `src/reich_panmictic_original.py`).

Point méthodologique : Reich **a déjà testé des DMI**, y compris dans une simulation de pulse et des comparaisons avec expansion (SI3), et a cherché des indices structuraux de DMI mitochondriale (SI2), sans en détecter. L'innovation ciblée proposée est **un jeu de quatre coûts génétiques réciproques indépendants**, portant sur deux interactions entre marqueur uniparental et partenaire autosomal. Notre test n'est donc ni une découverte de l'épistasie ni une comparaison exhaustive avec toutes les hypothèses explorées par Reich.

Les scripts utilisés pour reconstruire le modèle sont attribués à Reich. Les nouveaux fichiers de ce projet sont `src/epi_pulse.py`, `run_experiment.py`, `tests/test_pulse.py` et `plot_results.py`.

## 2. Modèle et observations

- Population panmictique **sans expansion**, `N=1450` diploïdes répartis équitablement entre hommes et femmes, proche de la taille effective diploïde harmonique de SI1 (~1450) entre 250 et 50 ka. Attention : égaler la taille du recensement à une taille effective est une **approximation**, non une preuve de calibration du Ne réalisé.
- Pulse de `f=0.05` à 250 ka ; `male_frac=0.5`, donc chaque marqueur uniparental est initialement ~5 % moderne. Chronologie : 6993 générations de 28,6 ans vers 50 ka.
- Sélection, reproduction et transmission : code original SI3. mtDNA vient de la mère, Y du père, 8 loci autosomiques diploïdes avec ségrégation mendélienne, 2 loci X ; l'échantillon tire 10 **mâles** sans remise.
- Autosomes **à l'extérieur des loci partenaires sélectionnés** : 6 loci neutres dans les simulations épistatiques, 8 en leur absence. C'est un proxy très grossier de l'ascendance génomique totale.
- **Succès principal** : la probabilité que **les dix mâles échantillonnés** portent *simultanément* le mtDNA moderne et le Y moderne, **et** que l'ascendance autosomale à la génération finale soit comprise entre 3 % et 7 %.
- **Succès secondaires** : fixation stricte des deux marqueurs ; probabilité d'échantillon indépendamment de l'ascendance ; fraction des réplicats dans l'intervalle d'ascendance.
- Probabilité conditionnelle exacte pour dix mâles, sans remplacement : `P10 = (K)_10 / (N_m)_10` où `K` est le nombre d'hommes portant **les deux** marqueurs modernes (et `(x)_10` la factorielle décroissante). Pour obtenir une estimation Monte Carlo plus efficace, `P10` est moyennée sur les répétitions, au lieu de simuler un seul échantillon de dix hommes par répétition.

### Paramètres d'épistasie (coûts, pas bonus)

| Nom du paramètre | Génotype concerné | Effet du coefficient `d` |
|---|---|---|
| `mt_mod_nuc_arch` | mtDNA moderne × autosome partenaire **archaïque** | Perte de viabilité `d`, pondérée par la dominance |
| `mt_arch_nuc_mod` | mtDNA archaïque × autosome partenaire **moderne** | Même règle dans l'autre direction |
| `y_mod_nuc_arch` | Y moderne × autosome partenaire archaïque (mâles) | Perte de viabilité `d` |
| `y_arch_nuc_mod` | Y archaïque × autosome partenaire moderne (mâles) | Perte de viabilité `d` |

La survie résultante est le **produit des quatre termes de survie**, multiplié par les effets de sélection déjà présents dans le modèle original. L'hypothèse de dominance par défaut est **additive** : une copie autosomale incompatible produit la moitié de la pénalité de deux copies. Alternatives testables : `dominant`, `recessive`.

Les deux partenaires sont placés sur les loci autosomiques 0 et 1 (pas des gènes humains précis). L'hypothèse que de tels loci aient réellement existé est *non démontrée*. Le modèle ne reproduit ni l'ensemble des interactions moléculaires ni les mutations délétères en amont ; celles-ci sont représentées seulement par des coefficients tirés ou fixés.

## 3. Conditions minimales (a priori, exploration)

1. **Neutre** : tous coefficients nuls ; probabilité analytique approchée de double fixation = `f² = 0.0025` pour des lignées neutres indépendantes et un pulse sans biais sexuel.
2. **Référence Reich approximative** : `s_mt=0.0032`, `s_Y=0.0013`, deux avantages représentatifs mentionnés dans SI1 et le préprint. **Ce n'est pas la reproduction de sa distribution intégrée, ni de la courbe publiée 2–3 %.** Avec `--mt-posterior`, on tire en revanche `s_mt` dans la posterior de SI1 (11698 valeurs) comme le fait son code SI3 ; le Y reste à 0.0013.
3. **DMI symétrique** : quatre pénalités égales (`0.01` ou `0.05`).
4. **DMI asymétrique moderne/archaïque** : dans une direction les coûts sont 0, dans l'autre 0.01 ou 0.05, **puis inversion**. Cette comparaison est importante pour éviter d'imposer un succès des lignées modernes.
5. **Interaction DMI + avantage du cliquet de Muller** : `s_mt=0.0032, s_Y=0.0013` et pénalités réciproques `0.01`.

**ATTENTION** : les pénalités 1 % / 5 % sont des **valeurs exploratoires non validées biologiquement**. Leur admissibilité demanderait un ancrage dans des données moléculaires ou expérimentales extérieures à ce prototype, et des analyses de sensibilité plus larges. Le fait qu'une simulation « marche » ne rend pas ses paramètres plausibles.

## 4. Installation et exécution

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v

# Évaluation correcte à ~50 ka (inclut le filtre autosomal).
# EFFICACE : arrêt anticipé sur mt/Y, puis continuation complète
# UNIQUEMENT des trajectoires susceptibles de satisfaire le critère principal.
python run_experiment.py --scenario all --mode adaptive --reps 1000 --N 1450 --gens 6993

# CONTRÔLE intégral : poursuit également les trajectoires où les marqueurs ont échoué.
python run_experiment.py --scenario reich_point --mode full --reps 100

# Écran rapide : mesure UNIQUEMENT les marqueurs mt/Y.
# Il arrête les répétitions dès que mtDNA et Y sont chacun fixés ou perdus.
# LA MESURE AUTOSOMALE À 50 KA EST ALORS INVALIDE.
python run_experiment.py --scenario all --mode quick --reps 1000

# Exemple avec la distribution mitochondriale de SI1 fournie par Reich.
python run_experiment.py --scenario reich_point --mode full --reps 1000 \
  --mt-posterior source/mechanisms_code/mt_gap_posterior_pooled_rna.txt

python compute_autosomal_limit.py
python plot_results.py
python plot_autosomal_sensitivity.py
```

Pour utiliser l'environnement **NixOS** (pour figer complètement cet environnement, générer et conserver ensuite un `flake.lock`), à la racine du dossier :

```bash
nix develop -c python -m unittest discover -s tests -v
nix develop -c python run_experiment.py --scenario all --mode adaptive --reps 1000
```

Les sorties `results/*.csv` contiennent **un réplicat par ligne**, sa graine RNG, les paramètres de niveau supérieur, les fréquences des marqueurs, la proportion autosomale, la probabilité d'obtenir dix mâles « doubles modernes » et la variable conjointe avec filtre autosomal. Les `results/*.json` contiennent des estimations moyennes et des intervalles bootstrap 95 % (incertitude Monte Carlo **seulement**, non une incertitude historique complète).

**Mode `adaptive`** : le programme commence par un parcours rapide. Si la probabilité d'avoir dix mâles portant les deux marqueurs est strictement nulle, l'événement conjoint est impossible : pas besoin de poursuivre les autosomes. Sinon, il relance **la même graine** avec l'intégralité des générations, et calcule l'ascendance finale. Une optimisation coupe la sélection sur mtDNA/Y **après** leur absorption : elle devient constante pour tous les individus et n'affecte donc plus le tirage des génotypes neutres. Cette optimisation conserve la loi de reproduction mais consomme un flux de nombres aléatoires différent après absorption, et les autosomes individuels ne sont pas identiques à ceux d'une exécution sans optimisation. La mesure principale reste non biaisée sous ces hypothèses (aucun second pulse et sélection uniquement sur mtDNA/Y après absorption). Pour les DMI, l'optimisation de sélection n'est pas appliquée car leurs partenaires nucléaires demeurent soumis à sélection. **En mode `adaptive`, la probabilité d'être dans 3–7 % sur l'ensemble des trajectoires ne peut pas être estimée puisque seules les positives sont poursuivies.**

Important : `quick` arrête les simulations dès absorption des deux marqueurs ; sa statistique mt/Y est valide à 50 ka en l'absence de nouveau pulse, mais **sa fraction autosomale est mesurée avant 50 ka**. C'est pour cela que la sortie `target_auto` et `P_joint_and_auto` sont mises à blanc dans ce mode.

## 5. Vérification avant une conclusion scientifique

- Comparaison zéro-effet contre `reich_panmictic_original.py` avec graines identiques (test automatique de parité) ; vérification des règles de transmission et de pénalités complémentaires.
- Faire > 1000 réplicats par jeu de paramètres : pour une probabilité de 0,25 %, **100 réplicats donnent en moyenne 0,25 succès**, ce qui ne permet rien de conclure d'un zéro.
- Pré-définir une grille de paramètres justifiée empiriquement (formes de dominance, intensités, sex-ratio, N / Ne, date de mélange, choix du Y, s_mt posterior, architecture des loci).
- Réaliser les mêmes comparaisons par reproduction des codes originaux SI3 de **range expansion** (`spatial_sim2.py`, `spatial_sim3.py`, `band_model/bandsim.py`), et calibrer leurs taux de flux pour obtenir 3–7 % d'ascendance autosomale. Ces modèles ne sont **pas** encore exécutés dans ce prototype.
- Rapporter à la fois taux de réussite **avant** et **après** conditionnement à 3–7 % autosomaux, afin de ne pas favoriser artificiellement un modèle par calibration post hoc.
- Comparer un modèle enrichi au modèle simple en tenant compte de son nombre de paramètres (sensitivity analysis, ABC / posterior predictive checks, Bayes factors ou validation hors échantillon), et non seulement du maximum sur la grille.
- Valider la plausibilité des mécanismes de DMI à l'aide des données d'interaction mt-nucléaire et de la contrainte génétique discutées en SI2 (y compris les limites du résultat négatif).

## 6. Sources et limites importantes

- Préprint, 13 octobre 2026 : pages 5–7, 20–21, non évalué par les pairs à ce stade.
- SI1 pages 1–4 : `N_M,uni=7000`, `N_A,uni=2250`, `N_N,uni≈725`, `T_mix=8741` et `T_samp=1748`, 6993 générations, `s_mt` médian 0.32 %, et Y env. 0.09–0.17 % suivant les paramètres. Inférence intégrée de cofixation ≲2–3 %.
- SI2 : aucune preuve trouvée de DMI mitochondriale structurale aux interfaces examinées ; **ce n'est pas une exclusion générale des mécanismes épistatiques**.
- SI3 : Reich étudie **déjà** des DMI, y compris mtDNA × Y, mtDNA × autosomes, et X × Y ; ce travail prend appui sur ces analyses, il n'en révèle pas l'absence.
- Les simulations ne possèdent pas d'étalonnage de fitness de nouveaux loci sur de vraies séquences, pas de reconstruction génomique, pas de modèle de recombinaison multi-loci réaliste à l'échelle du génome et pas de comparaison de vraisemblance structurée. Le scénario « direction moderne » n'est pas une force directionnelle positive explicitement imposée sur mtDNA et Y, mais une pénalité sur certains **génotypes**. Il peut très bien conduire à la disparition du partenaire nucléaire moderne.

## 7. Licence et provenance

Le programme sous `src/reich_panmictic_original.py` est une **copie attribuée** d'un script livré dans `SI3codebase.zip` de David Reich ; il est réutilisé ici exclusivement pour permettre la réplicabilité de l'expérience réalisée sur les fichiers fournis. Vérifier les conditions de licence applicables au code avant toute redistribution publique. Les autres scripts du prototype sont une adaptation expérimentale indépendante.

## 8. Résultats pilotes préliminaires (archives dans `results/`)

| Condition | n | Succès parmi 10 mâles (mt/Y) | 95 % IC Wilson | Succès joint **avec** 3–7 % autosomal avec 8 loci |
|---|---:|---:|---:|---:|
| Référence Reich approximative avec tirages SI1 de s_mt | 160 | 7 (4,375 %) | 2,14–8,75 % | 0/160 (IC 0–2,34 %) |
| DMI symétrique 1 % | 90 | 0 | 0–4,09 % | 0/90 |
| DMI direction 1, 5 % | 90 | 0 | 0–4,09 % | 0/90 |
| DMI direction opposée, 5 % | 90 | 0 | 0–4,09 % | 0/90 |
| Contrôle neutre | 80 | 0 | environ 0–4,6 % | Non testé intégralement sur cette série |

**Le zéro à l'étape autosomale est principalement un avertissement de modélisation, pas un résultat biologique.** À 50 ka, plusieurs des huit loci sont devenus monomorphes : les pourcentages ont alors des pas de 12,5 %. Par exemple, parmi les sept trajectoires sélectionnées retenues, les proportions autosomales finales sont : 25 %, 0 %, 0 %, 7,21 %, 0 %, 2,37 %, 0 %. Le filtre 3–7 % exclut les sept. Il faut **modéliser davantage de blocs d'ascendance recombinants**, ou adopter une statistique autosomale agrégée explicitement définie, puis recommencer la comparaison.

**Contrôle analytique de l'artefact** : si chaque locus neutre finit fixé ancien/moderne de façon indépendante et avec probabilité 5 % moderne, le nombre de loci modernes fixés suit Binomiale(L, 0,05). Dans cette limite longue, la probabilité que la moyenne appartienne à 3–7 % vaut **0 % pour 8 loci, 85,1 % pour 256 loci et 99,6 % pour 1 024 loci** (voir `compute_autosomal_limit.py` et `figures/autosomal_loci_limit.png`). Ce calcul illustratif n'est **pas** une simulation de génomes et ne prouve pas qu'une des histoires démographiques est correcte.

**Conclusion provisoire** : les simulations pilotes ne soutiennent pas encore l'idée qu'une incompatibilité épistatique puisse à elle seule remplacer l'expansion. Les expériences doivent être répétées à forte puissance, avec davantage de segments autosomiques, des architectures génétiques mieux justifiées et les modèles d'expansion originaux exécutés en parallèle. Le préprint n'a pas été « réfuté ».

## Mise à jour v2 — sélection épistatique directionnelle

Les expériences à 500 répétitions ont montré **13/500 fixations conjointes** pour
`reich_point` et **0/500** pour `reich_plus_symmetric_1pct`. Ces résultats indiquent
une réduction de la fixation sous **cette** épistasie, sans exclure d'autres architectures.
Le modèle à 1 % n'est pas une estimation biologique validée. Il s'agit d'un paramètre
exploratoire.

**Correction méthodologique :** les anciens scénarios `direction_mod_1pct`
et `direction_arch_1pct` testent l'épistasie **sans** le fond sélectif de référence.
Les scénarios préfixés `reich_plus_` ajoutés dans cette version **conservent**
la sélection Y (`s=0.0013`) et la possibilité de tirer `s_mt` dans la distribution SI1.

- `reich_plus_symmetric_0p1pct`, `reich_plus_symmetric_0p3pct`, `reich_plus_symmetric_1pct` : pénalités réciproques identiques (0,1 %, 0,3 %, 1 %).
- `reich_plus_favor_mod_0p1pct`, `_0p3pct`, `_1pct` : pénalisent uniquement les **marqueurs archaïques** en présence de partenaires autosomiques modernes.
- `reich_plus_favor_arch_0p1pct`, `_0p3pct`, `_1pct` : pénalisent uniquement les **marqueurs modernes** en présence de partenaires autosomiques archaïques.

Les étiquettes « favor » décrivent le **sens de la pénalité conditionnelle** et ne
préjugent pas du résultat global : l'architecture peut modifier les fréquences des
partenaires autosomiques et les associations entre loci.

On peut également modifier librement les quatre termes sans toucher au code :

```sh
nix develop -c python run_experiment.py \
  --scenario reich_point --mode adaptive --reps 200 --seed 62126 \
  --mt-posterior source/mechanisms_code/mt_gap_posterior_pooled_rna.txt \
  --mt-mod-nuc-arch 0 --mt-arch-nuc-mod 0.003 \
  --y-mod-nuc-arch 0 --y-arch-nuc-mod 0.003 \
  --output results/reich_plus_custom_200.csv
```

Exemple de scénario nommé :

```sh
nix develop -c python run_experiment.py \
  --scenario reich_plus_favor_mod_0p3pct --mode adaptive --reps 200 \
  --seed 62126 \
  --mt-posterior source/mechanisms_code/mt_gap_posterior_pooled_rna.txt \
  --output results/favor_mod_0p3pct_200.csv
```

Analyse comparative des CSV :

```sh
nix develop -c python compare_runs.py results/reference_500.csv results/epistasis_500.csv
```

**Caveat important :** dans le scénario épistatique, les deux loci autosomiques
impliqués dans les incompatibilités sont exclus de la statistique d'ascendance,
qui repose alors sur **6 loci neutres**, alors que la référence en utilise **8**.
Il faut standardiser le jeu de loci sentinelles et améliorer la représentation
recombinante du génome avant de comparer sérieusement le taux de succès
`joint_and_target` (3–7 %). La rareté initiale des marqueurs modernes signifie
également qu'une pénalité « symétrique » de 1 % peut se traduire par une sélection
nette en défaveur des marqueurs modernes, après dissipation des associations
d'ascendance initiales. Il faut tester les deux directions avec les mêmes priors.
