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

---

# Contrat V2 (prévu) — assistant conversationnel V2.2

> **Statut : prévu, pas encore en ligne.** L'API du port 8000 sert toujours la V1 ci-dessus. Ce
> contrat décrit ce que l'endpoint V2 renverra : il reprend la sortie de
> `AssistantV22.repondre()` (`src/moteur_v22.py`). Les champs de la V1 restent inchangés.

## `POST /v2/conversation`

Un message du client par appel. Le serveur garde l'état de la conversation (projet, pistes,
piste choisie) par `conversation_id`.

### Requête

| Champ             | Type    | Obligatoire        | Description                                                            |
| ----------------- | ------- | ------------------ | ---------------------------------------------------------------------- |
| `conversation_id` | string  | non                | Absent : nouvelle conversation (l'identifiant est renvoyé)             |
| `message`         | string  | oui                | 1 à 500 caractères, en français                                        |
| `reformuler`      | boolean | non (défaut false) | `true` : réponse reformulée par llama3.2:3b (environ 5 fois plus lent) |

```json
{
  "conversation_id": "c-42",
  "message": "je prends la piste 1",
  "reformuler": false
}
```

### Réponse `200`

| Champ                                    | Type             | Description                                                                                             |
| ---------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------- |
| `conversation_id`                        | string           | À renvoyer au message suivant                                                                           |
| `intention`                              | string           | `nouvelle_demande`, `precision`, `question_piste`, `choix_piste`, `demande_echantillons`, `hors_sujet`  |
| `texte`                                  | string           | Réponse à afficher au client (paragraphes séparés par `\n`)                                             |
| `projet`                                 | objet            | `division`, `type_de_produit`, `arome_principal`, `profil_recherche[]`, `contraintes[]`                 |
| `pistes`                                 | liste (0 à 3)    | Pistes d'arômes, sans produit ni marque du commerce                                                     |
| `pistes[].numero`                        | integer          | 1, 2 ou 3                                                                                               |
| `pistes[].aromes`                        | string           | Ex. `"citron vert"`, `"citron vert + citron"`                                                           |
| `pistes[].explication`                   | string           | Phrase d'explication                                                                                    |
| `pistes[].origine`                       | string           | D'où vient la piste : nombre de produits, association observée, ou « à valider en dégustation »         |
| `pistes[].references`                    | liste            | Références de la banque de démo (vide si aucune ne correspond)                                          |
| `pistes[].references[].code`             | string           | Code fictif `DEMO-001` à `DEMO-030`                                                                     |
| `pistes[].references[].nom`              | string           | Ex. `"Citron vert bio"`                                                                                 |
| `pistes[].references[].profil_sensoriel` | string           | Ex. `"citron vert juteux, frais, légèrement amer"`                                                      |
| `pistes[].references[].forme`            | string           | `soluble eau`, `huile` ou `poudre`                                                                      |
| `pistes[].references[].labels`           | liste de strings | Parmi `naturel`, `vegan`, `bio`, `halal`, `casher`, `sans allergène`                                    |
| `pistes[].sans_reference`                | liste de strings | Arômes sans référence proche : création sur mesure à proposer                                           |
| `solutions`                              | liste            | TasteSolutions ajoutées selon les contraintes (« peu sucré » → Sweetness), même format que `references` |
| `piste_choisie`                          | objet \| null    | `{ "numero", "aromes" }`                                                                                |
| `brief_final`                            | objet \| null    | Après le choix d'une piste, voir ci-dessous                                                             |
| `demande_echantillons`                   | objet \| null    | Récapitulatif à afficher : `brief_final` + `statut` (`"brouillon, non envoyé (prototype)"`) + `date`    |
| `version_modele`                         | string           | `v2.2.1-references`                                                                                     |
| `attribution`                            | string           | Mention ODbL **à afficher**                                                                             |

`brief_final` : `division`, `type_de_produit`, `piste`, `aromes[]`, `profil[]`, `contraintes[]`,
`codes_references[]` (codes DEMO de la piste), `codes_solutions[]` (codes DEMO des solutions),
`creation_sur_mesure[]` (arômes sans référence), `brief_du_client` (messages du client).

Exemple après « je prends la piste 1 » (texte et explications abrégés) :

```json
{
  "conversation_id": "c-42",
  "intention": "choix_piste",
  "texte": "Excellent choix : la piste 1, citron vert. Votre brief : boisson pétillante, arôme citron vert, contraintes : peu sucré et bio. Références retenues : DEMO-004 et DEMO-028. …",
  "projet": {
    "division": "arôme alimentaire",
    "type_de_produit": "boisson pétillante",
    "arome_principal": "citron vert",
    "profil_recherche": [],
    "contraintes": ["peu sucré", "bio"]
  },
  "pistes": [
    {
      "numero": 1,
      "aromes": "citron vert",
      "explication": "Citron vert seul : un goût franc, facile à reconnaître. …",
      "origine": "l'arôme citron vert est utilisé par … boissons pétillantes étudiées",
      "references": [
        {
          "code": "DEMO-004",
          "nom": "Citron vert bio",
          "profil_sensoriel": "citron vert juteux, frais, légèrement amer",
          "forme": "soluble eau",
          "labels": ["naturel", "bio", "vegan"]
        }
      ],
      "sans_reference": []
    }
  ],
  "solutions": [
    {
      "code": "DEMO-028",
      "nom": "Sweetness",
      "profil_sensoriel": "renforce la perception sucrée pour réduire le sucre ajouté",
      "forme": "soluble eau",
      "labels": ["naturel", "vegan", "halal", "casher"]
    }
  ],
  "piste_choisie": { "numero": 1, "aromes": "citron vert" },
  "brief_final": {
    "division": "arôme alimentaire",
    "type_de_produit": "boisson pétillante",
    "piste": 1,
    "aromes": ["citron vert"],
    "profil": [],
    "contraintes": ["peu sucré", "bio"],
    "codes_references": ["DEMO-004"],
    "codes_solutions": ["DEMO-028"],
    "creation_sur_mesure": [],
    "brief_du_client": "je voudrais créer une boisson / pétillante, goût citron vert, pas trop sucrée / elle doit être bio"
  },
  "demande_echantillons": null,
  "version_modele": "v2.2.1-references",
  "attribution": "Étude de marché réalisée sur des données d'Open Food Facts (ODbL)"
}
```

### Obligations et limites (V2)

- **Références fictives** : les codes `DEMO-xxx` viennent de
  `data/processed/banque_references_demo.csv`, un exemple inventé pour la démo (voir son
  `.meta.json`). Ce ne sont pas de vraies références Givaudan : l'interface doit l'indiquer.
- **Aucun envoi** : `demande_echantillons` est un récapitulatif à afficher ; rien n'est transmis.
- **Ni produit ni marque du commerce** dans `texte` et `pistes` (vérifié par les tests).
- **Temps de réponse** : voir `docs/v2_notes.md` (mode rapide par défaut).
