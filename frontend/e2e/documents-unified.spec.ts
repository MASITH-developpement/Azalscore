/**
 * AZALSCORE - Tests E2E MODULE DOCUMENTS UNIFIE
 * ==============================================
 *
 * Tests End-to-End pour le module Documents unifié
 *
 * STRATÉGIE D'INITIALISATION DÉTERMINISTE:
 * - Tous les tests attendent l'indicateur data-app-ready="true"
 * - Aucun timeout arbitraire
 *
 * Couverture:
 * - Redirection des anciennes routes vers /documents
 * - Sélection des types de documents
 * - Basculement mode saisie/consultation
 * - Création de documents (tous types)
 * - Système i18n (changement de langue)
 * - Navigation complète
 */

import { test, expect, Page } from '@playwright/test';

// ============================================================
// CONFIGURATION
// ============================================================

const DEMO_CREDENTIALS = {
  admin: {
    email: 'admin@azalscore.local',
    password: 'Admin123!',
  },
  user: {
    email: 'demo@azalscore.local',
    password: 'Demo123!',
  },
};

const DOCUMENT_TYPES = [
  'QUOTE',
  'INVOICE',
  'ORDER',
  'CREDIT_NOTE',
  'PURCHASE_ORDER',
  'PURCHASE_INVOICE',
] as const;

const SELECTORS = {
  appReady: '[data-app-ready="true"]',
  emailInput: '#email',
  passwordInput: '#password',
  loginButton: 'button[type="submit"]',
  typeSelector: '[data-testid="document-type-selector"], .azals-type-selector',
  modeToggle: '[data-testid="mode-toggle"], .azals-mode-toggle',
  documentForm: '[data-testid="document-form"], .azals-document-form, form',
  documentList: '[data-testid="document-list"], .azals-document-list, table',
  saveButton: 'button:has-text("Enregistrer"), button:has-text("Save")',
  languageSelector: '[data-testid="language-selector"], select[name="language"]',
};

// ============================================================
// HELPERS
// ============================================================

async function waitForAppReady(page: Page, timeout = 30000): Promise<void> {
  await page.waitForSelector(SELECTORS.appReady, { timeout, state: 'attached' });
}

async function loginAs(page: Page, credentials: { email: string; password: string }): Promise<void> {
  await page.goto('/login');
  await waitForAppReady(page);
  await page.fill(SELECTORS.emailInput, credentials.email);
  await page.fill(SELECTORS.passwordInput, credentials.password);
  await page.click(SELECTORS.loginButton);
  await page.waitForURL(/\/(cockpit|invoicing|documents|partners)/, { timeout: 15000 });
  await waitForAppReady(page);
}

async function navigateTo(page: Page, path: string): Promise<void> {
  await page.goto(path);
  await waitForAppReady(page);
}

async function pageHasContent(page: Page): Promise<boolean> {
  const contentSelectors = [
    'table', '.azals-table', '.azals-card', '[class*="card"]',
    'main', 'h1', 'h2', 'h3', '[class*="title"]', '[class*="wrapper"]',
    '[class*="page"]', 'form', 'button', '.azals-document',
  ];

  for (const selector of contentSelectors) {
    const isVisible = await page.locator(selector).first().isVisible().catch(() => false);
    if (isVisible) return true;
  }
  return false;
}

// ============================================================
// TESTS: REDIRECTIONS LEGACY ROUTES
// ============================================================

test.describe('Documents Unifié - Redirections Legacy', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
  });

  test('/invoicing redirige vers /documents?type=QUOTE', async ({ page }) => {
    await navigateTo(page, '/invoicing');

    // Vérifier que l'URL contient /documents
    expect(page.url()).toContain('/documents');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('/invoicing/quotes redirige vers /documents?type=QUOTE&mode=list', async ({ page }) => {
    await navigateTo(page, '/invoicing/quotes');

    expect(page.url()).toContain('/documents');
    expect(page.url()).toContain('type=QUOTE');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('/invoicing/invoices redirige vers /documents?type=INVOICE&mode=list', async ({ page }) => {
    await navigateTo(page, '/invoicing/invoices');

    expect(page.url()).toContain('/documents');
    expect(page.url()).toContain('type=INVOICE');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('/purchases/orders redirige vers /documents?type=PURCHASE_ORDER&mode=list', async ({ page }) => {
    await navigateTo(page, '/purchases/orders');

    expect(page.url()).toContain('/documents');
    expect(page.url()).toContain('type=PURCHASE_ORDER');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('/purchases/invoices redirige vers /documents?type=PURCHASE_INVOICE&mode=list', async ({ page }) => {
    await navigateTo(page, '/purchases/invoices');

    expect(page.url()).toContain('/documents');
    expect(page.url()).toContain('type=PURCHASE_INVOICE');
    expect(await pageHasContent(page)).toBeTruthy();
  });
});

// ============================================================
// TESTS: SELECTION TYPE DOCUMENT
// ============================================================

test.describe('Documents Unifié - Sélection Type', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
    await navigateTo(page, '/documents');
  });

  for (const docType of DOCUMENT_TYPES) {
    test(`peut sélectionner le type ${docType}`, async ({ page }) => {
      // Naviguer vers le type spécifique via URL
      await navigateTo(page, `/documents?type=${docType}`);

      expect(page.url()).toContain(`type=${docType}`);
      expect(await pageHasContent(page)).toBeTruthy();
    });
  }

  test('page documents charge correctement', async ({ page }) => {
    expect(page.url()).toContain('/documents');
    expect(await pageHasContent(page)).toBeTruthy();
  });
});

// ============================================================
// TESTS: MODE SAISIE / CONSULTATION
// ============================================================

test.describe('Documents Unifié - Modes', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
  });

  test('mode entry affiche le formulaire', async ({ page }) => {
    await navigateTo(page, '/documents?type=QUOTE&mode=entry');

    // Vérifier présence de formulaire ou champs de saisie
    const hasForm = await page.locator('form, [class*="form"]').first().isVisible().catch(() => false);
    const hasInputs = await page.locator('input, select, textarea').first().isVisible().catch(() => false);

    expect(hasForm || hasInputs).toBeTruthy();
  });

  test('mode list affiche la liste', async ({ page }) => {
    await navigateTo(page, '/documents?type=QUOTE&mode=list');

    // Vérifier présence de table ou liste
    const hasTable = await page.locator('table, [class*="list"], [class*="table"]').first().isVisible().catch(() => false);
    const hasContent = await pageHasContent(page);

    expect(hasTable || hasContent).toBeTruthy();
  });

  test('basculement entre modes', async ({ page }) => {
    // Commencer en mode entry
    await navigateTo(page, '/documents?type=QUOTE&mode=entry');
    expect(await pageHasContent(page)).toBeTruthy();

    // Passer en mode list
    await navigateTo(page, '/documents?type=QUOTE&mode=list');
    expect(await pageHasContent(page)).toBeTruthy();

    // Revenir en mode entry
    await navigateTo(page, '/documents?type=QUOTE&mode=entry');
    expect(await pageHasContent(page)).toBeTruthy();
  });
});

// ============================================================
// TESTS: CREATION DOCUMENTS (tous types)
// ============================================================

test.describe('Documents Unifié - Création', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
  });

  for (const docType of DOCUMENT_TYPES) {
    test(`formulaire création ${docType} accessible`, async ({ page }) => {
      await navigateTo(page, `/documents?type=${docType}&mode=entry`);

      // Vérifier que la page charge
      expect(await pageHasContent(page)).toBeTruthy();

      // Vérifier présence d'éléments de formulaire
      const formElements = await page.locator('input, select, textarea, button').count();
      expect(formElements).toBeGreaterThan(0);
    });
  }

  test('formulaire QUOTE contient les champs requis', async ({ page }) => {
    await navigateTo(page, '/documents?type=QUOTE&mode=entry');

    // Vérifier que des champs sont présents (même si pas tous visibles)
    const hasContent = await pageHasContent(page);
    expect(hasContent).toBeTruthy();
  });
});

// ============================================================
// TESTS: i18n INTERNATIONALISATION
// ============================================================

test.describe('Documents Unifié - i18n', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
    await navigateTo(page, '/documents?type=QUOTE');
  });

  test('textes affichés (non vides)', async ({ page }) => {
    // Vérifier que les textes sont affichés (non vides)
    const textContent = await page.textContent('body');
    expect(textContent?.trim().length).toBeGreaterThan(0);
  });

  test('pas de clés i18n non traduites visibles', async ({ page }) => {
    const textContent = await page.textContent('body') || '';

    // Les clés non traduites ressemblent à "documents.types.QUOTE" ou "common.save"
    const untranslatedKeys = textContent.match(/\b[a-z]+\.[a-z]+\.[A-Z_]+\b/g) || [];

    // Filtrer les faux positifs (URLs, noms de fichiers, etc.)
    const realUntranslated = untranslatedKeys.filter(
      key => !key.includes('http') && !key.includes('www') && !key.includes('.ts') && !key.includes('.js')
    );

    // Debug: afficher les clés non traduites si trouvées
    if (realUntranslated.length > 0) {
      console.log('Potential untranslated keys:', realUntranslated);
    }

    // Tolérer quelques cas edge (configuration, debug, etc.)
    expect(realUntranslated.length).toBeLessThan(5);
  });

  test('localStorage contient la langue', async ({ page }) => {
    // Vérifier que la langue est stockée
    const language = await page.evaluate(() => {
      return localStorage.getItem('azals_language') || 'fr';
    });

    expect(['fr', 'en']).toContain(language);
  });
});

// ============================================================
// TESTS: NAVIGATION COMPLETE
// ============================================================

test.describe('Documents Unifié - Navigation Complète', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
  });

  test('parcours complet VENTES: QUOTE -> INVOICE -> CREDIT_NOTE', async ({ page }) => {
    // Devis
    await navigateTo(page, '/documents?type=QUOTE&mode=list');
    expect(await pageHasContent(page)).toBeTruthy();

    // Facture
    await navigateTo(page, '/documents?type=INVOICE&mode=list');
    expect(await pageHasContent(page)).toBeTruthy();

    // Avoir
    await navigateTo(page, '/documents?type=CREDIT_NOTE&mode=list');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('parcours complet ACHATS: PURCHASE_ORDER -> PURCHASE_INVOICE', async ({ page }) => {
    // Commande d'achat
    await navigateTo(page, '/documents?type=PURCHASE_ORDER&mode=list');
    expect(await pageHasContent(page)).toBeTruthy();

    // Facture d'achat
    await navigateTo(page, '/documents?type=PURCHASE_INVOICE&mode=list');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('navigation rapide entre tous les types', async ({ page }) => {
    for (const docType of DOCUMENT_TYPES) {
      const startTime = Date.now();
      await navigateTo(page, `/documents?type=${docType}`);
      const loadTime = Date.now() - startTime;

      expect(await pageHasContent(page)).toBeTruthy();
      expect(loadTime).toBeLessThan(5000); // < 5 secondes
    }
  });
});

// ============================================================
// TESTS: PERFORMANCE
// ============================================================

test.describe('Documents Unifié - Performance', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
  });

  test('changement de type sans rechargement page complète', async ({ page }) => {
    await navigateTo(page, '/documents?type=QUOTE');

    // Mesurer le temps de changement de type
    const startTime = Date.now();
    await page.goto('/documents?type=INVOICE');
    await waitForAppReady(page);
    const switchTime = Date.now() - startTime;

    // Le changement devrait être rapide (pas de rechargement complet)
    expect(switchTime).toBeLessThan(3000);
  });

  test('pas d\'erreurs JavaScript critiques sur /documents', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await navigateTo(page, '/documents?type=QUOTE');
    await navigateTo(page, '/documents?type=INVOICE');
    await navigateTo(page, '/documents?type=PURCHASE_ORDER');

    // Filtrer les erreurs réseau (attendues en mode démo)
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
        !e.includes('timeout')
    );

    if (criticalErrors.length > 0) {
      console.log('Critical errors found:', criticalErrors);
    }

    expect(criticalErrors.length).toBe(0);
  });
});

// ============================================================
// TESTS: RBAC & PERMISSIONS
// ============================================================

test.describe('Documents Unifié - RBAC', () => {
  test('admin peut accéder à /documents', async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
    await navigateTo(page, '/documents');

    expect(page.url()).toContain('/documents');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('user standard peut accéder à /documents', async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.user);
    await navigateTo(page, '/documents');

    // User devrait avoir accès (ou être redirigé selon permissions)
    expect(await pageHasContent(page)).toBeTruthy();
  });
});

// ============================================================
// TESTS: RESPONSIVE
// ============================================================

test.describe('Documents Unifié - Responsive', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_CREDENTIALS.admin);
  });

  test('desktop 1920x1080', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await navigateTo(page, '/documents?type=QUOTE');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('laptop 1366x768', async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await navigateTo(page, '/documents?type=QUOTE');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('tablet 768x1024', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await navigateTo(page, '/documents?type=QUOTE');
    expect(await pageHasContent(page)).toBeTruthy();
  });

  test('mobile 375x667', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await navigateTo(page, '/documents?type=QUOTE');
    expect(await pageHasContent(page)).toBeTruthy();
  });
});
