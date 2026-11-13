import { HttpException } from '@nestjs/common';
import { ErrorFilter } from './error.filter.js';

describe('ErrorFilter', () => {
  const filter = new ErrorFilter();

  function run(exception: unknown) {
    const captured: { status?: number; body?: unknown } = {};
    const res = {
      status(code: number) {
        captured.status = code;
        return this;
      },
      json(body: unknown) {
        captured.body = body;
        return this;
      },
    };
    const host = {
      switchToHttp: () => ({ getResponse: () => res }),
    };
    filter.catch(exception, host as never);
    return captured;
  }

  it('preserves 502 HttpException whose message mentions JSON', () => {
    const out = run(
      new HttpException("L'IA a renvoyé une réponse JSON invalide.", 502),
    );
    expect(out.status).toBe(502);
    expect(out.body).toEqual({
      error: "L'IA a renvoyé une réponse JSON invalide.",
    });
  });

  it('preserves 504 HttpException', () => {
    const out = run(
      new HttpException("L'IA n'a pas répondu dans les 60 secondes.", 504),
    );
    expect(out.status).toBe(504);
  });

  it('maps body-parser SyntaxError to 400 with stable message', () => {
    const out = run(
      new SyntaxError('Unexpected token < in JSON at position 0'),
    );
    expect(out.status).toBe(400);
    expect(out.body).toEqual({ error: 'Corps JSON invalide.' });
  });

  it('maps body-parser message pattern to 400', () => {
    const err = Object.assign(new Error("Expected property name or '}'"), {
      type: 'entity.parse.failed',
    });
    const out = run(err);
    expect(out.status).toBe(400);
    expect(out.body).toEqual({ error: 'Corps JSON invalide.' });
  });
});
