# Mesures brutes du benchmark (2026-11-10T14:14:26)

Fichier généré par `benchmark/run_benchmark.py`, ne pas éditer.

## Configuration

| clé              | valeur                               |
| ---------------- | ------------------------------------ |
| os               | Windows 11 (10.0.26200)              |
| cpu              | 13th Gen Intel(R) Core(TM) i5-13420H |
| coeurs_physiques | 8                                    |
| threads          | 12                                   |
| ram_go           | 15.6                                 |
| gpu              | Intel(R) UHD Graphics                |
| python           | 3.12.10                              |
| ollama           | 0.40.16                              |

## Recherche (briefs Flavors)

| modele            | texte_indexe               | indexation_s | cache | chargement_s | vram_octets | categorie_top5_pct | categorie_rang1_pct | precision_top5_pct | arome_dans_nom_top5_pct | ms_par_requete |
| ----------------- | -------------------------- | ------------ | ----- | ------------ | ----------- | ------------------ | ------------------- | ------------------ | ----------------------- | -------------- |
| tfidf (baseline)  | complet                    | 0.5          | False | 0.0          | 0           | 83.3               | 66.7                | 56.7               | 100.0                   | 2.1            |
| nomic-embed-text  | nom + categorie + 300 car. | 156.6        | True  | 0.9          | 0           | 100.0              | 83.3                | 76.7               | 100.0                   | 77.1           |
| bge-m3            | nom + categorie + 300 car. | 587.5        | True  | 3.6          | 0           | 100.0              | 100.0               | 86.7               | 91.7                    | 78.9           |
| mxbai-embed-large | nom + categorie + 300 car. | 735.8        | True  | 1.2          | 0           | 100.0              | 75.0                | 63.3               | 83.3                    | 94.2           |

## Extraction LLM (15 briefs)

| modele               | chargement_s | vram_octets | division_pct | json_valide_pct | arome_principal_pct | s_par_brief |
| -------------------- | ------------ | ----------- | ------------ | --------------- | ------------------- | ----------- |
| mots-cles (baseline) | 0.0          | 0           | 93.3         |                 |                     | 0.0         |
| qwen2.5:1.5b         | 5.4          | 0           | 93.3         | 100.0           | 86.7                | 1.8         |
| qwen2.5:3b           | 8.5          | 0           | 100.0        | 100.0           | 86.7                | 2.9         |
| llama3.2:3b          | 12.3         | 0           | 100.0        | 100.0           | 100.0               | 4.0         |

## Top 3 par brief

### 1. Je lance une marque de desserts végétaux et je cherche un goût pistache gourmand, pas trop sucré

| modele            | rang | product_name                                  | query_category       | score  |
| ----------------- | ---- | --------------------------------------------- | -------------------- | ------ |
| tfidf (baseline)  | 1    | Flan entremets Pistache                       | desserts_aromatises  | 0.0978 |
| tfidf (baseline)  | 2    | Boisson rafraîchissante aux extraits végétaux | boissons_aromatisees | 0.0969 |
| tfidf (baseline)  | 3    | Milkshake minceur chocolat                    | boissons_lactees     | 0.0724 |
| nomic-embed-text  | 1    | Flan entremets Pistache                       | desserts_aromatises  | 0.7513 |
| nomic-embed-text  | 2    | Dessert végétal soja au chocolat, brique 530g | boissons_vegetales   | 0.7376 |
| nomic-embed-text  | 3    | Dessert végétal soja au chocolat, brique 530g | boissons_vegetales   | 0.7352 |
| bge-m3            | 1    | Flan entremets Pistache                       | desserts_aromatises  | 0.5681 |
| bge-m3            | 2    | Dessert végétal au lait de coco               | desserts_aromatises  | 0.5582 |
| bge-m3            | 3    | Gourmand & Végétal Ananas                     | desserts_aromatises  | 0.538  |
| mxbai-embed-large | 1    | Dessert végétal, Noisettes Amandes (4 Pots)   | desserts_aromatises  | 0.7365 |
| mxbai-embed-large | 2    | Flan entremets Pistache                       | desserts_aromatises  | 0.7355 |
| mxbai-embed-large | 3    | Dessert végétal soja au chocolat, brique 530g | boissons_vegetales   | 0.732  |

### 2. boisson protéinée vanille pour sportifs, base pois

| modele            | rang | product_name                                                   | query_category      | score  |
| ----------------- | ---- | -------------------------------------------------------------- | ------------------- | ------ |
| tfidf (baseline)  | 1    | Boisson au soja vanille                                        | boissons_vegetales  | 0.1031 |
| tfidf (baseline)  | 2    | Boisson Soja Vanille                                           | boissons_vegetales  | 0.0926 |
| tfidf (baseline)  | 3    | Barista avoine vanille                                         | boissons_vegetales  | 0.0904 |
| nomic-embed-text  | 1    | Mix De Protéines à La Vanille Et Banane Bio - 400 G - Purasana | boissons_proteinees | 0.7849 |
| nomic-embed-text  | 2    | Bio Protein Vanille                                            | boissons_proteinees | 0.7848 |
| nomic-embed-text  | 3    | Proteine                                                       | boissons_proteinees | 0.773  |
| bge-m3            | 1    | Mix De Protéines à La Vanille Et Banane Bio - 400 G - Purasana | boissons_proteinees | 0.6988 |
| bge-m3            | 2    | Bio Protein Vanille                                            | boissons_proteinees | 0.6776 |
| bge-m3            | 3    | Protein Warrior Blend Vanille                                  | boissons_proteinees | 0.6638 |
| mxbai-embed-large | 1    | Sportéus saveur Vanille                                        | boissons_lactees    | 0.7892 |
| mxbai-embed-large | 2    | 100% Whey Poudre De Protéine, 907 G, Crème à La Vanille        | boissons_proteinees | 0.778  |
| mxbai-embed-large | 3    | Protein Warrior Blend Vanille                                  | boissons_proteinees | 0.7639 |

### 3. arôme fraise pour yaourt à boire

| modele            | rang | product_name                                            | query_category      | score  |
| ----------------- | ---- | ------------------------------------------------------- | ------------------- | ------ |
| tfidf (baseline)  | 1    | Yaourt à boire fermier Fraise                           | boissons_lactees    | 0.2134 |
| tfidf (baseline)  | 2    | Yaourt a boiresaveur fraise                             | boissons_lactees    | 0.1958 |
| tfidf (baseline)  | 3    | Yaourt à boire fraise                                   | boissons_lactees    | 0.1908 |
| nomic-embed-text  | 1    | Yaourt à boire bio et local - Fraise                    | boissons_lactees    | 0.7524 |
| nomic-embed-text  | 2    | Yaourt à boire fermier Fraise                           | boissons_lactees    | 0.7499 |
| nomic-embed-text  | 3    | Yaourts Panier De Yoplait Fruits Rouges 12 Pots De 125g | desserts_aromatises | 0.7462 |
| bge-m3            | 1    | Yaourt à boire saveur fraise                            | boissons_lactees    | 0.7119 |
| bge-m3            | 2    | Yaourt a boiresaveur fraise                             | boissons_lactees    | 0.7099 |
| bge-m3            | 3    | Yaourt a boire fraise                                   | boissons_lactees    | 0.7025 |
| mxbai-embed-large | 1    | Yaourt a boire fraise                                   | boissons_lactees    | 0.7471 |
| mxbai-embed-large | 2    | Yaourt à boire fraise                                   | boissons_lactees    | 0.7446 |
| mxbai-embed-large | 3    | Yaourt à boire aromatisé Goût Fraise                    | boissons_lactees    | 0.7436 |

### 4. sirop goût menthe pour cafés

| modele            | rang | product_name                         | query_category       | score  |
| ----------------- | ---- | ------------------------------------ | -------------------- | ------ |
| tfidf (baseline)  | 1    | Sirop de Menthe                      | boissons_aromatisees | 0.4198 |
| tfidf (baseline)  | 2    | Sirop de Menthe Verte                | boissons_aromatisees | 0.3995 |
| tfidf (baseline)  | 3    | Sirop Menthe                         | boissons_aromatisees | 0.3189 |
| nomic-embed-text  | 1    | Sirop Menthe                         | boissons_aromatisees | 0.6716 |
| nomic-embed-text  | 2    | Sirop de Menthe Verte                | boissons_aromatisees | 0.6611 |
| nomic-embed-text  | 3    | Sirop de Menthe                      | boissons_aromatisees | 0.6568 |
| bge-m3            | 1    | Sirop de Menthe Verte                | boissons_aromatisees | 0.6787 |
| bge-m3            | 2    | Sirop Menthe                         | boissons_aromatisees | 0.6768 |
| bge-m3            | 3    | Sirop de Menthe                      | boissons_aromatisees | 0.6759 |
| mxbai-embed-large | 1    | Thé Glacé Goût Mangue                | boissons_aromatisees | 0.7312 |
| mxbai-embed-large | 2    | Yaourt à boire aromatisé Goût Fraise | boissons_lactees     | 0.6955 |
| mxbai-embed-large | 3    | Mini Yop Gôut Fraise                 | boissons_lactees     | 0.6914 |

### 5. un shake protéiné à prendre après la muscu, goût chocolat

| modele            | rang | product_name                                                                                              | query_category      | score  |
| ----------------- | ---- | --------------------------------------------------------------------------------------------------------- | ------------------- | ------ |
| tfidf (baseline)  | 1    | Protein Shake 330ML Chocolat                                                                              | boissons_proteinees | 0.0906 |
| tfidf (baseline)  | 2    | Soy Protein Isolate 90 Biscuit Choco-Caramel                                                              | boissons_proteinees | 0.0769 |
| tfidf (baseline)  | 3    | Impact Whey Protein, Blueberry and Raspberry Stevia                                                       | boissons_proteinees | 0.0767 |
| nomic-embed-text  | 1    | Milk-shake Chocolat, Riches En Protéines, Repas Minceur, Les 9 Milk-shakes De 30 Grammes, Marque Gerlinéa | boissons_proteinees | 0.7864 |
| nomic-embed-text  | 2    | Protein Shake 330ML Chocolat                                                                              | boissons_proteinees | 0.7783 |
| nomic-embed-text  | 3    | Whey Protein goût Chocolat                                                                                | boissons_proteinees | 0.7748 |
| bge-m3            | 1    | Protein Shake 330ML Chocolat                                                                              | boissons_proteinees | 0.6719 |
| bge-m3            | 2    | Shape Shake Protein, Schokolade                                                                           | boissons_proteinees | 0.6656 |
| bge-m3            | 3    | Milk-shake Chocolat, Riches En Protéines, Repas Minceur, Les 9 Milk-shakes De 30 Grammes, Marque Gerlinéa | boissons_proteinees | 0.6613 |
| mxbai-embed-large | 1    | Milk-shake Chocolat, Riches En Protéines, Repas Minceur, Les 9 Milk-shakes De 30 Grammes, Marque Gerlinéa | boissons_proteinees | 0.8272 |
| mxbai-embed-large | 2    | Whey* - Goût Chocolat. *WHEY = Protéines de lactosérum.                                                   | boissons_proteinees | 0.8165 |
| mxbai-embed-large | 3    | Whey Protein goût Chocolat                                                                                | boissons_proteinees | 0.8069 |

### 6. une boisson sans lait pour le petit-déjeuner, goût noisette

| modele            | rang | product_name                                                    | query_category       | score  |
| ----------------- | ---- | --------------------------------------------------------------- | -------------------- | ------ |
| tfidf (baseline)  | 1    | Noisette sans sucres                                            | boissons_vegetales   | 0.1319 |
| tfidf (baseline)  | 2    | Boisson végétale Noisette au chocolat                           | boissons_vegetales   | 0.1158 |
| tfidf (baseline)  | 3    | Boisson sans théine saveur pêche abricot                        | boissons_aromatisees | 0.1079 |
| nomic-embed-text  | 1    | Boisson gourmande Amandes noisettes                             | boissons_vegetales   | 0.7394 |
| nomic-embed-text  | 2    | Boisson végétale Noisette au chocolat                           | boissons_vegetales   | 0.7281 |
| nomic-embed-text  | 3    | Petit Filou Gourde Fraise 80G                                   | boissons_lactees     | 0.7184 |
| bge-m3            | 1    | Noisette sans sucres                                            | boissons_vegetales   | 0.6416 |
| bge-m3            | 2    | Lait de noisette cacao                                          | boissons_vegetales   | 0.6232 |
| bge-m3            | 3    | Gout chocolat noisette                                          | boissons_vegetales   | 0.618  |
| mxbai-embed-large | 1    | Mini Yop Gôut Fraise                                            | boissons_lactees     | 0.7537 |
| mxbai-embed-large | 2    | Gout chocolat noisette                                          | boissons_vegetales   | 0.7522 |
| mxbai-embed-large | 3    | Petits Filous Tub's Goûts Myrtille et Abricot (édition limitée) | boissons_lactees     | 0.7476 |

### 7. une petite crème qui a le goût d'enfance, comme chez mamie

| modele            | rang | product_name                                                    | query_category       | score  |
| ----------------- | ---- | --------------------------------------------------------------- | -------------------- | ------ |
| tfidf (baseline)  | 1    | Strawberry                                                      | boissons_aromatisees | 0.092  |
| tfidf (baseline)  | 2    | Whey protéines                                                  | boissons_proteinees  | 0.0904 |
| tfidf (baseline)  | 3    | Milical Pur Protéines Vanille                                   | boissons_proteinees  | 0.0839 |
| nomic-embed-text  | 1    | Petits Filous (Magic Duo Goût Framboise & Goût Vanille)         | desserts_aromatises  | 0.6878 |
| nomic-embed-text  | 2    | Petits Filous Tub's Goûts Myrtille et Abricot (édition limitée) | boissons_lactees     | 0.676  |
| nomic-embed-text  | 3    | 1L Sirop Peche Giffard                                          | boissons_aromatisees | 0.6718 |
| bge-m3            | 1    | CREME BRULEE 4x100g                                             | desserts_aromatises  | 0.574  |
| bge-m3            | 2    | Crème brûlée                                                    | desserts_aromatises  | 0.5672 |
| bge-m3            | 3    | MINI YAB saveurs 4 fraise banane 4 pêche abricot                | boissons_lactees     | 0.5645 |
| mxbai-embed-large | 1    | Petits Filous (Magic Duo Goût Framboise & Goût Vanille)         | desserts_aromatises  | 0.746  |
| mxbai-embed-large | 2    | Petits Filous Tub's Goûts Myrtille et Abricot (édition limitée) | boissons_lactees     | 0.7394 |
| mxbai-embed-large | 3    | Mini Yop Gôut Fraise                                            | boissons_lactees     | 0.6981 |

### 8. une limonade pétillante au citron pour l'été

| modele            | rang | product_name                  | query_category       | score  |
| ----------------- | ---- | ----------------------------- | -------------------- | ------ |
| tfidf (baseline)  | 1    | Pétillante Saveur Citron vert | boissons_aromatisees | 0.2091 |
| tfidf (baseline)  | 2    | Limonade                      | boissons_aromatisees | 0.1763 |
| tfidf (baseline)  | 3    | 1L LIMONADE ARTISANAL LORINA  | boissons_aromatisees | 0.1548 |
| nomic-embed-text  | 1    | Limonade                      | boissons_aromatisees | 0.7587 |
| nomic-embed-text  | 2    | Hamoud Limonade 1.5L PET      | boissons_aromatisees | 0.7469 |
| nomic-embed-text  | 3    | 1L LIMONADE ARTISANAL LORINA  | boissons_aromatisees | 0.7417 |
| bge-m3            | 1    | Lemonade Lemon                | boissons_aromatisees | 0.5979 |
| bge-m3            | 2    | Limonade à la myrtille        | boissons_aromatisees | 0.5867 |
| bge-m3            | 3    | Limonade                      | boissons_aromatisees | 0.5833 |
| mxbai-embed-large | 1    | Pétillante Saveur Citron vert | boissons_aromatisees | 0.7789 |
| mxbai-embed-large | 2    | Limonade                      | boissons_aromatisees | 0.765  |
| mxbai-embed-large | 3    | Hamoud Limonade 1.5L PET      | boissons_aromatisees | 0.7636 |

### 9. un lait chocolaté pour le goûter des enfants

| modele            | rang | product_name                                           | query_category      | score  |
| ----------------- | ---- | ------------------------------------------------------ | ------------------- | ------ |
| tfidf (baseline)  | 1    | lait chocolaté                                         | boissons_lactees    | 0.2721 |
| tfidf (baseline)  | 2    | Impact Whey Protein, Natural Chocolate                 | boissons_proteinees | 0.0839 |
| tfidf (baseline)  | 3    | Whey protein Chocolate                                 | boissons_proteinees | 0.079  |
| nomic-embed-text  | 1    | RÉCRÉ O'LÉ Goûter laitier Gourdes Multivariétés 12x85g | desserts_aromatises | 0.7546 |
| nomic-embed-text  | 2    | Amande Chocolatée                                      | boissons_vegetales  | 0.7475 |
| nomic-embed-text  | 3    | lait chocolaté                                         | boissons_lactees    | 0.7446 |
| bge-m3            | 1    | Matin léger - Boisson au lait au chocolat              | boissons_lactees    | 0.6419 |
| bge-m3            | 2    | Dessert lacté au lait de brebis et au chocolat 2x115g  | desserts_aromatises | 0.6302 |
| bge-m3            | 3    | lait chocolaté                                         | boissons_lactees    | 0.6237 |
| mxbai-embed-large | 1    | RÉCRÉ O'LÉ Goûter laitier Gourdes Multivariétés 12x85g | desserts_aromatises | 0.7474 |
| mxbai-embed-large | 2    | MON PREMIER CACOLAC BRICK 20 CL                        | boissons_lactees    | 0.7369 |
| mxbai-embed-large | 3    | Candy'up Edition Limitée                               | boissons_lactees    | 0.7365 |

### 10. une boisson au soja goût vanille pour une clientèle vegan

| modele            | rang | product_name                                  | query_category     | score  |
| ----------------- | ---- | --------------------------------------------- | ------------------ | ------ |
| tfidf (baseline)  | 1    | Boisson au soja vanille                       | boissons_vegetales | 0.3717 |
| tfidf (baseline)  | 2    | Boisson Soja Vanille                          | boissons_vegetales | 0.3341 |
| tfidf (baseline)  | 3    | Boisson au soja vanille                       | boissons_vegetales | 0.3042 |
| nomic-embed-text  | 1    | Boissons soja vanille                         | boissons_vegetales | 0.7927 |
| nomic-embed-text  | 2    | Boisson bio au soja saveur vanille            | boissons_vegetales | 0.7867 |
| nomic-embed-text  | 3    | Boisson Soja Vanille                          | boissons_vegetales | 0.786  |
| bge-m3            | 1    | Soja vanille                                  | boissons_vegetales | 0.6944 |
| bge-m3            | 2    | Boissons soja vanille                         | boissons_vegetales | 0.6935 |
| bge-m3            | 3    | Soja Vanille bio                              | boissons_vegetales | 0.6932 |
| mxbai-embed-large | 1    | Dessert végétal soja au chocolat, brique 530g | boissons_vegetales | 0.7792 |
| mxbai-embed-large | 2    | Dessert végétal soja au chocolat, brique 530g | boissons_vegetales | 0.779  |
| mxbai-embed-large | 3    | Boisson au soja vanille                       | boissons_vegetales | 0.7697 |

### 11. une eau avec un petit goût de fruits rouges, sans sucre

| modele            | rang | product_name                                            | query_category       | score  |
| ----------------- | ---- | ------------------------------------------------------- | -------------------- | ------ |
| tfidf (baseline)  | 1    | Soja fruits rouges                                      | desserts_aromatises  | 0.216  |
| tfidf (baseline)  | 2    | Sirop de fruits rouges                                  | boissons_aromatisees | 0.199  |
| tfidf (baseline)  | 3    | Sirop de Grenadine                                      | boissons_aromatisees | 0.1957 |
| nomic-embed-text  | 1    | Petits Filous (Magic Duo Goût Framboise & Goût Vanille) | desserts_aromatises  | 0.7476 |
| nomic-embed-text  | 2    | Sirop de fruits rouges                                  | boissons_aromatisees | 0.7449 |
| nomic-embed-text  | 3    | Sirop grenadine au sucre de canne                       | boissons_aromatisees | 0.7393 |
| bge-m3            | 1    | Jelly Babies                                            | boissons_aromatisees | 0.65   |
| bge-m3            | 2    | Sirop de fruits rouges                                  | boissons_aromatisees | 0.6372 |
| bge-m3            | 3    | Noisette sans sucres                                    | boissons_vegetales   | 0.6243 |
| mxbai-embed-large | 1    | Soda goût Citron-Citron Vert                            | boissons_aromatisees | 0.7607 |
| mxbai-embed-large | 2    | Leche y fruta (sin grasas)                              | boissons_lactees     | 0.75   |
| mxbai-embed-large | 3    | Thé Glacé Goût Mangue                                   | boissons_aromatisees | 0.743  |

### 12. un yaourt onctueux à la noix de coco

| modele            | rang | product_name                                                                          | query_category      | score  |
| ----------------- | ---- | ------------------------------------------------------------------------------------- | ------------------- | ------ |
| tfidf (baseline)  | 1    | Riz noix de coco                                                                      | boissons_vegetales  | 0.3156 |
| tfidf (baseline)  | 2    | Boisson à base de noix de coco                                                        | boissons_vegetales  | 0.2778 |
| tfidf (baseline)  | 3    | Boisson biologique à base de riz et noix de coco sans gluten                          | boissons_vegetales  | 0.242  |
| nomic-embed-text  | 1    | Yaourts Fermiers Noix de Coco                                                         | desserts_aromatises | 0.7817 |
| nomic-embed-text  | 2    | Yaourt au lait entier à l'arôme naturel de : fraise - citron - noix de coco - vanille | desserts_aromatises | 0.7408 |
| nomic-embed-text  | 3    | Yaourt au lait entier saveur coco                                                     | desserts_aromatises | 0.7375 |
| bge-m3            | 1    | Yaourt au lait entier saveur coco                                                     | desserts_aromatises | 0.6496 |
| bge-m3            | 2    | Yaourts Fermiers Noix de Coco                                                         | desserts_aromatises | 0.6461 |
| bge-m3            | 3    | Yaourt à boire YOP parfum coco                                                        | boissons_lactees    | 0.6285 |
| mxbai-embed-large | 1    | Yaourts Fermiers Noix de Coco                                                         | desserts_aromatises | 0.8359 |
| mxbai-embed-large | 2    | Yaourt au lait entier saveur coco                                                     | desserts_aromatises | 0.781  |
| mxbai-embed-large | 3    | Yaourt au lait entier à l'arôme naturel de : fraise - citron - noix de coco - vanille | desserts_aromatises | 0.7673 |

## Sorties LLM

| id  | modele       | sortie                                                                                                                                                                                             | division_ok | arome_ok | secondes |
| --- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | -------- | -------- |
| 1   | qwen2.5:1.5b | { "division": "flavors", "application": "dessert", "aromes": ["pistache", "gourmand"], "contraintes": ["vegétal", "non sucré"] }                                                                   | True        | True     | 2.24     |
| 2   | qwen2.5:1.5b | { "division": "flavors", "application": "soupe", "aromes": ["vanille"], "contraintes": ["sucre", "origine française", "sportif"] }                                                                 | True        | True     | 2.07     |
| 3   | qwen2.5:1.5b | { "division": "flavors", "application": "yaourt", "aromes": ["fruits", "sour", "creme"], "contraintes": [] }                                                                                       | True        | False    | 1.86     |
| 4   | qwen2.5:1.5b | { "division": "flavors", "application": "boisson", "aromes": ["menthe"], "contraintes": [] }                                                                                                       | True        | True     | 1.48     |
| 5   | qwen2.5:1.5b | { "division": "flavors", "application": "shake", "aromes": ["chocolat"], "contraintes": ["sucre", "origine française", "santé", "prix raisonnable"] }                                              | True        | True     | 1.88     |
| 6   | qwen2.5:1.5b | { "division": "flavors", "application": "boisson", "aromes": ["noisette"], "contraintes": [] }                                                                                                     | True        | True     | 1.33     |
| 7   | qwen2.5:1.5b | { "division": "flavors", "application": "biscuit", "aromes": ["anis", "coco", "chocolat", "clou de girofle"], "contraintes": [] }                                                                  | True        | False    | 2.1      |
| 8   | qwen2.5:1.5b | { "division": "flavors", "application": "limonade", "aromes": ["citron", "limon", "pétillant"], "contraintes": ["sucre", "origine locale", "été", "low calorie"] }                                 | True        | True     | 2.68     |
| 9   | qwen2.5:1.5b | { "division": "flavors", "application": "lait", "aromes": ["chocolat", "léger"], "contraintes": ["sourcé en France", "sans sucre", "pour enfants"] }                                               | True        | True     | 2.17     |
| 10  | qwen2.5:1.5b | { "division": "flavors", "application": "boisson", "aromes": ["vanille"], "contraintes": ["vegan"] }                                                                                               | True        | True     | 1.4      |
| 11  | qwen2.5:1.5b | { "division": "flavors", "application": "eau", "aromes": ["fruit rouge"], "contraintes": [] }                                                                                                      | True        | True     | 1.31     |
| 12  | qwen2.5:1.5b | { "division": "flavors", "application": "yogurt", "aromes": ["coco", "savoureux"], "contraintes": ["vegan", "low-fat", "natural"] }                                                                | True        | True     | 1.78     |
| 13  | qwen2.5:1.5b | { "division": "flavors", "application": "savon", "aromes": ["lavande"], "contraintes": ["faits main"] }                                                                                            | False       | True     | 1.47     |
| 14  | qwen2.5:1.5b | { "division": "fragrance", "application": "shampoing", "aromes": ["citron", "orange", "pamplemousse"], "contraintes": [] }                                                                         | True        | True     | 1.58     |
| 15  | qwen2.5:1.5b | { "division": "fragrance", "application": "parfum", "aromes": ["fleuri", "léger"], "contraintes": [] }                                                                                             | True        | True     | 1.46     |
| 1   | qwen2.5:3b   | { "division": "flavors", "application": "biscuit", "aromes": ["pistache", "gourmand", "pas trop sucré"], "contraintes": [] }                                                                       | True        | True     | 3.26     |
| 2   | qwen2.5:3b   | { "division": "flavors", "application": "boisson", "aromes": ["vanille", "amande"], "contraintes": [] }                                                                                            | True        | True     | 2.6      |
| 3   | qwen2.5:3b   | { "division": "flavors", "application": "yaourt à boire", "aromes": ["fraise", "yaourt"], "contraintes": [] }                                                                                      | True        | True     | 2.71     |
| 4   | qwen2.5:3b   | { "division": "flavors", "application": "sirop", "aromes": ["menthe", "café"], "contraintes": [] }                                                                                                 | True        | True     | 2.53     |
| 5   | qwen2.5:3b   | { "division": "flavors", "application": "shake", "aromes": ["chocolat", "protéiné"], "contraintes": [] }                                                                                           | True        | True     | 2.72     |
| 6   | qwen2.5:3b   | { "division": "flavors", "application": "boisson", "aromes": ["noisette", "amande"], "contraintes": [] }                                                                                           | True        | True     | 2.74     |
| 7   | qwen2.5:3b   | { "division": "flavors", "application": "crème", "aromes": ["vanille", "chocolat"], "contraintes": [] }                                                                                            | True        | True     | 2.76     |
| 8   | qwen2.5:3b   | { "division": "flavors", "application": "boisson", "aromes": ["limon", "citron"], "contraintes": [] }                                                                                              | True        | False    | 3.04     |
| 9   | qwen2.5:3b   | { "division": "flavors", "application": "boisson", "aromes": ["chocolat", "vanille"], "contraintes": [] }                                                                                          | True        | True     | 2.94     |
| 10  | qwen2.5:3b   | { "division": "flavors", "application": "boisson", "aromes": ["vanille", "soja"], "contraintes": [] }                                                                                              | True        | True     | 2.64     |
| 11  | qwen2.5:3b   | { "division": "flavors", "application": "boisson", "aromes": ["fraise", "grenat"], "contraintes": [ "sans sucre" ] }                                                                               | True        | False    | 3.31     |
| 12  | qwen2.5:3b   | { "division": "flavors", "application": "yaourt", "aromes": ["noix de coco", "onctuosité"], "contraintes": [] }                                                                                    | True        | True     | 3.42     |
| 13  | qwen2.5:3b   | { "division": "fragrance", "application": "savon", "aromes": ["lavande", "eucalyptus"], "contraintes": [] }                                                                                        | True        | True     | 3.17     |
| 14  | qwen2.5:3b   | { "division": "fragrance", "application": "gel douche", "aromes": ["agrumes", "jus d'orange"], "contraintes": [] }                                                                                 | True        | True     | 2.84     |
| 15  | qwen2.5:3b   | { "division": "fragrance", "application": "parfum pour femme", "aromes": ["fleurie", "léger"], "contraintes": [] }                                                                                 | True        | True     | 3.36     |
| 1   | llama3.2:3b  | { "division" : "flavors", "application" : "décoration de desserts végétaux", "aromes" : ["pistache", "gourmand", "froide"], "contraintes" : ["pas trop sucré", "origine végétale"] }               | True        | True     | 5.79     |
| 2   | llama3.2:3b  | { "division" : "flavors", "application" : "boisson", "aromes" : ["vanille", "protéine", "fruits rouges"], "contraintes" : ["sucre réduit", "origine naturelle", "gluten libre", "cible sportif"] } | True        | True     | 5.6      |
| 3   | llama3.2:3b  | { "division" : "flavors", "application" : "yaourt", "aromes" : ["fraise", "citron"], "contraintes" : [] }                                                                                          | True        | True     | 3.75     |
| 4   | llama3.2:3b  | { "division" : "flavors", "application" : "sirop", "aromes" : ["menthe", "froide", "énergisant"], "contraintes" : [] }                                                                             | True        | True     | 4.41     |
| 5   | llama3.2:3b  | { "division" : "flavors", "application" : "shake protéiné", "aromes" : ["chocolat", "vanille"], "contraintes" : [] }                                                                               | True        | True     | 4.07     |
| 6   | llama3.2:3b  | { "division" : "flavors", "application" : "boisson", "aromes" : ["noisette", "caramel", "vanille"], "contraintes" : [] }                                                                           | True        | True     | 4.16     |
| 7   | llama3.2:3b  | { "division" : "flavors", "application" : "crème", "aromes" : ["vanille", "caramel", "cannelle"], "contraintes" : [] }                                                                             | True        | True     | 3.68     |
| 8   | llama3.2:3b  | { "division" : "flavors", "application" : "limonade", "aromes" : ["citron", "froide", "été"], "contraintes" : [] }                                                                                 | True        | True     | 3.61     |
| 9   | llama3.2:3b  | { "division" : "flavors", "application" : "lait", "aromes" : ["chocolat", "caramel", "vanille"], "contraintes" : [] }                                                                              | True        | True     | 3.53     |
| 10  | llama3.2:3b  | { "division" : "flavors", "application" : "boisson", "aromes" : ["vanille", "soja", "creme"], "contraintes" : ["vegan", "sucre absent"] }                                                          | True        | True     | 4.1      |
| 11  | llama3.2:3b  | { "division" : "flavors", "application" : "eau", "aromes" : ["fruits rouges", "citron"], "contraintes" : ["sans sucre"] }                                                                          | True        | True     | 3.64     |
| 12  | llama3.2:3b  | { "division" : "flavors", "application" : "yaourt", "aromes" : ["noix de coco", "vanille", "caramel"], "contraintes" : [] }                                                                        | True        | True     | 3.6      |
| 13  | llama3.2:3b  | { "division" : "fragrance", "application" : "savon", "aromes" : ["lavande", "herbace"], "contraintes" : [] }                                                                                       | True        | True     | 3.28     |
| 14  | llama3.2:3b  | { "division" : "fragrance", "application" : "gel douche", "aromes" : ["citron", "orange", "bergamote"], "contraintes" : [] }                                                                       | True        | True     | 3.41     |
| 15  | llama3.2:3b  | { "division" : "fragrance", "application" : "parfum", "aromes" : ["fleur", "citron", "vanille"], "contraintes" : [] }                                                                              | True        | True     | 3.62     |
