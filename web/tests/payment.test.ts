import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createMockConversationService } from '../src/services/adapters/mock-conversation.ts';
import { createMockPaymentService } from '../src/services/adapters/mock-payment.ts';
import { createMockRequestService } from '../src/services/adapters/mock-request.ts';
import {
  briefKey,
  paymentMatchesBrief,
} from '../src/services/payment-service.ts';
import { ServiceError } from '../src/services/conversation-service.ts';
import { buildJourney } from '../src/app/journey.ts';

async function selectedProject() {
  const service = createMockConversationService({ delay: 0 });
  const options = await service.send({
    message: 'Une boisson pétillante au citron vert',
  });
  return service.send({
    session_id: options.session_id,
    message: '',
    piste_id: options.pistes[0].id,
  });
}

test('un refus de paiement ne crée pas de succès ; une reprise et un double clic partagent un seul reçu', async () => {
  const payment = createMockPaymentService({ delay: 2 });
  const snapshot = await selectedProject();
  const input = {
    idempotencyKey: 'same-payment',
    briefKey: briefKey(snapshot.brief),
    outcome: 'declined' as const,
  };
  await assert.rejects(
    payment.pay(input),
    (error: unknown) =>
      error instanceof ServiceError && error.code === 'PAYMENT_DECLINED',
  );
  const first = payment.pay({ ...input, outcome: 'success' });
  const duplicate = payment.pay({ ...input, outcome: 'success' });
  assert.equal(first, duplicate);
  const [a, b] = await Promise.all([first, duplicate]);
  assert.equal(a.id, b.id);
  assert.equal(a.amountCents, 1000);
  assert.equal(a.status, 'succeeded_demo');
  assert.ok(paymentMatchesBrief(a, snapshot.brief));
});

test('un paiement annulé peut être repris sans produire un ancien succès', async () => {
  const service = createMockPaymentService({ delay: 10 });
  const snapshot = await selectedProject();
  const input = {
    idempotencyKey: 'cancelled-payment',
    briefKey: briefKey(snapshot.brief),
    outcome: 'success' as const,
  };
  const controller = new AbortController();
  const pending = service.pay(input, { signal: controller.signal });
  controller.abort();
  await assert.rejects(
    pending,
    (error: unknown) =>
      error instanceof DOMException && error.name === 'AbortError',
  );
  assert.equal((await service.pay(input)).status, 'succeeded_demo');
});

test('une demande d’échantillon exige un paiement pour son brief exact', async () => {
  const snapshot = await selectedProject();
  assert.ok(snapshot.brief);
  const request = createMockRequestService({ delay: 0 });
  const payment = await createMockPaymentService({ delay: 0 }).pay({
    idempotencyKey: 'paid-project',
    briefKey: briefKey(snapshot.brief),
    outcome: 'success',
  });
  const input = {
    idempotencyKey: 'request',
    kind: 'sample' as const,
    brief: snapshot.brief,
    projectDescription: 'Une boisson au citron vert',
    contact: {
      name: 'Camille Martin',
      company: 'Atelier Démo',
      email: 'camille@example.com',
      phone: '',
      projectStage: 'prototype' as const,
      monthlyVolume: 'unknown' as const,
    },
  };
  await assert.rejects(
    request.submit(input),
    (error: unknown) =>
      error instanceof ServiceError && error.code === 'PAYMENT_REQUIRED',
  );
  const changed = { ...snapshot.brief, contraintes: ['bio'] };
  assert.equal(paymentMatchesBrief(payment, changed), false);
  await assert.rejects(
    request.submit({ ...input, brief: changed, payment }),
    (error: unknown) =>
      error instanceof ServiceError && error.code === 'PAYMENT_REQUIRED',
  );
  const result = await request.submit({ ...input, payment });
  assert.equal(result.payment?.id, payment.id);
  assert.equal(result.status, 'submitted_demo');
});

test('les étapes futures suivent les prérequis ; un contact expert reste gratuit', () => {
  const base = {
    hasProject: true,
    hasOptions: true,
    hasBrief: true,
    hasPayment: false,
    expert: false,
    finished: false,
  };
  const unpaid = buildJourney(base);
  assert.equal(unpaid.find((step) => step.id === 'payment')?.available, true);
  assert.equal(unpaid.find((step) => step.id === 'request')?.available, false);
  assert.equal(
    buildJourney({ ...base, hasPayment: true }).find(
      (step) => step.id === 'request',
    )?.available,
    true,
  );
  const changed = buildJourney({ ...base, hasOptions: false, hasBrief: false });
  assert.equal(changed.find((step) => step.id === 'choose')?.available, false);
  assert.equal(changed.find((step) => step.id === 'payment')?.available, false);
  const expert = buildJourney({ ...base, expert: true });
  assert.equal(expert.find((step) => step.id === 'payment')?.skipped, true);
  assert.equal(expert.find((step) => step.id === 'request')?.available, true);
});

test('retirer bio enlève la contrainte et invalide le choix précédent', async () => {
  const service = createMockConversationService({ delay: 0 });
  const start = await service.send({
    message: 'Une boisson au citron vert bio',
  });
  await service.send({
    session_id: start.session_id,
    message: '',
    piste_id: start.pistes[0].id,
  });
  const corrected = await service.send({
    session_id: start.session_id,
    message: 'Finalement, sans bio',
  });
  assert.deepEqual(corrected.compris.contraintes, []);
  assert.equal(corrected.brief, null);
  assert.equal(corrected.etape, 'pistes');
});

test('un arôme non couvert remplace explicitement l’ancien besoin sans réutiliser ses pistes', async () => {
  for (const message of [
    'Finalement, de la mangue',
    'Remplacer le citron vert par de la mangue',
  ]) {
    const service = createMockConversationService({ delay: 0 });
    const start = await service.send({ message: 'Une boisson au citron vert' });
    const corrected = await service.send({
      session_id: start.session_id,
      message,
    });
    assert.equal(corrected.compris.arome, 'mangue');
    assert.equal(corrected.etape, 'relance');
    assert.deepEqual(corrected.pistes, []);
    assert.match(corrected.reponse, /n’est pas couvert/);
  }
});
