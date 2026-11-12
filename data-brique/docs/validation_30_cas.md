# Validation sur les 30 cas de référence (V2.2, `v2.2.3-mecanismes`)

Mesure du 2026-11-12. Les cas (`benchmark/cas_reference_30.csv`) ont été écrits avant le test et n'ont pas été modifiés. Le résultat **avant correction** (V2.2.2, 18/30) est conservé dans `benchmark/sorties/validation_30_cas_avant.csv`.

## Avant / après les corrections par mécanismes

| Critère                       | Avant (V2.2.2) | Après (v2.2.3-mecanismes) |
| ----------------------------- | -------------- | ------------------------- |
| Type de produit               | 27/30 (90%)    | 27/30 (90%)               |
| Arôme(s), tous trouvés        | 25/30 (83%)    | 30/30 (100%)              |
| Arôme principal               | 23/30 (77%)    | 30/30 (100%)              |
| Contraintes                   | 29/30 (97%)    | 29/30 (97%)               |
| Comportement                  | 21/30 (70%)    | 30/30 (100%)              |
| Aucune marque                 | 30/30 (100%)   | 30/30 (100%)              |
| Aucun chiffre inventé         | 30/30 (100%)   | 30/30 (100%)              |
| Aucun prix inventé            | 30/30 (100%)   | 30/30 (100%)              |
| **Cas entièrement réussi**    | 18/30 (60%)    | 26/30 (87%)               |
| Cas réussis — boisson_agrumes | 11/15 (73%)    | 13/15 (87%)               |
| Cas réussis — autre_produit   | 7/10 (70%)     | 8/10 (80%)                |
| Cas réussis — flou_hors_sujet | 0/5 (0%)       | 5/5 (100%)                |
| Temps moyen par cas           | 0.80 s         | 1.37 s                    |
| Temps médian par cas          | 0.60 s         | 0.73 s                    |

Cas gagnés : C10, C14, C22, C26, C27, C28, C29, C30. Cas perdus : aucun.

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
| Arôme(s), tous trouvés        | 30/30 (100%) | 15/15 (100%)    | 10/10 (100%)  | 5/5 (100%)      |
| Arôme principal               | 30/30 (100%) | 15/15 (100%)    | 10/10 (100%)  | 5/5 (100%)      |
| Contraintes (égalité stricte) | 29/30 (97%)  | 14/15 (93%)     | 10/10 (100%)  | 5/5 (100%)      |
| Comportement                  | 30/30 (100%) | 15/15 (100%)    | 10/10 (100%)  | 5/5 (100%)      |
| Aucune marque citée           | 30/30 (100%) | 15/15 (100%)    | 10/10 (100%)  | 5/5 (100%)      |
| Aucun chiffre inventé         | 30/30 (100%) | 15/15 (100%)    | 10/10 (100%)  | 5/5 (100%)      |
| Aucun prix inventé            | 30/30 (100%) | 15/15 (100%)    | 10/10 (100%)  | 5/5 (100%)      |
| **Cas entièrement réussi**    | 26/30 (87%)  | 13/15 (87%)     | 8/10 (80%)    | 5/5 (100%)      |

Temps de réponse V2.2 : moyenne 1.37 s, médiane 0.73 s, max 6.17 s ; modèle appelé pour 5 cas sur 30 (moyenne 5.31 s ces fois-là, 0.59 s sinon).

## Comparaison V1 / V2.1 / V2.2

| Critère comparable                                     | V1                           | V2.1         | V2.2         |
| ------------------------------------------------------ | ---------------------------- | ------------ | ------------ |
| Division (flavors, ou aucune pour les cas flous)       | 26/30 (87%)                  | 29/30 (97%)  | 29/30 (97%)  |
| Arôme principal                                        | —                            | 29/30 (97%)  | 30/30 (100%) |
| Arôme(s) attendus dans les 5 produits recommandés (V1) | 13/23 (57%)                  | —            | —            |
| Pistes ou relance, cas qui l'attendent                 | —                            | 25/26 (96%)  | 26/26 (100%) |
| Aucune marque citée                                    | (produits du commerce : non) | 30/30 (100%) | 30/30 (100%) |
| Temps moyen par cas                                    | < 0,1 s                      | 5.13 s       | 1.37 s       |

## Échecs (réponse obtenue)

### C05 — « une eau aromatisée à l'orange sans sucre ajouté »

- Échec : Type de produit
- Attendu : type `boisson`, arômes `orange`, contraintes `peu sucré`, comportement `pistes`
- Obtenu : type `boisson pétillante`, arômes `orange`, contraintes `peu sucré`, comportement `pistes` (etape `pistes`, intention `nouvelle_demande`)
- Réponse :

> Votre projet : boisson pétillante à l'orange, peu sucrée.
> J'ai étudié les 50 boissons pétillantes du marché les plus proches de votre projet, toutes peu sucrées.
> Voici mes pistes :
>
> 1. Orange seul : un goût franc, facile à reconnaître. 20 des 50 produits les plus proches de votre projet l'utilisent.
>    Référence : DEMO-006 Orange douce (orange mûre, juteuse, sucrée ; soluble eau).
> 2. Orange + agrumes : l'association la plus fréquente sur le marché (10 produits sur 20 à l'orange). Un choix rassurant, que les consommateurs connaissent déjà.
>    Référence : DEMO-012 Agrumes mélangés (citron, orange et pamplemousse, frais et équilibré ; soluble eau).
> 3. Orange + figue : une association rare sur le marché (1 produit), qui peut vous démarquer tout en restant crédible.
>    Référence : DEMO-006 Orange douce (orange mûre, juteuse, sucrée ; soluble eau). Aucune référence proche pour l'arôme figue dans la banque : une création sur mesure est possible.
>    Pour votre contrainte de recette : DEMO-028 Sweetness (renforce la perception sucrée pour réduire le sucre ajouté ; soluble eau).
>    Laquelle vous tente ?

### C11 — « une boisson aux agrumes pour enfants, pas trop acide »

- Échec : Contraintes (égalité stricte)
- Attendu : type `boisson`, arômes `agrumes`, contraintes `—`, comportement `pistes`
- Obtenu : type `boisson`, arômes `agrumes`, contraintes `pour enfants`, comportement `pistes` (etape `pistes`, intention `nouvelle_demande`)
- Réponse :

> Votre projet : boisson aux agrumes, pour enfants.
> J'ai étudié les 50 boissons du marché les plus proches de votre projet.
> Je n'ai pas pu filtrer l'étude sur « pour enfants » : les données du marché ne le précisent pas. Je reste sur les boissons et je garde cette contrainte dans votre brief.
> Voici mes pistes :
>
> 1. Agrumes seuls : un goût franc, facile à reconnaître. 33 des 50 produits les plus proches de votre projet l'utilisent.
>    Référence : DEMO-012 Agrumes mélangés (citron, orange et pamplemousse, frais et équilibré ; soluble eau).
> 2. Agrumes + orange : l'association la plus fréquente sur le marché (23 produits sur 33 aux agrumes). Un choix rassurant, que les consommateurs connaissent déjà.
>    Référence : DEMO-012 Agrumes mélangés (citron, orange et pamplemousse, frais et équilibré ; soluble eau).
> 3. Agrumes + cerise : une association rare sur le marché (1 produit), qui peut vous démarquer tout en restant crédible.
>    Référence : DEMO-012 Agrumes mélangés (citron, orange et pamplemousse, frais et équilibré ; soluble eau). Aucune référence proche pour l'arôme cerise dans la banque : une création sur mesure est possible.
>    Laquelle vous tente ?

### C21 — « chips goût barbecue »

- Échec : Type de produit
- Attendu : type `snack salé`, arômes `barbecue`, contraintes `—`, comportement `pistes`
- Obtenu : type `chips`, arômes `barbecue`, contraintes `—`, comportement `creation_sur_mesure|pistes` (etape `pistes`, intention `nouvelle_demande`)
- Réponse :

> Votre projet : chips au barbecue.
> J'ai étudié les 50 produits du marché les plus proches de votre projet.
> Notre catalogue ne contient pas de produits de ce type (« chips ») : j'ai étudié les produits les plus proches, le marché étudié est donc limité.
> Voici mes pistes :
>
> 1. Barbecue seul : un goût franc, facile à reconnaître. Aucun des 50 produits les plus proches de votre projet ne l'utilise : c'est une place encore libre sur ce marché.
>    Aucune référence proche pour l'arôme barbecue dans la banque : une création sur mesure est possible.
> 2. Barbecue + pêche : le goût pêche est le plus présent dans les produits proches de votre projet (30 produits). L'association avec barbecue n'y apparaît pas encore (aucun produit proche n'est au barbecue) : à valider en dégustation.
>    Référence : DEMO-018 Thé noir pêche (thé noir infusé, pêche juteuse ; soluble eau). Aucune référence proche pour l'arôme barbecue dans la banque : une création sur mesure est possible.
> 3. Barbecue + café : un goût rare dans les produits proches (1 produit) et jamais associé au barbecue : une piste originale, à tester.
>    Référence : DEMO-016 Café torréfié (café torréfié, notes grillées, légère amertume ; soluble eau). Aucune référence proche pour l'arôme barbecue dans la banque : une création sur mesure est possible.
>    Laquelle vous tente ? Avez-vous une contrainte : bio, vegan, peu sucré ?

### C24 — « je fais des biscuits, je veux un goût noisette »

- Échec : Type de produit
- Attendu : type `biscuit`, arômes `noisette`, contraintes `—`, comportement `pistes`
- Obtenu : type `biscuits`, arômes `noisette`, contraintes `—`, comportement `creation_sur_mesure|pistes` (etape `pistes`, intention `nouvelle_demande`)
- Réponse :

> Votre projet : biscuits à la noisette.
> J'ai étudié les 50 produits du marché les plus proches de votre projet.
> Notre catalogue ne contient pas de produits de ce type (« biscuits ») : j'ai étudié les produits les plus proches, le marché étudié est donc limité.
> Voici mes pistes :
>
> 1. Noisette seule : un goût franc, facile à reconnaître. 43 des 50 produits les plus proches de votre projet l'utilisent.
>    Aucune référence proche pour l'arôme noisette dans la banque : une création sur mesure est possible.
> 2. Noisette + chocolat : l'association la plus fréquente sur le marché (30 produits sur 43 à la noisette). Un choix rassurant, que les consommateurs connaissent déjà.
>    Référence : DEMO-020 Chocolat noir (cacao intense, notes torréfiées ; poudre). Aucune référence proche pour l'arôme noisette dans la banque : une création sur mesure est possible.
> 3. Noisette + abricot : une association rare sur le marché (1 produit), qui peut vous démarquer tout en restant crédible.
>    Aucune référence proche pour les arômes noisette et abricot dans la banque : une création sur mesure est possible.
>    Laquelle vous tente ? Avez-vous une contrainte : bio, vegan, peu sucré ?

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

## Après les corrections par mécanismes (v2.2.3, 2026-11-12)

Règle suivie : aucune correction au cas par cas (aucun arôme, type ou marque ajouté un par un). Les
mécanismes corrigés sont décrits dans `docs/v2_notes.md`, section V2.2.3, et testés dans
`tests/test_mecanismes.py`. Les seuils ont été calibrés sur des exemples propres, distincts des
30 cas ; le jeu de test caché n'a pas été utilisé.

- **Résultat :** 26/30 cas entièrement réussis (18/30 avant) ; aucun cas perdu ; cas flous ou
  hors sujet : 5/5 (0/5 avant) ; arôme principal : 100 % (77 % avant).
- **Temps :** médiane 0,73 s ; les 5 cas qui appellent llama3.2:3b (mots inconnus) prennent de
  3,5 à 6 s.

Échecs restants :

| Cas | Obtenu                      | Commentaire                                                                                                                                                                                       |
| --- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C05 | type « boisson pétillante » | « eau aromatisée » est rattachée par bge-m3 au type le plus proche du catalogue (score 0,69), où eaux aromatisées et eaux gazeuses se confondent ; le cas attend « boisson ».                     |
| C11 | contrainte « pour enfants » | **Cas discutable** : « pour enfants » est une contrainte légitime du brief ; le cas n'en attend aucune. Ni le cas ni le moteur ne sont modifiés.                                                  |
| C21 | type « chips »              | **Cas discutable** : « chips » est le type cité par le client, gardé tel quel, avec la mention d'un marché étudié limité ; le cas attend « snack salé ». Ni le cas ni le moteur ne sont modifiés. |
| C24 | type « biscuits »           | Type gardé tel que le client l'a écrit (pluriel) ; le cas attend « biscuit ». Le comparateur est strict.                                                                                          |

Remarques :

- **C04, « un sirop au pamplemousse rose » :** « rose » est aussi relevé comme arôme. La liste
  Fragrance acceptée en Flavors contient « rose ». Le cas reste réussi, puisque l'arôme attendu
  est trouvé.
- **Division :** 29/30. L'un des cas hors sujet reçoit la division `flavors` après l'appel au
  modèle, sans effet sur la réponse.
