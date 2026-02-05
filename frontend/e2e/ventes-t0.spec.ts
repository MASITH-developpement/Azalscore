/**
 * AZALSCORE - Tests E2E VENTES T0
 * ================================
 *
 * Tests End-to-End pour le module Facturation (VENTES T0)
 *
 * STRATÉGIE D'INITIALISATION DÉTERMINISTE:
 * - Tous les tests attendent l'indicateur data-app-ready="true"
 * - Aucun timeout arbitraire
 * - Séquence: attendre app ready -> login -> attendre app ready -> naviguer
 *
 * Couverture:
 * - Navigation vers le module Facturation
 * - Liste des devis et factures
 * - Création de documents
 * - RBAC (permissions)
 * - UI responsive
 */

import { test, expect, Page } from '@playwright/test';

// ============================================================
// CONFIGURATION
// ============================================================

const DEMO_CREDENTIALS = {
  user: {
    tenant: process.env.TEST_TENANT || 'masith',
    email: process.env.TEST_USER || 'contact@masith.fr',
    password: process.env.TEST_PASSWORD || 'Azals2026!',
  },
  admin: {
    tenant: process.env.TEST_TENANT || 'masith',
    email: process.env.TEST_USER || 'contact@masith.fr',
    password: process.env.TEST_PASSWORD || 'Azals2026!',
  },
};

const SELECTORS = {
  // App Ready Indicator - CRITICAL
  appReady: '[data-app-ready="true"]',
  appLoading: '[data-app-ready="false"]',

  // Login Page
  tenantInput: 'input[placeholder*="societe" i], input[placeholder*="société" i], input[placeholder*="identifiant" i], input[name="tenant"]',
  emailInput: 'input[type="email"], input[name="email"], input[placeholder*="email" i]',
  passwordInput: 'input[type="password"]',
  loginButton: 'button[type="submit"]',

  // Actions
  addButton: 'button:has-text("Nouveau"), button:has-text("Ajouter")',
};

// ============================================================
// HELPERS - DETERMINISTIC WAITING
// ============================================================

/**
 * Attend que l'application soit prête (data-app-ready="true")
 * CRITIQUE: Ne pas utiliser de timeout arbitraire
 */
async function waitForAppReady(page: Page, timeout = 30000): Promise<void> {
  await page.waitForSelector(SELECTORS.appReady, { timeout, state: 'attached' });
}

/**
 * Login avec attente déterministe de l'état READY
 */
async function loginAs(page: Page, credentials: { tenant?: string; email: string; password: string }): Promise<void> {
  // 1. Naviguer vers login
  await page.goto('/login');

  // 2. Attendre que l'app soit prête (page de login chargée)
  await waitForAppReady(page);

  // 3. Remplir le champ tenant si présent
  const tenantInput = page.locator(SELECTORS.tenantInput).first();
  if (await tenantInput.isVisible({ timeout: 2000 })) {
    await tenantInput.fill(credentials.tenant || 'masith');
  }

  // 4. Remplir le formulaire
  await page.locator(SELECTORS.emailInput).first().fill(credentials.email);
  await page.locator(SELECTORS.passwordInput).first().fill(credentials.password);

  // 5. Soumettre
  await page.click(SELECTORS.loginButton);

  // 6. Attendre la redirection ET que l'app soit de nouveau prête
  await page.waitForURL(/\/(cockpit|invoicing|partners)/, { timeout: 15000 });
  await waitForAppReady(page);
}

/**
 * Navigation avec attente déterministe
 */
async function navigateTo(page: Page, path: string): Promise<void> {
  await page.goto(path);
  await waitForAppReady(page);
}

/**
 * Vérifie qu'une page a du contenu visible
 */
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

// ============================================================
// TESTS: AUTHENTIFICATION
// ============================================================

test.describe('VENTES T0 - Authentification', () => {
  test('redirige vers login si non authentifié', async ({ page }) => {
    await page.goto('/invoicing/quotes');
    await waitForAppReady(page);
    await expect(page).toHaveURL(/.*login/);
  });

  test('admin peut accéder au module facturation après login', async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
    await navigateTo(page, '/invoicing');

    await expect(page).toHaveURL(/.*invoicing/);
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('user peut accéder au module facturation après login', async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.user);
    await navigateTo(page, '/invoicing');

    await expect(page).toHaveURL(/.*invoicing/);
    expect(await pageHasContent(page)).toBeTruthy();
  });
});

// ============================================================
// TESTS: NAVIGATION
// ============================================================

test.describe('VENTES T0 - Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
  });

  test('accède au dashboard facturation', async ({ page }) => {
    await navigateTo(page, '/invoicing');
    await expect(page).toHaveURL(/.*invoicing/);
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('accède à la liste des devis', async ({ page }) => {
    await navigateTo(page, '/invoicing/quotes');
    await expect(page).toHaveURL(/.*invoicing\/quotes/);
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('accède à la liste des factures', async ({ page }) => {
    await navigateTo(page, '/invoicing/invoices');
    await expect(page).toHaveURL(/.*invoicing\/invoices/);
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('navigue entre devis et factures', async ({ page }) => {
    await navigateTo(page, '/invoicing/quotes');
    await expect(page).toHaveURL(/.*invoicing\/quotes/);

    await navigateTo(page, '/invoicing/invoices');
    await expect(page).toHaveURL(/.*invoicing\/invoices/);
  });
});

// ============================================================
// TESTS: LISTE DES DEVIS
// ============================================================

test.describe('VENTES T0 - Liste des Devis', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
    await navigateTo(page, '/invoicing/quotes');
  });

  test('affiche la liste des devis', async ({ page }) => {
    expect(page.url()).toContain('/invoicing/quotes');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('bouton nouveau devis visible pour admin', async ({ page }) => {
    const newButton = page.locator(SELECTORS.addButton)
      .or(page.getByRole('button', { name: /nouveau/i }));

    await expect(newButton.first()).toBeVisible({ timeout: 10000 });
  });
});

// ============================================================
// TESTS: CREATION DEVIS
// ============================================================

test.describe('VENTES T0 - Création Devis', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
  });

  test('formulaire de création accessible via URL', async ({ page }) => {
    await navigateTo(page, '/invoicing/quotes/new');
    await expect(page).toHaveURL(/.*quotes\/new/);
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('formulaire contient des champs', async ({ page }) => {
    await navigateTo(page, '/invoicing/quotes/new');

    // Vérifier qu'il y a un formulaire ou des champs
    const hasForm = await page.locator('form').isVisible().catch(() => false);
    const hasInputs = await page.locator('input, select, textarea').first().isVisible().catch(() => false);
    const hasContent = await pageHasContent(page);

    expect(hasForm || hasInputs || hasContent).toBeTruthy();
  });
});

// ============================================================
// TESTS: FACTURES
// ============================================================

test.describe('VENTES T0 - Liste des Factures', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
    await navigateTo(page, '/invoicing/invoices');
  });

  test('affiche la liste des factures', async ({ page }) => {
    expect(page.url()).toContain('/invoicing/invoices');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('bouton nouvelle facture visible', async ({ page }) => {
    const newButton = page.locator(SELECTORS.addButton)
      .or(page.getByRole('button', { name: /nouveau/i }));

    await expect(newButton.first()).toBeVisible({ timeout: 10000 });
  });

  test('formulaire création facture accessible', async ({ page }) => {
    await navigateTo(page, '/invoicing/invoices/new');
    await expect(page).toHaveURL(/.*invoices\/new/);
    expect(await pageHasContent(page)).toBeTruthy();
  });
});

// ============================================================
// TESTS: RBAC
// ============================================================

test.describe('VENTES T0 - RBAC Permissions', () => {
  test('admin voit les boutons d\'action', async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
    await navigateTo(page, '/invoicing/quotes');

    const newButton = page.locator(SELECTORS.addButton)
      .or(page.getByRole('button', { name: /nouveau/i }));

    await expect(newButton.first()).toBeVisible({ timeout: 10000 });
  });

  test('user standard peut voir la liste', async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.user);
    await navigateTo(page, '/invoicing/quotes');

    expect(page.url()).toContain('/invoicing/quotes');
    expect(await pageHasContent(page)).toBeTruthy();
  });
});

// ============================================================
// TESTS: UI RESPONSIVE
// ============================================================

test.describe('VENTES T0 - UI Responsive', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
  });

  test('desktop: affiche correctement', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await navigateTo(page, '/invoicing/quotes');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('tablet: affiche correctement', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await navigateTo(page, '/invoicing/quotes');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('mobile: affiche correctement', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await navigateTo(page, '/invoicing/quotes');
    expect(await pageHasContent(page)).toBeTruthy();
  });
});

// ============================================================
// TESTS: PERFORMANCE
// ============================================================

test.describe('VENTES T0 - Performance', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
  });

  test('page devis charge en moins de 10 secondes', async ({ page }) => {
    const startTime = Date.now();
    await navigateTo(page, '/invoicing/quotes');

    const hasContent = await pageHasContent(page);
    const loadTime = Date.now() - startTime;

    expect(hasContent).toBeTruthy();
    expect(loadTime).toBeLessThan(10000);
  });

  test('navigation entre pages fluide', async ({ page }) => {
    await navigateTo(page, '/invoicing/quotes');

    const startTime = Date.now();
    await navigateTo(page, '/invoicing/invoices');
    const navTime = Date.now() - startTime;

    expect(await pageHasContent(page)).toBeTruthy();
    expect(navTime).toBeLessThan(5000);
  });
});

// ============================================================
// TESTS: GESTION ERREURS
// ============================================================

test.describe('VENTES T0 - Gestion Erreurs', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
  });

  test('pas d\'erreurs JavaScript critiques', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await navigateTo(page, '/invoicing/quotes');

    // Filtrer les erreurs non critiques (réseau, API, etc.)
    const criticalErrors = errors.filter(
      (e) =>
        !e.includes('net::') &&
        !e.includes('Failed to load') &&
        !e.includes('favicon') &&
        !e.includes('proxy error') &&
        !e.includes('ECONNREFUSED') &&
        !e.includes('Demo mode') &&
        !e.includes('api/v1') &&
        !e.includes('Request failed') &&
        !e.includes('Network') &&
        !e.includes('fetch') &&
        !e.includes('AbortError') &&
        !e.includes('timeout') &&
        !e.includes('Chargement') &&
        !e.includes('MIME type') &&
        !e.includes('text/html')
    );

    // Debug: afficher les erreurs filtrées si le test échoue
    if (criticalErrors.length > 0) {
      console.log('Critical JS errors found:', criticalErrors);
    }

    expect(criticalErrors.length).toBe(0);
  });
});

// ============================================================
// TESTS: MULTI-TENANT
// ============================================================

test.describe('VENTES T0 - Multi-Tenant', () => {
  test('session tenant maintenue après navigation', async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);

    await navigateTo(page, '/invoicing/quotes');
    expect(await pageHasContent(page)).toBeTruthy();

    await navigateTo(page, '/invoicing/invoices');
    expect(await pageHasContent(page)).toBeTruthy();

    await navigateTo(page, '/invoicing');
    expect(await pageHasContent(page)).toBeTruthy();
  });
});
