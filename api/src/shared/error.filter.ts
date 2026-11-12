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

    if (
      exception instanceof SyntaxError &&
      'status' in exception &&
      (exception as { status: number }).status === 400
    ) {
      return res.status(400).json({ error: 'Corps JSON invalide.' });
    }

    console.error(exception);
    return res.status(500).json({ error: 'Impossible de traiter la demande.' });
  }
}
