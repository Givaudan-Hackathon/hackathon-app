# Benchmark des modèles Ollama appliqués au moteur

Objectif : choisir les modèles locaux de la V2 du moteur « brief client → recommandation », pour de
petits clients Flavors qui décrivent leur projet avec leurs mots, sans jargon.

Persona : **Lou**, cofondatrice d'une marque de desserts végétaux, qui cherche « un goût pistache
gourmand, pas trop sucré ».

- Script : `python benchmark/run_benchmark.py` (depuis `data-brique/`, Ollama lancé localement).
- Jeu de test : [`briefs_test.csv`](briefs_test.csv), 15 briefs.
- Mesures brutes : [`sorties/mesures.md`](sorties/mesures.md) et `mesures.json`, plus le détail par brief
  dans `details_recherche.csv` et `details_llm.csv`.
- Date du run : 10/11/2026.

## Configuration du PC

| Élément        | Valeur                                                                        |
| -------------- | ----------------------------------------------------------------------------- |
| CPU            | Intel Core i5-13420H (13e génération), 8 cœurs / 12 threads                   |
| RAM            | 15,6 Go                                                                       |
| GPU            | Aucun GPU dédié (Intel UHD intégré, non utilisé par Ollama : `size_vram = 0`) |
| Système        | Windows 11 Pro (build 26200)                                                  |
| Logiciels      | Ollama 0.40.16, Python 3.12.10                                                |
| Modèles Ollama | Quantifications par défaut : embeddings en F16, LLM en Q4_K_M                 |

Tous les calculs tournent donc **sur CPU**. Les temps dépendent de la charge du PC : pendant le run,
Edge et VS Code étaient ouverts.

## Jeu de test

Les 15 briefs sont écrits en langage courant :

- **12 briefs Flavors :**
  - le brief de Lou ;
  - les 3 briefs Flavors de la baseline ;
  - 3 briefs difficiles avec synonymes :
    - « shake protéiné » : le catalogue parle de _whey_ ou de _protein_ ;
    - « sans lait » : il faut comprendre _végétal_ ;
    - « goût d'enfance » : il faut deviner _vanille_ ou _caramel_ ;
  - 5 briefs courants : limonade citron, lait chocolaté, soja vanille, eau fruits rouges, yaourt coco.
- **3 briefs Fragrance** (lavande, agrumes, floral) : ils servent à vérifier la détection de division.

Pour chaque brief, `briefs_test.csv` donne la division attendue, la `query_category` attendue et
l'arôme attendu (avec des alternatives séparées par `|`).

## Partie 1 — Recherche (embeddings) sur le catalogue Flavors

Le catalogue est la partie Flavors de `sample_v1.csv` (1 000 produits). La recherche est évaluée
sur les 12 briefs Flavors.

**Texte indexé :**

- **Embeddings :** nom + catégorie + 300 premiers caractères des ingrédients.
- **TF-IDF :** texte complet, identique à la baseline (`src/moteur_v1.py`).

**Mise en œuvre :**

- **Préfixes :** chaque modèle reçoit les préfixes recommandés par sa fiche Ollama (`search_query:` /
  `search_document:` pour nomic, consigne de requête pour mxbai, aucun pour bge-m3).
- **Similarité :** cosinus.
- **Cache :** les vecteurs sont dans `benchmark/cache/` (non versionné). La clé de cache combine le
  modèle, son digest Ollama et les textes indexés.

| Modèle            | Catégorie attendue dans le top 5 | Catégorie attendue au rang 1 | Précision top 5¹ | Arôme dans le nom (top 5)² | Indexation (1 000 produits) | Temps moyen par requête |
| ----------------- | -------------------------------- | ---------------------------- | ---------------- | -------------------------- | --------------------------- | ----------------------- |
| TF-IDF (baseline) | 83 %                             | 67 %                         | 57 %             | 100 %                      | 0,5 s                       | 2 ms                    |
| nomic-embed-text  | **100 %**                        | 83 %                         | 77 %             | **100 %**                  | 157 s                       | 77 ms                   |
| **bge-m3**        | **100 %**                        | **100 %**                    | **87 %**         | 92 %                       | 588 s                       | 79 ms                   |
| mxbai-embed-large | **100 %**                        | 75 %                         | 63 %             | 83 %                       | 736 s                       | 94 ms                   |

¹ Part des 5 produits recommandés qui appartiennent à la catégorie attendue (moyenne sur les briefs).
² Part des briefs dont au moins un des 5 produits porte l'arôme attendu dans son nom.

Avec 12 briefs, un brief pèse 8,3 points : les écarts de moins de 10 points ne sont pas
significatifs.

**Échecs au rang 1 :**

- **TF-IDF :** 4 briefs ratés (pois/protéiné, goût d'enfance, fruits rouges, yaourt coco). Pour 2
  d'entre eux, aucun produit de la bonne catégorie n'est dans le top 5.
- **nomic-embed-text :** lait chocolaté et eau fruits rouges, tous deux renvoyés vers des desserts.
- **mxbai-embed-large :** boisson protéinée pois, boisson sans lait (classée en boissons lactées
  parce que le brief contient le mot « lait ») et lait chocolaté.

## Partie 2 — Extraction du brief par LLM

Le LLM transforme le brief en JSON `{division, application, aromes, contraintes}`. Le schéma JSON est
imposé à Ollama (paramètre `format`, `division` ∈ {flavors, fragrance}), avec `temperature = 0` et
`seed = 42`. Le prompt est en français et identique pour les 3 modèles.

L'évaluation porte sur les 15 briefs :

- **JSON valide :** la sortie se parse et respecte le schéma.
- **Arôme principal correct :** le 1er élément de `aromes` correspond à l'arôme attendu, en
  comparant des mots entiers sans accents ni pluriel. « noix de coco » est accepté pour « coco » ;
  « anis » est refusé pour « vanille ».

| Modèle                       | Division correcte | JSON valide | Arôme principal correct | Temps moyen par brief | Chargement du modèle |
| ---------------------------- | ----------------- | ----------- | ----------------------- | --------------------- | -------------------- |
| Mots-clés (baseline, rappel) | 93 %              | —           | —                       | < 1 ms                | —                    |
| qwen2.5:1.5b                 | 93 %              | 100 %       | 87 %                    | **1,8 s**             | 5 s                  |
| qwen2.5:3b                   | **100 %**         | 100 %       | 87 %                    | 2,9 s                 | 9 s                  |
| **llama3.2:3b**              | **100 %**         | 100 %       | **100 %**               | 4,0 s                 | 12 s                 |

**Erreurs relevées :**

- **Mots-clés (baseline) :** « limonade pétillante au citron » ne contient aucun mot-clé, le brief
  part en `indeterminee`.
- **qwen2.5:1.5b :**
  - il classe « savons faits main » en _flavors_ ;
  - il extrait « fruits » pour le yaourt à boire fraise, et « anis » pour le goût d'enfance ;
  - il invente des contraintes absentes du brief (« origine française », « prix raisonnable »).
- **qwen2.5:3b :**
  - « limon » au lieu de « citron » pour la limonade ;
  - « fraise » au lieu de « fruits rouges » pour l'eau aromatisée ;
  - il range « pas trop sucré » dans les arômes au lieu des contraintes.
- **llama3.2:3b :**
  - l'arôme principal est toujours juste, mais il ajoute souvent des arômes secondaires inventés :
    « froide » pour la pistache, « caramel, vanille » pour le lait chocolaté, « citron, vanille »
    pour le parfum fleuri ;
  - il reformule parfois l'application (« décoration de desserts végétaux »).
- **Biais du prompt :** l'exemple d'application « biscuit » donné dans le prompt a été recopié par
  qwen2.5:3b pour Lou et par qwen2.5:1.5b pour le goût d'enfance. À corriger en V2 (exemples hors
  sujet, ou pas d'exemple).

`contraintes` et `application` ne sont pas notés automatiquement : la lecture des sorties montre que
ce sont les champs les moins fiables, quel que soit le modèle.

## Trois exemples concrets

Top 3 de chaque modèle d'embedding (nom du produit, catégorie, score cosinus), puis la sortie de
chaque LLM.

### 1. Lou — « Je lance une marque de desserts végétaux et je cherche un goût pistache gourmand, pas trop sucré »

Attendu : `desserts_aromatises`, arôme pistache.

| Modèle            | Rang 1                                            | Rang 2                                                                    | Rang 3                                                              |
| ----------------- | ------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| TF-IDF            | Flan entremets Pistache (desserts) 0,10           | Boisson rafraîchissante aux extraits végétaux (boissons aromatisées) 0,10 | Milkshake minceur chocolat (boissons lactées) 0,07                  |
| nomic-embed-text  | Flan entremets Pistache (desserts) 0,75           | Dessert végétal soja au chocolat (boissons végétales) 0,74                | Dessert végétal soja au chocolat, doublon (boissons végétales) 0,74 |
| bge-m3            | Flan entremets Pistache (desserts) 0,57           | Dessert végétal au lait de coco (desserts) 0,56                           | Gourmand & Végétal Ananas (desserts) 0,54                           |
| mxbai-embed-large | Dessert végétal Noisettes Amandes (desserts) 0,74 | Flan entremets Pistache (desserts) 0,74                                   | Dessert végétal soja au chocolat (boissons végétales) 0,73          |

| LLM          | Sortie                                                                                                                                                                           |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| qwen2.5:1.5b | `{"division": "flavors", "application": "dessert", "aromes": ["pistache", "gourmand"], "contraintes": ["vegétal", "non sucré"]}`                                                 |
| qwen2.5:3b   | `{"division": "flavors", "application": "biscuit", "aromes": ["pistache", "gourmand", "pas trop sucré"], "contraintes": []}`                                                     |
| llama3.2:3b  | `{"division": "flavors", "application": "décoration de desserts végétaux", "aromes": ["pistache", "gourmand", "froide"], "contraintes": ["pas trop sucré", "origine végétale"]}` |

Tous les modèles trouvent le flan pistache, mais c'est le **seul** produit pistache du catalogue
de test : `sample_v1` n'en contient qu'un, contre 30 dans le catalogue complet Flavors.

bge-m3 est le seul à remplir son top 3 de desserts végétaux, ce qui répond bien au projet de Lou.
qwen2.5:1.5b donne la meilleure décomposition, mais transforme « pas trop sucré » en « non sucré ».

### 2. Synonyme — « une petite crème qui a le goût d'enfance, comme chez mamie »

Attendu : `desserts_aromatises`, arôme vanille ou caramel.

| Modèle            | Rang 1                                            | Rang 2                                                 | Rang 3                                                   |
| ----------------- | ------------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------- |
| TF-IDF            | Strawberry (boissons aromatisées) 0,09            | Whey protéines (boissons protéinées) 0,09              | Milical Pur Protéines Vanille (boissons protéinées) 0,08 |
| nomic-embed-text  | Petits Filous framboise & vanille (desserts) 0,69 | Petits Filous myrtille abricot (boissons lactées) 0,68 | Sirop Pêche Giffard (boissons aromatisées) 0,67          |
| bge-m3            | Crème brûlée 4x100g (desserts) 0,57               | Crème brûlée (desserts) 0,57                           | Mini Yab fraise banane (boissons lactées) 0,56           |
| mxbai-embed-large | Petits Filous framboise & vanille (desserts) 0,75 | Petits Filous myrtille abricot (boissons lactées) 0,74 | Mini Yop fraise (boissons lactées) 0,70                  |

| LLM          | Sortie                                                                                                                            |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| qwen2.5:1.5b | `{"division": "flavors", "application": "biscuit", "aromes": ["anis", "coco", "chocolat", "clou de girofle"], "contraintes": []}` |
| qwen2.5:3b   | `{"division": "flavors", "application": "crème", "aromes": ["vanille", "chocolat"], "contraintes": []}`                           |
| llama3.2:3b  | `{"division": "flavors", "application": "crème", "aromes": ["vanille", "caramel", "cannelle"], "contraintes": []}`                |

Ce brief ne contient aucun mot du catalogue, et le TF-IDF échoue complètement. bge-m3 est le seul
modèle d'embedding à proposer des crèmes desserts, et la crème brûlée correspond bien à un goût
caramel-vanille d'enfance. llama3.2:3b donne la meilleure interprétation (vanille, caramel), qui
permettrait de relancer la recherche avec ces arômes.

### 3. Synonyme — « un shake protéiné à prendre après la muscu, goût chocolat »

Attendu : `boissons_proteinees`, arôme chocolat.

| Modèle            | Rang 1                                                 | Rang 2                                            | Rang 3                                                 |
| ----------------- | ------------------------------------------------------ | ------------------------------------------------- | ------------------------------------------------------ |
| TF-IDF            | Protein Shake 330ML Chocolat 0,09                      | Soy Protein Isolate 90 Biscuit Choco-Caramel 0,08 | Impact Whey Protein, Blueberry and Raspberry 0,08      |
| nomic-embed-text  | Milk-shake Chocolat riche en protéines (Gerlinéa) 0,79 | Protein Shake 330ML Chocolat 0,78                 | Whey Protein goût Chocolat 0,77                        |
| bge-m3            | Protein Shake 330ML Chocolat 0,67                      | Shape Shake Protein, Schokolade 0,67              | Milk-shake Chocolat riche en protéines (Gerlinéa) 0,66 |
| mxbai-embed-large | Milk-shake Chocolat riche en protéines (Gerlinéa) 0,83 | Whey - Goût Chocolat 0,82                         | Whey Protein goût Chocolat 0,81                        |

Les 12 produits de ce tableau sont tous des boissons protéinées.

| LLM          | Sortie                                                                                                                                                |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| qwen2.5:1.5b | `{"division": "flavors", "application": "shake", "aromes": ["chocolat"], "contraintes": ["sucre", "origine française", "santé", "prix raisonnable"]}` |
| qwen2.5:3b   | `{"division": "flavors", "application": "shake", "aromes": ["chocolat", "protéiné"], "contraintes": []}`                                              |
| llama3.2:3b  | `{"division": "flavors", "application": "shake protéiné", "aromes": ["chocolat", "vanille"], "contraintes": []}`                                      |

Tous les modèles réussissent ce brief : le TF-IDF y arrive grâce au mot « chocolat » et au mot
« shake », mais il classe en 3e position une whey myrtille-framboise. Les embeddings relient bien
« protéiné » à _whey_ et _protein_, et ne renvoient que du chocolat. qwen2.5:1.5b invente 4
contraintes qui ne sont pas dans le brief.

## Recommandation pour la V2

1. **Recherche : bge-m3**, à la place du TF-IDF. C'est le seul modèle à 100 % au rang 1, avec la
   meilleure précision top 5 (87 % contre 57 %). Il comprend les synonymes et les briefs sans mot du
   catalogue (« goût d'enfance »), et il est multilingue, ce qui compte pour les noms de produits en
   anglais ou en allemand.
   - **Coût :** l'indexation est lente sur ce PC (10 min pour 1 000 produits, soit environ 1 h 30
     pour les 8 943 produits du catalogue complet). Elle ne se fait qu'une fois, et les vecteurs se
     cachent. La requête coûte environ 80 ms.
   - **Repli :** nomic-embed-text, si le temps d'indexation pose problème (4 fois plus rapide, 100 %
     dans le top 5, mais 83 % au rang 1).
   - mxbai-embed-large n'apporte rien ici : il est le plus lent et a le moins bon rang 1.
2. **Extraction : llama3.2:3b.** C'est le seul modèle à 100 % sur la division et sur l'arôme
   principal, avec 4 s par brief sur CPU, acceptable pour une démo.
   - Ne garder que la division et le **premier** arôme : il ajoute des arômes secondaires inventés.
   - Garder les mots-clés de la baseline en repli si Ollama ne répond pas.
   - qwen2.5:3b reste une alternative plus rapide (2,9 s), mais moins fiable sur l'arôme.
   - qwen2.5:1.5b est écarté : erreur de division sur un savon, contraintes inventées.
3. **Pipeline V2 proposé :**
   1. llama3.2:3b extrait la division et l'arôme principal ;
   2. bge-m3 cherche dans le catalogue de la division, à partir du brief enrichi de l'arôme extrait.
      Exemple pour le goût d'enfance : « crème vanille caramel ».
4. **Données :** indexer le **catalogue complet** Flavors (8 943 produits) plutôt que l'échantillon.
   Avec un seul produit pistache dans `sample_v1`, le brief de Lou ne peut pas recevoir 5
   propositions pertinentes.
5. **Avant la validation de jeudi :**
   - corriger l'exemple « biscuit » du prompt ;
   - noter `contraintes` et `application` ;
   - étendre le jeu de test aux 30 cas de référence, avec une note de pertinence par produit et pas
     seulement par catégorie.

## Limites

- **Taille du jeu :** 15 briefs écrits par l'équipe. C'est un banc d'essai pour comparer les
  modèles entre eux, pas une validation de la qualité finale.
- **Métrique de catégorie :** elle est grossière. Certains produits sont mal rangés dans le
  catalogue : le « Dessert végétal soja au chocolat » est en `boissons_vegetales`, et ce produit
  figure deux fois sous deux codes différents.
- **Temps :** ils sont mesurés sur un seul PC, avec d'autres applications ouvertes.
  - Le chargement de chaque modèle est exclu des temps de requête et donné à part.
  - Le temps d'indexation est celui du premier calcul ; les runs suivants lisent le cache.
  - Le script appelle Ollama sur `127.0.0.1` : sous Windows, `localhost` ajoutait environ 2 s à
    chaque requête (tentative IPv6).
