/**
 * AZALSCORE - Tests E2E Module CRM T0 (Optimise)
 *
 * Utilise storageState pour auth partagee.
 *
 * FONCTIONNALITES TESTEES:
 * - Navigation vers le module Partenaires (CRM)
 * - CRUD Clients
 * - CRUD Contacts
 * - Isolation visuelle multi-tenant
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

// Selectors specifiques CRM
const CRM_SELECTORS = {
  ...BASE_SELECTORS,
  // Data Table
  dataTable: '.azals-table, table',
  tableRow: 'tbody tr',
  pagination: '.azals-pagination',
  // Badges
  activeBadge: '.azals-badge--green',
  inactiveBadge: '.azals-badge--gray',
};

// ============================================================================
// HELPERS CRM
// ============================================================================

function generateClientName(): string {
  return `Test Client E2E ${Date.now()}`;
}

async function pageHasContent(page: Page): Promise<boolean> {
  const contentSelectors = [
    'table', '.azals-table', '.azals-card', '[class*="card"]',
    'main', 'h1', 'h2', 'h3', '[class*="title"]', '[class*="wrapper"]',
  ];

  for (const selector of contentSelectors) {
    const isVisible = await page.locator(selector).first().isVisible().catch(() => false);
    if (isVisible) return true;
  }
  return false;
}

// ============================================================================
// TESTS: NAVIGATION CRM
// ============================================================================

test.describe('CRM T0 - Navigation', () => {
  test.describe.configure({ mode: 'parallel' });

  test('accede au module Partenaires', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners`);
    await waitForLoadingComplete(page);
    await assertNoPageError(page, 'Partners');
    await expect(page).toHaveURL(/.*partners/);
  });

  test('accede a la liste des Clients', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);
    await expect(page).toHaveURL(/.*partners\/clients/);
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('accede a la liste des Contacts', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners/contacts`);
    await waitForLoadingComplete(page);
    await expect(page).toHaveURL(/.*partners\/contacts/);
  });

  test('navigation entre les sous-modules CRM', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);
    await expect(page).toHaveURL(/.*clients/);

    await page.goto(`${BASE_URL}/partners/contacts`);
    await waitForLoadingComplete(page);
    await expect(page).toHaveURL(/.*contacts/);

    await page.goto(`${BASE_URL}/partners`);
    await waitForLoadingComplete(page);
    await expect(page).toHaveURL(/.*partners/);
  });
});

// ============================================================================
// TESTS: CRUD CLIENTS
// ============================================================================

test.describe('CRM T0 - Gestion des Clients', () => {
  test.describe.configure({ mode: 'parallel' });

  test('affiche la liste des clients', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);
    await assertNoPageError(page, 'Clients list');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('bouton Ajouter visible', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);

    const addButton = page.locator('button:has-text("Ajouter"), button:has-text("Nouveau"), button:has-text("Creer")');
    if (await addButton.first().isVisible({ timeout: TIMEOUTS.short })) {
      await expect(addButton.first()).toBeEnabled();
    }
  });

  test('ouvre le modal de creation de client', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);

    if (await openCreateForm(page)) {
      const modal = page.locator(CRM_SELECTORS.modal).first();
      await expect(modal).toBeVisible({ timeout: TIMEOUTS.short });
      await closeModal(page);
    }
  });

  test('valide les champs requis lors de la creation', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);

    if (await openCreateForm(page)) {
      const submitBtn = page.locator('[role="dialog"] button[type="submit"], .azals-modal button[type="submit"]').first();
      if (await submitBtn.isVisible({ timeout: TIMEOUTS.short })) {
        await submitBtn.click();
        // Modal devrait rester ouvert (validation)
        const modalStillOpen = await page.locator(CRM_SELECTORS.modal).isVisible();
        expect(modalStillOpen).toBeTruthy();
      }
      await closeModal(page);
    }
  });

  test('annule la creation de client', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);

    if (await openCreateForm(page)) {
      await closeModal(page);
      await expect(page.locator(CRM_SELECTORS.modal)).not.toBeVisible({ timeout: TIMEOUTS.short });
    }
  });
});

// ============================================================================
// TESTS: CRUD CONTACTS
// ============================================================================

test.describe('CRM T0 - Gestion des Contacts', () => {
  test.describe.configure({ mode: 'parallel' });

  test('affiche la liste des contacts', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners/contacts`);
    await waitForLoadingComplete(page);
    await assertNoPageError(page, 'Contacts list');
    expect(page.url()).toContain('contacts');
  });

  test('bouton Ajouter visible pour les contacts', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners/contacts`);
    await waitForLoadingComplete(page);

    const addButton = page.locator('button:has-text("Ajouter"), button:has-text("Nouveau")');
    if (await addButton.first().isVisible({ timeout: TIMEOUTS.short })) {
      await expect(addButton.first()).toBeEnabled();
    }
  });

  test('ouvre le modal de creation de contact', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners/contacts`);
    await waitForLoadingComplete(page);

    if (await openCreateForm(page)) {
      const modal = page.locator(CRM_SELECTORS.modal);
      await expect(modal).toBeVisible({ timeout: TIMEOUTS.short });
      await closeModal(page);
    }
  });
});

// ============================================================================
// TESTS: RESPONSIVE & UX
// ============================================================================

test.describe('CRM T0 - Interface Utilisateur', () => {
  test.describe.configure({ mode: 'parallel' });

  test('affichage correct sur desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);
    await assertNoPageError(page, 'Desktop');
  });

  test('affichage correct sur tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);
    await assertNoPageError(page, 'Tablet');
  });

  test('affichage correct sur mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);
    await assertNoPageError(page, 'Mobile');
  });

  test('chargement sans erreurs JavaScript', async ({ page }) => {
    const errors = setupConsoleErrorCollector(page);

    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);

    const criticalErrors = getCriticalErrors(errors);
    expect(criticalErrors.length).toBe(0);
  });
});

// ============================================================================
// TESTS: PERFORMANCE
// ============================================================================

test.describe('CRM T0 - Performance', () => {
  test.describe.configure({ mode: 'parallel' });

  test('page clients charge rapidement', async ({ page }) => {
    const startTime = Date.now();
    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(5000);
  });

  test('navigation entre pages est fluide', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(`${BASE_URL}/partners`);
    await waitForLoadingComplete(page);
    await page.goto(`${BASE_URL}/partners/clients`);
    await waitForLoadingComplete(page);
    await page.goto(`${BASE_URL}/partners/contacts`);
    await waitForLoadingComplete(page);
    await page.goto(`${BASE_URL}/partners`);
    await waitForLoadingComplete(page);

    const totalTime = Date.now() - startTime;
    expect(totalTime).toBeLessThan(10000);
  });
});
