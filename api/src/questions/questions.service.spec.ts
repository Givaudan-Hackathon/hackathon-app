import { Test } from '@nestjs/testing';
import { afterEach, vi } from 'vitest';
import { PG_POOL } from '../database/database.module.js';
import { QuestionsService } from './questions.service.js';

describe('QuestionsService', () => {
  let service: QuestionsService;

  const fakePool = {
    query: async () => ({ rows: [{ id: 1 }] }),
  };

  beforeEach(async () => {
    process.env.AI_BASE_URL = 'http://fake';
    process.env.AI_MODEL = 'fake';
    const moduleRef = await Test.createTestingModule({
      providers: [QuestionsService, { provide: PG_POOL, useValue: fakePool }],
    }).compile();
    service = moduleRef.get(QuestionsService);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns 504 when body read times out', async () => {
    vi.stubGlobal('fetch', async () => ({
      ok: true,
      json: async () => {
        const err = new Error('timeout');
        err.name = 'TimeoutError';
        throw err;
      },
    }));

    await expect(service.create('q')).rejects.toMatchObject({ status: 504 });
  });

  it('returns 502 when body is not valid JSON', async () => {
    vi.stubGlobal('fetch', async () => ({
      ok: true,
      json: async () => {
        throw new SyntaxError('Unexpected token < in JSON');
      },
    }));

    await expect(service.create('q')).rejects.toMatchObject({ status: 502 });
  });

  it('returns 502 when provider responds non-OK', async () => {
    vi.stubGlobal('fetch', async () => ({
      ok: false,
      status: 500,
    }));

    await expect(service.create('q')).rejects.toMatchObject({ status: 502 });
  });
});
