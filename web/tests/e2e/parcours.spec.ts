import { expect, test, type Page } from '@playwright/test';
import { createMockConversationService } from '../../src/services/adapters/mock-conversation.ts';

test.beforeEach(async ({ page }) => {
  const service = createMockConversationService({ delay: 80 });
  await page.route('**/api/conversation', async (route) => {
    const data = await service.send(route.request().postDataJSON());
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(data),
    });
  });
});

async function selectPiste(page: Page, index = 0) {
  await page
    .getByRole('button', { name: /Explorer :/ })
    .nth(index)
    .click();
  await page
    .getByRole('button', { name: 'Choisir cette piste', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Vérifier mon brief', exact: true })
    .first()
    .click();
}

async function noOverflow(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
}
async function start(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Une boisson fraîche' }).click();
  await expect(
    page.getByRole('heading', { name: '3 pistes pour votre projet' }),
  ).toBeVisible();
}
async function pay(page: Page) {
  await page
    .getByRole('checkbox', { name: 'Je confirme mon intérêt', exact: false })
    .check();
  await page
    .getByRole('button', { name: /Simuler le paiement de 10,00/ })
    .click();
  await expect(
    page.getByRole('heading', { name: 'Parlons de votre projet.' }),
  ).toBeVisible();
}
async function fillContact(page: Page) {
  await page.getByLabel('Où en êtes-vous ?').selectOption('prototype');
  await page.getByLabel('Produit fini prévu par mois').selectOption('unknown');
  await page.getByLabel('Prénom et nom').fill('Camille Martin');
  await page
    .getByLabel('Société', { exact: true })
    .fill('Atelier Démonstration');
  await page.getByLabel('E-mail professionnel').fill('camille@example.com');
}

test('sans piste, les questions affinent le besoin avant de proposer des arômes', async ({
  page,
}) => {
  await page.goto('/');
  await page
    .getByRole('textbox', { name: 'Qu’avez-vous envie de créer ?' })
    .fill('Je veux créer un produit alimentaire.');
  await page
    .getByRole('button', { name: 'Explorer les arômes de mon projet' })
    .click();
  const nav = page.getByRole('navigation', { name: 'Étapes de votre projet' });
  await expect(nav.getByRole('button', { name: '2. Affiner' })).toHaveAttribute(
    'aria-current',
    'step',
  );
  await expect(nav.getByRole('button', { name: '3. Choisir' })).toBeDisabled();
  await expect(page.locator('.chat-assistant')).toContainText(
    'Dans quel produit souhaitez-vous retrouver ce goût',
  );
  await expect(page.locator('.options-section')).toHaveCount(0);
  const answer = page.getByRole('textbox', { name: 'Précisons votre idée' });
  await answer.fill('Une boisson pétillante');
  await page.getByRole('button', { name: 'Envoyer ma précision' }).click();
  await expect(page.locator('.chat-assistant')).toContainText(
    'Quel goût imaginez-vous ?',
  );
  await expect(nav.getByRole('button', { name: '3. Choisir' })).toBeDisabled();
  await answer.fill('Citron vert');
  await page.getByRole('button', { name: 'Envoyer ma précision' }).click();
  await expect(
    page.getByRole('heading', { name: '3 pistes pour votre projet' }),
  ).toBeVisible();
  await expect(page.locator('.atelier-option')).toHaveCount(3);
  await expect(nav.getByRole('button', { name: '4. Paiement' })).toBeDisabled();
  await noOverflow(page);
});

test('accueil et dialogues centrés, accessibles et utilisables en petit écran', async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');
  await expect(
    page.getByRole('heading', {
      name: 'Vos idées ont de la saveur. Donnons-leur vie.',
    }),
  ).toBeVisible();
  await page
    .locator('.hero-photo')
    .evaluate((img) => (img as HTMLImageElement).decode());
  await page
    .locator('.hero-art')
    .evaluate((element) =>
      Promise.all(
        element
          .getAnimations({ subtree: true })
          .map((animation) => animation.finished.catch(() => undefined)),
      ),
    );
  await page.screenshot({
    path: `../.scratch/qa/v2/accueil-${testInfo.project.name}.png`,
    fullPage: true,
  });
  const original = page.viewportSize()!;
  for (const viewport of [original, { width: original.width, height: 360 }]) {
    await page.setViewportSize(viewport);
    const help = page.getByRole('button', { name: 'Obtenir de l’aide' });
    await help.click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await expect
      .poll(() =>
        dialog.evaluate(
          (el) =>
            el
              .getAnimations()
              .filter((animation) => animation.playState === 'running').length,
        ),
      )
      .toBe(0);
    const box = await dialog.boundingBox();
    const clientWidth = await page.evaluate(
      () => document.body.getBoundingClientRect().width,
    );
    expect(Math.abs(box!.x + box!.width / 2 - clientWidth / 2)).toBeLessThan(2);
    expect(
      Math.abs(box!.y + box!.height / 2 - viewport.height / 2),
    ).toBeLessThan(2);
    expect(box!.height).toBeLessThanOrEqual(viewport.height - 30);
    await page.keyboard.press('Tab');
    expect(
      await dialog.evaluate((el) => el.contains(document.activeElement)),
    ).toBe(true);
    await page.screenshot({
      path: `../.scratch/qa/v2/dialogue-${testInfo.project.name}-${viewport.height}.png`,
    });
    await page.keyboard.press('Escape');
    await expect(dialog).not.toBeVisible();
    await expect(help).toBeFocused();
    expect(await page.evaluate(() => document.body.style.overflow)).toBe('');
  }
  await page.setViewportSize(original);
  await page.getByRole('button', { name: 'Vos données' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.mouse.click(5, 5);
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await noOverflow(page);
  await expect(page.locator('.ingredient-tile')).toHaveCount(5);
  expect(errors).toEqual([]);
});

test('propositions en premier, étapes lisibles, paiement refusé puis accepté et confirmation explicite', async ({
  page,
}, testInfo) => {
  await start(page);
  const nav = page.getByRole('navigation', { name: 'Étapes de votre projet' });
  for (const button of await nav.getByRole('button').all())
    await expect(button).toBeVisible();
  await expect(nav.getByRole('button', { name: '3. Choisir' })).toHaveAttribute(
    'aria-current',
    'step',
  );
  await expect(
    nav.getByRole('button', { name: '5. Votre demande' }),
  ).toBeDisabled();
  expect(
    await page
      .locator('.options-section')
      .evaluate((el) =>
        Boolean(
          el.compareDocumentPosition(
            document.querySelector('.conversation-panel')!,
          ) & Node.DOCUMENT_POSITION_FOLLOWING,
        ),
      ),
  ).toBe(true);
  await page.screenshot({
    path: `../.scratch/qa/v2/pistes-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await selectPiste(page, 0);
  await page.getByRole('button', { name: 'Passer au paiement fictif' }).click();
  await expect(
    nav.getByRole('button', { name: '4. Paiement' }),
  ).toHaveAttribute('aria-current', 'step');
  await expect(
    nav.getByRole('button', { name: '5. Votre demande' }),
  ).toBeDisabled();
  await page
    .getByRole('button', { name: /Simuler le paiement de 10,00/ })
    .click();
  await expect(
    page.getByText(
      'Confirmez votre intérêt pour ce projet avant de continuer.',
    ),
  ).toBeVisible();
  await page
    .getByRole('checkbox', { name: 'Je confirme mon intérêt', exact: false })
    .check();
  await page.locator('.payment-scenarios > summary').click();
  await page.getByLabel('Résultat du paiement fictif').selectOption('declined');
  await page
    .getByRole('button', { name: /Simuler le paiement de 10,00/ })
    .click();
  await expect(page.getByRole('alert')).toContainText('Paiement fictif refusé');
  await expect(
    nav.getByRole('button', { name: '5. Votre demande' }),
  ).toBeDisabled();
  await page.getByLabel('Résultat du paiement fictif').selectOption('success');
  await noOverflow(page);
  await page.screenshot({
    path: `../.scratch/qa/v2/paiement-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page
    .getByRole('button', { name: /Simuler le paiement de 10,00/ })
    .dblclick();
  await expect(
    page.getByRole('heading', { name: 'Parlons de votre projet.' }),
  ).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Votre demande a été simulée.' }),
  ).toHaveCount(0);
  await page
    .getByRole('button', { name: 'Simuler l’envoi de ma demande' })
    .click();
  await expect(
    page.getByText('Indiquez votre prénom et votre nom.'),
  ).toBeVisible();
  await fillContact(page);
  await page.screenshot({
    path: `../.scratch/qa/v2/demande-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page
    .getByRole('button', { name: 'Simuler l’envoi de ma demande' })
    .dblclick();
  await expect(
    page.getByRole('heading', { name: 'Votre demande a été simulée.' }),
  ).toBeVisible();
  await expect(
    page.getByText('Aucun e-mail ni échantillon n’a été envoyé.'),
  ).toBeVisible();
  await expect(page.locator('.confirmation-payment')).toContainText('10,00');
  await noOverflow(page);
  await page.screenshot({
    path: `../.scratch/qa/v2/confirmation-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole('button', { name: 'Explorer une autre idée' }).click();
  await expect(
    page.getByRole('heading', {
      name: 'Vos idées ont de la saveur. Donnons-leur vie.',
    }),
  ).toBeVisible();
});

test('retours sans perte, corrections du brief et nouvelle validation du paiement', async ({
  page,
}) => {
  await start(page);
  await page.getByRole('button', { name: '1. Votre idée' }).click();
  await expect(page.getByLabel('Décrivez votre projet')).toHaveValue(
    /citron vert/,
  );
  await page
    .getByRole('button', { name: 'Poursuivre avec cette idée' })
    .click();
  await selectPiste(page, 0);
  await page.getByRole('button', { name: 'Passer au paiement fictif' }).click();
  await pay(page);
  await fillContact(page);
  await page.getByRole('button', { name: '4. Paiement' }).click();
  await expect(
    page.getByText('Paiement déjà simulé pour ce projet.'),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Continuer vers ma demande' }).click();
  await expect(page.getByLabel('Prénom et nom')).toHaveValue('Camille Martin');
  await page.getByRole('button', { name: '2. Affiner' }).click();
  await page
    .getByRole('textbox', { name: 'Une précision ou une question ?' })
    .fill('Elle doit être bio.');
  await page.getByRole('button', { name: 'Envoyer ma précision' }).click();
  await expect(
    page.getByRole('button', { name: '5. Votre demande' }),
  ).toBeDisabled();
  await expect(
    page.getByRole('button', { name: '4. Paiement' }),
  ).toBeDisabled();
  await selectPiste(page, 1);
  await page.getByRole('button', { name: 'Passer au paiement fictif' }).click();
  await expect(
    page.getByText('Paiement déjà simulé pour ce projet.'),
  ).toHaveCount(0);
  await pay(page);
  await expect(page.getByLabel('Prénom et nom')).toHaveValue('Camille Martin');
  await expect(page.getByLabel('E-mail professionnel')).toHaveValue(
    'camille@example.com',
  );
  await expect(page.getByLabel('Où en êtes-vous ?')).toHaveValue('prototype');
  await noOverflow(page);
});

test('refuser puis demander un contact sans paiement, avec images de remplacement', async ({
  page,
}) => {
  await page.route('**/*.webp', (route) => route.abort());
  await start(page);
  await expect(page.locator('.ingredient-fallback').first()).toBeVisible();
  await page
    .getByRole('button', { name: 'Aucune de ces pistes ne me convient' })
    .click();
  await expect(
    page.getByText('Dites-moi ce qui manque', { exact: false }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'En parler avec un expert', exact: true })
    .click();
  await expect(
    page.getByRole('heading', { name: 'Parlons de votre projet.' }),
  ).toBeVisible();
  await fillContact(page);
  await page
    .getByRole('button', { name: 'Simuler l’envoi de ma demande' })
    .click();
  await expect(
    page.getByRole('heading', { name: 'Votre demande a été simulée.' }),
  ).toBeVisible();
  await expect(page.locator('.confirmation-payment')).toHaveCount(0);
  await noOverflow(page);
});

test('texte traité sans HTML et mouvement réduit respecté', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  expect(
    await page
      .locator('.hero-photo')
      .evaluate((el) => getComputedStyle(el).animationName),
  ).toBe('none');
  const message =
    'Une boisson au citron vert <img src=x onerror="window.injected=true">';
  await page
    .getByRole('textbox', { name: 'Qu’avez-vous envie de créer ?' })
    .fill(message);
  await page
    .getByRole('button', { name: 'Explorer les arômes de mon projet' })
    .click();
  await expect(page.locator('.chat-user')).toContainText(message);
  expect(await page.locator('.chat-user img').count()).toBe(0);
  await page.getByRole('button', { name: 'Obtenir de l’aide' }).click();
  expect(
    await page
      .getByRole('dialog')
      .evaluate((el) => getComputedStyle(el).animationName),
  ).toBe('none');
});

test('footer en bas des pages courtes, étapes persistantes et réinitialisation confirmée', async ({
  page,
}) => {
  const original = page.viewportSize()!;
  await page.setViewportSize({ width: original.width, height: 1800 });
  await page.goto('/');
  await page
    .getByRole('textbox', { name: 'Qu’avez-vous envie de créer ?' })
    .fill('Une boisson');
  await page
    .getByRole('button', { name: 'Explorer les arômes de mon projet' })
    .click();
  await expect(
    page.getByRole('textbox', { name: 'Précisons votre idée' }),
  ).toBeEnabled();
  const geometry = await page.evaluate(() => ({
    footer: document.querySelector('footer')!.getBoundingClientRect().bottom,
    main: document.querySelector('main')!.getBoundingClientRect().bottom,
    footerTop: document.querySelector('footer')!.getBoundingClientRect().top,
    height: window.innerHeight,
    doc: document.documentElement.scrollHeight,
  }));
  expect(Math.abs(geometry.footer - geometry.height)).toBeLessThan(2);
  expect(geometry.main).toBeLessThanOrEqual(geometry.footerTop);
  await page
    .getByRole('button', { name: 'Nouvelle idée', exact: true })
    .click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('button', { name: 'Garder mon projet' }).click();
  await expect(
    page.getByRole('textbox', { name: 'Précisons votre idée' }),
  ).toBeVisible();
  await page.setViewportSize(original);
  await page.evaluate(() =>
    window.scrollTo(0, document.documentElement.scrollHeight),
  );
  expect(
    (await page.locator('.journey-bar').boundingBox())!.y,
  ).toBeGreaterThanOrEqual(0);
  await noOverflow(page);
});

test('une indisponibilité conserve la saisie et permet une reprise explicite', async ({
  page,
}) => {
  const service = createMockConversationService({ delay: 0 });
  const sent: string[] = [];
  await page.route('**/api/conversation', async (route) => {
    const input = route.request().postDataJSON();
    sent.push(input.message);
    if (sent.length === 1) {
      await route.fulfill({
        status: 503,
        json: { error: 'Assistant indisponible. Réessayez.' },
      });
    } else {
      await route.fulfill({ json: await service.send(input) });
    }
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Une boisson fraîche' }).click();
  await expect(page.getByRole('alert')).toContainText('Assistant indisponible');
  await expect(page.locator('.atelier-option')).toHaveCount(0);
  await expect(page.locator('.chat-composer textarea')).toHaveValue(sent[0]);
  expect(sent).toHaveLength(1);
  await page.getByRole('button', { name: 'Réessayer', exact: true }).click();
  await expect(page.locator('.atelier-option')).toHaveCount(3);
  expect(sent).toEqual([sent[0], sent[0]]);
  await page
    .getByRole('button', { name: 'Préciser mon projet', exact: true })
    .click();
  await page.locator('.chat-composer textarea').fill('Finalement bio');
  await page.route('**/api/conversation', (route) =>
    route.fulfill({
      status: 502,
      json: { error: 'Réponse incomplète. Réessayez.' },
    }),
  );
  await page.getByRole('button', { name: 'Envoyer ma précision' }).click();
  await expect(page.getByRole('alert')).toContainText('Réponse incomplète');
  await expect(page.locator('.chat-composer textarea')).toHaveValue(
    'Finalement bio',
  );
  await expect(page.locator('.project-summary')).toContainText(
    'boisson pétillante',
  );
  await noOverflow(page);
});

test('annuler l’attente conserve le texte et ignore la réponse tardive', async ({
  page,
}) => {
  const service = createMockConversationService({ delay: 0 });
  let release!: () => void;
  let completed!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const settled = new Promise<void>((resolve) => {
    completed = resolve;
  });
  let calls = 0;
  await page.route('**/api/conversation', async (route) => {
    calls++;
    if (calls === 1) {
      const data = await service.send(route.request().postDataJSON());
      await gate;
      await route.fulfill({ json: data }).catch(() => undefined);
      completed();
    } else {
      await route.fulfill({
        json: await service.send(route.request().postDataJSON()),
      });
    }
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Une boisson fraîche' }).click();
  await expect(
    page.getByRole('button', { name: 'Annuler l’attente' }),
  ).toBeVisible();
  await expect.poll(() => calls).toBe(1);
  await expect(page.locator('.chat-composer textarea')).toBeDisabled();
  await page.getByRole('button', { name: 'Annuler l’attente' }).click();
  await expect(
    page.getByRole('status').filter({ hasText: 'L’attente a été annulée' }),
  ).toContainText('L’attente a été annulée');
  const composer = page.locator('.chat-composer textarea');
  await expect(composer).not.toHaveValue('');
  await composer.fill('Un yaourt à la fraise');
  await page.getByRole('button', { name: 'Envoyer ma précision' }).click();
  await expect(page.locator('.project-summary')).toContainText('yaourt');
  release();
  await settled;
  await expect(page.locator('.project-summary')).toContainText('yaourt');
  await expect(page.locator('.atelier-sheet')).toContainText('Fraise');
  expect(calls).toBe(2);
});

for (const count of [1, 2]) {
  test(`${count} piste(s) : le titre et les alternatives suivent la réponse Data`, async ({
    page,
  }) => {
    const service = createMockConversationService({ delay: 0 });
    await page.route('**/api/conversation', async (route) => {
      const data = await service.send(route.request().postDataJSON());
      data.pistes = data.pistes.slice(0, count);
      await route.fulfill({ json: data });
    });
    await page.goto('/');
    await page.getByRole('button', { name: 'Une boisson fraîche' }).click();
    await expect(
      page.getByRole('heading', {
        name: `${count} ${count === 1 ? 'piste' : 'pistes'} pour votre projet`,
      }),
    ).toBeVisible();
    await expect(page.locator('.atelier-option')).toHaveCount(count);
    await expect(page.locator('.atelier-sheet')).toHaveCount(1);
    await noOverflow(page);
  });
}
