# Validation sur les 30 cas de référence (V2.2, `v2.2.2-references`)

Mesure du 2026-11-12, **avant toute correction**. Les cas (`benchmark/cas_reference_30.csv`) ont été écrits avant le test et n'ont pas été modifiés.

## Méthode

- Chaque cas est le **premier message d'une nouvelle session**.
- V2.2 : `AssistantV22` en mode rapide (défaut), catalogue Flavors complet (8 943 produits), modèles préchargés. Script : `benchmark/valider_30_cas.py`.
- **Type** : `compris.type_produit` égal au type attendu (vide attendu → aucun type).
- **Arôme(s)** : tous les arômes attendus figurent dans `compris.aromes` ; aucun attendu → aucun arôme. L'arôme principal (`compris.arome`) est aussi mesuré à part.
- **Contraintes** : égalité stricte des ensembles. Seule équivalence : « vegan » des cas = contrainte « végétal » du moteur. Une contrainte en trop (ex. « pour enfants ») est un échec.
- **Comportement** : `pistes` si `etape = pistes` ; `creation_sur_mesure` si, en plus, l'arôme principal n'a aucune référence DEMO ; `hors_sujet` ou `question` selon `intention` ; sinon `relance`.
- **Aucune marque** : aucune marque du catalogue (mot à mot) dans la réponse, y compris une marque citée par le client (ex. « Coca-Cola », 153 produits au catalogue). Le champ `brands` d'Open Food Facts contient aussi des mots génériques : une « marque » identique au vocabulaire du moteur (arôme, type, contrainte, profil) est ignorée. Formes ignorées présentes au catalogue : « aucun », « bio », « cola », « creme dessert », « delice », « delices », « ensemble », « fruite », « gourmand », « original », « proteines », « santal », « simple », « vanille », « vegetal », « vrai », « yaourt ».
- **Aucun chiffre inventé** : chaque nombre de la réponse vient des données de l'étude de marché (comptages), d'un numéro de piste ou du message du client. **Aucun prix** : ni « € », ni « euros », ni « prix de ».
- **Cas réussi** : tous les critères ci-dessus à la fois.
- **V1** (`MoteurV1`) : division ; l'arôme est jugé sur les 5 produits recommandés (tous les arômes attendus présents dans leurs noms), car V1 n'extrait pas d'arôme.
- **V2.1** (`MoteurV21.pistes`, catalogue complet) : division, arôme principal, pistes ou relance. V2.1 n'a ni type de produit, ni contraintes, ni intention `hors_sujet` / `question`, ni références : ces critères ne sont pas comparables.

## Résultats V2.2

| Critère                       | Global       | boisson_agrumes | autre_produit | flou_hors_sujet |
| ----------------------------- | ------------ | --------------- | ------------- | --------------- |
| Type de produit               | 27/30 (90%)  | 14/15 (93%)     | 8/10 (80%)    | 5/5 (100%)      |
| Arôme(s), tous trouvés        | 25/30 (83%)  | 12/15 (80%)     | 9/10 (90%)    | 4/5 (80%)       |
| Arôme principal               | 23/30 (77%)  | 10/15 (67%)     | 9/10 (90%)    | 4/5 (80%)       |
| Contraintes (égalité stricte) | 29/30 (97%)  | 14/15 (93%)     | 10/10 (100%)  | 5/5 (100%)      |
| Comportement                  | 21/30 (70%)  | 12/15 (80%)     | 9/10 (90%)    | 0/5 (0%)        |
| Aucune marque citée           | 30/30 (100%) | 15/15 (100%)    | 10/10 (100%)  | 5/5 (100%)      |
| Aucun chiffre inventé         | 30/30 (100%) | 15/15 (100%)    | 10/10 (100%)  | 5/5 (100%)      |
| Aucun prix inventé            | 30/30 (100%) | 15/15 (100%)    | 10/10 (100%)  | 5/5 (100%)      |
| **Cas entièrement réussi**    | 18/30 (60%)  | 11/15 (73%)     | 7/10 (70%)    | 0/5 (0%)        |

Temps de réponse V2.2 : moyenne 0.80 s, médiane 0.60 s, max 5.75 s ; modèle appelé pour 2 cas sur 30 (moyenne 4.71 s ces fois-là, 0.52 s sinon).

## Comparaison V1 / V2.1 / V2.2

| Critère comparable                                     | V1                           | V2.1         | V2.2         |
| ------------------------------------------------------ | ---------------------------- | ------------ | ------------ |
| Division (flavors, ou aucune pour les cas flous)       | 26/30 (87%)                  | 29/30 (97%)  | 30/30 (100%) |
| Arôme principal                                        | —                            | 29/30 (97%)  | 23/30 (77%)  |
| Arôme(s) attendus dans les 5 produits recommandés (V1) | 13/23 (57%)                  | —            | —            |
| Pistes ou relance, cas qui l'attendent                 | —                            | 25/26 (96%)  | 21/26 (81%)  |
| Aucune marque citée                                    | (produits du commerce : non) | 30/30 (100%) | 30/30 (100%) |
| Temps moyen par cas                                    | < 0,1 s                      | 5.09 s       | 0.80 s       |

## Échecs (réponse obtenue)

### C05 — « une eau aromatisée à l'orange sans sucre ajouté »

- Échec : Type de produit
- Attendu : type `boisson`, arômes `orange`, contraintes `peu sucré`, comportement `pistes`
- Obtenu : type `—`, arômes `orange`, contraintes `peu sucré`, comportement `pistes` (etape `pistes`, intention `nouvelle_demande`)
- Réponse :

> Votre projet : à l'orange, peu sucré.
> J'ai étudié les 50 produits du marché les plus proches de votre projet, tous peu sucrés.
> Voici mes pistes :
>
> 1. Orange seul : un goût franc, facile à reconnaître. 43 des 50 produits les plus proches de votre projet l'utilisent.
>    Référence : DEMO-006 Orange douce (orange mûre, juteuse, sucrée ; soluble eau).
> 2. Orange + citron : l'association la plus fréquente sur le marché (17 produits sur 43 à l'orange). Un choix rassurant, que les consommateurs connaissent déjà.
>    Référence : DEMO-012 Agrumes mélangés (citron, orange et pamplemousse, frais et équilibré ; soluble eau).
> 3. Orange + figue : une association rare sur le marché (1 produit), qui peut vous démarquer tout en restant crédible.
>    Référence : DEMO-006 Orange douce (orange mûre, juteuse, sucrée ; soluble eau). Aucune référence proche pour l'arôme figue dans la banque : une création sur mesure est possible.
>    Pour votre contrainte de recette : DEMO-028 Sweetness (renforce la perception sucrée pour réduire le sucre ajouté ; soluble eau).
>    Laquelle vous tente ?

### C10 — « sirop de mandarine pour cocktails sans alcool »

- Échec : Arôme(s), tous trouvés, Comportement
- Attendu : type `sirop`, arômes `mandarine`, contraintes `—`, comportement `pistes`
- Obtenu : type `sirop`, arômes `—`, contraintes `—`, comportement `relance` (etape `relance`, intention `nouvelle_demande`)
- Réponse :

> J'ai bien noté votre projet : sirop. Parmi les 50 sirops du marché les plus proches, les arômes les plus courants sont : citron (24 produits), cerise (7 produits) et orange (4 produits). Quel goût recherchez-vous ?

### C11 — « une boisson aux agrumes pour enfants, pas trop acide »

- Échec : Arôme(s), tous trouvés, Contraintes (égalité stricte), Comportement
- Attendu : type `boisson`, arômes `agrumes`, contraintes `—`, comportement `pistes`
- Obtenu : type `boisson`, arômes `—`, contraintes `pour enfants`, comportement `relance` (etape `relance`, intention `nouvelle_demande`)
- Réponse :

> J'ai bien noté votre projet : boisson. Parmi les 50 boissons du marché les plus proches, les arômes les plus courants sont : cola (13 produits), pomme (9 produits) et fraise (7 produits). Quel type de boisson : plutôt pétillante, thé glacé, sirop, lactée ou végétale ? Quel goût recherchez-vous ?

### C14 — « une boisson à la bergamote halal »

- Échec : Arôme(s), tous trouvés, Comportement
- Attendu : type `boisson`, arômes `bergamote`, contraintes `halal`, comportement `pistes`
- Obtenu : type `boisson`, arômes `—`, contraintes `halal`, comportement `relance` (etape `relance`, intention `nouvelle_demande`)
- Réponse :

> J'ai bien noté votre projet : boisson. Parmi les 10 boissons du marché les plus proches, les arômes les plus courants sont : caramel (2 produits), orange (1 produit) et grenade (1 produit). Quel type de boisson : plutôt pétillante, thé glacé, sirop, lactée ou végétale ? Quel goût recherchez-vous ?

### C21 — « chips goût barbecue »

- Échec : Type de produit
- Attendu : type `snack salé`, arômes `barbecue`, contraintes `—`, comportement `pistes`
- Obtenu : type `chips`, arômes `barbecue`, contraintes `—`, comportement `creation_sur_mesure|pistes` (etape `pistes`, intention `nouvelle_demande`)
- Réponse :

> Votre projet : chips au barbecue.
> J'ai étudié les 50 produits du marché les plus proches de votre projet.
> Voici mes pistes :
>
> 1. Barbecue seul : un goût franc, facile à reconnaître. Aucun des 50 produits les plus proches de votre projet ne l'utilise : c'est une place encore libre sur ce marché.
>    Aucune référence proche pour l'arôme barbecue dans la banque : une création sur mesure est possible.
> 2. Barbecue + pêche : le goût pêche est le plus présent dans les produits proches de votre projet (30 produits). L'association avec barbecue n'y apparaît pas encore (aucun produit proche n'est au barbecue) : à valider en dégustation.
>    Référence : DEMO-018 Thé noir pêche (thé noir infusé, pêche juteuse ; soluble eau). Aucune référence proche pour l'arôme barbecue dans la banque : une création sur mesure est possible.
> 3. Barbecue + café : un goût rare dans les produits proches (1 produit) et jamais associé au barbecue : une piste originale, à tester.
>    Référence : DEMO-016 Café torréfié (café torréfié, notes grillées, légère amertume ; soluble eau). Aucune référence proche pour l'arôme barbecue dans la banque : une création sur mesure est possible.
>    Laquelle vous tente ? Avez-vous une contrainte : bio, vegan, peu sucré ?

### C22 — « une glace au durian »

- Échec : Arôme(s), tous trouvés, Comportement
- Attendu : type `glace`, arômes `durian`, contraintes `—`, comportement `creation_sur_mesure`
- Obtenu : type `glace`, arômes `—`, contraintes `—`, comportement `relance` (etape `relance`, intention `nouvelle_demande`)
- Réponse :

> J'ai bien noté votre projet : glace. Parmi les 45 glaces du marché les plus proches, les arômes les plus courants sont : coco (39 produits), vanille (32 produits) et chocolat (29 produits). Quel goût recherchez-vous ?

### C24 — « je fais des biscuits, je veux un goût noisette »

- Échec : Type de produit
- Attendu : type `biscuit`, arômes `noisette`, contraintes `—`, comportement `pistes`
- Obtenu : type `—`, arômes `noisette|biscuit`, contraintes `—`, comportement `creation_sur_mesure|pistes` (etape `pistes`, intention `nouvelle_demande`)
- Réponse :

> Votre projet : à la noisette.
> J'ai étudié les 50 produits du marché les plus proches de votre projet.
> Voici mes pistes :
>
> 1. Noisette seule : un goût franc, facile à reconnaître. 50 des 50 produits les plus proches de votre projet l'utilisent.
>    Aucune référence proche pour l'arôme noisette dans la banque : une création sur mesure est possible.
> 2. Noisette + chocolat : l'association la plus fréquente sur le marché (26 produits sur 50 à la noisette). Un choix rassurant, que les consommateurs connaissent déjà.
>    Référence : DEMO-020 Chocolat noir (cacao intense, notes torréfiées ; poudre). Aucune référence proche pour l'arôme noisette dans la banque : une création sur mesure est possible.
> 3. Noisette + café : une association rare sur le marché (1 produit), qui peut vous démarquer tout en restant crédible.
>    Référence : DEMO-016 Café torréfié (café torréfié, notes grillées, légère amertume ; soluble eau). Aucune référence proche pour l'arôme noisette dans la banque : une création sur mesure est possible.
>    Laquelle vous tente ? Avez-vous une contrainte : bio, vegan, peu sucré ?

### C26 — « je veux un truc bon »

- Échec : Comportement
- Attendu : type `—`, arômes `—`, contraintes `—`, comportement `relance`
- Obtenu : type `—`, arômes `—`, contraintes `—`, comportement `question` (etape `relance`, intention `question`)
- Réponse :

> Je n'ai pas l'information sur ce point : un conseiller Givaudan pourra vous répondre. Je vous aide à trouver l'arôme de votre futur produit. Quel produit voulez-vous créer, et quel goût imaginez-vous ?

### C27 — « quelle heure est-il ? »

- Échec : Comportement
- Attendu : type `—`, arômes `—`, contraintes `—`, comportement `hors_sujet`
- Obtenu : type `—`, arômes `—`, contraintes `—`, comportement `question` (etape `relance`, intention `question`)
- Réponse :

> Je n'ai pas l'information sur ce point : un conseiller Givaudan pourra vous répondre. Je vous aide à trouver l'arôme de votre futur produit. Quel produit voulez-vous créer, et quel goût imaginez-vous ?

### C28 — « c'est combien un échantillon ? »

- Échec : Comportement
- Attendu : type `—`, arômes `—`, contraintes `—`, comportement `question (ne pas inventer de prix)`
- Obtenu : type `—`, arômes `—`, contraintes `—`, comportement `relance` (etape `relance`, intention `demande_echantillons`)
- Réponse :

> Pour vous proposer des échantillons, décrivez-moi d'abord votre projet : quel produit, et quel goût ?

### C29 — « donne-moi la recette de Coca-Cola »

- Échec : Arôme(s), tous trouvés, Comportement
- Attendu : type `—`, arômes `—`, contraintes `—`, comportement `hors_sujet (aucune marque)`
- Obtenu : type `—`, arômes `cola`, contraintes `—`, comportement `relance` (etape `relance`, intention `nouvelle_demande`)
- Réponse :

> J'ai bien noté le goût cola. Quel type de produit voulez-vous créer ? Avez-vous une contrainte : bio, vegan, peu sucré ?

### C30 — « quel est le meilleur arôme ? »

- Échec : Comportement
- Attendu : type `—`, arômes `—`, contraintes `—`, comportement `relance`
- Obtenu : type `—`, arômes `—`, contraintes `—`, comportement `question` (etape `relance`, intention `question`)
- Réponse :

> Je n'ai pas l'information sur ce point : un conseiller Givaudan pourra vous répondre. Je vous aide à trouver l'arôme de votre futur produit. Quel produit voulez-vous créer, et quel goût imaginez-vous ?

## Limites de la mesure

- 30 cas courts, un seul message chacun : la conversation (précisions, retraits, choix) est couverte par les tests pytest, pas par cette validation.
- Critères stricts écrits avant la mesure : un type absent de la liste du moteur (« snack salé », « biscuit ») ou une contrainte en trop compte comme un échec, même si la réponse reste utile.
- Le contrôle « aucun chiffre inventé » vérifie la provenance des nombres, pas leur interprétation dans la phrase.
- Le contrôle des marques porte sur les marques du catalogue Open Food Facts : une marque absente du catalogue ne serait pas détectée.
- V2.1 et V2.2 dépendent d'Ollama (llama3.2:3b, bge-m3) ; résultats obtenus à température 0, sur le CPU de l'équipe.

<!-- analyse manuelle : conservee quand le script regenere ce fichier -->

## Analyse des échecs (mesure du 2026-11-12, avant correction)

Une première exécution donnait 2/30 : le contrôle des marques comptait comme marques des mots
génériques présents dans le champ `brands` d'Open Food Facts (« Fruité », « Vanille », « Cola »,
des variantes de « bio »…). Le contrôle des chiffres ignorait aussi les nombres stockés en texte
dans l'étude (« seulement 7 produits »). Ces deux défauts venaient de la **mesure** ; ils ont été
corrigés dans le script. Le moteur n'a pas été modifié. Les résultats ci-dessus sont ceux de la
mesure corrigée.

| Cause                                                                                                                                                                                                                                                 | Cas                |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| Arôme absent de la liste de référence Flavors (mandarine, bergamote ne sont que dans la liste Fragrance ; agrumes, durian absents). Quand une règle reconnaît le type, le modèle n'est pas appelé, donc l'arôme est perdu → relance au lieu de pistes | C10, C11, C14, C22 |
| Le type « thé glacé » donne l'arôme « thé » (motif `the glace` de la liste) : l'arôme principal devient « thé » au lieu de pêche / citron (cas comptés réussis, car les arômes attendus sont bien présents)                                           | C03, C08           |
| Type absent de la liste du moteur : « eau aromatisée », « biscuit », « chips » (attendu : « snack salé ») ; « biscuit » est lu comme un arôme                                                                                                         | C05, C21, C24      |
| Contrainte en trop : « pour enfants » relevée alors que le cas n'en attend pas                                                                                                                                                                        | C11                |
| Messages flous ou hors sujet : un « ? » donne l'intention `question` là où le cas attend `hors_sujet` (« quelle heure est-il ? ») ou `relance` (« quel est le meilleur arôme ? », « je veux un truc bon »)                                            | C26, C27, C30      |
| « c'est combien un échantillon ? » : la règle « échantillon » passe avant la détection d'une question ; réponse sans prix inventé, mais comportement `relance` au lieu de `question`                                                                  | C28                |
| « recette de Coca-Cola » : « cola » est extrait comme arôme et le bot relance (« J'ai bien noté le goût cola ») au lieu de `hors_sujet`. La marque n'est pas citée, mais le goût en est tiré                                                          | C29                |

À retenir :

- **Fiabilité :** aucune marque, aucun chiffre inventé et aucun prix inventé sur les 30 cas, et la
  division est correcte à 100 %.
- **Arôme principal :** V2.1, qui appelle toujours le modèle, trouve mieux l'arôme principal (97 %
  contre 77 %). C'est le coût de l'optimisation « règles d'abord » de la V2.2 : 0,75 s par cas
  contre 5,1 s.
- **Cas flous :** les 5 cas flous ou hors sujet échouent sur l'intention attendue. Le bot ne dit
  rien de faux, mais il classe ces messages en `question` ou en `relance`, pas comme les cas
  l'attendent.
