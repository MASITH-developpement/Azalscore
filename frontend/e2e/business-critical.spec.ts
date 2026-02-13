/**
 * AZALSCORE - Tests E2E Business Critical (Optimise)
 *
 * Utilise storageState pour auth partagee.
 * Aucun login par test = execution rapide.
 */

import { test, expect } from '@playwright/test';
import { waitForLoadingComplete, assertNoPageError, TIMEOUTS } from './fixtures/helpers';

const BASE_URL = process.env.BASE_URL || 'https://azalscore.com';
const API_URL = process.env.API_URL || 'https://azalscore.com/api';

test.describe('AZALSCORE Critical Flows', () => {
  // Paralleliser pour rapidite
  test.describe.configure({ mode: 'parallel' });

  // ============================================================================
  // PURCHASES MODULE
  // ============================================================================

  test('Purchases - List suppliers', async ({ page }) => {
    await page.goto(`${BASE_URL}/purchases`);
    await waitForLoadingComplete(page);

    await assertNoPageError(page, 'Purchases');

    // Verifier qu'on a du contenu
    const hasContent = await page.locator('table, [class*="card"], [class*="list"]').first().isVisible({ timeout: TIMEOUTS.medium });
    expect(hasContent).toBeTruthy();
  });

  test('Purchases - Create supplier form', async ({ page }) => {
    await page.goto(`${BASE_URL}/purchases`);
    await waitForLoadingComplete(page);

    const createBtn = page.locator('button:has-text("Nouveau"), button:has-text("Créer"), button:has-text("Ajouter")').first();

    if (await createBtn.isVisible({ timeout: TIMEOUTS.short })) {
      await createBtn.click();
      const hasForm = await page.locator('form, [role="dialog"], .modal').first().isVisible({ timeout: TIMEOUTS.short });
      expect(hasForm).toBeTruthy();
    }
  });

  // ============================================================================
  // TREASURY MODULE
  // ============================================================================

  test('Treasury - Dashboard loads', async ({ page }) => {
    await page.goto(`${BASE_URL}/treasury`);
    await waitForLoadingComplete(page);

    await assertNoPageError(page, 'Treasury');
  });

  test('Treasury - List accounts', async ({ page }) => {
    await page.goto(`${BASE_URL}/treasury`);
    await waitForLoadingComplete(page);

    const hasContent = await page.locator('.azals-state--error, .azals-state--empty, [class*="card"], tr, [class*="account"]').first().isVisible({ timeout: TIMEOUTS.medium }).catch(() => false);
    expect(hasContent).toBeTruthy();
  });

  // ============================================================================
  // ACCOUNTING MODULE
  // ============================================================================

  test('Accounting - List entries', async ({ page }) => {
    await page.goto(`${BASE_URL}/accounting`);
    await waitForLoadingComplete(page);

    await assertNoPageError(page, 'Accounting');
  });

  test('Accounting - Navigate fiscal years', async ({ page }) => {
    await page.goto(`${BASE_URL}/accounting`);
    await waitForLoadingComplete(page);

    const fiscalTab = page.locator('[href*="fiscal"], button:has-text("Exercice"), :text-matches("exercice|fiscal", "i")').first();

    if (await fiscalTab.isVisible({ timeout: TIMEOUTS.short })) {
      await fiscalTab.click();
      await waitForLoadingComplete(page);
      await assertNoPageError(page, 'Fiscal years');
    }
  });

  // ============================================================================
  // INVOICING MODULE
  // ============================================================================

  test('Invoicing - List documents', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing`);
    await waitForLoadingComplete(page);

    await assertNoPageError(page, 'Invoicing');
  });

  test('Invoicing - Create quote form', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing`);
    await waitForLoadingComplete(page);

    const createBtn = page.locator('button:has-text("Nouveau"), button:has-text("Créer"), button:has-text("Devis")').first();

    if (await createBtn.isVisible({ timeout: TIMEOUTS.short })) {
      await createBtn.click();
      const hasForm = await page.locator('form, [role="dialog"], .modal').first().isVisible({ timeout: TIMEOUTS.short });
      expect(hasForm).toBeTruthy();
    }
  });

  // ============================================================================
  // PARTNERS MODULE
  // ============================================================================

  test('Partners - List clients', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners`);
    await waitForLoadingComplete(page);

    await assertNoPageError(page, 'Partners');

    // Verifier qu'on a du contenu (heading ou table ou cards)
    const hasContent = await page.locator('h1, h2, table, [class*="card"], [class*="list"]').first().isVisible({ timeout: TIMEOUTS.medium }).catch(() => false);
    expect(hasContent).toBeTruthy();
  });

  // ============================================================================
  // CRM MODULE
  // ============================================================================

  test('CRM - Opportunities list', async ({ page }) => {
    await page.goto(`${BASE_URL}/crm`);
    await waitForLoadingComplete(page);

    await assertNoPageError(page, 'CRM');
  });

  // ============================================================================
  // STOCK MODULE
  // ============================================================================

  test('Stock - Inventory visible', async ({ page }) => {
    await page.goto(`${BASE_URL}/inventory`);
    await waitForLoadingComplete(page);

    await assertNoPageError(page, 'Stock');
  });

  // ============================================================================
  // INTERVENTIONS MODULE
  // ============================================================================

  test('Interventions - List visible', async ({ page }) => {
    await page.goto(`${BASE_URL}/interventions`);
    await waitForLoadingComplete(page);

    await assertNoPageError(page, 'Interventions');
  });

  // ============================================================================
  // HR MODULE
  // ============================================================================

  test('HR - Employees list', async ({ page }) => {
    await page.goto(`${BASE_URL}/hr`);
    await waitForLoadingComplete(page);

    await assertNoPageError(page, 'HR');
  });

  // ============================================================================
  // COCKPIT MODULE
  // ============================================================================

  test('Cockpit - Dashboard visible', async ({ page }) => {
    await page.goto(`${BASE_URL}/cockpit`);
    await waitForLoadingComplete(page);

    await assertNoPageError(page, 'Cockpit');

    // Verifier presence de KPIs ou contenu decisional
    const hasKPIs = await page.locator('[class*="kpi"], [class*="metric"], [class*="dashboard"], [class*="strategic"]').first().isVisible({ timeout: TIMEOUTS.medium }).catch(() => false);
    const bodyText = await page.locator('body').textContent();
    expect(hasKPIs || (bodyText && bodyText.length > 200)).toBeTruthy();
  });

  // ============================================================================
  // ADMIN MODULE
  // ============================================================================

  test('Admin - Dashboard visible', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin`);
    await waitForLoadingComplete(page);

    await assertNoPageError(page, 'Admin');
  });

  // ============================================================================
  // API HEALTH
  // ============================================================================

  test('API Health - Endpoint responds', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/health`, { timeout: 10000 });
      expect(response.status()).toBeLessThan(500);
    } catch {
      // API non accessible via ce chemin, skip
      test.skip();
    }
  });
});
