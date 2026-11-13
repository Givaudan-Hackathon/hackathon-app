import assert from 'node:assert/strict';
import test from 'node:test';
import { createHttpConversationService } from '../src/services/adapters/http-conversation.ts';
import { createMockConversationService } from '../src/services/adapters/mock-conversation.ts';
import { ServiceError } from '../src/services/conversation-service.ts';

async function sample() {
  const data = await createMockConversationService({ delay: 0 }).send({
    message: 'Une boisson pétillante au citron vert',
  });
  data.compris.profil = ['frais'];
  data.pistes[0].references_sans_label = [
    { arome: 'citron vert', code: 'DEMO-004', label_manquant: 'halal' },
  ];
  return data;
}

test('HTTP transmet le contexte et conserve les profils, réserves et ajouts Data', async () => {
  const data = { ...(await sample()), information_future: { conserver: true } };
  let calls = 0;
  const fetcher: typeof fetch = async (url, options) => {
    calls++;
    assert.equal(url, '/api/conversation');
    assert.deepEqual(JSON.parse(String(options?.body)), {
      session_id: 'session',
      message: 'Frais',
      piste_id: null,
      guidage: true,
    });
    return Response.json(data);
  };
  const service = createHttpConversationService({ fetcher });
  const result = await service.send({
    session_id: 'session',
    message: '  Frais  ',
  });
  assert.deepEqual(result.compris.profil, ['frais']);
  assert.equal(
    result.pistes[0].references_sans_label[0].label_manquant,
    'halal',
  );
  assert.deepEqual(result.information_future, { conserver: true });
  assert.equal(calls, 1);
});

test('une panne HTTP ne déclenche ni réponse fictive ni nouvelle tentative automatique', async () => {
  let calls = 0;
  const fetcher: typeof fetch = async () => {
    calls++;
    return Response.json({ error: 'Assistant indisponible.' }, { status: 503 });
  };
  await assert.rejects(
    createHttpConversationService({ fetcher }).send({ message: 'Une boisson' }),
    (error) => error instanceof ServiceError && error.code === 'UNAVAILABLE',
  );
  assert.equal(calls, 1);
});

test('une réponse JSON incomplète est refusée', async () => {
  for (const data of [
    null,
    [],
    {},
    { session_id: 'x', reponse: 'incomplet' },
  ]) {
    const fetcher: typeof fetch = async () => Response.json(data);
    await assert.rejects(
      createHttpConversationService({ fetcher }).send({
        message: 'Une boisson',
      }),
      (error) =>
        error instanceof ServiceError && error.code === 'INVALID_RESPONSE',
    );
  }
});

test('422 reste distinct d’une panne réseau', async () => {
  const fetcher: typeof fetch = async () =>
    Response.json({ error: 'Piste inconnue.' }, { status: 422 });
  await assert.rejects(
    createHttpConversationService({ fetcher }).send({
      message: '',
      piste_id: 'ancienne',
    }),
    (error) => error instanceof ServiceError && error.code === 'INVALID_CHOICE',
  );
});

test('le délai inclut la lecture du corps', async () => {
  const fetcher: typeof fetch = async () => {
    const response = Response.json({});
    response.json = async () => {
      await new Promise((resolve) => setTimeout(resolve, 15));
      throw new DOMException('Aborted', 'AbortError');
    };
    return response;
  };
  await assert.rejects(
    createHttpConversationService({ fetcher, timeoutMs: 5 }).send({
      message: 'Une boisson',
    }),
    (error) => error instanceof ServiceError && error.code === 'TIMEOUT',
  );
});

test('annuler une requête conserve son statut d’annulation', async () => {
  const controller = new AbortController();
  const fetcher: typeof fetch = async () => {
    controller.abort();
    throw new DOMException('Aborted', 'AbortError');
  };
  await assert.rejects(
    createHttpConversationService({ fetcher }).send(
      { message: 'Une boisson' },
      { signal: controller.signal },
    ),
    (error) => error instanceof DOMException && error.name === 'AbortError',
  );
});
