# Inventaire local de provenance — version 1

`provenance.json` enregistre les SHA-256 des octets présents localement au moment
de l'inventaire I1. Les chemins sont relatifs à la racine PaleoGen-RL.
Le périmètre comprend tous les fichiers de `reich_study/`, tous ceux de
`reich_experiment_v2/source/` et la copie
`reich_experiment_v2/src/reich_panmictic_original.py`. Les caches `__pycache__`,
`.pyc` et `.pyo` sont exclus. Les extensions du prototype et les résultats simulés
ne sont pas des ressources externes de cet inventaire.

Depuis `reich_experiment_v2/` :

```sh
nix develop -c python verify_provenance.py
nix develop -c python -m unittest discover -s tests -p 'test_provenance.py'
```

La commande fonctionne hors réseau, sans extraire les archives ni importer les
moteurs tiers. Elle produit un rapport JSON ordonné : `ok`, `missing`, `modified`,
`unregistered`, `unreadable` ou `outside_root` pour chaque chemin. Une erreur de
format donne `invalid_registry`. Le code de retour est 0 seulement si toutes les
ressources correspondent à l'inventaire ; sinon il est 1. Le contrôle ne répare ni
le registre ni les fichiers. Les valeurs par défaut sont indépendantes du dossier
courant ; `--root` et `--registry` permettent une vérification sur une copie locale.

Une empreinte confirme l'intégrité par rapport à cette copie locale, pas
l'authenticité éditoriale du document. L'identification bibliographique des cinq
PDF principaux est désormais consignée dans `sources.json` (I2), séparément de
l'inventaire des octets. Le contrat des observations est défini dans
`observations.md` et `observations.json` (I3).
`manifest.json` demeure le contexte historique du prototype.

Chaque entrée contient une politique `redistribution` et sa justification `basis`.
Les statuts possibles sont `authorized` (autorisée), `not_authorized` (non
autorisée) et `not_established` (non établie). En l'absence d'une preuve vérifiée
d'autorisation, toutes les ressources actuelles sont `not_established`, y compris
les archives du prototype susceptibles de contenir du code tiers. Ce statut ne
constitue pas une affirmation d'interdiction. Un contrôle d'intégrité réussi ne
donne aucune permission de redistribution. L'export documentaire I4 décrit
ci-dessous exclut les deux derniers statuts.

Toute mise à jour d'empreinte exige une revue de l'origine du nouveau fichier et
de la raison de son changement, suivie d'une modification explicite du registre
et d'une nouvelle vérification. Une autorisation doit être accompagnée de sa
preuve dans `basis` avant changement du statut. Ne pas remplacer automatiquement
les empreintes après un échec : conserver les ressources de référence et examiner
l'écart en premier lieu.

## Sources scientifiques identifiées — catalogue version 1

La revue locale du texte de la première page de chaque PDF établit les
correspondances suivantes. Les titres complets figurent dans `sources.json`.

| Identifiant | Fichier sous `reich_study/` | Preuve, page PDF 1 | Version locale |
| --- | --- | --- | --- |
| `reich-preprint` | `2026.03.11.711219v2.full.pdf` | Titre, DOI, date et avertissement sur l'évaluation par les pairs | v2, publiée le 13 octobre 2026 ; SHA-256 |
| `SI1` | `media-1.pdf` | En-tête « Supplementary Information section 1 » | SHA-256 du contenu |
| `SI2` | `media-3.pdf` | En-tête « Supplementary Information section 2 » | SHA-256 du contenu |
| `SI3` | `media-5.pdf` | En-tête « Supplementary Information section 3 » | SHA-256 du contenu |
| `SI4` | `media-7.pdf` | En-tête « Supplementary Information section 4 » | SHA-256 du contenu |

Le DOI affiché est `10.64898/2026.03.11.711219`. Le numéro v2 provient du
nom local et du manifeste historique ; la date est affichée sur la première
page. Celle-ci précise que le préprint n'a pas été certifié par évaluation par
les pairs. Le catalogue emploie donc `preprint_not_peer_reviewed`, y compris
pour ses suppléments : ce statut décrit les documents fournis, sans prétendre
connaître leur éventuel statut éditorial ultérieur.

Pour SI1–SI4, aucune date ou révision autonome n'est établie. Leur version
locale est `sha256:<empreinte>`, `posted_date` est nul et `parent_id` relie le
supplément au préprint fourni. Cette association locale n'est pas une
certification indépendante que chaque supplément a été publié à la date du
préprint. Une modification de leurs octets exige une nouvelle version de contenu.

Depuis `reich_experiment_v2/`, exécuter :

```sh
nix develop -c python verify_sources.py
nix develop -c python -m unittest discover -s tests -p 'test_sources.py'
```

Le contrôle vérifie le schéma, les identités, leur parenté, les preuves paginées
déclarées, l'accord des empreintes avec I1 et les octets des cinq PDF. Il retourne
0 seulement si tout concorde, sinon 1 avec diagnostic JSON. Il ne réinterprète
pas le texte des PDF : la lecture initiale a été effectuée avec `pdftotext`,
sans extraction des archives. Aucune dépendance PDF n'est nécessaire aux tests.
Les assertions scientifiques des documents, leur authenticité externe et les
conditions de redistribution ne sont pas validées par ce contrôle. Les
politiques I1 demeurent inchangées.

## Export documentaire local — I4

Depuis `reich_experiment_v2/`, choisir un chemin ZIP inexistant dans un dossier
déjà présent, puis exécuter :

```sh
nix develop -c python export_public.py --output /tmp/paleogen-m1-public.zip
nix develop -c python -m unittest discover -s tests -p 'test_public_export.py'
```

La commande fonctionne hors réseau. `--root` permet de désigner une autre copie
locale ; par défaut la racine est déduite du script, indépendamment du dossier
courant. Elle retourne 0 sur succès, 1 avec un diagnostic JSON en cas d'échec
d'export (2 pour des arguments de commande invalides). Une destination existante
est refusée ; aucun fichier de référence n'est remplacé. Les destinations sous
`reich_study/` et `reich_experiment_v2/source/` sont interdites.

L'archive conserve les chemins relatifs du dépôt et contient exactement ces
documents sélectionnés :

- `docs/science/observations.json` et `docs/science/observations.md` ;
- `docs/science/provenance.json` et `docs/science/provenance.md` ;
- `docs/science/sources.json`.

Les ressources externes du registre ne sont ajoutées que si leur statut est
`authorized`, leur justification non vide, leur contenu présent et leur SHA-256
conforme. Les liens symboliques, y compris dans les dossiers parents d'un fichier
sélectionné, sont refusés. Il n'existe aucune option pour contourner la politique.
Avec le registre actuel, **aucun des 32 contenus externes n'est inclus**. Leurs
chemins, empreintes et politiques restent décrits dans les métadonnées ; leurs
octets ne sont pas distribués. Une ressource exclue peut manquer sans empêcher
l'export documentaire, et son contenu n'est pas lu pour construire l'archive.
Une nouvelle ressource externe détectée mais non inventoriée est également
exclue, avec le motif `not_inventoried`.

`export_manifest.json`, schéma 1, liste les chemins et SHA-256 réellement inclus,
ainsi que les exclusions motivées. Il ne contient pas sa propre empreinte. Le
contrat et le registre sont validés avant création de la destination. Les octets
contrôlés sont ceux écrits dans le ZIP. Ordre, dates et permissions internes sont
fixes : à entrées et environnement de compression identiques, le ZIP est identique.
La commande n'ajoute aucun horodatage d'exécution ni chemin absolu de machine au
manifeste. Elle ne parcourt pas globalement le dépôt : fichiers personnels, caches,
résultats et simulateurs ne sont pas sélectionnés implicitement.

Cet export constitue un paquet documentaire avec ressources éventuellement
autorisées, pas une distribution exécutable PaleoGen-RL v0.1. Les commandes de
validation citées dans les documents supposent le dépôt de développement et ne
sont pas embarquées dans ce paquet. Il ne règle pas la licence globale du futur
projet public et n'effectue aucune publication distante. Les garanties M10/M11
restent à établir. Les autorisations supplémentaires ne peuvent venir que d'une
revue explicite du registre, jamais du succès d'un test d'export.
