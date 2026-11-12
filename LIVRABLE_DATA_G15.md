# Livrable Data — groupe G15

Hackathon Givaudan, thème 02 : plateforme de commande intelligente.
Document de synthèse de la brique Data. Tous les chiffres renvoient à un fichier du dépôt.

## 0. Présentation

**Le prototype.** Un client décrit son projet en texte libre (« un yaourt à la fraise »).
L'assistant :

1. comprend le type de produit, les arômes et les contraintes ;
2. étudie les produits du marché les plus proches ;
3. propose 3 pistes d'arômes, justifiées par ce marché ;
4. rédige le brief de la piste choisie ;
5. prépare un brouillon de demande d'échantillons, jamais envoyé.

**Vocabulaire.** Chaque terme a un seul sens dans ce document.

| Terme                  | Sens                                                                                                         |
| ---------------------- | ------------------------------------------------------------------------------------------------------------ |
| Division               | Flavors (arômes) ou Fragrance (parfums).                                                                     |
| Type de produit        | Le produit du client : boisson, yaourt, glace… (champ `compris.type_produit`).                               |
| Famille                | Le groupe d'un produit du catalogue : boissons aromatisées, boissons protéinées… (colonne `query_category`). |
| Arôme principal        | Le 1er goût compris (champ `compris.arome`).                                                                 |
| Cas entièrement réussi | Un cas de validation qui remplit les 8 critères à la fois (section 4).                                       |

**Équipe Data.**

| Membre        | Travail visible dans l'historique Git                                                                                                                                                                                                                                                                                      |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Meryem Lizoul | Tout le dossier [data-brique/](https://github.com/Givaudan-Hackathon/hackathon-app/tree/docs/livrable-data-g15/data-brique) : données, pipeline, moteurs V1 → V2.3, benchmark, validation, API, applis Streamlit, docs.                                                                                                    |
| Owen Lambert  | Compte Git `justeowen`. Service RAG du dossier [rag/](https://github.com/Givaudan-Hackathon/hackathon-app/tree/docs/livrable-data-g15/rag), importé du fork `example-rag` (FastAPI + ChromaDB + Ollama), [PR #16](https://github.com/Givaudan-Hackathon/hackathon-app/pull/16). Ce service n'est pas appelé par le moteur. |

**Date.** 12/11/2026.

**Versions.**

| Version           | Où                                                                                                                         | État                                              |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `v2.2.5-contexte` | [PR #18](https://github.com/Givaudan-Hackathon/hackathon-app/pull/18), tête `0db9b30`                                      | Fusionnée dans `develop` (commit `c670bcf`).      |
| `v2.3.0-affiner`  | Branche [`feature/data-affiner`](https://github.com/Givaudan-Hackathon/hackathon-app/tree/feature/data-affiner), `569fc85` | En ligne sur l'API (port 8000). Pas encore de PR. |

## 1. Données

**Sources.**

- Open Food Facts : export parquet officiel, révision figée `99d3492`. Licence ODbL 1.0 / DbCL.
- Open Beauty Facts : même export, même révision. Licence ODbL 1.0 / DbCL.
- IFRA, Sirene, commandes : étudiées, non intégrées au moteur. Voir l'inventaire.

**Volumes.**

| Jeu                                                                                                                                                            | Lignes |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| Catalogue Flavors complet, utilisé par le moteur ([flavors_catalogue_complet.csv](data-brique/data/processed/catalogue_complet/flavors_catalogue_complet.csv)) | 8 943  |
| Échantillon v1 : 1 000 Flavors + 1 193 Fragrance ([sample_v1.csv](data-brique/data/processed/sample_v1.csv))                                                   | 2 193  |
| Échantillon v0, API `/search`, gardé pour comparaison ([off_obf_sample_v0.csv](data-brique/data/raw/off_obf_sample_v0.csv))                                    | 1 042  |

Filtres communs : vendu en France, langue `fr`, produit non obsolète. Flavors : les ingrédients
citent un arôme. Détail dans [sample_v1.meta.json](data-brique/data/processed/sample_v1.meta.json).

**Qualité avant / après (Flavors, v0 → v1).**

| Indicateur          | v0  | v1   |
| ------------------- | --- | ---- |
| Mention d'un arôme  | 35% | 100% |
| Vendus en France    | 73% | 100% |
| Langue `fr`         | 76% | 100% |
| Ingrédients remplis | 97% | 100% |

Source : [comparaison_v0_v1.md](data-brique/docs/comparaison_v0_v1.md). Le 100 % d'arôme vient du
filtre : il est obtenu par construction.

**Banque de références DEMO.** 30 références fictives (DEMO-001 à DEMO-030), inspirées des gammes
publiques TasteEssentials, TasteCollections et TasteSolutions. Ce ne sont pas de vraies
références Givaudan. Fichiers : [banque_references_demo.csv](data-brique/data/processed/banque_references_demo.csv)
et [banque_references_demo.meta.json](data-brique/data/processed/banque_references_demo.meta.json).

**Preuves.**

- [inventaire_sources.md](data-brique/docs/inventaire_sources.md) : sources, licences, accès, biais.
- [quality_report.md](data-brique/docs/quality_report.md) : taux de remplissage par champ et par famille.
- [LICENSE_DONNEES.md](data-brique/data/LICENSE_DONNEES.md) : attribution ODbL.
- Aucune donnée personnelle : les champs contributeurs sont exclus à l'extraction.

## 2. Pipeline

| Étape                   | Script                                                                           | Ce qu'il fait                                                                               |
| ----------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Extraction              | [extract_exports.py](data-brique/scripts/extract_exports.py)                     | Télécharge les exports à la révision figée, puis les filtre en local avec DuckDB.           |
| Échantillon + catalogue | [build_sample_v1.py](data-brique/scripts/build_sample_v1.py)                     | 200 Flavors par famille (graine 42), Fragrance exhaustive, catalogue complet. Déterministe. |
| Qualité                 | [quality_report.py](data-brique/scripts/quality_report.py)                       | Écrit `quality_report.md`.                                                                  |
| Banque DEMO             | [creer_banque_references.py](data-brique/scripts/creer_banque_references.py)     | Écrit la banque de 30 références fictives et son `.meta.json`.                              |
| Indexation              | [indexer_catalogue_complet.py](data-brique/scripts/indexer_catalogue_complet.py) | Vecteurs bge-m3 des 8 943 produits : 54 min sur le CPU de l'équipe, reprise possible.       |

Commandes (depuis `data-brique/`) :

```bash
.venv/Scripts/python scripts/extract_exports.py
.venv/Scripts/python scripts/build_sample_v1.py
.venv/Scripts/python scripts/quality_report.py
.venv/Scripts/python scripts/indexer_catalogue_complet.py
```

**Reproduction testée.** [reproduire.md](data-brique/docs/reproduire.md) : toutes les commandes
ont été exécutées sur une copie neuve du dépôt (commit `569fc85`). Le guide donne les versions
(Python 3.12.10, Ollama 0.40.16, ID des modèles), le poste et les problèmes connus.

## 3. Modèle

**Principe : RAG local, sans entraînement.**

- **Recherche :** bge-m3 (via Ollama) compare la demande aux 8 943 produits du catalogue.
- **Compréhension :** règles d'abord. llama3.2:3b (via Ollama) n'est appelé que s'il reste un mot
  inconnu.
- **Local :** tout tourne sur le PC, sans API externe.

**Ce que fait l'assistant.**

1. **Étude de marché :** les 50 produits les plus proches, comptage des arômes et des associations.
2. **3 pistes :** l'arôme seul, l'association la plus fréquente, une association rare.
3. **Références DEMO :** une référence fictive par arôme, ou « création sur mesure » s'il n'y en a pas.
4. **Garde-fous :** aucune marque citée, aucun prix, chaque chiffre vient de l'étude de marché.
5. **Affiner (V2.3) :** avant les pistes, 2 questions (goût, intensité). Les choix sont tirés des
   données, avec toujours « Je ne sais pas, proposez-moi ».

**Benchmark des modèles.** 15 briefs, run du 10/11/2026. Rapport :
[Benchmark_llm.pdf](data-brique/benchmark/Benchmark_llm.pdf) ; mêmes résultats en Markdown, avec
les mesures brutes : [resultats.md](data-brique/benchmark/resultats.md).

| Recherche           | Famille attendue dans le top 5 | Famille attendue au rang 1 | Précision top 5 | Temps / requête |
| ------------------- | ------------------------------ | -------------------------- | --------------- | --------------- |
| TF-IDF (baseline)   | 83 %                           | 67 %                       | 57 %            | 2 ms            |
| nomic-embed-text    | 100 %                          | 83 %                       | 77 %            | 77 ms           |
| **bge-m3 (retenu)** | 100 %                          | 100 %                      | 87 %            | 79 ms           |
| mxbai-embed-large   | 100 %                          | 75 %                       | 63 %            | 94 ms           |

| Compréhension            | Division | Arôme principal | Temps / brief |
| ------------------------ | -------- | --------------- | ------------- |
| Mots-clés (baseline)     | 93 %     | —               | < 1 ms        |
| qwen2.5:1.5b             | 93 %     | 87 %            | 1,8 s         |
| qwen2.5:3b               | 100 %    | 87 %            | 2,9 s         |
| **llama3.2:3b (retenu)** | 100 %    | 100 %           | 4,0 s         |

**Versions.** Détail dans [v2_notes.md](data-brique/docs/v2_notes.md).

| Version | Apport                                                                                      |
| ------- | ------------------------------------------------------------------------------------------- |
| V1      | Baseline TF-IDF + mots-clés ([baseline_v1.ipynb](data-brique/notebooks/baseline_v1.ipynb)). |
| V2      | llama3.2:3b + bge-m3, mêmes sorties que V1.                                                 |
| V2.1    | Pistes d'arômes, sans produit ni marque.                                                    |
| V2.2    | Assistant conversationnel : pistes, brief, brouillon d'échantillons.                        |
| V2.2.1  | Types de produit, références DEMO, mode rapide, catalogue complet.                          |
| V2.2.2  | Corrections de la revue Codex de la PR #18.                                                 |
| V2.2.3  | Corrections par mécanismes après la validation 30 cas.                                      |
| V2.2.4  | Corrections de la 3e revue Codex.                                                           |
| V2.2.5  | Mots de lieu et de contexte (« au bord de l'eau »).                                         |
| V2.3    | Étape Affiner, synonymes (limette = citron vert).                                           |

## 4. Métriques : 30 cas de référence et 10 cas jamais vus

**Protocole.** [validation_30_cas.md](data-brique/docs/validation_30_cas.md)

- **Deux jeux, deux rôles.**
  - **Les 30 cas de référence** ([cas_reference_30.csv](data-brique/benchmark/cas_reference_30.csv))
    ont été écrits avant la 1re mesure et n'ont jamais été modifiés. Ils ont servi à diagnostiquer
    les échecs, puis à corriger des **mécanismes** du moteur (vocabulaire, types, intentions,
    marques), jamais un cas précis. Ils ont ensuite servi à mesurer. Ce jeu n'est donc pas
    indépendant des corrections.
  - **Les 10 cas jamais vus** ([cas_finaux_10.csv](data-brique/benchmark/cas_finaux_10.csv)) ont été
    fournis après les corrections, puis mesurés sans rien modifier, ni avant ni après. C'est le
    seul jeu indépendant.
  - D'où l'écart : 26/30 sur le jeu qui a guidé les corrections, 6/10 sur le jeu indépendant.
- **Mesure.** Chaque cas est le 1er message d'une nouvelle session.
- **8 critères stricts :** type de produit, arômes, arôme principal, contraintes, comportement,
  aucune marque, aucun chiffre inventé, aucun prix.
- **Étape Affiner :** si le 1er message donne `etape = affiner`, la mesure répond « Je ne sais
  pas, proposez-moi » et juge le comportement sur la 2e réponse.

**30 cas de référence : avant / après les corrections.**

| Critère                     | Avant (V2.2.2) | Après (v2.3.0-affiner) |
| --------------------------- | -------------- | ---------------------- |
| Type de produit             | 27/30          | 27/30                  |
| Arôme(s), tous trouvés      | 25/30          | 30/30                  |
| Arôme principal             | 23/30          | 30/30                  |
| Contraintes                 | 29/30          | 29/30                  |
| Comportement                | 21/30          | 30/30                  |
| Marque, chiffre, prix       | 30/30          | 30/30                  |
| **Cas entièrement réussis** | **18/30**      | **26/30**              |

Cas perdus : aucun. Échecs restants : C05, C11, C21, C24. C11 et C21 sont discutables (réponse
utile, critère strict). Sorties : [validation_30_cas_avant.csv](data-brique/benchmark/sorties/validation_30_cas_avant.csv),
[validation_30_cas.csv](data-brique/benchmark/sorties/validation_30_cas.csv).

Version « avant » : `v2.2.2-references`. Version « après » : `v2.3.0-affiner` (commit `569fc85`).

**10 cas jamais vus : 6/10 cas entièrement réussis**, mesurés sur `v2.2.3-mecanismes` (commit
`75d259d`). Détail : [validation_cas_finaux.md](data-brique/benchmark/sorties/validation_cas_finaux.md).
Les 4 échecs :

| Cas | Message                                                            | Échec                                                            |
| --- | ------------------------------------------------------------------ | ---------------------------------------------------------------- |
| F01 | « on prépare un ice tea maison à la framboise, sans sucre ajouté » | « Ice Tea » est aussi une marque : le type de produit est perdu. |
| F07 | « une sauce barbecue fumée »                                       | Le goût est absorbé par le nom du produit : relance.             |
| F09 | « quels sont vos délais pour un échantillon ? »                    | Classée demande d'échantillons, pas question.                    |
| F10 | « je veux le goût du Nutella »                                     | Marque absente du catalogue : relance, pas hors sujet.           |

Ces 4 cas ne sont pas corrigés : la décision revient au Product ([ticket #29](https://github.com/Givaudan-Hackathon/hackathon-app/issues/29)).

**Comparaison des versions.** Chaque ligne mesure un seul critère. La division et l'arôme
principal sont 2 des 8 critères : un cas peut les réussir et échouer sur un autre critère. Le
« cas entièrement réussi » est donc toujours inférieur ou égal à eux : ce n'est pas une
régression. V1 et V2.1 ne produisent pas tous les champs : leur « cas entièrement réussi » n'est
pas mesurable (—).

30 cas de référence (même run que `v2.3.0-affiner`, [validation_30_cas.csv](data-brique/benchmark/sorties/validation_30_cas.csv)) :

| Critère mesuré                             | V1      | V2.1   | v2.3.0-affiner |
| ------------------------------------------ | ------- | ------ | -------------- |
| Division                                   | 26/30   | 29/30  | 29/30          |
| Arôme principal                            | —       | 29/30  | 30/30          |
| Pistes ou relance (26 cas qui l'attendent) | —       | 25/26  | 26/26          |
| Cas entièrement réussi                     | —       | —      | 26/30          |
| Temps moyen par cas                        | < 0,1 s | 4,95 s | 1,76 s         |

10 cas jamais vus (run du commit `75d259d`, [validation_cas_finaux.csv](data-brique/benchmark/sorties/validation_cas_finaux.csv)) :

| Critère mesuré                            | V1      | V2.1   | v2.2.3-mecanismes |
| ----------------------------------------- | ------- | ------ | ----------------- |
| Division                                  | 6/10    | 8/10   | 9/10              |
| Arôme principal                           | —       | 7/10   | 9/10              |
| Pistes ou relance (8 cas qui l'attendent) | —       | 7/8    | 7/8               |
| Cas entièrement réussi                    | —       | —      | 6/10              |
| Temps moyen par cas                       | < 0,1 s | 3,24 s | 2,15 s            |

`v2.3.0-affiner` n'a pas été mesurée sur les 10 cas jamais vus.

**Temps de `v2.3.0-affiner` (30 cas).** Moyenne 1,76 s, médiane 0,95 s, temps du 1er message de
chaque cas. Le modèle est appelé pour 5 cas sur 30 : 7,30 s en moyenne ces fois-là, 0,65 s
sinon. Pour comparaison, `v2.2.5-contexte` mesurait 1,06 s de moyenne et 0,50 s de médiane, sans
l'étape Affiner (même fichier, commit `0db9b30`).

**Tests.** 89 tests pytest ([tests/](https://github.com/Givaudan-Hackathon/hackathon-app/tree/docs/livrable-data-g15/data-brique/tests)), dont les non-régressions des 3 revues
Codex ([test_revue_codex.py](data-brique/tests/test_revue_codex.py),
[test_revue_codex_3.py](data-brique/tests/test_revue_codex_3.py)) et l'étape Affiner
([test_affiner.py](data-brique/tests/test_affiner.py)).

```bash
.venv/Scripts/python -m pytest -q
.venv/Scripts/python benchmark/valider_30_cas.py
.venv/Scripts/python benchmark/valider_30_cas.py --cas benchmark/cas_finaux_10.csv --sortie benchmark/sorties/validation_cas_finaux.csv
```

## 5. API

FastAPI ([api/main.py](data-brique/api/main.py)), port 8000. Swagger automatique sur `/docs`.
Contrat : [contrat_api.md](data-brique/docs/contrat_api.md).

| Route                | Rôle                                                                |
| -------------------- | ------------------------------------------------------------------- |
| `GET /sante`         | État de l'API. Renvoie `baseline-v1` (contrat V1 inchangé).         |
| `POST /recommander`  | V1 : brief → division, champ `application`, 5 produits recommandés. |
| `POST /conversation` | V2 : un message par appel → objet complet de la conversation.       |

**Contrat V2.** Entrée : `{session_id, message, piste_id}`. Chaque réponse contient l'objet
complet : `session_id`, `etape`, `intention`, `reponse`, `compris`, `questions`, `pistes`,
`solutions`, `brief`, `echantillons`, `version_modele`, `attribution`. Aucun champ renommé ni
supprimé ; la nouvelle valeur `etape = affiner` doit être gérée par le front (voir « Changements
pour le front (V2.3) » dans le contrat).

**Exemple réel** (API locale, `v2.3.0-affiner`, 12/11/2026). 1er message « un yaourt à la fraise » :

```json
{
  "etape": "affiner",
  "pistes": [],
  "questions": [
    {
      "id": "gout",
      "question": "Quel goût de fraise imaginez-vous ?",
      "choix": [
        "fraise des bois",
        "fraise mûre",
        "sucrée",
        "juteuse",
        "Je ne sais pas, proposez-moi"
      ]
    },
    {
      "id": "intensite",
      "question": "Quelle intensité pour le goût fraise ?",
      "choix": [
        "intensité discrète",
        "intensité présente",
        "intensité marquée",
        "Je ne sais pas, proposez-moi"
      ]
    }
  ],
  "version_modele": "v2.3.0-affiner"
}
```

Après « Je ne sais pas, proposez-moi », le choix de la piste `fraise`, puis « je voudrais des
échantillons » :

```json
{
  "etape": "echantillons",
  "echantillons": {
    "type_produit": "yaourt",
    "piste_id": "fraise",
    "aromes": ["fraise"],
    "codes_references": ["DEMO-024"],
    "statut": "brouillon_non_envoye"
  },
  "attribution": "Étude de marché réalisée sur des données d'Open Food Facts (ODbL)"
}
```

(extraits ; les autres champs sont toujours présents)

**Accès.** Tunnel ngrok sur un domaine statique : https://aloof-glorify-epiphany.ngrok-free.dev
(Swagger : https://aloof-glorify-epiphany.ngrok-free.dev/docs). L'URL reste la même tant que le
tunnel est relancé avec ce domaine. En-tête à ajouter : `ngrok-skip-browser-warning: true`.

**Temps de réponse.** 0,3 à 1,2 s via ngrok. Environ 5 s quand le message appelle le modèle
(contrat, section « Obligations et limites (V2) »).

**Applis de démonstration** ([reproduire.md](data-brique/docs/reproduire.md), section 5) :

- port 8501 : [demo_streamlit.py](data-brique/demo_streamlit.py), test du contrat V2 ;
- port 8502 : [demo_parcours.py](data-brique/demo_parcours.py), parcours client complet, questions
  Affiner en boutons.

## 6. Intégration Tech

État au 12/11/2026, d'après les tickets et les PR :

- **Contrat :** la [PR #18](https://github.com/Givaudan-Hackathon/hackathon-app/pull/18) est
  fusionnée dans `develop`. Le ticket [#31](https://github.com/Givaudan-Hackathon/hackathon-app/issues/31)
  prend son contrat comme « contrat de départ à préserver ».
- **Relais NestJS → API Python :** en cours, ticket [#31](https://github.com/Givaudan-Hackathon/hackathon-app/issues/31) (ouvert).
- **Front React :** en cours, ticket [#20](https://github.com/Givaudan-Hackathon/hackathon-app/issues/20)
  et [PR #28](https://github.com/Givaudan-Hackathon/hackathon-app/pull/28) (brouillon).
- **Étape Affiner :** ticket [#30](https://github.com/Givaudan-Hackathon/hackathon-app/issues/30). Elle ne
  bloque pas la 1re intégration ; la valeur `affiner` demandera d'adapter les consommateurs.
- **Validation métier :** ticket [#29](https://github.com/Givaudan-Hackathon/hackathon-app/issues/29) (ouvert).

## 7. Limites

- **Références fictives :** les codes DEMO sont inventés. Aucune vraie référence Givaudan.
- **Hébergement :** l'API tourne sur le PC de l'équipe (CPU), exposée par ngrok. Elle s'arrête
  avec le PC.
- **Pas d'authentification :** l'API de démo est un prototype. Toute personne qui a l'URL peut
  l'appeler.
- **Validation :** les 30 cas ont guidé les corrections ; seul le jeu de 10 cas est indépendant.
- **Cas jamais vus : 6/10.** F01, F07, F09, F10 attendent la décision du Product (ticket #29).
- **Couverture du catalogue :** boissons et desserts aromatisés. Glaces, yaourts aux fruits,
  biscuits, snacks salés et sauces sont hors catalogue : le marché étudié est alors limité, et la
  réponse le dit.
- **Biais de l'échantillon :** quota de 200 par famille, sans lien avec les proportions du marché.
- **Mesure :** critères stricts, un seul message par cas. La conversation est couverte par les
  tests pytest.
- **Sessions :** gardées en mémoire ; un redémarrage de l'API les efface.

## 8. Tableau récapitulatif

| Livrable     | Preuves dans le dépôt                                                                                                                                                                                                                                                                                                                |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1. Données   | [inventaire_sources.md](data-brique/docs/inventaire_sources.md), [quality_report.md](data-brique/docs/quality_report.md), [comparaison_v0_v1.md](data-brique/docs/comparaison_v0_v1.md), [LICENSE_DONNEES.md](data-brique/data/LICENSE_DONNEES.md)                                                                                   |
| 2. Pipeline  | [scripts/](https://github.com/Givaudan-Hackathon/hackathon-app/tree/docs/livrable-data-g15/data-brique/scripts), [reproduire.md](data-brique/docs/reproduire.md)                                                                                                                                                                     |
| 3. Modèle    | [Benchmark_llm.pdf](data-brique/benchmark/Benchmark_llm.pdf), [resultats.md](data-brique/benchmark/resultats.md), [v2_notes.md](data-brique/docs/v2_notes.md), [src/](https://github.com/Givaudan-Hackathon/hackathon-app/tree/docs/livrable-data-g15/data-brique/src), [baseline_v1.ipynb](data-brique/notebooks/baseline_v1.ipynb) |
| 4. Métriques | [validation_30_cas.md](data-brique/docs/validation_30_cas.md), [benchmark/sorties/](https://github.com/Givaudan-Hackathon/hackathon-app/tree/docs/livrable-data-g15/data-brique/benchmark/sorties), [tests/](https://github.com/Givaudan-Hackathon/hackathon-app/tree/docs/livrable-data-g15/data-brique/tests)                      |
| 5. API       | [api/main.py](data-brique/api/main.py), [contrat_api.md](data-brique/docs/contrat_api.md), Swagger `/docs`                                                                                                                                                                                                                           |

| Suivi                           | Lien                                                                          |
| ------------------------------- | ----------------------------------------------------------------------------- |
| PR #18 (V1 → V2.2.5, fusionnée) | https://github.com/Givaudan-Hackathon/hackathon-app/pull/18                   |
| Branche V2.3                    | https://github.com/Givaudan-Hackathon/hackathon-app/tree/feature/data-affiner |
| Ticket #29 : validation métier  | https://github.com/Givaudan-Hackathon/hackathon-app/issues/29                 |
| Ticket #30 : étape Affiner      | https://github.com/Givaudan-Hackathon/hackathon-app/issues/30                 |
| Ticket #31 : relais NestJS      | https://github.com/Givaudan-Hackathon/hackathon-app/issues/31                 |
