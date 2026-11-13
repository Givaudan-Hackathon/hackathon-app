import type {
  DemoReference,
  FlavorOption,
} from '../services/conversation-service.ts';

// Sous-ensemble fictif de la banque DEMO de la PR Data #18.
export const catalog: Record<string, DemoReference> = {
  lemon: {
    code: 'DEMO-002',
    nom: 'Citron jaune bio',
    profil_sensoriel: 'Citron jaune juteux, notes de zeste, acidulé',
    forme: 'soluble eau',
    labels: ['naturel', 'bio', 'vegan'],
  },
  lime: {
    code: 'DEMO-004',
    nom: 'Citron vert bio',
    profil_sensoriel: 'Citron vert juteux, frais, légèrement amer',
    forme: 'soluble eau',
    labels: ['naturel', 'bio', 'vegan'],
  },
  grapefruit: {
    code: 'DEMO-008',
    nom: 'Pamplemousse',
    profil_sensoriel: 'Pamplemousse frais, amertume légère, zeste',
    forme: 'soluble eau',
    labels: ['naturel', 'vegan', 'halal'],
  },
  vanilla: {
    code: 'DEMO-014',
    nom: 'Vanille bourbon',
    profil_sensoriel: 'Vanille ronde, crémeuse, notes boisées',
    forme: 'soluble eau',
    labels: ['naturel', 'halal', 'casher'],
  },
  strawberry: {
    code: 'DEMO-024',
    nom: 'Fraise mûre',
    profil_sensoriel: 'Fraise mûre, sucrée, juteuse',
    forme: 'soluble eau',
    labels: ['naturel', 'vegan', 'sans allergène'],
  },
};

export const flavors = [
  {
    key: 'lime',
    id: 'citron-vert',
    label: 'citron vert',
    // L’alias « lime » ne doit pas être reconnu dans « alimentaire ».
    match: /citron vert|citron-vert|\blimes?\b/,
  },
  {
    key: 'grapefruit',
    id: 'pamplemousse',
    label: 'pamplemousse',
    match: /pamplemousse/,
  },
  { key: 'lemon', id: 'citron', label: 'citron', match: /citron/ },
  { key: 'vanilla', id: 'vanille', label: 'vanille', match: /vanille/ },
  { key: 'strawberry', id: 'fraise', label: 'fraise', match: /fraise/ },
];

export function createOptions(flavorKey: string): FlavorOption[] {
  const primary =
    flavors.find((flavor) => flavor.key === flavorKey) ?? flavors[0];
  const alternatives =
    flavorKey === 'lime'
      ? ['lemon', 'grapefruit']
      : flavorKey === 'vanilla'
        ? ['strawberry', 'lemon']
        : flavorKey === 'strawberry'
          ? ['vanilla', 'lime']
          : ['lime', 'vanilla'];
  const pairs = [[], [alternatives[0]], [alternatives[1]]];
  return pairs.map((pair, index) => {
    const keys = [flavorKey, ...pair];
    const aromes = keys.map(
      (key) =>
        flavors.find((flavor) => flavor.key === key)?.label ?? primary.label,
    );
    const refs = keys.map((key) => catalog[key]);
    return {
      id: [
        primary.id,
        ...pair.map((key) => flavors.find((flavor) => flavor.key === key)?.id),
      ].join('+'),
      rang: (index + 1) as 1 | 2 | 3,
      nom: aromes
        .map((name) => name[0].toUpperCase() + name.slice(1))
        .join(' & '),
      description: ['L’essentiel', 'L’équilibre', 'La découverte'][index],
      explication: [
        `Une expression franche de ${primary.label}, pour garder le goût que vous avez imaginé au premier plan.`,
        `Une association avec ${aromes[1]}, pour apporter une autre nuance à votre création. À valider en dégustation.`,
        `Une autre direction autour de ${aromes[1]}, à explorer si vous souhaitez un profil plus singulier.`,
      ][index],
      aromes,
      nb_produits_marche: 0,
      references: refs,
      sans_reference: [],
      references_sans_label: [],
      image: null,
    };
  });
}
