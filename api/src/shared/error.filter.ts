import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
} from '@nestjs/common';
import type { Response } from 'express';

@Catch()
export class ErrorFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const res = host.switchToHttp().getResponse<Response>();

    const msg = (exception as { message?: unknown })?.message;
    const cause = (exception as { cause?: unknown })?.cause;

    const isJsonParseError =
      exception instanceof SyntaxError ||
      cause instanceof SyntaxError ||
      (typeof exception === 'object' &&
        exception !== null &&
        ((exception as { type?: unknown }).type === 'entity.parse.failed' ||
          (typeof msg === 'string' &&
            (msg.includes('JSON') ||
              msg.startsWith('Unexpected token') ||
              msg.startsWith('Expected property')))));

    if (isJsonParseError) {
      return res.status(400).json({ error: 'Corps JSON invalide.' });
    }

    if (exception instanceof HttpException) {
      const status = exception.getStatus();
      const response = exception.getResponse();
      let message: string;
      if (typeof response === 'string') {
        message = response;
      } else {
        const obj = response as { message?: unknown; error?: unknown };
        message =
          typeof obj.message === 'string'
            ? obj.message
            : typeof obj.error === 'string'
              ? obj.error
              : 'Erreur';
      }
      return res.status(status).json({ error: message });
    }

    console.error(exception);
    return res.status(500).json({ error: 'Impossible de traiter la demande.' });
  }
}
