import { expect, test, type Page } from '@playwright/test';

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
    page.getByRole('heading', { name: 'Trois pistes, à vous d’explorer.' }),
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
  await page.getByRole('button', { name: 'Choisir cet arôme' }).first().click();
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
  await page.getByRole('button', { name: 'Choisir cet arôme' }).first().click();
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
  await page.getByRole('button', { name: 'Choisir cet arôme' }).nth(1).click();
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
  await expect(page.locator('.ingredient-fallback')).toHaveCount(3);
  await page.getByRole('button', { name: 'Aucun ne me convient' }).click();
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
