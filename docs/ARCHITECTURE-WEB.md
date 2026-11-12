# Architecture du prototype client

Cible du [ticket #19](https://github.com/Givaudan-Hackathon/hackathon-app/issues/19),
à implémenter dans le [ticket #20](https://github.com/Givaudan-Hackathon/hackathon-app/issues/20).
Le code actuel reste le formulaire Vite/TypeScript du socle : React et Tailwind
ne sont pas installés par ce cadrage. L’[ADR 0008](adr/0008-interface-react.md)
porte le choix du front et reste soumis à la revue de la proposition.

## Périmètre et frontière des services

Le prototype accompagne un petit client dans un projet d’arômes alimentaires :
décrire, affiner, choisir une piste, relire le brief et préparer une demande.
Le commercial reçoit ensuite une synthèse et décide de la suite ; son interface,
le paiement et la commande ferme sont hors du lot web. La confirmation du MVP
indique une simulation, sans affirmer qu’un commercial ou un échantillon a été envoyé.

Cible des échanges : navigateur React → API applicative Nest → API Data Python.
Nest reste une migration proposée dans l’ADR 0009. Pour le ticket web, un
adaptateur simulé remplace le service conversationnel ; aucun accès direct à
Python n’est installé et aucun nom de route Nest métier n’est présenté comme existant.
Le `openapi.yaml` racine continue de décrire uniquement les trois routes du socle.

## Découpage à créer avec le parcours

```text
web/src/
  app/                         composition de l’application et navigation
  components/ui/               boutons, champs, panneaux, progression
  features/
    conversation/              fil, saisie, aperçu compris et état du dialogue
    recommendations/           pistes, références, sélection et visuels
    request/                   relecture, coordonnées et demande simulée
  services/
    conversation-service.ts    interface indépendante de React
    request-service.ts         dépôt applicatif, distinct de la conversation
    adapters/                  implémentation simulée ; HTTP dans un ticket ultérieur
  mocks/                       scénarios déterministes conformes au contrat Data
  assets/                      photos et autres ressources locales
  styles/                      entrée Tailwind et tokens
```

Les fichiers sont ajoutés lorsqu’ils ont un usage, sans `.gitkeep` ni abstractions
vides. Les composants UI reçoivent leurs données et actions par propriétés.
Les fonctionnalités utilisent les services, jamais les fixtures directement.
Les adaptateurs n’importent ni composant React ni état d’affichage.
Les dépendances entre fonctionnalités passent par la composition dans `app/`.

Vite reste sur 5173, avec le proxy `/api` vers 3000 et les workspaces npm existants.
Le ticket #20 ajoutera React/TSX, Tailwind via Vite, le contrôle TypeScript et
la prise en charge TSX dans ESLint/lint-staged, sans affaiblir `qualite`.
Le formulaire de test actuel restera accessible pendant la migration.
Une navigation de parcours suffit au MVP ; aucune dépendance de routage ou de
store global n’est requise à ce stade. Motion est facultatif ; les transitions
retenues peuvent commencer en CSS.

## État et progression

Un `useReducer` au niveau du parcours conserve le fil, la réponse Data complète,
la requête en cours et l’état local du dépôt. L’étape visible est dérivée de la
réponse ; aucune seconde copie modifiable de `compris`, `brief` ou `pistes` n’est
maintenue dans les composants. Les champs de formulaire non envoyés restent locaux.

| État reçu             | Présentation                                | Action client                                                             |
| --------------------- | ------------------------------------------- | ------------------------------------------------------------------------- |
| Pas encore de réponse | Accueil et description du projet            | Envoyer une description ou partir d’un exemple                            |
| `relance`             | Conversation et informations déjà comprises | Répondre en texte, préciser ou dire que l’on ne sait pas                  |
| `pistes`              | Jusqu’à trois pistes et leur explication    | Choisir par identifiant, préciser ou refuser                              |
| `recapitulatif`       | Brief de la piste choisie                   | Corriger ou demander la préparation d’échantillons                        |
| `echantillons`        | Brouillon d’échantillons et relecture       | Compléter les coordonnées puis confirmer explicitement la demande simulée |

La division doit être `flavors` pour poursuivre le parcours de ce MVP. Une
réponse portant sur les fragrances est expliquée au client et ne produit pas
une fausse proposition d’arômes alimentaires.

Une correction peut ramener Data à `pistes` et remettre `brief` et `echantillons`
à `null`. Le front remplace alors le snapshot et invalide sa sélection locale
et le brouillon de dépôt lié au brief précédent. La présence de `echantillons`
avec `brouillon_non_envoye` n’est jamais assimilée à une transmission commerciale.

L’état de dépôt est séparé : `editing`, `submitting`, `submitted_demo` ou `error`.
La soumission relit la sélection et les coordonnées en cours ; le bouton est
bloqué pendant l’envoi et un échec conserve les champs. Le stockage effectif,
l’idempotence serveur et le statut de transmission appartiendront à l’API applicative.

## Contrat Data V2 pris comme référence

Source consultée : [contrat de la PR #18 au commit 0cec17f](https://github.com/Givaudan-Hackathon/hackathon-app/blob/0cec17ffedb225a4a5804a7077cb973c4bfdc503/data-brique/docs/contrat_api.md).
La PR est en brouillon : cette lecture ne constitue ni son approbation ni son
intégration. L’[exemple JSON](exemples/conversation-v2.json) reprend son exemple
de réponse complète ; les comptes de produits sont ceux de cet exemple, pas
une mesure effectuée par le front ni des scores de correspondance.

Types de frontière à reprendre lors de l’implémentation :

```ts
type DataStep = 'relance' | 'pistes' | 'recapitulatif' | 'echantillons';
type DataIntent =
  | 'nouvelle_demande'
  | 'precision'
  | 'question'
  | 'question_piste'
  | 'choix_piste'
  | 'demande_echantillons'
  | 'hors_sujet';

type ConversationInput = {
  session_id?: string | null;
  message: string;
  piste_id?: string | null;
};

type UnderstoodProject = {
  division: 'flavors' | 'fragrance' | null;
  type_produit: string | null;
  arome: string | null;
  aromes: string[];
  contraintes: string[];
};

type DemoReference = {
  code: string;
  nom: string;
  profil_sensoriel: string;
  forme: string;
  labels: string[];
};

type FlavorOption = {
  id: string;
  rang: 1 | 2 | 3;
  nom: string;
  description: string;
  explication: string;
  aromes: string[];
  nb_produits_marche: number;
  references: DemoReference[];
  sans_reference: string[];
  image: null; // Contrat actuel : toute extension URL sera coordonnée avec Data.
};

type ClientBrief = {
  type_produit: string | null;
  piste_id: string;
  aromes: string[];
  contraintes: string[];
  codes_references: string[];
  codes_solutions: string[];
  creation_sur_mesure: string[];
};

type SampleDraft = ClientBrief & {
  statut: 'brouillon_non_envoye';
  date: string;
  brief_client: string;
};

type ConversationSnapshot = {
  session_id: string;
  etape: DataStep;
  intention: DataIntent;
  reponse: string;
  compris: UnderstoodProject;
  pistes: FlavorOption[];
  solutions: DemoReference[];
  brief: ClientBrief | null;
  echantillons: SampleDraft | null;
  version_modele: string;
  attribution: string;
};

interface ConversationService {
  send(
    input: ConversationInput,
    options?: { signal?: AbortSignal },
  ): Promise<ConversationSnapshot>;
}
```

La sélection envoie `piste_id`, avec `message: ''` si nécessaire, et reprend le
`session_id` de la réponse précédente. Un message contient au plus 500 caractères.
Les pistes sont identifiées par `id`, les références par `code` : une piste peut
regrouper plusieurs références et ne doit pas être assimilée à un produit unique.
`compris` est un objet complet en V2, et non le nullable de la première capture.
`question_piste`, `solutions`, `version_modele` et `attribution` font partie du contrat.

TypeScript ne valide pas une réponse HTTP à l’exécution : l’adaptateur vérifiera
les propriétés requises, les énumérations, la limite de trois pistes et les
relations étape/brief/brouillon avant de remplacer l’état. Une réponse incompatible
produit une erreur lisible. Aucun HTML ou code reçu du modèle n’est exécuté :
`reponse` reste du texte et ses sauts de ligne sont préservés.

## Sessions, erreurs et concurrence

Une seule requête conversationnelle est autorisée à la fois dans une session.
Le front désactive les actions concurrentes et ignore les réponses devenues
obsolètes après un nouveau départ. Un `AbortSignal` permet d’abandonner l’affichage
d’une requête ; il ne garantit pas l’annulation du traitement dans Python.
Aucun rejeu automatique de POST n’est prévu : une réponse perdue peut correspondre
à un message déjà traité. La reprise doit rendre ce cas compréhensible au client.

Les `422` de la Data distinguent saisie invalide et identifiant de piste périmé.
Les erreurs réseau/indisponibilité sont présentées séparément d’une absence de
proposition métier. Le simulateur couvre ces états sans nécessiter Ollama.
Les sessions Data sont en mémoire et expirent après deux heures d’inactivité ;
un redémarrage les efface. Si une session connue est remplacée, informer le client
et réinitialiser les sélections dépendantes, sans annoncer une reprise persistée.

## Images et scénario de démonstration

La banque Data contient 30 références **fictives** ; le lot web couvre cinq visuels
locaux associés à des identifiants convenus avec Data et Product. Proposition
de couverture issue du catalogue de la PR : `DEMO-002` (citron jaune bio),
`DEMO-004` (citron vert bio), `DEMO-008` (pamplemousse), `DEMO-014` (vanille bourbon)
et `DEMO-024` (fraise mûre). Ce sous-ensemble et les visuels restent à confirmer
au ticket #20 ; il ne réduit pas implicitement les réponses du service Data.

Le scénario de base recommandé est la boisson pétillante au citron vert, déjà
illustrée dans le contrat Data, avec correction « bio », sélection et brouillon.
Le dessert pistache du Figma reste une inspiration UX ; il n’est pas présenté
comme une référence disponible dans cette banque, qui ne contient pas de pistache.

L’affichage résout un visuel depuis une table locale indexée par identifiant
convenu de piste ou code de référence, puis utilise une image générique si rien
ne correspond. Il ne déduit pas un chemin depuis le texte libre de l’IA.
Prévoir une alternative textuelle et le remplacement d’une image introuvable.
Si Data fournit ensuite une URL, adapter ce seul résolveur et le contrat validé.
Les ressources temporaires Figma ne deviennent pas des URL d’exécution.

Les fiches affichent `explication`, les références et profils disponibles.
Aucun radar, pourcentage de correspondance ou note sensorielle n’est inventé.
Les codes DEMO et leurs labels restent explicitement de démonstration, et
`attribution` est affiché avec les résultats comme le demande le contrat Data.

## Direction visuelle et accessibilité

Références fonctionnelles : [écrans Figma](https://www.figma.com/design/GDjhfTwpyERJJXVe8F2r7w/?node-id=39-254)
et [story map](https://www.figma.com/board/iRqdnbmixlrQirqkqALZyj/?node-id=0-1).
Le contenu et les états sont conservés ; la mise en scène peut évoluer.

Palette de départ : encre `#0f2a33`, fond `#f4f7f8`, surface `#ffffff`, texte
secondaire `#4a5f66` et bordure `#d5dee1`, repris du brouillon. L’accent végétal
`#b9d35c` est une proposition à relire, pas une couleur officielle certifiée.
IBM Plex Sans reprend la typographie du Figma, avec une police système de repli.

La composition met une photographie alimentaire au premier plan à l’accueil.
Sur ordinateur, le besoin compris reste visible à côté de l’échange ; sur mobile,
il devient repliable sans masquer la progression. Le relief CSS valorise les
images ; les transitions montrent la sélection et l’évolution du récapitulatif.
Pas d’attente artificielle, de fond animé permanent ni d’information disponible
uniquement au survol. Focus visible, actions au clavier, contraste vérifié,
réponses annoncées sans interruption et respect du mouvement réduit sont requis.

Les skills obligatoires sont référencés dans [web/AGENTS.md](../web/AGENTS.md).
`frontend-design` guide les choix visuels ; `vercel-react-best-practices` s’applique
aux parties React pertinentes pour Vite ; `web-design-guidelines` sert à la revue
du parcours livré. Les règles spécifiques à Next.js ne créent aucune dépendance Next.

## Vérification et passage à m2

Le ticket #20 conservera les contrôles racine et ajoutera un typecheck réel.
La vérification cible correction/invalidation, choix d’un identifiant, absence
de résultat, reprise après erreur et prévention du double dépôt. Tester le
parcours à 360 et 1440 px, au clavier et avec mouvement réduit.

Le [ticket #21](https://github.com/Givaudan-Hackathon/hackathon-app/issues/21) porte
le démarrage Compose de l’écran aux données, la démo et le tag m2. Le simulateur
web ne prouve pas le raccordement API/Data/PostgreSQL. Toute route métier ou
migration nécessaire sera coordonnée et versionnée avec son contrat ; le modèle
complet de base reste un chantier ultérieur au front. La revue de la PR #18
et la disponibilité des données sont des dépendances distinctes du code web.
