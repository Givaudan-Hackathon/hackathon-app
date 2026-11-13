import { Test } from '@nestjs/testing';
import { afterEach, beforeEach, vi } from 'vitest';
import { ConversationService } from './conversation.service.js';

const snapshot = () => ({
  session_id: 'session-test',
  etape: 'relance',
  intention: 'precision',
  reponse: 'Quel produit préparez-vous ?',
  compris: {
    division: null,
    type_produit: null,
    arome: null,
    aromes: [],
    contraintes: [],
    profil: ['frais'],
  },
  pistes: [],
  solutions: [],
  brief: null,
  echantillons: null,
  version_modele: 'test',
  attribution: 'Données de démonstration',
  extra_field: { conserve: true },
});

describe('ConversationService', () => {
  let service: ConversationService;
  beforeEach(async () => {
    vi.stubEnv('DATA_API_BASE_URL', 'http://fake-python/');
    vi.stubEnv('DATA_API_TIMEOUT_MS', '30000');
    const module = await Test.createTestingModule({
      providers: [ConversationService],
    }).compile();
    service = module.get(ConversationService);
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });
  it('rejette un message vide sans piste', async () => {
    await expect(service.relayToPython({ message: ' ' })).rejects.toMatchObject(
      { status: 400 },
    );
  });
  it('préserve le snapshot complet et transmet les identifiants', async () => {
    const data = snapshot();
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => data });
    vi.stubGlobal('fetch', fetchMock);
    expect(
      await service.relayToPython({
        session_id: 'session-test',
        message: '  Frais  ',
        piste_id: null,
      }),
    ).toEqual(data);
    expect(fetchMock).toHaveBeenCalledWith(
      'http://fake-python/conversation',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          session_id: 'session-test',
          message: 'Frais',
          piste_id: null,
        }),
        headers: expect.objectContaining({
          'ngrok-skip-browser-warning': 'true',
        }),
      }),
    );
  });
  it.each([
    null,
    [],
    {},
    'texte',
    { ...snapshot(), reponse: null },
    { ...snapshot(), pistes: [1, 2] },
    { ...snapshot(), etape: 'inconnue' },
    { ...snapshot(), session_id: '' },
  ])('refuse une réponse inexploitable : %j', async (data) => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: async () => data }),
    );
    await expect(
      service.relayToPython({ message: 'Bonjour' }),
    ).rejects.toMatchObject({ status: 502 });
  });
  it.each([500, 503, 429])(
    'classe HTTP %s comme panne du service',
    async (status) => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValue({
          ok: false,
          status,
          json: async () => ({ detail: 'trace interne' }),
        }),
      );
      await expect(
        service.relayToPython({ message: 'Bonjour' }),
      ).rejects.toMatchObject({ status: 503 });
    },
  );
  it.each([400, 422])(
    'distingue HTTP %s d’une panne serveur',
    async (status) => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValue({
          ok: false,
          status,
          json: async () => ({ detail: 'piste inconnue' }),
        }),
      );
      await expect(
        service.relayToPython({ message: '', piste_id: 'ancienne-piste' }),
      ).rejects.toMatchObject({ status: 422 });
    },
  );
  it.each(['TimeoutError', 'AbortError'])(
    'préserve 504 pendant fetch : %s',
    async (name) => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockRejectedValue(Object.assign(new Error(), { name })),
      );
      await expect(
        service.relayToPython({ message: 'Bonjour' }),
      ).rejects.toMatchObject({ status: 504 });
    },
  );
  it.each([true, false])(
    'préserve 504 pendant la lecture du corps, succès=%s',
    async (ok) => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValue({
          ok,
          status: ok ? 200 : 500,
          json: async () => {
            throw Object.assign(new Error(), { name: 'AbortError' });
          },
        }),
      );
      await expect(
        service.relayToPython({ message: 'Bonjour' }),
      ).rejects.toMatchObject({ status: 504 });
    },
  );
  it('classe un JSON invalide en 502', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => {
          throw new SyntaxError();
        },
      }),
    );
    await expect(
      service.relayToPython({ message: 'Bonjour' }),
    ).rejects.toMatchObject({ status: 502 });
  });
  it('ne transforme pas une panne HTML en erreur client', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => {
          throw new SyntaxError();
        },
      }),
    );
    await expect(
      service.relayToPython({ message: 'Bonjour' }),
    ).rejects.toMatchObject({ status: 503 });
  });
  it('classe une panne réseau en 503', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network')));
    await expect(
      service.relayToPython({ message: 'Bonjour' }),
    ).rejects.toMatchObject({ status: 503 });
  });
});
