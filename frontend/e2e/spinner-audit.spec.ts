/**
 * AZALSCORE - Audit Spinners (Optimise)
 *
 * Verifie qu'aucun ecran ne reste bloque en chargement.
 * Utilise storageState pour auth partagee.
 */

import { test, expect } from '@playwright/test';
import { assertNoActiveSpinners, waitForLoadingComplete, TIMEOUTS } from './fixtures/helpers';

const BASE_URL = process.env.BASE_URL || 'https://azalscore.com';

// Modules a tester
const MODULES = [
  { route: '/cockpit', label: 'Cockpit' },
  { route: '/invoicing', label: 'Facturation' },
  { route: '/purchases', label: 'Achats' },
  { route: '/treasury', label: 'Tresorerie' },
  { route: '/accounting', label: 'Comptabilite' },
  { route: '/partners', label: 'Partenaires' },
  { route: '/interventions', label: 'Interventions' },
  { route: '/inventory', label: 'Stock' },
  { route: '/hr', label: 'RH' },
  { route: '/admin', label: 'Admin' },
  { route: '/crm', label: 'CRM' },
];

// ============================================================
// Routes publiques (sans auth)
// ============================================================

test.describe('Audit spinners - Routes publiques', () => {
  test('Page login - pas de spinner infini', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded' });
    await assertNoActiveSpinners(page, 'Login');
  });
});

// ============================================================
// Routes authentifiees (avec storageState)
// ============================================================

test.describe('Audit spinners - Routes authentifiees', () => {
  test.describe.configure({ mode: 'parallel' });

  // Test chaque module
  for (const mod of MODULES) {
    test(`${mod.label} (${mod.route}) - pas de spinner infini`, async ({ page }) => {
      await page.goto(`${BASE_URL}${mod.route}`);
      await assertNoActiveSpinners(page, mod.label);
    });
  }
});

// ============================================================
// Tests de navigation rapide
// ============================================================

test.describe('Audit spinners - Navigation rapide', () => {
  test('Navigation entre modules sans spinner persistant', async ({ page }) => {
    // Naviguer rapidement entre plusieurs modules
    const quickRoutes = ['/cockpit', '/invoicing', '/purchases', '/partners'];

    for (const route of quickRoutes) {
      await page.goto(`${BASE_URL}${route}`);
      await waitForLoadingComplete(page);

      // Verifier pas de spinner apres chargement
      const hasSpinner = await page.locator('.azals-state--loading, .animate-spin').first().isVisible().catch(() => false);
      expect(hasSpinner, `Spinner persistant sur ${route}`).toBe(false);
    }
  });

  test('Retour arriere sans spinner infini', async ({ page }) => {
    await page.goto(`${BASE_URL}/cockpit`);
    await waitForLoadingComplete(page);

    await page.goto(`${BASE_URL}/invoicing`);
    await waitForLoadingComplete(page);

    await page.goBack();
    await waitForLoadingComplete(page);

    await assertNoActiveSpinners(page, 'Retour arriere');
  });
});
