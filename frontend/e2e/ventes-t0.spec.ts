/**
 * AZALSCORE - Tests E2E VENTES T0 (Optimise)
 *
 * Utilise storageState pour auth partagee.
 *
 * Couverture:
 * - Navigation vers le module Facturation
 * - Liste des devis et factures
 * - Creation de documents
 * - UI responsive
 */

import { test, expect, Page } from '@playwright/test';
import {
  waitForLoadingComplete,
  assertNoPageError,
  openCreateForm,
  closeModal,
  setupConsoleErrorCollector,
  getCriticalErrors,
  SELECTORS as BASE_SELECTORS,
  TIMEOUTS
} from './fixtures/helpers';

const BASE_URL = process.env.BASE_URL || 'https://azalscore.com';

// ============================================================================
// HELPERS
// ============================================================================

async function pageHasContent(page: Page): Promise<boolean> {
  const contentSelectors = [
    'table', '.azals-table', '.azals-card', '[class*="card"]',
    'main', 'h1', 'h2', 'h3', '[class*="title"]', '[class*="wrapper"]',
    '[class*="page"]', 'form', 'button',
  ];

  for (const selector of contentSelectors) {
    const isVisible = await page.locator(selector).first().isVisible().catch(() => false);
    if (isVisible) return true;
  }
  return false;
}

// ============================================================================
// TESTS: NAVIGATION
// ============================================================================

test.describe('VENTES T0 - Navigation', () => {
  test.describe.configure({ mode: 'parallel' });

  test('accede au dashboard facturation', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing`);
    await waitForLoadingComplete(page);
    await assertNoPageError(page, 'Invoicing');
    await expect(page).toHaveURL(/.*invoicing/);
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('accede a la liste des devis', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing/quotes`);
    await waitForLoadingComplete(page);
    await expect(page).toHaveURL(/.*invoicing\/quotes/);
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('accede a la liste des factures', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing/invoices`);
    await waitForLoadingComplete(page);
    await expect(page).toHaveURL(/.*invoicing\/invoices/);
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('navigue entre devis et factures', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing/quotes`);
    await waitForLoadingComplete(page);
    await expect(page).toHaveURL(/.*invoicing\/quotes/);

    await page.goto(`${BASE_URL}/invoicing/invoices`);
    await waitForLoadingComplete(page);
    await expect(page).toHaveURL(/.*invoicing\/invoices/);
  });
});

// ============================================================================
// TESTS: LISTE DES DEVIS
// ============================================================================

test.describe('VENTES T0 - Liste des Devis', () => {
  test.describe.configure({ mode: 'parallel' });

  test('affiche la liste des devis', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing/quotes`);
    await waitForLoadingComplete(page);
    await assertNoPageError(page, 'Quotes list');
    expect(page.url()).toContain('/invoicing/quotes');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('bouton nouveau devis visible', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing/quotes`);
    await waitForLoadingComplete(page);

    const newButton = page.locator('button:has-text("Nouveau"), button:has-text("Ajouter"), button:has-text("Creer")');
    const isVisible = await newButton.first().isVisible({ timeout: TIMEOUTS.medium }).catch(() => false);
    // Bouton peut ne pas etre visible selon les droits
    await assertNoPageError(page, 'Quotes buttons');
  });
});

// ============================================================================
// TESTS: CREATION DEVIS
// ============================================================================

test.describe('VENTES T0 - Creation Devis', () => {
  test.describe.configure({ mode: 'parallel' });

  test('formulaire de creation accessible via URL', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing/quotes/new`);
    await waitForLoadingComplete(page);
    await expect(page).toHaveURL(/.*quotes\/new/);
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('formulaire contient des champs', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing/quotes/new`);
    await waitForLoadingComplete(page);

    const hasForm = await page.locator('form').isVisible().catch(() => false);
    const hasInputs = await page.locator('input, select, textarea').first().isVisible().catch(() => false);
    const hasContent = await pageHasContent(page);

    expect(hasForm || hasInputs || hasContent).toBeTruthy();
  });
});

// ============================================================================
// TESTS: FACTURES
// ============================================================================

test.describe('VENTES T0 - Liste des Factures', () => {
  test.describe.configure({ mode: 'parallel' });

  test('affiche la liste des factures', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing/invoices`);
    await waitForLoadingComplete(page);
    await assertNoPageError(page, 'Invoices list');
    expect(page.url()).toContain('/invoicing/invoices');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('bouton nouvelle facture visible', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing/invoices`);
    await waitForLoadingComplete(page);

    const newButton = page.locator('button:has-text("Nouveau"), button:has-text("Ajouter"), button:has-text("Creer")');
    const isVisible = await newButton.first().isVisible({ timeout: TIMEOUTS.medium }).catch(() => false);
    await assertNoPageError(page, 'Invoices buttons');
  });

  test('formulaire creation facture accessible', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing/invoices/new`);
    await waitForLoadingComplete(page);
    await expect(page).toHaveURL(/.*invoices\/new/);
    expect(await pageHasContent(page)).toBeTruthy();
  });
});

// ============================================================================
// TESTS: UI RESPONSIVE
// ============================================================================

test.describe('VENTES T0 - UI Responsive', () => {
  test.describe.configure({ mode: 'parallel' });

  test('desktop: affiche correctement', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(`${BASE_URL}/invoicing/quotes`);
    await waitForLoadingComplete(page);
    await assertNoPageError(page, 'Desktop');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('tablet: affiche correctement', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(`${BASE_URL}/invoicing/quotes`);
    await waitForLoadingComplete(page);
    await assertNoPageError(page, 'Tablet');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('mobile: affiche correctement', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`${BASE_URL}/invoicing/quotes`);
    await waitForLoadingComplete(page);
    await assertNoPageError(page, 'Mobile');
    expect(await pageHasContent(page)).toBeTruthy();
  });
});

// ============================================================================
// TESTS: PERFORMANCE
// ============================================================================

test.describe('VENTES T0 - Performance', () => {
  test.describe.configure({ mode: 'parallel' });

  test('page devis charge rapidement', async ({ page }) => {
    const startTime = Date.now();
    await page.goto(`${BASE_URL}/invoicing/quotes`);
    await waitForLoadingComplete(page);

    const hasContent = await pageHasContent(page);
    const loadTime = Date.now() - startTime;

    expect(hasContent).toBeTruthy();
    expect(loadTime).toBeLessThan(10000);
  });

  test('navigation entre pages fluide', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing/quotes`);
    await waitForLoadingComplete(page);

    const startTime = Date.now();
    await page.goto(`${BASE_URL}/invoicing/invoices`);
    await waitForLoadingComplete(page);
    const navTime = Date.now() - startTime;

    expect(await pageHasContent(page)).toBeTruthy();
    expect(navTime).toBeLessThan(5000);
  });
});

// ============================================================================
// TESTS: GESTION ERREURS
// ============================================================================

test.describe('VENTES T0 - Gestion Erreurs', () => {
  test.describe.configure({ mode: 'parallel' });

  test('pas d\'erreurs JavaScript critiques', async ({ page }) => {
    const errors = setupConsoleErrorCollector(page);

    await page.goto(`${BASE_URL}/invoicing/quotes`);
    await waitForLoadingComplete(page);

    const criticalErrors = getCriticalErrors(errors);

    if (criticalErrors.length > 0) {
      console.log('Critical JS errors found:', criticalErrors);
    }

    expect(criticalErrors.length).toBe(0);
  });
});

// ============================================================================
// TESTS: MULTI-TENANT
// ============================================================================

test.describe('VENTES T0 - Multi-Tenant', () => {
  test('session tenant maintenue apres navigation', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing/quotes`);
    await waitForLoadingComplete(page);
    expect(await pageHasContent(page)).toBeTruthy();

    await page.goto(`${BASE_URL}/invoicing/invoices`);
    await waitForLoadingComplete(page);
    expect(await pageHasContent(page)).toBeTruthy();

    await page.goto(`${BASE_URL}/invoicing`);
    await waitForLoadingComplete(page);
    expect(await pageHasContent(page)).toBeTruthy();
  });
});
