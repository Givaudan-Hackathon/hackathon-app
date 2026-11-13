import { expect, test } from '@playwright/test';

test('parcours réel React → Nest → Python, guidage et demande simulée', async ({
  page,
}, info) => {
  const statuses: number[] = [];
  page.on('response', (response) => {
    if (new URL(response.url()).pathname === '/api/conversation')
      statuses.push(response.status());
  });
  await page.goto('/');
  await page
    .getByRole('textbox', { name: 'Qu’avez-vous envie de créer ?' })
    .fill('Je voudrais créer une boisson');
  await page
    .getByRole('button', { name: 'Explorer les arômes de mon projet' })
    .click();
  await page
    .getByRole('button', { name: 'boisson pétillante', exact: true })
    .click();
  const composer = page.locator('.chat-composer textarea');
  await expect(composer).toBeEnabled();
  await composer.fill('citron vert');
  await page.getByRole('button', { name: 'Envoyer ma précision' }).click();
  await expect(
    page.getByRole('button', { name: 'frais', exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'frais', exact: true }).click();
  await expect(page.locator('.atelier-sheet')).toBeVisible();
  expect(await page.locator('.atelier-option').count()).toBeGreaterThanOrEqual(
    1,
  );
  expect(await page.locator('.atelier-option').count()).toBeLessThanOrEqual(3);
  await expect(page.locator('.atelier-profiles')).toContainText(
    'Profil sensoriel',
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  if (info.project.name === 'mobile') {
    const positions = await page.evaluate(() => ({
      options: document
        .querySelector('.atelier-options')!
        .getBoundingClientRect().top,
      summary: document
        .querySelector('.atelier-sidebar')!
        .getBoundingClientRect().top,
    }));
    expect(positions.options).toBeLessThan(positions.summary);
  }
  await page.screenshot({
    path: `.scratch/qa/live-atelier-${info.project.name}.png`,
    fullPage: true,
  });
  await page
    .getByRole('button', { name: 'Choisir cette piste', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Vérifier mon brief', exact: true })
    .first()
    .click();
  await expect(
    page.getByRole('dialog', { name: 'Vérifier votre brief' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Passer au paiement fictif' }).click();
  await expect(
    page.getByRole('heading', { name: 'Donnons une suite à votre projet.' }),
  ).toBeVisible();
  // Le brouillon conservé par Python après « merci » ne déclenche aucun paiement.
  await page.getByRole('button', { name: '2. Affiner' }).click();
  await composer.fill('merci');
  await page.getByRole('button', { name: 'Envoyer ma précision' }).click();
  await expect(
    page.getByRole('button', { name: '3. Choisir' }),
  ).toHaveAttribute('aria-current', 'step');
  await expect(page.locator('.payment-panel')).toHaveCount(0);
  await page
    .getByRole('button', { name: 'Vérifier mon brief', exact: true })
    .first()
    .click();
  await page.getByRole('button', { name: 'Passer au paiement fictif' }).click();
  await page
    .getByRole('checkbox', { name: 'Je confirme mon intérêt', exact: false })
    .check();
  await page
    .getByRole('button', { name: /Simuler le paiement de 10,00/ })
    .click();
  await page.getByLabel('Où en êtes-vous ?').selectOption('prototype');
  await page.getByLabel('Produit fini prévu par mois').selectOption('unknown');
  await page.getByLabel('Prénom et nom').fill('Camille Démonstration');
  await page
    .getByLabel('Société', { exact: true })
    .fill('Atelier de démonstration');
  await page.getByLabel('E-mail professionnel').fill('camille@example.com');
  await page
    .getByRole('button', { name: 'Simuler l’envoi de ma demande' })
    .click();
  await expect(
    page.getByRole('heading', { name: 'Votre demande a été simulée.' }),
  ).toBeVisible();
  expect(statuses.length).toBeGreaterThanOrEqual(6);
  expect(statuses.every((status) => status === 200)).toBe(true);
});
