import { createOptions, flavors } from '../../mocks/catalog.ts';
import {
  ServiceError,
  validateSnapshot,
  wait,
  type ClientBrief,
  type ConversationService,
  type ConversationSnapshot,
} from '../conversation-service.ts';

const normalize = (text: string) =>
  text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

export function createMockConversationService({
  delay = 450,
  failNext = false,
} = {}): ConversationService {
  const sessions = new Map<
    string,
    { snapshot: ConversationSnapshot; messages: string[] }
  >();
  let shouldFail = failNext;
  return {
    async send(input, options) {
      const message = input.message.trim();
      if ((!message && !input.piste_id) || message.length > 500)
        throw new ServiceError(
          'INVALID_INPUT',
          'Décrivez votre projet en 1 à 500 caractères, ou choisissez une proposition.',
        );
      await wait(delay, options?.signal);
      if (shouldFail) {
        shouldFail = false;
        throw new ServiceError(
          'UNAVAILABLE',
          'L’assistant est momentanément indisponible. Votre saisie est conservée ; réessayez.',
        );
      }
      const previous = input.session_id
        ? sessions.get(input.session_id)
        : undefined;
      const snapshot: ConversationSnapshot = previous
        ? structuredClone(previous.snapshot)
        : {
            session_id: crypto.randomUUID(),
            etape: 'relance',
            intention: 'nouvelle_demande',
            reponse:
              'Quel produit souhaitez-vous créer, et quel goût imaginez-vous ?',
            compris: {
              division: null,
              type_produit: null,
              arome: null,
              aromes: [],
              contraintes: [],
            },
            pistes: [],
            solutions: [],
            brief: null,
            echantillons: null,
            version_modele: 'demo-web-v2',
            attribution:
              'Simulation du contrat Data V2. Références DEMO fictives ; aucune étude de marché exécutée.',
          };
      const messages = [...(previous?.messages ?? [])];
      const text = normalize(message);
      if (input.piste_id) {
        const selected = snapshot.pistes.find(
          (piste) => piste.id === input.piste_id,
        );
        if (!selected)
          throw new ServiceError(
            'INVALID_CHOICE',
            'Cette proposition n’est plus disponible. Choisissez l’un des arômes affichés.',
          );
        const brief: ClientBrief = {
          type_produit: snapshot.compris.type_produit,
          piste_id: selected.id,
          aromes: selected.aromes,
          contraintes: [...snapshot.compris.contraintes],
          codes_references: selected.references.map((ref) => ref.code),
          codes_solutions: [],
          creation_sur_mesure: [],
        };
        snapshot.brief = brief;
        snapshot.echantillons = null;
        snapshot.etape = 'recapitulatif';
        snapshot.intention = 'choix_piste';
        snapshot.reponse = `Votre choix : ${selected.nom}. Prenez un instant pour relire votre projet. Vous pourrez ensuite préparer une demande d’échantillon, sans engagement.`;
      } else if (
        /echantillon|preparer ma demande/.test(text) &&
        snapshot.brief
      ) {
        snapshot.etape = 'echantillons';
        snapshot.intention = 'demande_echantillons';
        snapshot.echantillons = {
          ...snapshot.brief,
          statut: 'brouillon_non_envoye',
          date: new Date().toISOString().slice(0, 10),
          brief_client: messages.join(' / '),
        };
        snapshot.reponse =
          'Votre récapitulatif est prêt. Complétez vos coordonnées pour simuler la transmission de votre demande. Aucun échantillon n’est envoyé dans cette démonstration.';
      } else if (
        /pourquoi|difference|livraison|prix|combien|delai/.test(text) &&
        previous
      ) {
        snapshot.intention = /pourquoi|difference/.test(text)
          ? 'question_piste'
          : 'question';
        snapshot.reponse =
          snapshot.intention === 'question_piste'
            ? 'Chaque proposition présente une direction gustative et son explication. Ces références sont fictives : une dégustation et l’avis d’un expert permettraient de confirmer votre choix.'
            : 'Les quantités, tarifs et délais seront à confirmer avec un conseiller. Ce prototype vous permet de préparer votre besoin, sans engagement.';
      } else if (/aucun|ne convient|pas trouve|autre proposition/.test(text)) {
        snapshot.etape = 'relance';
        snapshot.intention = 'precision';
        snapshot.pistes = [];
        snapshot.brief = null;
        snapshot.echantillons = null;
        snapshot.reponse =
          'Dites-moi ce qui manque : plus de fraîcheur, une note plus douce, un autre ingrédient ? Vous pouvez aussi préparer une demande de contact avec un expert.';
      } else if (/^(bonjour|merci|salut|bonsoir)[ !.]*$/.test(text)) {
        snapshot.intention = 'hors_sujet';
        snapshot.reponse =
          'Bonjour ! Décrivez le produit que vous aimeriez créer et le goût que vous recherchez. Une boisson au citron vert, par exemple ?';
      } else {
        const product = /boisson|soda|limonade|eau|jus/.test(text)
          ? /petillant|soda|limonade/.test(text)
            ? 'boisson pétillante'
            : 'boisson'
          : /yaourt/.test(text)
            ? 'yaourt'
            : /glace/.test(text)
              ? 'glace'
              : /biscuit|sable/.test(text)
                ? 'biscuit'
                : /dessert|creme/.test(text)
                  ? 'dessert'
                  : null;
        // La simulation reconnaît un vocabulaire limité ; elle explicite les
        // arômes non couverts plutôt que de réutiliser un ancien choix.
        const desiredText = /remplac\w*.*\bpar\b/.test(text)
          ? text.split(/\bpar\b/).at(-1)!
          : text;
        const flavorText = desiredText.replace(
          /\b(?:sans|pas de|plus de)\s+(?:citron(?:\s+vert|\s+jaune)?|pamplemousse|vanille|fraise)\b/g,
          '',
        );
        const unsupportedFlavor =
          /\b(mangue|menthe|chocolat|pistache|coco|peche|framboise|ananas|kiwi|banane|cafe)\b/.exec(
            flavorText,
          )?.[1];
        const flavor = flavors.find((item) => item.match.test(flavorText));
        const removesFlavor = flavorText !== desiredText;
        const isNewProject = Boolean(
          previous &&
          product &&
          snapshot.compris.type_produit &&
          !snapshot.compris.type_produit.includes(product) &&
          !product.includes(snapshot.compris.type_produit),
        );
        if (isNewProject)
          snapshot.compris = {
            division: null,
            type_produit: null,
            arome: null,
            aromes: [],
            contraintes: [],
          };
        snapshot.compris.type_produit =
          product ?? snapshot.compris.type_produit;
        if (unsupportedFlavor) {
          snapshot.compris.arome = unsupportedFlavor;
          snapshot.compris.aromes = [unsupportedFlavor];
        } else if (flavor) {
          snapshot.compris.arome = flavor.label;
          snapshot.compris.aromes = [flavor.label];
        } else if (removesFlavor) {
          snapshot.compris.arome = null;
          snapshot.compris.aromes = [];
        }
        for (const [pattern, removal, label] of [
          [
            /peu sucre|pas trop sucre|moins sucre/,
            /(?:retir\w*|enlev\w*).{0,30}(?:peu sucre|moins sucre)/,
            'peu sucré',
          ],
          [
            /\bbio\b/,
            /\b(?:sans|pas(?: de)?|plus(?: de)?|non)\s+bio\b|\b(?:retir\w*|enlev\w*).{0,20}\bbio\b/,
            'bio',
          ],
          [
            /vegetal|vegan/,
            /\b(?:sans|pas(?: de)?|plus(?: de)?|non)\s+(?:vegetal|vegan)\b/,
            'végétal',
          ],
        ] as const) {
          if (removal.test(text))
            snapshot.compris.contraintes = snapshot.compris.contraintes.filter(
              (constraint) => constraint !== label,
            );
          else if (
            pattern.test(text) &&
            !snapshot.compris.contraintes.includes(label)
          )
            snapshot.compris.contraintes.push(label);
        }
        snapshot.compris.division = /parfum|bougie|savon/.test(text)
          ? 'fragrance'
          : snapshot.compris.type_produit
            ? 'flavors'
            : null;
        snapshot.brief = null;
        snapshot.echantillons = null;
        snapshot.intention =
          previous && !isNewProject ? 'precision' : 'nouvelle_demande';
        messages.push(message);
        const knownFlavor = flavors.find(
          (item) => item.label === snapshot.compris.arome,
        );
        if (snapshot.compris.division === 'fragrance') {
          snapshot.etape = 'relance';
          snapshot.pistes = [];
          snapshot.reponse =
            'Ce parcours est consacré aux arômes alimentaires. Décrivez un projet de boisson, dessert ou autre produit alimentaire pour continuer.';
        } else if (!snapshot.compris.type_produit) {
          snapshot.etape = 'relance';
          snapshot.pistes = [];
          snapshot.reponse =
            'Dans quel produit souhaitez-vous retrouver ce goût : une boisson, un dessert, un yaourt, une glace ou un biscuit ?';
        } else if (!knownFlavor) {
          snapshot.etape = 'relance';
          snapshot.pistes = [];
          snapshot.reponse = unsupportedFlavor
            ? `L’arôme « ${unsupportedFlavor} » n’est pas couvert par cette démonstration. Choisissez citron vert, citron jaune, pamplemousse, vanille ou fraise, ou préparez une demande de contact avec un expert.`
            : 'Quel goût imaginez-vous ? Cette démonstration permet d’explorer le citron vert, le citron jaune, le pamplemousse, la vanille et la fraise.';
        } else {
          snapshot.etape = 'pistes';
          snapshot.pistes = createOptions(knownFlavor.key);
          snapshot.reponse = `Voici trois directions à explorer pour votre ${snapshot.compris.type_produit}. Comparez leurs profils, choisissez celle qui vous inspire ou précisez votre idée.`;
        }
      }
      const validated = validateSnapshot(snapshot);
      sessions.set(validated.session_id, { snapshot: validated, messages });
      return structuredClone(validated);
    },
  };
}
