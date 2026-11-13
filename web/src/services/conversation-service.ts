import { snapshotSchema } from '../../../api/src/contracts/conversation.ts';
import type { ConversationSnapshot } from '../../../api/src/contracts/conversation.ts';
export {
  referenceSchema,
  snapshotSchema,
} from '../../../api/src/contracts/conversation.ts';
export type {
  ConversationSnapshot,
  FlavorOption,
  DemoReference,
  ClientBrief,
} from '../../../api/src/contracts/conversation.ts';

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
