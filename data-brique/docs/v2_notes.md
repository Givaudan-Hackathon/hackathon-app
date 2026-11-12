# Moteur V2 — notes

Code : `src/moteur_v2.py`.

- **V2 :** classe `MoteurV2`, même format de sortie que `MoteurV1` (produits recommandés).
- **V2.1 :** classe `MoteurV21`, qui renvoie des pistes d'arômes sans produit ni marque (voir plus
  bas).
- **V2.2 :** classes `MoteurV22` et `AssistantV22` (`src/moteur_v22.py`), assistant
  conversationnel en mode RAG (voir la dernière section).

Démos, depuis `data-brique/`, avec le venv activé et Ollama lancé : `python demo_bot.py` (V2.1)
et `python demo_bot_v22.py` (V2.2).

## Fonctionnement

1. **Compréhension.** llama3.2:3b, appelé via Ollama sur `127.0.0.1`, extrait du brief un JSON
   `{application, division, aromes}`, avec `temperature 0`. Le moteur garde la division et le
   premier arôme. Le champ `application` est demandé en premier pour que le modèle nomme le produit
   avant de choisir la division. Sans lui, « une petite crème qui a le goût d'enfance » partait en
   Fragrance.
2. **Recherche Flavors.** bge-m3 compare le brief, enrichi de l'arôme extrait, aux vecteurs du
   catalogue (similarité cosinus). Les vecteurs utilisés sont ceux du benchmark, en cache dans
   `benchmark/cache/` (Flavors de `sample_v1`, 1 000 produits).
3. **Recherche Fragrance.** TF-IDF de la V1, sans changement.
4. **Repli.** Si Ollama ne répond pas, le moteur renvoie le résultat exact de la V1 avec
   `mode = "repli_v1"`.
5. **Catalogue complet.** `MoteurV2(catalogue="complet")` cible les 8 943 produits Flavors.
   L'indexation n'est pas encore faite : il faut lancer `.indexer()` volontairement (environ
   1 h 30 sur le CPU de l'équipe).

## Résultats sur les 15 briefs du benchmark

Les chiffres viennent de `benchmark/compare_v1_v2.py`. Le détail par brief est dans
`benchmark/sorties/comparaison_v1_v2.csv`.

| Mesure                                    | V1     | V2    |
| ----------------------------------------- | ------ | ----- |
| Division correcte (15)                    | 93 %   | 100 % |
| Arôme principal correct (15)              | —      | 100 % |
| Catégorie attendue au rang 1 (12 Flavors) | 67 %   | 100 % |
| Catégorie attendue dans le top 5 (12)     | 83 %   | 100 % |
| Précision top 5 (12 Flavors)              | 57 %   | 88 %  |
| Temps par brief                           | ~10 ms | 3,5 s |

## Limites connues

- **Résultats optimistes.** Le prompt (règle sur « goût » / « odeur », ajout du champ
  `application`) a été ajusté sur ces mêmes 15 briefs. La validation indépendante se fera jeudi
  sur les 30 cas de référence.
- **« pas trop sucré » n'est pas encore pris en compte.** Les contraintes (sucre, végétal, cible…)
  ne sont pas extraites et ne filtrent pas les résultats. Le brief de Lou reçoit des desserts sans
  critère de teneur en sucre.
- **Un seul produit nommé « pistache » dans `sample_v1`**, contre 30 dans le catalogue complet. Il
  faudra indexer le catalogue complet pour la V2 finale.
- **Temps de réponse.** Le premier appel prend environ 15 s, le temps de charger les modèles ;
  ensuite, 3 à 5 s par brief, sur CPU.
- **API.** L'API (port 8000) sert encore la V1. Le passage de l'API à la V2 n'est pas fait.

## Relance et contexte de la conversation (V2 et V2.1)

- **Pas d'invention.** Si le brief ne contient ni produit ni arôme identifiable (« Bonjour »,
  « C'est combien la livraison ? »), le moteur ne cherche rien. Il renvoie `arome: null`,
  `mode = "relance"` et la question « Quel goût recherchez-vous ? Pour quel type de produit ? ».
- **Prompt.** Le modèle peut répondre `division: "aucune"` avec une liste d'arômes vide.
- **Garde-fou dans le code.**
  - Un arôme n'est gardé que s'il figure dans le message, ou si le client parle de goût, d'odeur
    ou d'une sensation (« goût d'enfance » donne vanille).
  - Un produit n'est gardé que s'il figure dans le message. Sinon, le moteur cherche dans le
    message un nom de produit courant (yaourt, sirop, savon…).
- **Conversation.** La classe `Conversation` garde la demande en cours. Un message la complète au
  lieu de la remplacer s'il répond à une relance, s'il commence par « plutôt », « pour »,
  « sans »…, ou s'il fait 4 mots ou moins sans nommer de produit. « nouvelle demande » repart de
  zéro.

## V2.1 — pistes d'arômes, sans produit ni marque

Décision de l'équipe : les petits clients veulent créer leur propre produit avec un arôme
Givaudan. Le bot ne propose donc aucun produit ni aucune marque.

1. **Compréhension et recherche :** identiques à la V2 (llama3.2:3b, puis bge-m3 pour Flavors et
   TF-IDF V1 pour Fragrance).
2. **Étude de marché interne.** Le moteur prend les **50 produits les plus proches** du brief et
   repère les arômes cités dans leurs noms et ingrédients, à partir d'une liste de référence
   (`AROMES_FLAVORS` : 45 arômes, `AROMES_FRAGRANCE` : 36 notes, noms anglais inclus).
   - Mentions ignorées : jus de citron utilisé comme acidifiant, colorant caramel, beurre de
     cacao, fleur de sel.
   - Seuls des comptages sortent de cette étude, jamais un nom de produit ni une marque.
3. **Trois pistes**, chacune avec une phrase d'explication et un nombre de produits du marché :
   - (a) l'arôme principal seul ;
   - (b) l'association la plus fréquente avec l'arôme principal ;
   - (c) une association présente mais rare.
4. **Arôme principal trop rare.** Si moins de 3 produits proches utilisent l'arôme principal, ses
   associations ne sont pas mesurables. Les pistes (b) et (c) s'appuient alors sur les arômes du
   marché proche et le disent : `observee: false`, « association pas encore observée, à valider en
   dégustation ».
5. **Produit sans goût.** Si le client nomme un produit sans goût, le bot pose la question de
   relance et cite les goûts les plus courants sur ce marché (pour un yaourt à boire : fraise,
   framboise, vanille).
6. **Repli.** Sans Ollama, la division vient des mots-clés V1, l'arôme de la liste de référence et
   la recherche du TF-IDF V1.

### Résultats de test (échantillon `sample_v1`)

| Brief                             | Piste 1               | Piste 2                                                   | Piste 3                                       |
| --------------------------------- | --------------------- | --------------------------------------------------------- | --------------------------------------------- |
| Lou (desserts végétaux, pistache) | pistache (2 produits) | pistache + vanille (non observée ; vanille : 26 produits) | pistache + abricot (non observée ; 1 produit) |
| Dessert à la mangue pour enfants  | mangue (18)           | mangue + fruit de la passion (7)                          | mangue + thé (1)                              |
| … « plutôt une boisson »          | mangue (22)           | mangue + fruit de la passion (9)                          | mangue + banane (1)                           |

Les messages vagues testés (« Bonjour », « je voudrais quelque chose de bon », « C'est combien la
livraison ? ») donnent tous la question de relance.

Les tests pytest vérifient aussi qu'aucun nom de produit ni aucune marque du catalogue n'apparaît
dans le texte affiché au client.

### Limites de la V2.1

- **Lou :** l'échantillon ne contient que 2 produits proches à la pistache, donc ses pistes (b) et
  (c) ne viennent pas d'associations observées. Indexer le catalogue complet (30 produits
  pistache) devrait donner de vraies associations.
- **« pas trop sucré » n'est toujours pas pris en compte**, comme les autres contraintes.
- **Liste d'arômes faite à la main :** elle peut en oublier.
- **Arôme de base compté comme arôme :** le lait de coco ou d'amande des desserts végétaux est
  compté comme un arôme.
- **Nombres de produits :** ils portent sur les 50 produits les plus proches de l'échantillon de
  test, pas sur tout le marché.

## V2.2 — assistant conversationnel (RAG)

Code : `src/moteur_v22.py` (classes `MoteurV22` et `AssistantV22`). Démo :
`python demo_bot_v22.py` (options `--rapide`, `--trace`, `--complet`). La V2.1 et son bot
(`demo_bot.py`) sont inchangés : leurs sorties sont identiques avant et après la V2.2. L'API du
port 8000 sert toujours la V1.

### Fonctionnement, à chaque message

1. **Intention.** llama3.2:3b (sortie JSON) classe le message : nouvelle demande, précision,
   question sur une piste, choix d'une piste, demande d'échantillons, hors sujet.
   - Des garde-fous de code corrigent les cas évidents : « échantillon » dans le message,
     « je prends la piste 2 », une description sans question classée « question » par le modèle.
   - L'intention donnée par le modèle reste tracée (`etapes.intention_llm`). Dans le parcours de
     test, le modèle classe « un goût pistache gourmand, pas trop sucré… » en question ; le
     garde-fou le requalifie en précision.
2. **Projet cumulé.** Produit, arôme principal, profil (gourmand, fruité…) et contraintes sont
   mis à jour message par message. « plutôt une crème dessert » remplace le produit et garde le
   reste.
3. **Contraintes.** Liste de référence : peu sucré, sans sucre, végétal, bio, sans gluten, sans
   lactose, naturel, pour enfants, protéiné.
   - Elles filtrent l'étude de marché grâce aux labels et catégories Open Food Facts, parmi les
     300 produits les plus proches.
   - Une contrainte qui laisserait moins de 10 produits n'est pas appliquée, et le bot le dit.
     « Pour enfants » n'est jamais appliquée : les données ne le précisent pas.
4. **Étude de marché.** Celle de la V2.1 (aromes et associations des 50 produits proches),
   calculée sur les produits filtrés. Les études précédentes de la conversation sont gardées pour
   répondre aux questions (« pourquoi la vanille ? »).
5. **Réponse (RAG).**
   - Le code écrit un brouillon factuel à partir du contexte récupéré : projet, étude, pistes,
     chiffres ; pour une question, les chiffres de chaque arôme cité, y compris dans les études
     précédentes.
   - llama3.2:3b reformule ce brouillon sur un ton naturel, guidé par 2 exemples.
   - Vérification de chaque reformulation : aucun chiffre ni rapport « X des Y » ajouté ; aucun
     chiffre ni mot obligatoire oublié (arômes des pistes, « prototype »…) ; aucune marque ni nom
     de produit du catalogue ; ni « monsieur » ni « madame » ; aucune annonce d'envoi.
   - En cas d'échec : une seconde tentative, puis le brouillon tel quel.
   - Fautes récurrentes corrigées par le code (« une excellente choix » → « un excellent choix »).
6. **Parcours.** Pistes → choix d'une piste → récapitulatif du brief → demande d'échantillons. La
   demande est un brouillon affiché au client : rien n'est envoyé.

**Mode rapide.** `AssistantV22(reformuler=False)`, ou `repondre(message, reformuler=False)`
pour un appel : la réponse est le brouillon factuel, sans reformulation. C'est le paramètre à
exposer quand l'API passera à la V2.2.

**Essais écartés.** Une rédaction libre par le modèle à partir des faits (JSON, puis texte) a été
essayée d'abord. Le modèle 3B attribuait l'étude au client (« vous avez étudié »), recopiait ses
consignes, mélangeait des chiffres de deux faits et inventait des étapes (« service de
distribution »). Avec l'historique passé en messages, il répondait au brouillon comme à un
message du client.

### Parcours de test

Script : `benchmark/parcours_v22.py` (réponses enregistrées dans
`benchmark/sorties/parcours_v22.json` et `parcours_v22_rapide.json`).

Messages : « Bonjour » → « je voudrais créer un dessert » → « un goût pistache gourmand, pas
trop sucré, pour des desserts végétaux » → « plutôt une crème dessert » → « pourquoi la
vanille ? » → « je prends la piste 2 » → « comment je reçois des échantillons ? ».

- Les 7 intentions finales sont correctes.
- L'étude porte sur 19 crèmes dessert proches, toutes peu sucrées et végétales. Pistes :
  pistache seule, pistache + amande (amande : 13 produits), pistache + café (1 produit).
- « Pourquoi la vanille ? » : la vanille n'apparaît que dans 2 de ces 19 produits ; c'était
  l'arôme le plus fréquent (22 produits) dans l'étude précédente sur les desserts en général.
- Récapitulatif final : crème dessert, piste 2, pistache + amande, gourmand, peu sucré, végétal.
- 6 réponses sur 7 sont reformulées par le modèle. Pour la dernière, ses deux tentatives
  annonçaient « je vais vous transmettre votre demande » : elles ont été rejetées et le bot a
  affiché le brouillon.

### Temps par message (CPU de l'équipe, catalogue `sample_v1`)

| Mode                        | Moyenne | Min    | Max    | Parcours (7 messages) |
| --------------------------- | ------- | ------ | ------ | --------------------- |
| Avec reformulation          | 20,7 s  | 10,4 s | 29,4 s | 145 s                 |
| Rapide (sans reformulation) | 3,8 s   | 1,5 s  | 9,8 s  | 27 s                  |

Les messages les plus longs sont ceux qui relancent l'étude (compréhension + recherche).

### Tests

`tests/test_moteur_v22.py` (sans Ollama) : extraction des contraintes, vérification des
chiffres et des marques, rejet d'une reformulation fautive, parcours complet hors ligne, mode
rapide, corrections. Un test vérifie aussi les vraies réponses du modèle enregistrées dans
`parcours_v22.json` : aucune marque ni nom de produit, aucun chiffre absent du brouillon.

### Limites de la V2.2

- **Lenteur avec reformulation :** 10 à 30 s par message sur CPU (deux ou trois appels au modèle
  par tour). Le mode rapide répond en 2 à 10 s.
- **Reformulation proche du brouillon :** le modèle 3B ajoute surtout une courte réaction au
  début ; quand il s'écarte des faits, c'est le brouillon qui est affiché.
- **Vérification partielle :** elle contrôle les chiffres, les mots obligatoires, les marques et
  les annonces d'envoi, pas tout le sens d'une phrase.
- **Marques et mots courants :** 21 marques qui sont aussi des mots courants (« Ensemble »,
  « Nature »…) sont ignorées par la vérification.
- **Contraintes par labels :** un produit peu sucré sans label « low-sugar » n'est pas reconnu.
  Les teneurs en sucre (nutriments) ne sont pas dans le catalogue.
- **Pistache :** aucune crème dessert végétale et peu sucrée de l'échantillon n'utilise la
  pistache ; les pistes 2 et 3 sont donc « à valider en dégustation ». Indexer le catalogue
  complet reste à faire.
- **API :** pas encore branchée sur la V2.2.
