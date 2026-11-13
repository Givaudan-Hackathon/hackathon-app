import { HttpException, Injectable, Logger } from '@nestjs/common';
import { ConversationRequestDto } from './dto/conversation-request.dto.js';

@Injectable()
export class ConversationService {
  private readonly logger = new Logger(ConversationService.name);

  async relayToPython(
    payload: ConversationRequestDto,
  ): Promise<Record<string, unknown>> {
    const baseUrl = process.env.DATA_API_BASE_URL;

    if (!baseUrl) {
      throw new HttpException(
        'Configuration DATA_API_BASE_URL manquante.',
        500,
      );
    }

    const message = payload.message?.trim() || '';
    const pisteId = payload.piste_id?.trim() || null;

    // Règle métier : le message ne peut pas être vide si pas de piste_id
    if (!message && !pisteId) {
      throw new HttpException(
        { error: "Le message est requis si aucune piste_id n'est fournie." },
        400,
      );
    }

    const url = `${baseUrl.replace(/\/+$/, '')}/conversation`;

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true',
        },
        body: JSON.stringify({
          session_id: payload.session_id || null,
          message: message,
          piste_id: pisteId,
        }),
        signal: AbortSignal.timeout(30_000),
      });
    } catch (error: unknown) {
      if (
        error instanceof Error &&
        (error.name === 'TimeoutError' || error.name === 'AbortError')
      ) {
        throw new HttpException(
          { error: "Le service Data n'a pas répondu dans les 30 secondes." },
          504,
        );
      }
      this.logger.error('Erreur réseau Data:', error);
      throw new HttpException(
        { error: 'Le service Data est injoignable.' },
        503,
      );
    }

    if (!response.ok) {
      this.logger.warn(`Erreur Data HTTP ${response.status}`);
      let errorBody: Record<string, unknown>;
      try {
        errorBody = (await response.json()) as Record<string, unknown>;
      } catch {
        throw new HttpException(
          { error: 'Le service Data a renvoyé une erreur illisible.' },
          502,
        );
      }

      const errorMessage =
        typeof errorBody?.detail === 'string'
          ? errorBody.detail
          : typeof errorBody?.error === 'string'
            ? errorBody.error
            : 'Erreur Data inconnue.';

      throw new HttpException({ error: errorMessage }, 422);
    }

    try {
      const data = (await response.json()) as Record<string, unknown>;
      return data; // On retourne tout l'objet (brief, echantillons, etc.)
    } catch {
      throw new HttpException(
        { error: 'Le service Data a renvoyé un JSON invalide.' },
        502,
      );
    }
  }
}
