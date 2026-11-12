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
- **Stabilité** : les noms de champs ci-dessus ne changent pas. La V2 est un endpoint séparé
  (`POST /conversation`, ci-dessous).
- **Catalogue** : 2 193 produits vendus en France. Pas de données de prix, de stock ni de clients.

---

# Contrat V2 — assistant conversationnel (`POST /conversation`)

> **Statut : en ligne** sur la même API (port 8000, même URL ngrok), à côté de la V1.
> `/sante` et `/recommander` ne changent pas : `/sante` renvoie toujours `baseline-v1`. Les noms
> de champs ci-dessous sont ceux du contrat envoyé à l'équipe Tech ; ils ne changeront pas.

Le client envoie un message par appel. Le serveur garde l'état de la session (ce qui a été
compris, pistes proposées, piste choisie) par `session_id`. Chaque réponse contient **l'objet
complet**, jamais un delta : le front peut remplacer tout son état par la dernière réponse.

## Requête

| Champ        | Type           | Obligatoire | Description                                                                                                      |
| ------------ | -------------- | ----------- | ---------------------------------------------------------------------------------------------------------------- |
| `session_id` | string \| null | non         | `null`, absent ou inconnu : nouvelle session. L'identifiant est renvoyé ; le renvoyer à chaque message suivant.  |
| `message`    | string         | oui\*       | Message du client, en français, 500 caractères au plus. \*Peut être vide (`""`) si `piste_id` est fourni.        |
| `piste_id`   | string \| null | non         | `id` d'une piste de la dernière réponse : vaut choix de cette piste, quel que soit le message (bouton du front). |

```json
{ "session_id": "3f9c2a7b1d04", "message": "", "piste_id": "citron-vert" }
```

## Réponse `200`

| Champ            | Type                | Description                                                                                     |
| ---------------- | ------------------- | ----------------------------------------------------------------------------------------------- |
| `session_id`     | string              | Identifiant de la session, à renvoyer au message suivant                                        |
| `etape`          | string              | État de la session **après** ce message (valeurs ci-dessous)                                    |
| `intention`      | string              | Intention du **dernier** message du client (valeurs ci-dessous)                                 |
| `reponse`        | string              | Texte à afficher au client ; paragraphes séparés par `\n`                                       |
| `compris`        | objet               | Ce que l'assistant a compris du projet (voir ci-dessous)                                        |
| `pistes`         | liste (0 à 3)       | Pistes d'arômes proposées, triées par `rang` ; vide tant qu'il en manque pour étudier le marché |
| `solutions`      | liste de références | TasteSolutions ajoutées selon les contraintes (« peu sucré » → Sweetness) ; vide sinon          |
| `brief`          | objet \| null       | `null` tant qu'aucune piste n'est choisie                                                       |
| `echantillons`   | objet \| null       | `null`, ou brouillon de demande d'échantillons (statut `brouillon_non_envoye`)                  |
| `version_modele` | string              | `v2.2.1-references`                                                                             |
| `attribution`    | string              | Mention ODbL **à afficher**                                                                     |

### `compris`

| Champ          | Type                                 | Description                                         |
| -------------- | ------------------------------------ | --------------------------------------------------- |
| `division`     | `"flavors"` \| `"fragrance"` \| null | `null` tant que le produit n'est pas identifié      |
| `type_produit` | string \| null                       | Ex. `"boisson pétillante"`, `"glace"`, `"yaourt"`   |
| `arome`        | string \| null                       | Arôme principal                                     |
| `aromes`       | string[]                             | Arômes cités par le client, le principal en premier |
| `contraintes`  | string[]                             | Ex. `["peu sucré", "bio"]`                          |

### `pistes[]`

| Champ                | Type                | Description                                                                                                                              |
| -------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `id`                 | string              | Identifiant tiré des arômes (`"citron-vert"`, `"citron-vert+citron"`) : **stable** d'un message à l'autre tant que la piste est proposée |
| `rang`               | integer             | 1, 2 ou 3                                                                                                                                |
| `nom`                | string              | Ex. `"Citron vert + citron"`                                                                                                             |
| `description`        | string              | Type de piste : `"L'arôme seul"`, `"L'association la plus courante"` ou `"L'association originale"`                                      |
| `explication`        | string              | Pourquoi cette piste : nombre de produits du marché, association observée ou « à valider en dégustation »                                |
| `aromes`             | string[]            | Arômes de la piste                                                                                                                       |
| `nb_produits_marche` | integer             | Produits du marché étudié qui justifient la piste : produits avec l'arôme (piste 1) ou avec l'association (pistes 2 et 3)                |
| `references`         | liste de références | Références de la banque de démo (vide si aucune ne correspond)                                                                           |
| `sans_reference`     | string[]            | Arômes sans référence proche : création sur mesure à proposer                                                                            |
| `image`              | null                | Toujours `null` en V2 (pas d'images dans nos données) : le front affiche un visuel par défaut                                            |

### Références (`pistes[].references[]` et `solutions[]`)

| Champ              | Type     | Description                                                          |
| ------------------ | -------- | -------------------------------------------------------------------- |
| `code`             | string   | Code **fictif** `DEMO-001` à `DEMO-030`                              |
| `nom`              | string   | Ex. `"Citron vert bio"`                                              |
| `profil_sensoriel` | string   | Ex. `"citron vert juteux, frais, légèrement amer"`                   |
| `forme`            | string   | `"soluble eau"`, `"huile"` ou `"poudre"`                             |
| `labels`           | string[] | Parmi `naturel`, `vegan`, `bio`, `halal`, `casher`, `sans allergène` |

### `brief` (après le choix d'une piste)

| Champ                 | Type           | Description                                 |
| --------------------- | -------------- | ------------------------------------------- |
| `type_produit`        | string \| null | Type de produit du projet                   |
| `piste_id`            | string         | `id` de la piste choisie                    |
| `aromes`              | string[]       | Arômes de la piste choisie                  |
| `contraintes`         | string[]       | Contraintes du client                       |
| `codes_references`    | string[]       | Codes DEMO des références de la piste       |
| `codes_solutions`     | string[]       | Codes DEMO des solutions                    |
| `creation_sur_mesure` | string[]       | Arômes sans référence : création sur mesure |

### `echantillons`

Mêmes champs que `brief`, plus :

| Champ          | Type   | Description                                   |
| -------------- | ------ | --------------------------------------------- |
| `statut`       | string | Toujours `"brouillon_non_envoye"`             |
| `date`         | string | Date du brouillon, `AAAA-MM-JJ`               |
| `brief_client` | string | Messages du client qui ont construit le brief |

Rien n'est envoyé par la brique Data : l'enregistrement réel de la demande relève de l'API
applicative (équipe Tech).

### Valeurs de `etape` (état après le message)

| Valeur          | Signification                                                                          | `pistes` | `brief` | `echantillons` |
| --------------- | -------------------------------------------------------------------------------------- | -------- | ------- | -------------- |
| `relance`       | Il manque une information (type de produit, goût) ; `reponse` pose au plus 2 questions | vide     | null    | null           |
| `pistes`        | Les pistes sont proposées ; le client peut préciser, poser une question ou choisir     | 1 à 3    | null    | null           |
| `recapitulatif` | Une piste est choisie ; `reponse` récapitule le brief et propose des échantillons      | 1 à 3    | objet   | null           |
| `echantillons`  | Le brouillon de demande d'échantillons est prêt (non envoyé)                           | 1 à 3    | objet   | objet          |

Un nouveau message de précision (« elle doit être bio ») après un choix relance l'étude : retour
à `pistes`, `brief` et `echantillons` repassent à `null`.

### Valeurs de `intention` (dernier message du client)

| Valeur                 | Signification                                                   | Exemple                                                  |
| ---------------------- | --------------------------------------------------------------- | -------------------------------------------------------- |
| `nouvelle_demande`     | Premier projet, ou projet différent du projet en cours          | « je voudrais créer une boisson »                        |
| `precision`            | Complète ou corrige le projet en cours (type, goût, contrainte) | « pétillante, goût citron vert », « elle doit être bio » |
| `question`             | Question générale, sans rapport avec les pistes                 | « c'est combien la livraison ? »                         |
| `question_piste`       | Question sur les pistes ou un arôme                             | « pourquoi vous proposez cette association ? »           |
| `choix_piste`          | Choix d'une piste (message ou `piste_id`)                       | « je prends la piste 1 »                                 |
| `demande_echantillons` | Demande d'échantillons                                          | « comment je reçois des échantillons ? »                 |
| `hors_sujet`           | Salutation, remerciement, message sans rapport                  | « Bonjour », « merci »                                   |

## Erreurs

| Code  | Cas                                                       | Corps                                                                           |
| ----- | --------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `422` | `message` vide sans `piste_id`, ou `message` trop long    | Format FastAPI : `{ "detail": [{ "loc": [...], "msg": "...", ... }] }`          |
| `422` | `piste_id` qui ne correspond à aucune piste de la session | `{ "detail": "piste_id inconnu : 'durian+fraise' (pistes actuelles : [...])" }` |

## Exemple de réponse complète

Après « comment je reçois des échantillons ? », 5e message du parcours « je voudrais créer une
boisson » → « pétillante, goût citron vert, pas trop sucrée » → « elle doit être bio » → « je
prends la piste 1 ». Réponse réelle (catalogue complet) :

```json
{
  "session_id": "3f9c2a7b1d04",
  "etape": "echantillons",
  "intention": "demande_echantillons",
  "reponse": "Voici le récapitulatif de votre demande d'échantillons (DEMO-004 et DEMO-028), juste en dessous. Dans ce prototype, la demande n'est pas envoyée : transmettez ce récapitulatif à un conseiller Givaudan. Je ne connais ni les délais, ni les quantités, ni le prix : le conseiller vous les donnera.",
  "compris": {
    "division": "flavors",
    "type_produit": "boisson pétillante",
    "arome": "citron vert",
    "aromes": ["citron vert"],
    "contraintes": ["peu sucré", "bio"]
  },
  "pistes": [
    {
      "id": "citron-vert",
      "rang": 1,
      "nom": "Citron vert",
      "description": "L'arôme seul",
      "explication": "Citron vert seul : un goût franc, facile à reconnaître. 36 des 50 produits les plus proches de votre projet l'utilisent.",
      "aromes": ["citron vert"],
      "nb_produits_marche": 36,
      "references": [
        {
          "code": "DEMO-004",
          "nom": "Citron vert bio",
          "profil_sensoriel": "citron vert juteux, frais, légèrement amer",
          "forme": "soluble eau",
          "labels": ["naturel", "bio", "vegan"]
        }
      ],
      "sans_reference": [],
      "image": null
    },
    {
      "id": "citron-vert+citron",
      "rang": 2,
      "nom": "Citron vert + citron",
      "description": "L'association la plus courante",
      "explication": "Citron vert + citron : l'association la plus fréquente sur le marché (22 produits sur 36 au citron vert). Un choix rassurant, que les consommateurs connaissent déjà.",
      "aromes": ["citron vert", "citron"],
      "nb_produits_marche": 22,
      "references": [
        {
          "code": "DEMO-004",
          "nom": "Citron vert bio",
          "profil_sensoriel": "citron vert juteux, frais, légèrement amer",
          "forme": "soluble eau",
          "labels": ["naturel", "bio", "vegan"]
        },
        {
          "code": "DEMO-002",
          "nom": "Citron jaune bio",
          "profil_sensoriel": "citron jaune juteux, notes de zeste, acidulé",
          "forme": "soluble eau",
          "labels": ["naturel", "bio", "vegan"]
        }
      ],
      "sans_reference": [],
      "image": null
    },
    {
      "id": "citron-vert+pamplemousse",
      "rang": 3,
      "nom": "Citron vert + pamplemousse",
      "description": "L'association originale",
      "explication": "Citron vert + pamplemousse : une association rare sur le marché (1 produit), qui peut vous démarquer tout en restant crédible.",
      "aromes": ["citron vert", "pamplemousse"],
      "nb_produits_marche": 1,
      "references": [
        {
          "code": "DEMO-004",
          "nom": "Citron vert bio",
          "profil_sensoriel": "citron vert juteux, frais, légèrement amer",
          "forme": "soluble eau",
          "labels": ["naturel", "bio", "vegan"]
        }
      ],
      "sans_reference": [],
      "image": null
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
  "brief": {
    "type_produit": "boisson pétillante",
    "piste_id": "citron-vert",
    "aromes": ["citron vert"],
    "contraintes": ["peu sucré", "bio"],
    "codes_references": ["DEMO-004"],
    "codes_solutions": ["DEMO-028"],
    "creation_sur_mesure": []
  },
  "echantillons": {
    "type_produit": "boisson pétillante",
    "piste_id": "citron-vert",
    "aromes": ["citron vert"],
    "contraintes": ["peu sucré", "bio"],
    "codes_references": ["DEMO-004"],
    "codes_solutions": ["DEMO-028"],
    "creation_sur_mesure": [],
    "statut": "brouillon_non_envoye",
    "date": "2026-11-12",
    "brief_client": "je voudrais créer une boisson / pétillante, goût citron vert, pas trop sucrée / elle doit être bio"
  },
  "version_modele": "v2.2.1-references",
  "attribution": "Étude de marché réalisée sur des données d'Open Food Facts (ODbL)"
}
```

## Exemple d'appel (TypeScript)

```ts
const reponse = await fetch(`${API_DATA_URL}/conversation`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true',
  },
  body: JSON.stringify({ session_id: sessionId, message, piste_id: null }),
});
if (!reponse.ok) throw new Error(`API Data : HTTP ${reponse.status}`);
const etat = await reponse.json(); // objet complet : remplace l'état du front
sessionId = etat.session_id;
```

## Obligations et limites (V2)

- **Références fictives** : les codes `DEMO-xxx` viennent de
  `data/processed/banque_references_demo.csv`, un exemple inventé pour la démo (voir son
  `.meta.json`). Ce ne sont pas de vraies références Givaudan : l'interface doit l'indiquer.
- **Aucun envoi** : `echantillons` est un brouillon à afficher ; l'enregistrement réel relève de
  l'API applicative.
- **Ni produit ni marque du commerce** dans `reponse` et `pistes` (vérifié par les tests).
- **Sessions en mémoire** : au plus 500, oubliées après 2 h sans message ; un redémarrage du
  serveur les efface (le front repart alors avec une nouvelle session).
- **Temps de réponse** : 0,3 à 1,2 s via ngrok ; environ 5 s quand le message demande le modèle
  (arôme hors liste, ex. « durian »).
