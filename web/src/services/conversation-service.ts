import { z } from 'zod';

export const referenceSchema = z.object({
  code: z.string().min(1),
  nom: z.string(),
  profil_sensoriel: z.string(),
  forme: z.string(),
  labels: z.array(z.string()),
});

const briefSchema = z.object({
  type_produit: z.string().nullable(),
  piste_id: z.string().min(1),
  aromes: z.array(z.string()),
  contraintes: z.array(z.string()),
  codes_references: z.array(z.string()),
  codes_solutions: z.array(z.string()),
  creation_sur_mesure: z.array(z.string()),
});

export const snapshotSchema = z
  .object({
    session_id: z.string().min(1),
    etape: z.enum(['relance', 'pistes', 'recapitulatif', 'echantillons']),
    intention: z.enum([
      'nouvelle_demande',
      'precision',
      'question',
      'question_piste',
      'choix_piste',
      'demande_echantillons',
      'hors_sujet',
    ]),
    reponse: z.string().min(1),
    compris: z.object({
      division: z.enum(['flavors', 'fragrance']).nullable(),
      type_produit: z.string().nullable(),
      arome: z.string().nullable(),
      aromes: z.array(z.string()),
      contraintes: z.array(z.string()),
    }),
    pistes: z
      .array(
        z.object({
          id: z.string().min(1),
          rang: z.union([z.literal(1), z.literal(2), z.literal(3)]),
          nom: z.string(),
          description: z.string(),
          explication: z.string(),
          aromes: z.array(z.string()),
          nb_produits_marche: z.number().int().nonnegative(),
          references: z.array(referenceSchema),
          sans_reference: z.array(z.string()),
          image: z.null(),
        }),
      )
      .max(3),
    solutions: z.array(referenceSchema),
    brief: briefSchema.nullable(),
    echantillons: briefSchema
      .extend({
        statut: z.literal('brouillon_non_envoye'),
        date: z.string(),
        brief_client: z.string(),
      })
      .nullable(),
    version_modele: z.string(),
    attribution: z.string(),
  })
  .superRefine((snapshot, ctx) => {
    const hasBrief = snapshot.brief !== null;
    const hasDraft = snapshot.echantillons !== null;
    const expectedBrief = ['recapitulatif', 'echantillons'].includes(
      snapshot.etape,
    );
    const validOptions =
      snapshot.etape === 'relance'
        ? snapshot.pistes.length === 0
        : snapshot.pistes.length > 0;
    const selectedExists =
      !snapshot.brief ||
      snapshot.pistes.some((piste) => piste.id === snapshot.brief?.piste_id);
    const uniqueIds =
      new Set(snapshot.pistes.map((piste) => piste.id)).size ===
      snapshot.pistes.length;
    const uniqueRanks =
      new Set(snapshot.pistes.map((piste) => piste.rang)).size ===
      snapshot.pistes.length;
    if (
      hasBrief !== expectedBrief ||
      hasDraft !== (snapshot.etape === 'echantillons') ||
      !validOptions ||
      !selectedExists ||
      !uniqueIds ||
      !uniqueRanks ||
      (snapshot.echantillons &&
        snapshot.echantillons.piste_id !== snapshot.brief?.piste_id)
    ) {
      ctx.addIssue({
        code: 'custom',
        message: 'La réponse ne correspond pas à l’étape du parcours.',
      });
    }
  });

export type ConversationSnapshot = z.infer<typeof snapshotSchema>;
export type FlavorOption = ConversationSnapshot['pistes'][number];
export type DemoReference = z.infer<typeof referenceSchema>;
export type ClientBrief = z.infer<typeof briefSchema>;
export type ConversationInput = {
  session_id?: string | null;
  message: string;
  piste_id?: string | null;
};
export type ServiceOptions = { signal?: AbortSignal };
export interface ConversationService {
  send(
    input: ConversationInput,
    options?: ServiceOptions,
  ): Promise<ConversationSnapshot>;
}

export class ServiceError extends Error {
  readonly code: string;
  constructor(code: string, message: string) {
    super(message);
    this.code = code;
    this.name = 'ServiceError';
  }
}

export function validateSnapshot(input: unknown): ConversationSnapshot {
  const result = snapshotSchema.safeParse(input);
  if (!result.success)
    throw new ServiceError(
      'INVALID_RESPONSE',
      'La réponse reçue est incomplète. Votre saisie est conservée ; veuillez réessayer.',
    );
  return result.data;
}

export function wait(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const abort = () => {
      clearTimeout(timer);
      signal?.removeEventListener('abort', abort);
      reject(new DOMException('Requête annulée', 'AbortError'));
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', abort);
      resolve();
    }, ms);
    if (signal?.aborted) abort();
    else signal?.addEventListener('abort', abort, { once: true });
  });
}
