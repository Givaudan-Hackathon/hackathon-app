# Contrat d'API — Brique Data (baseline V1)

API de recommandation : un brief client en texte libre → division (Flavors / Fragrance) et top k
produits du catalogue. Version du modèle : `baseline-v1` (mots-clés + TF-IDF).

- **URL de base** : communiquée par l'équipe Data (tunnel ngrok, change à chaque redémarrage du tunnel).
- **Swagger** : `<URL de base>/docs` (schémas complets et exemples exécutables).
- **Format** : JSON en UTF-8. Pas d'authentification. CORS ouvert (`*`), méthodes `GET` et `POST`.

## Ngrok : en-tête à ajouter

L'offre gratuite de ngrok affiche une page d'avertissement aux navigateurs. Pour l'éviter, ajouter
à chaque requête du front l'en-tête `ngrok-skip-browser-warning: true` (déjà autorisé par le CORS).

## `GET /sante`

Vérifie que l'API répond.

```json
{ "statut": "ok", "version_modele": "baseline-v1" }
```

## `POST /recommander`

### Requête

| Champ   | Type    | Obligatoire    | Contraintes                     |
| ------- | ------- | -------------- | ------------------------------- |
| `brief` | string  | oui            | 3 à 500 caractères, en français |
| `k`     | integer | non (défaut 5) | 1 à 20                          |

```json
{ "brief": "sirop goût menthe pour cafés", "k": 2 }
```

### Réponse `200`

| Champ                           | Type                                             | Description                                                                                                                          |
| ------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| `brief`                         | string                                           | Brief reçu                                                                                                                           |
| `division`                      | `"flavors"` \| `"fragrance"` \| `"indeterminee"` | `indeterminee` si le brief ne contient aucun mot-clé ou autant de chaque division ; la recherche porte alors sur les deux catalogues |
| `scores_division`               | `{ "flavors": int, "fragrance": int }`           | Nombre de mots-clés de chaque division trouvés dans le brief                                                                         |
| `recommandations`               | liste (longueur `k`)                             | Triée par `score` décroissant                                                                                                        |
| `recommandations[].code`        | string                                           | Code-barres EAN (identifiant stable)                                                                                                 |
| `recommandations[].nom`         | string \| null                                   | Nom du produit                                                                                                                       |
| `recommandations[].marque`      | string \| null                                   | Marque(s), séparées par des virgules                                                                                                 |
| `recommandations[].categorie`   | string                                           | Voir la liste ci-dessous                                                                                                             |
| `recommandations[].format`      | `"poudre"` \| `"pret_a_boire"` \| null           | Renseigné uniquement pour `boissons_proteinees`                                                                                      |
| `recommandations[].score`       | number                                           | Similarité entre 0 et 1, à 3 décimales                                                                                               |
| `recommandations[].url_produit` | string                                           | Fiche du produit sur Open Food Facts / Open Beauty Facts                                                                             |
| `version_modele`                | string                                           | `baseline-v1`                                                                                                                        |
| `attribution`                   | string                                           | Mention de licence **à afficher** (voir plus bas)                                                                                    |

```json
{
  "brief": "sirop goût menthe pour cafés",
  "division": "flavors",
  "scores_division": { "flavors": 4, "fragrance": 0 },
  "recommandations": [
    {
      "code": "3660668209510",
      "nom": "Sirop de Menthe",
      "marque": "Frigolet",
      "categorie": "boissons_aromatisees",
      "format": null,
      "score": 0.42,
      "url_produit": "https://world.openfoodfacts.org/product/3660668209510"
    },
    {
      "code": "3092712200226",
      "nom": "Sirop de Menthe Verte",
      "marque": "Teisseire",
      "categorie": "boissons_aromatisees",
      "format": null,
      "score": 0.399,
      "url_produit": "https://world.openfoodfacts.org/product/3092712200226"
    }
  ],
  "version_modele": "baseline-v1",
  "attribution": "Contient des données d'Open Food Facts / Open Beauty Facts, licence ODbL"
}
```

### Valeurs de `categorie`

- Flavors : `boissons_proteinees`, `boissons_vegetales`, `boissons_lactees`, `desserts_aromatises`, `boissons_aromatisees`
- Fragrance : `parfums`, `savons`, `gels_douche`, `deodorants`, `shampoings_gels_douche`, `savons_rasage`

### Erreurs

| Code  | Cas                                                          | Corps                                                                            |
| ----- | ------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| `422` | `brief` absent, trop court ou trop long ; `k` hors de 1 à 20 | Format FastAPI : `{ "detail": [{ "loc": [...], "msg": "...", "type": "..." }] }` |
| `400` | Corps qui n'est pas du JSON UTF-8 valide                     | `{ "detail": "There was an error parsing the body" }`                            |

## Exemple d'appel (TypeScript)

```ts
const reponse = await fetch(`${API_DATA_URL}/recommander`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true',
  },
  body: JSON.stringify({ brief: 'arôme fraise pour yaourt à boire', k: 5 }),
});
if (!reponse.ok) throw new Error(`API Data : HTTP ${reponse.status}`);
const resultat = await reponse.json();
```

## Obligations et limites

- **Attribution** : les données viennent d'Open Food Facts et d'Open Beauty Facts (licence ODbL).
  Le texte du champ `attribution` doit apparaître dans l'interface qui affiche les recommandations.
- **Qualité V1** : la division est correcte sur les 5 briefs de test, mais la pertinence du top 5
  est inégale (bonne pour « sirop menthe » ou « yaourt à boire fraise », faible pour
  « boisson protéinée base pois »). Le `score` sert à trier, pas à afficher comme une note : les
  valeurs restent basses (souvent inférieures à 0,3) même pour de bons résultats.
- **Stabilité** : les noms de champs ci-dessus ne changeront pas avec la V2 (jeudi). La V2 pourra
  ajouter des champs (application, notes extraites) ; `version_modele` indiquera le modèle utilisé.
- **Catalogue** : 2 193 produits vendus en France. Pas de données de prix, de stock ni de clients.
