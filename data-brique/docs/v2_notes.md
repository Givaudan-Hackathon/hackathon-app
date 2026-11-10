# Moteur V2 — notes

Code : `src/moteur_v2.py` (classe `MoteurV2`, même format de sortie que `MoteurV1`).
Démo : `python demo_bot.py`, depuis `data-brique/`, avec le venv activé et Ollama lancé.

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
- **Un seul produit pistache dans `sample_v1`**, contre 30 dans le catalogue complet. Il faudra
  indexer le catalogue complet pour la V2 finale.
- **Temps de réponse.** Le premier appel prend environ 15 s, le temps de charger les modèles ;
  ensuite, 3 à 5 s par brief, sur CPU.
- **API.** L'API (port 8000) sert encore la V1. Le passage de l'API à la V2 n'est pas fait.
