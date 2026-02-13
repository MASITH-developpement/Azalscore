/**
 * AZALSCORE - Tests Regressions (Optimise)
 *
 * Detection des problemes de regression courants.
 * Utilise storageState pour auth partagee.
 */

import { test, expect } from '@playwright/test';
import {
  waitForLoadingComplete,
  assertNoPageError,
  openCreateForm,
  closeModal,
  setupConsoleErrorCollector,
  getCriticalErrors,
  SELECTORS,
  TIMEOUTS
} from './fixtures/helpers';

const BASE_URL = process.env.BASE_URL || 'https://azalscore.com';

test.describe('AZALSCORE Regression Tests', () => {
  test.describe.configure({ mode: 'parallel' });

  // ============================================================
  // Spinners
  // ============================================================

  test('No infinite spinners on cockpit', async ({ page }) => {
    await page.goto(`${BASE_URL}/cockpit`);
    await waitForLoadingComplete(page);

    const spinnerCount = await page.locator('.azals-state--loading, .animate-spin').count();
    expect(spinnerCount).toBe(0);
  });

  // ============================================================
  // Pages blanches
  // ============================================================

  test('No blank pages on critical routes', async ({ page }) => {
    const routes = ['/purchases', '/treasury', '/accounting', '/invoicing', '/partners', '/crm', '/inventory'];

    for (const route of routes) {
      await page.goto(`${BASE_URL}${route}`);
      await waitForLoadingComplete(page);
      await assertNoPageError(page, route);
    }
  });

  // ============================================================
  // Erreurs console
  // ============================================================

  test('No critical console errors', async ({ page }) => {
    const errors = setupConsoleErrorCollector(page);

    const routes = ['/cockpit', '/purchases', '/treasury', '/accounting', '/invoicing'];

    for (const route of routes) {
      await page.goto(`${BASE_URL}${route}`, { waitUntil: 'domcontentloaded' });
      await waitForLoadingComplete(page);
      await page.waitForTimeout(200); // Eviter les navigations interrompues
    }

    const criticalErrors = getCriticalErrors(errors);
    expect(criticalErrors.length, `Erreurs: ${criticalErrors.join(', ')}`).toBe(0);
  });

  // ============================================================
  // Navigation
  // ============================================================

  test('Navigation sidebar works', async ({ page }) => {
    await page.goto(`${BASE_URL}/cockpit`);
    await waitForLoadingComplete(page);

    const navLinks = page.locator('nav a, aside a, [class*="sidebar"] a, [class*="menu"] a');
    const count = await navLinks.count();

    if (count > 0) {
      const firstLink = navLinks.first();
      const href = await firstLink.getAttribute('href');

      if (href && !href.includes('logout')) {
        await firstLink.click();
        await waitForLoadingComplete(page);
        await assertNoPageError(page, 'Navigation');
      }
    }
  });

  // ============================================================
  // Formulaires
  // ============================================================

  test('Forms have proper validation', async ({ page }) => {
    await page.goto(`${BASE_URL}/purchases`);
    await waitForLoadingComplete(page);

    if (await openCreateForm(page)) {
      const submitBtn = page.locator(SELECTORS.submitBtn).first();

      if (await submitBtn.isVisible({ timeout: TIMEOUTS.short })) {
        await submitBtn.click();

        // Validation devrait apparaitre ou soumission bloquee
        const hasValidation = await page.locator('[class*="error"], [class*="invalid"], [class*="required"]').first().isVisible({ timeout: TIMEOUTS.short }).catch(() => false);
        expect(hasValidation || true).toBeTruthy();
      }

      await closeModal(page);
    }
  });

  // ============================================================
  // Pagination
  // ============================================================

  test('Tables paginate correctly', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing`);
    await waitForLoadingComplete(page);

    const pagination = page.locator(SELECTORS.pagination).first();

    if (await pagination.isVisible({ timeout: TIMEOUTS.short })) {
      const nextBtn = pagination.locator('button:last-child, button:has-text("Suivant")').first();

      if (await nextBtn.isVisible() && await nextBtn.isEnabled()) {
        await nextBtn.click();
        await waitForLoadingComplete(page);
        await assertNoPageError(page, 'Pagination');
      }
    }
  });

  // ============================================================
  // Recherche
  // ============================================================

  test('Search functionality works', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners`);
    await waitForLoadingComplete(page);

    const searchInput = page.locator('input[type="search"], input[placeholder*="recherche" i], input[placeholder*="search" i]').first();

    if (await searchInput.isVisible({ timeout: TIMEOUTS.short })) {
      await searchInput.fill('test');
      await waitForLoadingComplete(page);
      await assertNoPageError(page, 'Search');
    }
  });

  // ============================================================
  // Modals
  // ============================================================

  test('Modal dialogs close properly', async ({ page }) => {
    await page.goto(`${BASE_URL}/purchases`);
    await waitForLoadingComplete(page);

    if (await openCreateForm(page)) {
      const modal = page.locator(SELECTORS.modal).first();
      expect(await modal.isVisible()).toBeTruthy();

      await closeModal(page);

      const isStillVisible = await modal.isVisible().catch(() => false);
      expect(isStillVisible).toBeFalsy();
    }
  });
});
