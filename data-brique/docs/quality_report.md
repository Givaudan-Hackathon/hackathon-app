# Rapport qualite — echantillon v1

2193 produits uniques (`data/processed/sample_v1.csv`).

## flavors (1000 produits)

| champ            | taux de remplissage |
| ---------------- | ------------------- |
| product_name     | 99%                 |
| brands           | 97%                 |
| categories_tags  | 100%                |
| labels_tags      | 74%                 |
| ingredients_text | 100%                |

- Mention arome / parfum dans les ingredients : **100%**
- Longueur mediane ingredients_text : 227 caracteres

| query_category       | produits | marque remplie | mention arome / parfum |
| -------------------- | -------- | -------------- | ---------------------- |
| boissons_aromatisees | 200      | 96%            | 100%                   |
| boissons_lactees     | 200      | 98%            | 100%                   |
| boissons_proteinees  | 200      | 98%            | 100%                   |
| boissons_vegetales   | 200      | 98%            | 100%                   |
| desserts_aromatises  | 200      | 96%            | 100%                   |

- Format des boissons proteinees : poudre 154, pret_a_boire 46 (heuristique nom + tags, quelques erreurs observees)

## fragrance (1193 produits)

| champ            | taux de remplissage |
| ---------------- | ------------------- |
| product_name     | 98%                 |
| brands           | 98%                 |
| categories_tags  | 100%                |
| labels_tags      | 60%                 |
| ingredients_text | 100%                |

- Mention arome / parfum dans les ingredients : **92%**
- Longueur mediane ingredients_text : 303 caracteres

| query_category         | produits | marque remplie | mention arome / parfum |
| ---------------------- | -------- | -------------- | ---------------------- |
| deodorants             | 315      | 99%            | 100%                   |
| gels_douche            | 400      | 99%            | 96%                    |
| parfums                | 88       | 97%            | 97%                    |
| savons                 | 315      | 98%            | 74%                    |
| savons_rasage          | 3        | 100%           | 100%                   |
| shampoings_gels_douche | 72       | 99%            | 100%                   |
