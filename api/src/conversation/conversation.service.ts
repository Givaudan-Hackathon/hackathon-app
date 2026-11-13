import { HttpException, Injectable, Logger } from '@nestjs/common';
import { snapshotSchema } from '../contracts/conversation.js';
import { ConversationRequestDto } from './dto/conversation-request.dto.js';

function timedOut(error: unknown): boolean {
  return (
    error instanceof Error &&
    ['TimeoutError', 'AbortError'].includes(error.name)
  );
}

@Injectable()
export class ConversationService {
  private readonly logger = new Logger(ConversationService.name);

  async relayToPython(
    payload: ConversationRequestDto,
  ): Promise<Record<string, unknown>> {
    const baseUrl = process.env.DATA_API_BASE_URL;
    const timeout = Number(process.env.DATA_API_TIMEOUT_MS ?? 30_000);
    let url: URL;
    try {
      if (
        !baseUrl ||
        !Number.isInteger(timeout) ||
        timeout < 1 ||
        timeout > 120_000
      )
        throw new Error('Invalid Data configuration');
      url = new URL(`${baseUrl.replace(/\/+$/, '')}/conversation`);
      if (!['http:', 'https:'].includes(url.protocol))
        throw new Error('Invalid protocol');
    } catch {
      throw new HttpException(
        { error: 'La configuration de l’assistant est indisponible.' },
        500,
      );
    }
    const message = payload.message?.trim() || '';
    const pisteId = payload.piste_id?.trim() || null;
    if ((!message && !pisteId) || message.length > 500)
      throw new HttpException(
        {
          error:
            'Décrivez votre besoin en 1 à 500 caractères ou choisissez une piste.',
        },
        400,
      );

    const signal = AbortSignal.timeout(timeout);
    let response: Response;
    try {
      response = await fetch(url.href, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true',
        },
        body: JSON.stringify({
          session_id: payload.session_id || null,
          message,
          piste_id: pisteId,
          ...(payload.guidage !== undefined
            ? { guidage: payload.guidage }
            : {}),
        }),
        signal,
      });
    } catch (error) {
      if (signal.aborted || timedOut(error))
        throw new HttpException(
          {
            error:
              'L’assistant met trop de temps à répondre. Réessayez dans un instant.',
          },
          504,
        );
      this.logger.warn('Service Data injoignable.');
      throw new HttpException(
        {
          error:
            'L’assistant est momentanément indisponible. Votre projet est conservé.',
        },
        503,
      );
    }

    let data: unknown;
    try {
      data = await response.json();
    } catch (error) {
      if (signal.aborted || timedOut(error))
        throw new HttpException(
          {
            error:
              'L’assistant met trop de temps à répondre. Réessayez dans un instant.',
          },
          504,
        );
      if (!response.ok && response.status >= 500)
        throw new HttpException(
          { error: 'L’assistant est momentanément indisponible.' },
          response.status === 504 ? 504 : 503,
        );
      throw new HttpException(
        { error: 'La réponse de l’assistant est illisible. Réessayez.' },
        502,
      );
    }
    if (!response.ok) {
      this.logger.warn(`Service Data HTTP ${response.status}.`);
      if ([400, 422].includes(response.status))
        throw new HttpException(
          {
            error:
              'Le message ou la piste n’a pas été accepté. Précisez votre projet ou choisissez une piste encore proposée.',
          },
          422,
        );
      if (response.status === 504)
        throw new HttpException(
          { error: 'L’assistant met trop de temps à répondre.' },
          504,
        );
      if (response.status >= 500 || response.status === 429)
        throw new HttpException(
          {
            error:
              'L’assistant est momentanément indisponible. Réessayez dans un instant.',
          },
          503,
        );
      throw new HttpException(
        { error: 'Le service de l’assistant n’a pas pu traiter la demande.' },
        502,
      );
    }
    if (!snapshotSchema.safeParse(data).success)
      throw new HttpException(
        { error: 'La réponse de l’assistant est incomplète. Réessayez.' },
        502,
      );
    return data as Record<string, unknown>;
  }
}
