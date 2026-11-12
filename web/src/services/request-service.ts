import { z } from 'zod';
import type { ClientBrief, ServiceOptions } from './conversation-service.ts';

export const contactSchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, 'Indiquez votre prénom et votre nom.')
    .max(120),
  company: z
    .string()
    .trim()
    .min(2, 'Indiquez le nom de votre société.')
    .max(160),
  email: z
    .string()
    .trim()
    .email('Indiquez une adresse e-mail valide.')
    .max(254),
  phone: z
    .string()
    .trim()
    .max(30, 'Le numéro est trop long.')
    .regex(/^[+()\d\s.-]*$/, 'Vérifiez le format de votre téléphone.'),
  projectStage: z.enum(['exploration', 'prototype', 'launch'], {
    error: 'Choisissez le stade de votre projet.',
  }),
  monthlyVolume: z.enum(['under_500', '500_5000', 'over_5000', 'unknown'], {
    error: 'Choisissez une quantité ou « Je ne sais pas encore ».',
  }),
});
export type Contact = z.infer<typeof contactSchema>;
export type RequestInput = {
  idempotencyKey: string;
  kind: 'sample' | 'expert';
  contact: Contact;
  brief: ClientBrief | null;
  projectDescription: string;
};
export type RequestReceipt = {
  id: string;
  status: 'submitted_demo';
  createdAt: string;
  kind: RequestInput['kind'];
};
export interface RequestService {
  submit(
    input: RequestInput,
    options?: ServiceOptions,
  ): Promise<RequestReceipt>;
}
