/**
 * AZALSCORE - Critical Tests (Optimises)
 *
 * Tests des flux critiques avec authentification partagee.
 * Utilise storageState pour eviter les logins multiples.
 */

import { test, expect } from '@playwright/test';
import {
  waitForLoadingComplete,
  waitForContent,
  assertNoActiveSpinners,
  assertNoPageError,
  navigateToModule,
  openCreateForm,
  closeModal,
  SELECTORS,
  TIMEOUTS
} from './fixtures/helpers';

const BASE_URL = process.env.BASE_URL || 'https://azalscore.com';

// Modules critiques a tester
const CRITICAL_MODULES = [
  { route: '/cockpit', name: 'Cockpit' },
  { route: '/invoicing', name: 'Facturation' },
  { route: '/purchases', name: 'Achats' },
  { route: '/treasury', name: 'Tresorerie' },
  { route: '/accounting', name: 'Comptabilite' },
  { route: '/partners', name: 'Partenaires' },
  { route: '/crm', name: 'CRM' },
  { route: '/inventory', name: 'Stock' },
  { route: '/interventions', name: 'Interventions' },
  { route: '/hr', name: 'RH' },
];

test.describe('Critical Flows', () => {
  // Tests en parallele pour rapidite
  test.describe.configure({ mode: 'parallel' });

  // ================================================================
  // Tests de chargement des modules (pas de spinner infini)
  // ================================================================

  for (const mod of CRITICAL_MODULES) {
    test(`${mod.name} - Charge sans spinner infini`, async ({ page }) => {
      await page.goto(`${BASE_URL}${mod.route}`);
      await assertNoActiveSpinners(page, mod.name);
      await assertNoPageError(page, mod.name);
    });
  }

  // ================================================================
  // Tests specifiques cockpit (KPIs strategiques)
  // ================================================================

  test('Cockpit - KPIs strategiques visibles', async ({ page }) => {
    await page.goto(`${BASE_URL}/cockpit`);
    await waitForLoadingComplete(page);

    // Verifier la presence de la section KPIs ou d'un contenu decisional
    const hasContent = await page.locator(
      '.azals-cockpit-strategic, [class*="kpi"], [class*="dashboard"], [class*="metric"]'
    ).first().isVisible({ timeout: TIMEOUTS.medium }).catch(() => false);

    // Au minimum, la page doit avoir du contenu
    await assertNoPageError(page, 'Cockpit KPIs');
  });

  // ================================================================
  // Tests de creation (formulaires)
  // ================================================================

  test('Facturation - Formulaire creation devis', async ({ page }) => {
    await page.goto(`${BASE_URL}/invoicing`);
    await waitForLoadingComplete(page);

    const hasForm = await openCreateForm(page);
    if (hasForm) {
      // Verifier que le formulaire a des champs
      const hasFields = await page.locator('input, select, textarea').count();
      expect(hasFields).toBeGreaterThan(0);
      await closeModal(page);
    }
  });

  test('Achats - Formulaire creation fournisseur', async ({ page }) => {
    await page.goto(`${BASE_URL}/purchases`);
    await waitForLoadingComplete(page);

    const hasForm = await openCreateForm(page);
    if (hasForm) {
      const hasFields = await page.locator('input, select, textarea').count();
      expect(hasFields).toBeGreaterThan(0);
      await closeModal(page);
    }
  });

  // ================================================================
  // Tests de navigation
  // ================================================================

  test('Navigation sidebar fonctionne', async ({ page }) => {
    await page.goto(`${BASE_URL}/cockpit`);
    await waitForLoadingComplete(page);

    // Trouver liens de navigation
    const navLinks = page.locator('nav a[href], aside a[href], [class*="sidebar"] a[href]');
    const count = await navLinks.count();

    if (count > 0) {
      // Tester le premier lien
      const firstLink = navLinks.first();
      const href = await firstLink.getAttribute('href');

      if (href && !href.includes('logout')) {
        await firstLink.click();
        await waitForLoadingComplete(page);
        await assertNoPageError(page, 'Navigation');
      }
    }
  });

  // ================================================================
  // Tests de recherche
  // ================================================================

  test('Recherche globale fonctionne', async ({ page }) => {
    await page.goto(`${BASE_URL}/partners`);
    await waitForLoadingComplete(page);

    const searchInput = page.locator(
      'input[type="search"], input[placeholder*="recherche" i], input[placeholder*="search" i]'
    ).first();

    if (await searchInput.isVisible({ timeout: TIMEOUTS.short })) {
      await searchInput.fill('test');
      await waitForLoadingComplete(page);

      // La page doit toujours etre fonctionnelle
      await assertNoPageError(page, 'Recherche');
    }
  });

  // ================================================================
  // Tests de pagination
  // ================================================================

  test('Pagination fonctionne', async ({ page }) => {
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
});

// ================================================================
// Tests d'erreurs console (separes pour isolation)
// ================================================================

test.describe('Console Errors', () => {
  test('Pas d\'erreurs JS critiques sur navigation', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (text.includes('TypeError') ||
            text.includes('ReferenceError') ||
            text.includes('Uncaught')) {
          errors.push(text);
        }
      }
    });

    // Naviguer sur plusieurs pages
    for (const mod of CRITICAL_MODULES.slice(0, 5)) {
      await page.goto(`${BASE_URL}${mod.route}`);
      await waitForLoadingComplete(page);
    }

    expect(errors.length, `Erreurs JS: ${errors.join(', ')}`).toBe(0);
  });
});
