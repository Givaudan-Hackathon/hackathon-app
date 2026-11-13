import { z } from 'zod';
import type { ClientBrief, ServiceOptions } from './conversation-service.ts';

// Tarif illustratif du prototype, sans prestataire de paiement ni débit réel.
export const DEMO_ENGAGEMENT_CENTS = 1000;
export const paymentReceiptSchema = z.object({
  id: z.string().startsWith('DEMO-PAY-'),
  status: z.literal('succeeded_demo'),
  amountCents: z.literal(DEMO_ENGAGEMENT_CENTS),
  currency: z.literal('EUR'),
  briefKey: z.string().min(1),
  createdAt: z.iso.datetime(),
});
export type PaymentReceipt = z.infer<typeof paymentReceiptSchema>;
export type PaymentInput = {
  idempotencyKey: string;
  briefKey: string;
  outcome: 'success' | 'declined';
};
export interface PaymentService {
  pay(input: PaymentInput, options?: ServiceOptions): Promise<PaymentReceipt>;
}
export function briefKey(brief: ClientBrief | null): string {
  return brief ? JSON.stringify(brief) : '';
}
export function paymentMatchesBrief(
  payment: PaymentReceipt | null | undefined,
  brief: ClientBrief | null,
): payment is PaymentReceipt {
  const parsed = paymentReceiptSchema.safeParse(payment);
  return Boolean(
    brief && parsed.success && parsed.data.briefKey === briefKey(brief),
  );
}
export function formatDemoAmount(amountCents = DEMO_ENGAGEMENT_CENTS): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
  }).format(amountCents / 100);
}
