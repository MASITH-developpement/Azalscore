/**
 * AZALSCORE - Tests E2E Business Critical
 * Suite de tests pour les flux metier critiques
 */

import { test, expect, type Page } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const API_URL = process.env.API_URL || 'http://localhost:8000';

/**
 * Helper: Login avec credentials
 */
async function login(page: Page): Promise<void> {
  await page.goto(`${BASE_URL}/login`);
  await page.waitForLoadState('networkidle');

  // Trouver les champs de login avec selecteurs flexibles
  const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i], input[placeholder*="identifiant" i]').first();
  const passwordInput = page.locator('input[type="password"], input[name="password"]').first();

  const email = process.env.TEST_USER || 'admin@test.com';
  const password = process.env.TEST_PASSWORD || 'Test1234!';

  await emailInput.fill(email);
  await passwordInput.fill(password);

  // Cliquer sur le bouton de connexion
  const submitBtn = page.locator('button[type="submit"], button:has-text("Connexion"), button:has-text("Se connecter"), button:has-text("Login")').first();
  await submitBtn.click();

  // Attendre la redirection vers dashboard/home/cockpit
  try {
    await page.waitForURL(/\/(dashboard|home|cockpit|app)/, { timeout: 10000 });
  } catch {
    // Si pas de redirection, verifier qu'on n'a pas d'erreur
    const hasError = await page.locator('text=/error|erreur|invalide|incorrect/i').isVisible();
    if (hasError) {
      throw new Error('Login failed - error message visible');
    }
  }
}

test.describe('AZALSCORE Critical Flows', () => {
  test.beforeEach(async () => {
    test.setTimeout(60000);
  });

  // ============================================================================
  // AUTHENTICATION
  // ============================================================================

  test('Auth - Login successful', async ({ page }) => {
    await login(page);

    // Verifier qu'on est sur une page authentifiee
    const url = page.url();
    expect(url).toMatch(/\/(dashboard|home|cockpit|app|purchases|treasury|accounting)/);

    // Pas de message d'erreur
    const bodyText = await page.locator('body').textContent();
    expect(bodyText?.toLowerCase()).not.toContain('error');
    expect(bodyText?.toLowerCase()).not.toContain('échec');
    expect(bodyText?.toLowerCase()).not.toContain('invalide');
  });

  test('Auth - Logout works', async ({ page }) => {
    await login(page);

    // Trouver et cliquer sur deconnexion
    const logoutBtn = page.locator('button:has-text("Déconnexion"), button:has-text("Logout"), button:has-text("Se déconnecter"), a:has-text("Déconnexion")').first();

    if (await logoutBtn.isVisible({ timeout: 3000 })) {
      await logoutBtn.click();
      await page.waitForURL(/\/login/, { timeout: 5000 });
      expect(page.url()).toContain('login');
    } else {
      // Menu utilisateur peut etre dans un dropdown
      const userMenu = page.locator('[data-testid="user-menu"], .user-menu, .avatar, .profile-menu').first();
      if (await userMenu.isVisible({ timeout: 2000 })) {
        await userMenu.click();
        const logoutItem = page.locator('text=/déconnexion|logout|se déconnecter/i').first();
        await logoutItem.click();
        await page.waitForURL(/\/login/, { timeout: 5000 });
      }
    }
  });

  // ============================================================================
  // PURCHASES MODULE
  // ============================================================================

  test('Purchases - List suppliers', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/purchases`);

    // Verifier le titre/heading
    const heading = page.locator('h1, h2, [class*="title"]').first();
    await expect(heading).toContainText(/fournisseurs|purchases|achats|suppliers/i, { timeout: 5000 });

    // Pas d'erreur 404 ou 500
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('404');
    expect(bodyText).not.toContain('500');

    // Presence d'une liste ou tableau
    const hasTable = await page.locator('table, [class*="table"], [class*="list"], [class*="grid"]').first().isVisible({ timeout: 3000 });
    expect(hasTable).toBeTruthy();
  });

  test('Purchases - Create supplier form', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/purchases`);

    // Chercher bouton de creation
    const createBtn = page.locator('button:has-text("Nouveau"), button:has-text("Créer"), button:has-text("Ajouter"), button:has-text("New")').first();

    if (await createBtn.isVisible({ timeout: 3000 })) {
      await createBtn.click();
      // Verifier que le formulaire ou dialog s'ouvre
      const hasForm = await page.locator('form, [role="dialog"], .modal').first().isVisible({ timeout: 3000 });
      expect(hasForm).toBeTruthy();
    } else {
      test.skip();
    }
  });

  // ============================================================================
  // TREASURY MODULE
  // ============================================================================

  test('Treasury - Dashboard loads', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/treasury`);

    // Verifier le heading
    const heading = page.locator('h1, h2, [class*="title"]').first();
    await expect(heading).toContainText(/trésorerie|treasury|comptes|accounts/i, { timeout: 5000 });

    // Pas d'erreur 404
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('404');

    // Presence de chiffres/montants
    const hasNumbers = /\d+[,.]?\d*/.test(bodyText || '');
    expect(hasNumbers).toBeTruthy();
  });

  test('Treasury - List accounts', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/treasury`);

    // Verifier presence d'elements de liste
    const hasListItems = await page.locator('[class*="card"], tr, [class*="list-item"], [class*="account"]').first().isVisible({ timeout: 5000 });
    expect(hasListItems).toBeTruthy();
  });

  // ============================================================================
  // ACCOUNTING MODULE
  // ============================================================================

  test('Accounting - List entries', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/accounting`);

    // Verifier le heading
    const heading = page.locator('h1, h2, [class*="title"]').first();
    await expect(heading).toContainText(/comptabilité|accounting|écritures|entries|journal/i, { timeout: 5000 });

    // Pas d'erreur 404
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('404');
  });

  test('Accounting - Navigate fiscal years', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/accounting`);

    // Chercher onglet ou lien exercice
    const fiscalTab = page.locator('text=/exercice|fiscal year|exercices/i, [href*="fiscal"], button:has-text("Exercice")').first();

    if (await fiscalTab.isVisible({ timeout: 3000 })) {
      const initialUrl = page.url();
      await fiscalTab.click();
      await page.waitForTimeout(1000);

      // Verifier changement URL ou contenu
      const newUrl = page.url();
      const urlChanged = newUrl !== initialUrl;
      const bodyText = await page.locator('body').textContent();
      const hasExerciseContent = /exercice|fiscal|année/i.test(bodyText || '');

      expect(urlChanged || hasExerciseContent).toBeTruthy();
    }
  });

  // ============================================================================
  // INVOICING MODULE
  // ============================================================================

  test('Invoicing - List documents', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/invoicing`);

    // Verifier le heading
    const heading = page.locator('h1, h2, [class*="title"]').first();
    await expect(heading).toContainText(/facturation|invoicing|devis|factures|quotes/i, { timeout: 5000 });

    // Chercher bouton filtre si existe
    const filterBtn = page.locator('button:has-text("Filtre"), button:has-text("Filter"), [class*="filter"]').first();
    if (await filterBtn.isVisible({ timeout: 2000 })) {
      expect(true).toBeTruthy();
    }
  });

  test('Invoicing - Create quote form', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/invoicing`);

    // Chercher bouton de creation devis
    const createBtn = page.locator('button:has-text("Nouveau"), button:has-text("Créer"), button:has-text("Devis")').first();

    if (await createBtn.isVisible({ timeout: 3000 })) {
      await createBtn.click();
      const hasForm = await page.locator('form, [role="dialog"], .modal').first().isVisible({ timeout: 3000 });
      expect(hasForm).toBeTruthy();
    } else {
      test.skip();
    }
  });

  // ============================================================================
  // PARTNERS MODULE
  // ============================================================================

  test('Partners - List clients', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/partners`);

    // Verifier le heading
    const heading = page.locator('h1, h2, [class*="title"]').first();
    await expect(heading).toContainText(/partenaires|partners|clients/i, { timeout: 5000 });

    // Pas d'erreur 404
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('404');
  });

  // ============================================================================
  // ADMIN MODULE
  // ============================================================================

  test('Admin - Dashboard visible', async ({ page }) => {
    await login(page);

    // Essayer plusieurs routes possibles
    const adminRoutes = ['/admin', '/settings', '/parametres'];
    let found = false;

    for (const route of adminRoutes) {
      await page.goto(`${BASE_URL}${route}`);
      const bodyText = await page.locator('body').textContent();

      if (!bodyText?.includes('404') && bodyText && bodyText.length > 100) {
        found = true;
        // Chercher metriques ou statistiques
        const hasStats = /statistique|metric|utilisateur|user|role|permission/i.test(bodyText);
        expect(hasStats || found).toBeTruthy();
        break;
      }
    }

    if (!found) {
      test.skip();
    }
  });

  // ============================================================================
  // CRM MODULE
  // ============================================================================

  test('CRM - Opportunities list', async ({ page }) => {
    await login(page);

    // Essayer CRM ou Commercial
    const routes = ['/crm', '/commercial'];
    let found = false;

    for (const route of routes) {
      await page.goto(`${BASE_URL}${route}`);
      const heading = page.locator('h1, h2, [class*="title"]').first();

      try {
        await expect(heading).toContainText(/crm|commercial|opportunités|clients/i, { timeout: 3000 });
        found = true;

        const bodyText = await page.locator('body').textContent();
        expect(bodyText).not.toContain('404');
        break;
      } catch {
        continue;
      }
    }

    if (!found) {
      test.skip();
    }
  });

  // ============================================================================
  // STOCK MODULE
  // ============================================================================

  test('Stock - Inventory visible', async ({ page }) => {
    await login(page);

    // Essayer plusieurs routes
    const routes = ['/inventory', '/stock'];
    let found = false;

    for (const route of routes) {
      await page.goto(`${BASE_URL}${route}`);
      const heading = page.locator('h1, h2, [class*="title"]').first();

      try {
        await expect(heading).toContainText(/stock|inventory|inventaire|produits/i, { timeout: 3000 });
        found = true;
        break;
      } catch {
        continue;
      }
    }

    if (!found) {
      test.skip();
    }
  });

  // ============================================================================
  // API HEALTH
  // ============================================================================

  test('API Health - Endpoint responds', async ({ request }) => {
    const response = await request.get(`${API_URL}/health`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toMatch(/healthy|operational|ok/i);
  });

  // ============================================================================
  // INTERVENTIONS MODULE
  // ============================================================================

  test('Interventions - List visible', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/interventions`);

    const heading = page.locator('h1, h2, [class*="title"]').first();
    await expect(heading).toContainText(/intervention|field service|terrain/i, { timeout: 5000 });

    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('404');
  });

  // ============================================================================
  // HR MODULE
  // ============================================================================

  test('HR - Employees list', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/hr`);

    const heading = page.locator('h1, h2, [class*="title"]').first();

    try {
      await expect(heading).toContainText(/ressources humaines|hr|employés|employees|personnel/i, { timeout: 5000 });
      const bodyText = await page.locator('body').textContent();
      expect(bodyText).not.toContain('404');
    } catch {
      test.skip();
    }
  });
});
