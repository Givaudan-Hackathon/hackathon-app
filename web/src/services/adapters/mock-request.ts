import {
  contactSchema,
  type RequestReceipt,
  type RequestService,
} from '../request-service.ts';
import { ServiceError, wait } from '../conversation-service.ts';

export function createMockRequestService({
  delay = 500,
  failNext = false,
} = {}): RequestService {
  const requests = new Map<string, Promise<RequestReceipt>>();
  let shouldFail = failNext;
  return {
    submit(input, options) {
      const contact = contactSchema.safeParse(input.contact);
      if (!contact.success)
        return Promise.reject(
          new ServiceError(
            'INVALID_CONTACT',
            'Vérifiez vos coordonnées avant de continuer.',
          ),
        );
      if (!input.idempotencyKey || (input.kind === 'sample' && !input.brief))
        return Promise.reject(
          new ServiceError(
            'INVALID_REQUEST',
            'Choisissez un arôme et relisez votre demande avant de continuer.',
          ),
        );
      const existing = requests.get(input.idempotencyKey);
      if (existing) return existing;
      const pending = wait(delay, options?.signal)
        .then((): RequestReceipt => {
          if (shouldFail) {
            shouldFail = false;
            throw new ServiceError(
              'UNAVAILABLE',
              'La demande n’a pas pu être simulée. Vos coordonnées sont conservées ; réessayez.',
            );
          }
          return {
            id: `DEMO-${crypto.randomUUID().slice(0, 8).toUpperCase()}`,
            status: 'submitted_demo',
            createdAt: new Date().toISOString(),
            kind: input.kind,
          };
        })
        .catch((error: unknown) => {
          requests.delete(input.idempotencyKey);
          throw error;
        });
      requests.set(input.idempotencyKey, pending);
      return pending;
    },
  };
}
