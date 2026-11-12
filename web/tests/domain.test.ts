import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createMockConversationService } from '../src/services/adapters/mock-conversation.ts';
import { createMockRequestService } from '../src/services/adapters/mock-request.ts';
import {
  snapshotSchema,
  ServiceError,
} from '../src/services/conversation-service.ts';
import {
  conversationReducer,
  initialConversation,
} from '../src/features/conversation/model.ts';

const project = 'Je crée une boisson pétillante au citron vert, peu sucrée.';
const contact = {
  name: 'Camille Martin',
  company: 'Atelier Démo',
  email: 'camille@example.com',
  phone: '',
  projectStage: 'prototype' as const,
  monthlyVolume: 'unknown' as const,
};

test('une idée incomplète provoque une relance sans inventer le goût', async () => {
  const service = createMockConversationService({ delay: 0 });
  const result = await service.send({
    message: 'Je voudrais créer une boisson.',
  });
  assert.equal(result.etape, 'relance');
  assert.equal(result.compris.arome, null);
  assert.deepEqual(result.pistes, []);
});

test('le parcours utilise un identifiant de piste, puis prépare un brouillon non envoyé', async () => {
  const service = createMockConversationService({ delay: 0 });
  const options = await service.send({ message: project });
  assert.equal(options.pistes.length, 3);
  const selected = await service.send({
    session_id: options.session_id,
    message: '',
    piste_id: options.pistes[0].id,
  });
  assert.equal(selected.etape, 'recapitulatif');
  assert.equal(selected.brief?.piste_id, options.pistes[0].id);
  assert.deepEqual(selected.brief?.codes_references, ['DEMO-004']);
  const draft = await service.send({
    session_id: options.session_id,
    message: 'Je souhaite un échantillon.',
  });
  assert.equal(draft.etape, 'echantillons');
  assert.equal(draft.echantillons?.statut, 'brouillon_non_envoye');
  assert.match(draft.reponse, /Aucun échantillon n’est envoyé/);
});

test('corriger le projet invalide sélection, brief et brouillon, sans changer le produit', async () => {
  const service = createMockConversationService({ delay: 0 });
  const first = await service.send({ message: project });
  await service.send({
    session_id: first.session_id,
    message: '',
    piste_id: first.pistes[0].id,
  });
  await service.send({
    session_id: first.session_id,
    message: 'Un échantillon, merci.',
  });
  const corrected = await service.send({
    session_id: first.session_id,
    message: 'Elle doit être bio.',
  });
  assert.equal(corrected.etape, 'pistes');
  assert.equal(corrected.brief, null);
  assert.equal(corrected.echantillons, null);
  assert.equal(corrected.compris.type_produit, 'boisson pétillante');
  assert.ok(corrected.compris.contraintes.includes('bio'));
});

test('refuser les propositions permet de préciser sans conserver un faux choix', async () => {
  const service = createMockConversationService({ delay: 0 });
  const first = await service.send({ message: project });
  const rejected = await service.send({
    session_id: first.session_id,
    message: 'Aucun ne me convient.',
  });
  assert.equal(rejected.etape, 'relance');
  assert.deepEqual(rejected.pistes, []);
  assert.equal(rejected.brief, null);
  assert.match(rejected.reponse, /expert/);
});

test('une piste inconnue est rejetée et la session reste utilisable', async () => {
  const service = createMockConversationService({ delay: 0 });
  const first = await service.send({ message: project });
  await assert.rejects(
    service.send({
      session_id: first.session_id,
      message: '',
      piste_id: 'inconnu',
    }),
    (error: unknown) =>
      error instanceof ServiceError && error.code === 'INVALID_CHOICE',
  );
  const next = await service.send({
    session_id: first.session_id,
    message: '',
    piste_id: first.pistes[0].id,
  });
  assert.equal(next.etape, 'recapitulatif');
});

test('annuler une correction simulée ne modifie pas la sélection disponible', async () => {
  const service = createMockConversationService({ delay: 5 });
  const first = await service.send({ message: project });
  const controller = new AbortController();
  const pending = service.send(
    { session_id: first.session_id, message: 'Finalement, à la fraise.' },
    { signal: controller.signal },
  );
  controller.abort();
  await assert.rejects(
    pending,
    (error: unknown) =>
      error instanceof DOMException && error.name === 'AbortError',
  );
  const selected = await service.send({
    session_id: first.session_id,
    message: '',
    piste_id: first.pistes[0].id,
  });
  assert.equal(selected.brief?.piste_id, first.pistes[0].id);
});

test('après une indisponibilité, une nouvelle tentative explicite peut aboutir', async () => {
  const service = createMockConversationService({ delay: 0, failNext: true });
  await assert.rejects(
    service.send({ message: project }),
    (error: unknown) =>
      error instanceof ServiceError && error.code === 'UNAVAILABLE',
  );
  assert.equal((await service.send({ message: project })).etape, 'pistes');
});

test('les cinq arômes du catalogue ont un parcours de démonstration', async () => {
  for (const flavor of [
    'citron vert',
    'citron jaune',
    'pamplemousse',
    'vanille',
    'fraise',
  ]) {
    const service = createMockConversationService({ delay: 0 });
    const result = await service.send({
      message: `Une boisson au goût ${flavor}.`,
    });
    assert.equal(result.etape, 'pistes', flavor);
    assert.equal(result.pistes.length, 3, flavor);
  }
});

test('le contrat refuse un état incohérent ou des pistes dupliquées', async () => {
  const snapshot = await createMockConversationService({ delay: 0 }).send({
    message: project,
  });
  assert.equal(
    snapshotSchema.safeParse({ ...snapshot, etape: 'echantillons' }).success,
    false,
  );
  assert.equal(
    snapshotSchema.safeParse({
      ...snapshot,
      pistes: [snapshot.pistes[0], snapshot.pistes[0]],
    }).success,
    false,
  );
});

test('une erreur conserve le snapshot précédent jusqu’à une réponse valide', async () => {
  const snapshot = await createMockConversationService({ delay: 0 }).send({
    message: project,
  });
  const previous = { ...initialConversation, snapshot };
  const failed = conversationReducer(previous, {
    type: 'failure',
    error: 'Indisponible',
  });
  assert.equal(failed.snapshot, snapshot);
  assert.equal(failed.error, 'Indisponible');
  assert.equal(failed.pending, false);
});

test('les doubles dépôts partagent le même reçu de simulation', async () => {
  const service = createMockRequestService({ delay: 2 });
  const input = {
    idempotencyKey: 'one-request',
    kind: 'expert' as const,
    brief: null,
    contact,
    projectDescription: project,
  };
  const first = service.submit(input);
  const second = service.submit(input);
  assert.equal(first, second);
  const [a, b] = await Promise.all([first, second]);
  assert.equal(a.id, b.id);
  assert.equal(a.status, 'submitted_demo');
});

test('un dépôt échoué est retentable sans produire un faux succès', async () => {
  const service = createMockRequestService({ delay: 0, failNext: true });
  const input = {
    idempotencyKey: 'retry',
    kind: 'expert' as const,
    brief: null,
    contact,
    projectDescription: project,
  };
  await assert.rejects(service.submit(input));
  assert.equal((await service.submit(input)).status, 'submitted_demo');
});

test('des coordonnées invalides ou un échantillon sans brief ne sont pas déposés', async () => {
  const service = createMockRequestService({ delay: 0 });
  const input = {
    idempotencyKey: 'invalid',
    kind: 'sample' as const,
    brief: null,
    contact,
    projectDescription: project,
  };
  await assert.rejects(
    service.submit(input),
    (error: unknown) =>
      error instanceof ServiceError && error.code === 'INVALID_REQUEST',
  );
  await assert.rejects(
    service.submit({
      ...input,
      kind: 'expert',
      contact: { ...contact, email: 'camille@' },
    }),
    (error: unknown) =>
      error instanceof ServiceError && error.code === 'INVALID_CONTACT',
  );
});

test('annuler un dépôt simulé ne crée pas de reçu et permet une nouvelle tentative', async () => {
  const service = createMockRequestService({ delay: 10 });
  const input = {
    idempotencyKey: 'cancelled',
    kind: 'expert' as const,
    brief: null,
    contact,
    projectDescription: project,
  };
  const controller = new AbortController();
  const pending = service.submit(input, { signal: controller.signal });
  controller.abort();
  await assert.rejects(
    pending,
    (error: unknown) =>
      error instanceof DOMException && error.name === 'AbortError',
  );
  assert.equal((await service.submit(input)).status, 'submitted_demo');
});
