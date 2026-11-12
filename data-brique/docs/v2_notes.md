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
  complet reste à faire (fait en V2.2.1, voir ci-dessous).
- **API :** branchée sur la V2.2.1 par `POST /conversation` (voir `docs/contrat_api.md`).

## V2.2.1 — types de produit, références DEMO, mode rapide, catalogue complet

Version : `v2.2.1-references`. Même code (`src/moteur_v22.py`, `demo_bot_v22.py`). Nouveau cas
de démo : boisson + agrumes (la pistache est abandonnée).

### Corrections du parcours

- **Type de produit.** 12 types reconnus dans le message : boisson pétillante (soda, limonade,
  « pétillante »), thé glacé, sirop, yaourt à boire, boisson protéinée, boisson lactée, boisson
  végétale, crème dessert, glace, yaourt, et les génériques « dessert » et « boisson ». Le type
  restreint l'étude aux catégories et aux mots-clés Open Food Facts correspondants. « Une
  boisson » cite maintenant orange, cola et citron (boissons aromatisées), et non plus les laits
  végétaux.
- **Filtres.** L'étude garde d'abord tous les produits du type, puis ceux qui respectent les
  contraintes, puis les 50 plus proches (bge-m3). Les contraintes ne changent jamais le type. Si
  une contrainte laisse moins de 10 produits, elle n'est pas appliquée et le bot le dit (« je
  reste sur les boissons pétillantes »). Exemple : seules 6 boissons pétillantes peu sucrées sont
  bio dans le catalogue ; le bio reste dans le brief et filtre les références.
- **Invention.** Toute réponse reformulée est rejetée si elle cite un arôme, un code DEMO ou un
  type de produit absent du brouillon, ou si une référence passe sous la mauvaise piste. Le
  brouillon dit d'où vient chaque piste (`origine`) : « association observée : 22 des 36 produits
  au citron vert étudiés y ajoutent l'arôme citron », ou « pas encore observée : à valider en
  dégustation ».
- **Questions.** Au plus 2 questions simples par message (type précis, goût, contrainte).
- **Accord.** « boisson pétillante au citron vert, peu sucrée » ; « yaourt à la fraise, peu sucré ».

### Banque de références de démo

- `data/processed/banque_references_demo.csv` (script `scripts/creer_banque_references.py`) :
  30 références **fictives** `DEMO-001` à `DEMO-030`, 13 agrumes (dont 4 bio), vanille, café,
  thé, laitier, chocolat, menthe, fruits rouges, mangue, coco, gingembre, et 3 TasteSolutions
  (Sweetness, Mouthfeel, Saltiness).
- `banque_references_demo.meta.json` : exemple fictif inspiré de sources publiques, pas de vraies
  références Givaudan. La répartition TasteEssentials / TasteCollections est à valider : le
  document de Product « Défi 02 » n'a pas été transmis.
- **Liaison.** Pour chaque arôme d'une piste, bge-m3 classe les références filtrées par
  application (boissons, sucré, laitier, salé) et par labels demandés (bio, vegan, naturel,
  halal, casher). Une référence n'est retenue que si elle cite l'arôme ; un score bge-m3 ≥ 0,65
  suffit sinon. Mesure : 0,58 à 0,72 quand la référence cite l'arôme, 0,55 au plus sinon
  (durian : 0,50). Une référence qui couvre toute l'association (citron vert et menthe) est
  préférée. Sans label demandé, la version standard passe avant la version bio.
- « peu sucré » ou « sans sucre » ajoute Sweetness, « moins gras » Mouthfeel, « moins salé »
  Saltiness. Sans référence proche, le bot propose une création sur mesure. Le récapitulatif
  liste les codes DEMO choisis.

### Vitesse

- **Règles d'abord.** La plupart des messages sont analysés sans modèle (« bonjour », « piste 1 »,
  « échantillons », types, arômes de la liste, contraintes, questions). Sinon, un seul appel à
  llama3.2:3b donne l'intention et l'extraction. Sur le parcours citron vert, le modèle n'est
  jamais appelé ; « un arôme durian pour une glace » l'appelle une fois (4 s).
- **Démarrage.** `prechauffer=True` charge les deux modèles (keep_alive 2 h) et les vecteurs :
  1 à 2 s au démarrage du bot.
- **Mode rapide par défaut** : la réponse est le brouillon factuel.

### Catalogue complet

`scripts/indexer_catalogue_complet.py` a indexé les 8 943 produits Flavors avec bge-m3 (54 min
sur le CPU de l'équipe, reprise possible). Le cache `benchmark/cache/bge-m3_complet.npz` n'est
pas versionné. `MoteurV22(catalogue="auto")`, le défaut, l'utilise quand il existe ; sinon,
l'échantillon `sample_v1`.

### Temps par message — parcours boisson + citron vert (7 messages)

Script : `benchmark/mesure_temps_v22.py` (détail dans `benchmark/sorties/temps_v22.csv`). « Avant » =
V2.2 du commit `fea195c`. CPU de l'équipe, Ollama seul en cours.

| Configuration                                 | Moyenne | Min    | Max    | Total   |
| --------------------------------------------- | ------- | ------ | ------ | ------- |
| Avant, reformulation (ancien défaut), sample  | 19,96 s | 3,39 s | 45,6 s | 139,7 s |
| Avant, rapide, sample                         | 5,64 s  | 1,84 s | 14,8 s | 39,5 s  |
| **Après, rapide (défaut), catalogue complet** | 0,29 s  | 0,00 s | 1,07 s | 2,0 s   |
| Après, rapide, sample                         | 0,19 s  | 0,00 s | 0,81 s | 1,4 s   |
| Après, reformulation (expérimental), complet  | 33,4 s  | 10,5 s | 87,1 s | 233,9 s |

Objectif « moins de 3 s par message » atteint en mode rapide.

### Mode reformulation : expérimental

`AssistantV22(reformuler=True)`, ou `demo_bot_v22.py --reformuler`, est désactivé par défaut et
n'est plus corrigé. La version officielle est le mode rapide.

Défauts constatés sur le parcours de test :

- **Lenteur :** 33 s par message en moyenne, jusqu'à 87 s avec deux tentatives.
- **Types de produit inventés :** « 50 sirops » recopié de l'exemple guidé ; un avis ajouté
  (« un peu prévisible »).
- **Annonce d'envoi :** « je vais vous transmettre votre demande ».
- **Références mal placées ou oubliées :** codes DEMO oubliés ou placés sous la mauvaise piste.

Les garde-fous rejettent ces réponses et le bot affiche alors le brouillon ; 4 réponses sur 8 ont
été rejetées.

### Parcours de test (mode rapide, catalogue complet)

Réponses dans `benchmark/sorties/parcours_v22.json` (mode reformulé :
`parcours_v22_reformule.json`).

- « je voudrais créer une boisson » : arômes courants orange (13), cola (11), citron (8), puis
  2 questions (type précis, goût).
- « pétillante, goût citron vert, pas trop sucrée » : 50 boissons pétillantes peu sucrées.
  Pistes : citron vert seul (37 produits ; DEMO-003), citron vert + citron (23 sur 37 ;
  DEMO-003 + DEMO-001), citron vert + fraise (1 produit ; DEMO-003 + DEMO-024). Solution :
  DEMO-028 Sweetness.
- « elle doit être bio » : filtre bio non appliqué à l'étude (6 produits), références bio
  (DEMO-004 citron vert bio, DEMO-002 citron jaune bio) ; pas de pamplemousse bio dans la banque
  (DEMO-008 sans le label).
- « pourquoi vous proposez cette association ? » : origine chiffrée des pistes 2 et 3.
- « je prends la piste 1 » → brief avec DEMO-004 et DEMO-028 ; « comment je reçois des
  échantillons ? » → récapitulatif avec les codes, non envoyé.
- « un arôme durian pour une glace » : 45 glaces au catalogue ; aucune référence durian →
  création sur mesure ; pistes durian + coco (DEMO-026) et durian + cassis (DEMO-023).

### Limites de la V2.2.1

- **Banque fictive** de 30 références : ce ne sont pas de vrais codes Givaudan.
- **Types et contraintes par mots-clés** et labels Open Food Facts : un produit mal catégorisé
  n'est pas compté.
- **Association « citron vert + citron » :** elle vient en partie des listes d'ingrédients
  (« arôme citron »). Elle est réelle dans les données, mais peu originale.
- **Arômes hors liste de référence** (durian) : seul le modèle les extrait ; sans Ollama, un
  repli prend le mot qui suit « arôme / goût / saveur ».
