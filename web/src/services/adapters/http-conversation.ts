import {
  ServiceError,
  validateSnapshot,
  type ConversationService,
} from '../conversation-service.ts';

export function createHttpConversationService({
  endpoint = '/api/conversation',
  timeoutMs = 35_000,
  fetcher = fetch,
}: {
  endpoint?: string;
  timeoutMs?: number;
  fetcher?: typeof fetch;
} = {}): ConversationService {
  if (
    !endpoint.startsWith('/api/') ||
    endpoint.startsWith('//') ||
    !Number.isInteger(timeoutMs) ||
    timeoutMs < 1 ||
    timeoutMs > 125_000
  )
    throw new Error('Configuration de la conversation invalide.');
  return {
    async send(input, options) {
      const message = input.message.trim();
      if ((!message && !input.piste_id) || message.length > 500)
        throw new ServiceError(
          'INVALID_INPUT',
          'Décrivez votre projet en 1 à 500 caractères ou choisissez une piste.',
        );
      const deadline = AbortSignal.timeout(timeoutMs);
      const signal = options?.signal
        ? AbortSignal.any([options.signal, deadline])
        : deadline;
      try {
        const response = await fetcher(endpoint, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify({
            session_id: input.session_id ?? null,
            message,
            piste_id: input.piste_id ?? null,
            guidage: true,
          }),
          signal,
        });
        let body: unknown;
        try {
          body = await response.json();
        } catch (error) {
          if (signal.aborted) throw error;
          if (response.ok)
            throw new ServiceError(
              'INVALID_RESPONSE',
              'La réponse de l’assistant est illisible. Votre saisie est conservée.',
            );
        }
        if (!response.ok) {
          const errorText =
            typeof body === 'object' &&
            body !== null &&
            'error' in body &&
            typeof body.error === 'string'
              ? body.error.slice(0, 600)
              : 'L’assistant est momentanément indisponible. Réessayez dans un instant.';
          throw new ServiceError(
            response.status === 422
              ? 'INVALID_CHOICE'
              : response.status === 400
                ? 'INVALID_INPUT'
                : response.status === 504
                  ? 'TIMEOUT'
                  : 'UNAVAILABLE',
            errorText,
          );
        }
        return validateSnapshot(body);
      } catch (error) {
        if (options?.signal?.aborted)
          throw new DOMException('Requête annulée', 'AbortError');
        if (deadline.aborted)
          throw new ServiceError(
            'TIMEOUT',
            'L’analyse prend trop de temps. Votre projet et votre saisie sont conservés ; vous pouvez réessayer.',
          );
        if (error instanceof ServiceError) throw error;
        throw new ServiceError(
          'UNAVAILABLE',
          'Impossible de joindre l’assistant. Votre saisie est conservée ; réessayez dans un instant.',
        );
      }
    },
  };
}
