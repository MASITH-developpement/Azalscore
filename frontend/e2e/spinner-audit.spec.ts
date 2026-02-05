/**
 * TEST E2E — Audit des spinners infinis AZALSCORE
 * Verifie que AUCUN ecran ne reste bloque en chargement apres 6 secondes.
 *
 * CIBLE : PRODUCTION (https://azalscore.com)
 *
 * Critere DOM precis :
 *   - INTERDIT apres 6s : .azals-state--loading (LoadingState actif = spinner infini)
 *   - INTERDIT apres 6s : .azals-app-init__spinner (spinner d'init app)
 *   - INTERDIT apres 6s : .azals-spinner (ancien spinner brut)
 *   - INTERDIT apres 6s : .animate-spin (Tailwind spin orphelin)
 *   - AUTORISE : .azals-state--error (ErrorState = timeout fonctionne, erreur affichee)
 *   - AUTORISE : .azals-state--empty (EmptyState = aucune donnee, ecran correct)
 *
 * Credentials : masith / contact@masith.fr / Gobelet2026!
 */

import { test, expect, type Page } from '@playwright/test';

// Production
const BASE_URL = 'https://azalscore.com';

// Credentials production
const PROD_TENANT = process.env.TEST_TENANT || 'masith';
const PROD_EMAIL = process.env.TEST_USER || 'contact@masith.fr';
const PROD_PASSWORD = process.env.TEST_PASSWORD || 'Azals2026!';

// Timeout d'attente apres navigation (6 secondes)
const SPINNER_TIMEOUT_MS = 6000;

// ============================================================
// HELPER : Login production
// ============================================================

async function loginProd(page: Page): Promise<void> {
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });

  // Attendre que le formulaire de login soit visible
  await page.waitForSelector('#tenant', { timeout: 15000 });

  // Remplir le formulaire
  await page.fill('#tenant', PROD_TENANT);
  await page.fill('#email', PROD_EMAIL);
  await page.fill('#password', PROD_PASSWORD);

  // Soumettre
  await page.click('button[type="submit"]');

  // Attendre que le login soit termine (le selecteur de module apparait)
  await page.waitForSelector('.azals-unified-header__selector', { timeout: 15000 });
}

// ============================================================
// HELPER : Naviguer vers un module via le dropdown
// ============================================================

async function navigateToModule(page: Page, menuLabel: string): Promise<void> {
  // Ouvrir le dropdown du selecteur de module
  await page.click('.azals-unified-header__selector');

  // Attendre que le dropdown apparaisse
  await page.waitForSelector('.azals-unified-header__dropdown', { timeout: 5000 });

  // Cliquer sur l'item du menu
  await page.click(`.azals-unified-header__item:has-text("${menuLabel}")`);

  // Attendre que le dropdown se ferme
  await page.waitForSelector('.azals-unified-header__dropdown', { state: 'detached', timeout: 5000 }).catch(() => {});
}

// ============================================================
// HELPER : Verifier l'absence de spinners ACTIFS
// ============================================================

async function assertNoActiveSpinner(page: Page, context: string): Promise<void> {
  // Attendre 6 secondes
  await page.waitForTimeout(SPINNER_TIMEOUT_MS);

  // 1. Verifier qu'aucun LoadingState actif n'est visible
  const loadingStateVisible = await page.locator('.azals-state--loading').first().isVisible().catch(() => false);
  expect(loadingStateVisible, `LoadingState (.azals-state--loading) encore actif apres 6s sur [${context}]`).toBe(false);

  // 2. Verifier qu'aucun spinner d'init de l'app n'est visible
  const initSpinner = await page.locator('.azals-app-init__spinner').first().isVisible().catch(() => false);
  expect(initSpinner, `Spinner d'init encore visible apres 6s sur [${context}]`).toBe(false);

  // 3. Verifier qu'aucun ancien spinner brut n'est visible
  const bareSpinner = await page.locator('.azals-spinner').first().isVisible().catch(() => false);
  expect(bareSpinner, `Spinner brut (.azals-spinner) encore visible apres 6s sur [${context}]`).toBe(false);

  // 4. Verifier qu'aucune animation spin orpheline n'existe
  const tailwindSpin = await page.locator('.animate-spin').first().isVisible().catch(() => false);
  expect(tailwindSpin, `Spinner Tailwind (.animate-spin) encore visible apres 6s sur [${context}]`).toBe(false);

  // LOG : diagnostiquer l'etat final
  const hasError = await page.locator('.azals-state--error').first().isVisible().catch(() => false);
  const hasEmpty = await page.locator('.azals-state--empty').first().isVisible().catch(() => false);
  if (hasError) {
    const errorTitle = await page.locator('.azals-state--error .azals-state__title').first().textContent().catch(() => '');
    const errorMsg = await page.locator('.azals-state--error .azals-state__message').first().textContent().catch(() => '');
    console.log(`  [INFO] ${context} : ErrorState -> "${errorTitle}" / "${errorMsg}"`);
  }
  if (hasEmpty) {
    console.log(`  [INFO] ${context} : EmptyState affiche`);
  }
}

// ============================================================
// TESTS : Route publique (login)
// ============================================================

test.describe('Audit spinners PRODUCTION — Routes publiques', () => {
  test('Page racine (login) — pas de spinner apres 6s', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
    await assertNoActiveSpinner(page, 'Page login');
  });
});

// ============================================================
// TESTS : Routes authentifiees (login production)
// ============================================================

const MODULES_TO_TEST = [
  { label: 'Nouvelle saisie', viewKey: 'saisie' },
  { label: 'Devis', viewKey: 'gestion-devis' },
  { label: 'Commandes', viewKey: 'gestion-commandes' },
  { label: 'Factures', viewKey: 'gestion-factures' },
  { label: 'Paiements', viewKey: 'gestion-paiements' },
  { label: 'Interventions', viewKey: 'gestion-interventions' },
  { label: 'CRM / Clients', viewKey: 'crm' },
  { label: 'Achats', viewKey: 'achats' },
  { label: 'Projets', viewKey: 'projets' },
  { label: 'Cockpit Dirigeant', viewKey: 'cockpit' },
];

test.describe('Audit spinners PRODUCTION — Routes authentifiees', () => {
  test.beforeEach(async ({ page }) => {
    await loginProd(page);
  });

  // Vue initiale apres login
  test('Vue initiale apres login — pas de spinner apres 6s', async ({ page }) => {
    await assertNoActiveSpinner(page, 'Vue initiale (saisie)');
  });

  // Chaque module via navigation menu
  for (const mod of MODULES_TO_TEST) {
    test(`${mod.label} (${mod.viewKey}) — pas de spinner apres 6s`, async ({ page }) => {
      await navigateToModule(page, mod.label);
      await assertNoActiveSpinner(page, mod.label);
    });
  }
});
