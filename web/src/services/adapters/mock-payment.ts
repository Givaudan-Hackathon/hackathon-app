import { ServiceError, wait } from '../conversation-service.ts';
import {
  DEMO_ENGAGEMENT_CENTS,
  type PaymentReceipt,
  type PaymentService,
} from '../payment-service.ts';

export function createMockPaymentService({ delay = 700 } = {}): PaymentService {
  const payments = new Map<string, Promise<PaymentReceipt>>();
  return {
    pay(input, options) {
      if (!input.idempotencyKey || !input.briefKey)
        return Promise.reject(
          new ServiceError(
            'INVALID_PAYMENT',
            'Choisissez un arôme avant de continuer.',
          ),
        );
      const key = `${input.idempotencyKey}:${input.briefKey}`;
      const existing = payments.get(key);
      if (existing) return existing;
      const pending = wait(delay, options?.signal)
        .then((): PaymentReceipt => {
          if (input.outcome === 'declined')
            throw new ServiceError(
              'PAYMENT_DECLINED',
              'Paiement fictif refusé. Aucun débit n’a eu lieu. Vous pouvez réessayer avec le scénario « Paiement accepté ».',
            );
          return {
            id: `DEMO-PAY-${crypto.randomUUID().slice(0, 8).toUpperCase()}`,
            status: 'succeeded_demo',
            amountCents: DEMO_ENGAGEMENT_CENTS,
            currency: 'EUR',
            briefKey: input.briefKey,
            createdAt: new Date().toISOString(),
          };
        })
        .catch((error: unknown) => {
          payments.delete(key);
          throw error;
        });
      payments.set(key, pending);
      return pending;
    },
  };
}
