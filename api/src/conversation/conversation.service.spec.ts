import { Test } from '@nestjs/testing';
import { afterEach, beforeEach, vi } from 'vitest';
import { ConversationService } from './conversation.service.js';

describe('ConversationService', () => {
  let service: ConversationService;

  beforeEach(async () => {
    process.env.DATA_API_BASE_URL = 'http://fake-python';
    const moduleRef = await Test.createTestingModule({
      providers: [ConversationService],
    }).compile();
    service = moduleRef.get(ConversationService);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('rejette un message vide sans piste_id', async () => {
    await expect(
      service.relayToPython({ message: '  ' }),
    ).rejects.toMatchObject({
      status: 400,
    });
  });

  it('transmet correctement et préserve la réponse complète', async () => {
    const mockResponse = {
      etape: 'pistes',
      pistes: [1, 2],
      extra_field: 'test',
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });
    vi.stubGlobal('fetch', fetchMock);

    const res = await service.relayToPython({ message: 'Je veux une boisson' });

    expect(res).toEqual(mockResponse);
    expect(fetchMock).toHaveBeenCalledWith(
      'http://fake-python/conversation',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'ngrok-skip-browser-warning': 'true',
        }),
      }),
    );
  });

  it('renvoie 504 si timeout', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockRejectedValue(
          Object.assign(new Error(), { name: 'TimeoutError' }),
        ),
    );
    await expect(
      service.relayToPython({ message: 'test' }),
    ).rejects.toMatchObject({ status: 504 });
  });

  it('renvoie 503 si service injoignable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('Network error')),
    );
    await expect(
      service.relayToPython({ message: 'test' }),
    ).rejects.toMatchObject({ status: 503 });
  });
});
