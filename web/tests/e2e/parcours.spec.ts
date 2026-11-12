import { expect, test } from '@playwright/test';

async function noOverflow(page: import('@playwright/test').Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
}

test('accueil, arômes illustrés et aide accessibles', async ({
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
  await noOverflow(page);
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
    path: `../.scratch/qa/accueil-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole('button', { name: 'Obtenir de l’aide' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await page.locator('#nos-aromes').scrollIntoViewIfNeeded();
  await expect(page.locator('.ingredient-tile')).toHaveCount(5);
  for (const image of await page.locator('.ingredient-tile img').all())
    await image.evaluate((img) => (img as HTMLImageElement).decode());
  expect(errors).toEqual([]);
});

test('corriger, choisir et simuler une demande complète', async ({
  page,
}, testInfo) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Une boisson fraîche' }).click();
  await expect(
    page.getByRole('heading', { name: 'Trois pistes, à vous d’explorer.' }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Choisir cet arôme' }),
  ).toHaveCount(3);
  await noOverflow(page);
  await page.screenshot({
    path: `../.scratch/qa/pistes-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole('button', { name: 'Choisir cet arôme' }).first().click();
  await expect(
    page.getByRole('button', { name: 'Préparer ma demande' }),
  ).toBeVisible();
  await page
    .getByRole('textbox', { name: 'Une précision ou une question ?' })
    .fill('Elle doit être bio.');
  await page.getByRole('button', { name: 'Envoyer ma précision' }).click();
  await expect(
    page.getByRole('heading', { name: 'Trois pistes, à vous d’explorer.' }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Préparer ma demande' }),
  ).toHaveCount(0);
  await expect(page.locator('.constraint-tags')).toContainText('bio');
  await page.getByRole('button', { name: 'Choisir cet arôme' }).first().click();
  await page.getByRole('button', { name: 'Préparer ma demande' }).click();
  await expect(
    page.getByRole('heading', { name: 'Parlons de votre projet.' }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Simuler l’envoi de ma demande' })
    .click();
  await expect(
    page.getByText('Indiquez votre prénom et votre nom.'),
  ).toBeVisible();
  await page.getByLabel('Où en êtes-vous ?').selectOption('prototype');
  await page.getByLabel('Produit fini prévu par mois').selectOption('unknown');
  await page.getByLabel('Prénom et nom').fill('Camille Martin');
  await page
    .getByLabel('Société', { exact: true })
    .fill('Atelier Démonstration');
  await page.getByLabel('E-mail professionnel').fill('camille@example.com');
  await noOverflow(page);
  await page.screenshot({
    path: `../.scratch/qa/demande-${testInfo.project.name}.png`,
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
  await noOverflow(page);
  await page.screenshot({
    path: `../.scratch/qa/confirmation-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole('button', { name: 'Explorer une autre idée' }).click();
  await expect(
    page.getByRole('heading', {
      name: 'Vos idées ont de la saveur. Donnons-leur vie.',
    }),
  ).toBeVisible();
});

test('refuser et rejoindre une demande de contact, avec images de remplacement', async ({
  page,
}) => {
  await page.route('**/*.webp', (route) => route.abort());
  await page.goto('/');
  await page.getByRole('button', { name: 'Une boisson fraîche' }).click();
  await expect(page.locator('.ingredient-fallback')).toHaveCount(3);
  await page.getByRole('button', { name: 'Aucun ne me convient' }).click();
  await expect(
    page.getByText('Dites-moi ce qui manque', { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Choisir cet arôme' }),
  ).toHaveCount(0);
  await page.getByRole('button', { name: 'En parler avec un expert' }).click();
  await expect(
    page.getByRole('heading', { name: 'Parlons de votre projet.' }),
  ).toBeVisible();
  await noOverflow(page);
});

test('texte utilisateur traité comme texte et mouvement réduit respecté', async ({
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
});
