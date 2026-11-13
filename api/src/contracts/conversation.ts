import { z } from 'zod';

// Contrat pur partagé par Nest et React ; les ajouts Data restent présents.
export const referenceSchema = z
  .object({
    code: z.string().min(1),
    nom: z.string(),
    profil_sensoriel: z.string(),
    forme: z.string(),
    labels: z.array(z.string()),
  })
  .passthrough();
const missingLabelSchema = z
  .object({
    arome: z.string(),
    code: z.string(),
    label_manquant: z.string(),
  })
  .passthrough();
export const briefSchema = z
  .object({
    type_produit: z.string().nullable(),
    piste_id: z.string().min(1),
    aromes: z.array(z.string()),
    contraintes: z.array(z.string()),
    codes_references: z.array(z.string()),
    codes_solutions: z.array(z.string()),
    creation_sur_mesure: z.array(z.string()),
    profil: z.array(z.string()).default([]),
    volume: z.string().nullable().default(null),
    references_sans_label: z.array(missingLabelSchema).default([]),
  })
  .passthrough();
const questionSchema = z
  .object({
    id: z.string().min(1),
    question: z.string().min(1),
    choix: z.array(z.string().min(1)).max(8).default([]),
  })
  .passthrough();
export const snapshotSchema = z
  .object({
    session_id: z.string().min(1),
    etape: z.enum([
      'relance',
      'affiner',
      'pistes',
      'recapitulatif',
      'echantillons',
    ]),
    intention: z.enum([
      'nouvelle_demande',
      'precision',
      'question',
      'question_piste',
      'choix_piste',
      'demande_echantillons',
      'hors_sujet',
    ]),
    reponse: z.string().trim().min(1),
    compris: z
      .object({
        division: z.enum(['flavors', 'fragrance']).nullable(),
        type_produit: z.string().nullable(),
        arome: z.string().nullable(),
        aromes: z.array(z.string()),
        contraintes: z.array(z.string()),
        profil: z.array(z.string()).default([]),
        volume: z.string().nullable().optional(),
      })
      .passthrough(),
    pistes: z
      .array(
        z
          .object({
            id: z.string().min(1),
            rang: z.union([z.literal(1), z.literal(2), z.literal(3)]),
            nom: z.string().min(1),
            description: z.string(),
            explication: z.string(),
            aromes: z.array(z.string()),
            nb_produits_marche: z.number().int().nonnegative(),
            references: z.array(referenceSchema),
            sans_reference: z.array(z.string()),
            references_sans_label: z.array(missingLabelSchema).default([]),
            image: z.string().min(1).nullable(),
          })
          .passthrough(),
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
    questions: z.array(questionSchema).max(2).default([]),
    version_modele: z.string().min(1),
    attribution: z.string().min(1),
  })
  .passthrough()
  .superRefine((snapshot, ctx) => {
    const expectedBrief = ['recapitulatif', 'echantillons'].includes(
      snapshot.etape,
    );
    const clarifying = ['relance', 'affiner'].includes(snapshot.etape);
    if (
      (snapshot.brief !== null) !== expectedBrief ||
      (snapshot.echantillons !== null) !==
        (snapshot.etape === 'echantillons') ||
      (clarifying
        ? snapshot.pistes.length !== 0
        : snapshot.pistes.length === 0) ||
      (snapshot.etape === 'affiner' && snapshot.questions.length === 0) ||
      (snapshot.brief &&
        !snapshot.pistes.some(
          (piste) => piste.id === snapshot.brief?.piste_id,
        )) ||
      new Set(snapshot.pistes.map((piste) => piste.id)).size !==
        snapshot.pistes.length ||
      new Set(snapshot.pistes.map((piste) => piste.rang)).size !==
        snapshot.pistes.length ||
      (snapshot.echantillons &&
        snapshot.echantillons.piste_id !== snapshot.brief?.piste_id)
    )
      ctx.addIssue({
        code: 'custom',
        message: 'La réponse ne correspond pas à l’étape du parcours.',
      });
  });
export type ConversationSnapshot = z.infer<typeof snapshotSchema>;
export type FlavorOption = ConversationSnapshot['pistes'][number];
export type DemoReference = z.infer<typeof referenceSchema>;
export type ClientBrief = z.infer<typeof briefSchema>;
