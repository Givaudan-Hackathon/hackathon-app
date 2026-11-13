export type JourneyPage = 'idea' | 'refine' | 'choose' | 'payment' | 'request';
export type JourneyStep = {
  id: JourneyPage;
  label: string;
  available: boolean;
  completed: boolean;
  hint: string;
  skipped?: boolean;
};
export function buildJourney({
  hasProject,
  hasOptions,
  hasBrief,
  hasPayment,
  expert,
  finished,
}: {
  hasProject: boolean;
  hasOptions: boolean;
  hasBrief: boolean;
  hasPayment: boolean;
  expert: boolean;
  finished: boolean;
}): JourneyStep[] {
  return [
    {
      id: 'idea',
      label: 'Votre idée',
      available: true,
      completed: hasProject,
      hint: 'Décrivez votre produit et le goût recherché.',
    },
    {
      id: 'refine',
      label: 'Affiner',
      available: hasProject,
      completed: hasOptions,
      hint: 'Commencez par décrire votre idée.',
    },
    {
      id: 'choose',
      label: 'Choisir',
      available: hasOptions,
      completed: hasBrief,
      hint: 'Précisez votre produit et un arôme pour obtenir des propositions.',
    },
    {
      id: 'payment',
      label: 'Paiement',
      available: hasBrief && !expert,
      completed: hasPayment,
      skipped: expert,
      hint: expert
        ? 'Aucun paiement pour une demande de contact.'
        : 'Choisissez un arôme avant de simuler le paiement.',
    },
    {
      id: 'request',
      label: 'Votre demande',
      available: expert || hasPayment,
      completed: finished,
      hint: 'Validez le paiement fictif avant de préparer votre demande d’échantillon.',
    },
  ];
}
