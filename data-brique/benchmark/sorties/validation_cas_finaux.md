# Validation sur 10 cas jamais vus (cas_finaux_10.csv) (V2.2, `v2.2.3-mecanismes`)

Mesure du 2026-11-12. Les cas (`benchmark/cas_reference_30.csv`) ont été écrits avant le test et n'ont pas été modifiés. Le résultat **avant correction** (V2.2.2, 18/30) est conservé dans `benchmark/sorties/validation_30_cas_avant.csv`.

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

| Critère                       | Global       | boisson    | autre_produit | flou_hors_sujet |
| ----------------------------- | ------------ | ---------- | ------------- | --------------- |
| Type de produit               | 8/10 (80%)   | 2/3 (67%)  | 3/4 (75%)     | 3/3 (100%)      |
| Arôme(s), tous trouvés        | 9/10 (90%)   | 3/3 (100%) | 3/4 (75%)     | 3/3 (100%)      |
| Arôme principal               | 9/10 (90%)   | 3/3 (100%) | 3/4 (75%)     | 3/3 (100%)      |
| Contraintes (égalité stricte) | 10/10 (100%) | 3/3 (100%) | 4/4 (100%)    | 3/3 (100%)      |
| Comportement                  | 7/10 (70%)   | 3/3 (100%) | 3/4 (75%)     | 1/3 (33%)       |
| Aucune marque citée           | 10/10 (100%) | 3/3 (100%) | 4/4 (100%)    | 3/3 (100%)      |
| Aucun chiffre inventé         | 10/10 (100%) | 3/3 (100%) | 4/4 (100%)    | 3/3 (100%)      |
| Aucun prix inventé            | 10/10 (100%) | 3/3 (100%) | 4/4 (100%)    | 3/3 (100%)      |
| **Cas entièrement réussi**    | 6/10 (60%)   | 2/3 (67%)  | 3/4 (75%)     | 1/3 (33%)       |

Temps de réponse V2.2 : moyenne 2.15 s, médiane 0.89 s, max 6.49 s ; modèle appelé pour 3 cas sur 10 (moyenne 5.77 s ces fois-là, 0.60 s sinon).

## Comparaison V1 / V2.1 / V2.2

| Critère comparable                                     | V1                           | V2.1         | V2.2         |
| ------------------------------------------------------ | ---------------------------- | ------------ | ------------ |
| Division (flavors, ou aucune pour les cas flous)       | 6/10 (60%)                   | 8/10 (80%)   | 9/10 (90%)   |
| Arôme principal                                        | —                            | 7/10 (70%)   | 9/10 (90%)   |
| Arôme(s) attendus dans les 5 produits recommandés (V1) | 3/7 (43%)                    | —            | —            |
| Pistes ou relance, cas qui l'attendent                 | —                            | 7/8 (88%)    | 7/8 (88%)    |
| Aucune marque citée                                    | (produits du commerce : non) | 10/10 (100%) | 10/10 (100%) |
| Temps moyen par cas                                    | < 0,1 s                      | 3.24 s       | 2.15 s       |

## Échecs (réponse obtenue)

### F01 — « on prépare un ice tea maison à la framboise, sans sucre ajouté »

- Échec : Type de produit
- Attendu : type `thé glacé`, arômes `framboise`, contraintes `peu sucré`, comportement `pistes`
- Obtenu : type `—`, arômes `framboise`, contraintes `peu sucré`, comportement `pistes` (etape `pistes`, intention `nouvelle_demande`)
- Réponse :

> Votre projet : à la framboise, peu sucré.
> J'ai étudié les 50 produits du marché les plus proches de votre projet, tous peu sucrés.
> Voici mes pistes :
>
> 1. Framboise seule : un goût franc, facile à reconnaître. 38 des 50 produits les plus proches de votre projet l'utilisent.
>    Référence : DEMO-023 Fruits rouges (fraise, framboise et cassis, fruité, légèrement acidulé ; soluble eau).
> 2. Framboise + fraise : l'association la plus fréquente sur le marché (11 produits sur 38 à la framboise). Un choix rassurant, que les consommateurs connaissent déjà.
>    Référence : DEMO-023 Fruits rouges (fraise, framboise et cassis, fruité, légèrement acidulé ; soluble eau).
> 3. Framboise + abricot : une association rare sur le marché (1 produit), qui peut vous démarquer tout en restant crédible.
>    Référence : DEMO-023 Fruits rouges (fraise, framboise et cassis, fruité, légèrement acidulé ; soluble eau). Aucune référence proche pour l'arôme abricot dans la banque : une création sur mesure est possible.
>    Pour votre contrainte de recette : DEMO-028 Sweetness (renforce la perception sucrée pour réduire le sucre ajouté ; soluble eau).
>    Laquelle vous tente ?

### F07 — « une sauce barbecue fumée »

- Échec : Type de produit, Arôme(s), tous trouvés, Comportement
- Attendu : type `sauce`, arômes `fumé`, contraintes `—`, comportement `pistes`
- Obtenu : type `sauce barbecue fumée`, arômes `—`, contraintes `—`, comportement `relance` (etape `relance`, intention `nouvelle_demande`)
- Réponse :

> J'ai bien noté votre projet : sauce barbecue fumée. Parmi les 50 produits du marché les plus proches, les arômes les plus courants sont : framboise (12 produits), coco (9 produits) et vanille (7 produits). Quel goût recherchez-vous ?

### F09 — « quels sont vos délais pour un échantillon ? »

- Échec : Comportement
- Attendu : type `—`, arômes `—`, contraintes `—`, comportement `question`
- Obtenu : type `—`, arômes `—`, contraintes `—`, comportement `relance` (etape `relance`, intention `demande_echantillons`)
- Réponse :

> Pour vous proposer des échantillons, décrivez-moi d'abord votre projet : quel produit, et quel goût ?

### F10 — « je veux le goût du Nutella »

- Échec : Comportement
- Attendu : type `—`, arômes `—`, contraintes `—`, comportement `hors_sujet (aucune marque)`
- Obtenu : type `—`, arômes `—`, contraintes `—`, comportement `relance` (etape `relance`, intention `nouvelle_demande`)
- Réponse :

> Quel type de produit voulez-vous créer ? Quel goût recherchez-vous ?

## Limites de la mesure

- 30 cas courts, un seul message chacun : la conversation (précisions, retraits, choix) est couverte par les tests pytest, pas par cette validation.
- Critères stricts écrits avant la mesure : un type absent de la liste du moteur (« snack salé », « biscuit ») ou une contrainte en trop compte comme un échec, même si la réponse reste utile.
- Le contrôle « aucun chiffre inventé » vérifie la provenance des nombres, pas leur interprétation dans la phrase.
- Le contrôle des marques porte sur les marques du catalogue Open Food Facts : une marque absente du catalogue ne serait pas détectée.
- V2.1 et V2.2 dépendent d'Ollama (llama3.2:3b, bge-m3) ; résultats obtenus à température 0, sur le CPU de l'équipe.
