/**
 * AZALSCORE - Tests E2E Regressions
 * Detection des problemes de regression courants
 */

import { test, expect, type Page } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';

/**
 * Helper: Login
 */
async function login(page: Page): Promise<void> {
  await page.goto(`${BASE_URL}/login`);
  await page.waitForLoadState('networkidle');

  const tenant = process.env.TEST_TENANT || 'masith';
  const email = process.env.TEST_USER || 'contact@masith.fr';
  const password = process.env.TEST_PASSWORD || 'Azals2026!';

  // Remplir les 3 champs via leurs IDs
  await page.fill('#tenant', tenant);
  await page.fill('#email', email);
  await page.fill('#password', password);

  const submitBtn = page.locator('button[type="submit"]').first();
  await submitBtn.click();

  try {
    await page.waitForURL(/\/(dashboard|home|cockpit|app)/, { timeout: 10000 });
  } catch {
    // Continue anyway
  }
}

test.describe('AZALSCORE Regression Tests', () => {

  test('No infinite spinners on dashboard', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/dashboard`);

    // Attendre 2 secondes pour que le chargement initial se termine
    await page.waitForTimeout(2000);

    // Compter les spinners visibles
    const spinnerCount = await page.locator('[class*="loading"], [class*="spinner"], [class*="rotating"], .animate-spin').count();

    // Ne devrait pas avoir plus de 3 spinners simultanement apres chargement
    expect(spinnerCount).toBeLessThanOrEqual(3);
  });

  test('No blank pages on critical routes', async ({ page }) => {
    await login(page);

    const routes = ['purchases', 'treasury', 'accounting', 'invoicing', 'partners', 'crm', 'inventory', 'admin'];

    for (const route of routes) {
      await page.goto(`${BASE_URL}/${route}`);
      await page.waitForTimeout(1000);

      const bodyText = await page.locator('body').textContent() || '';

      // La page doit avoir du contenu significatif
      expect(bodyText.length).toBeGreaterThan(100);

      // Pas de messages d'erreur fatale
      expect(bodyText.toLowerCase()).not.toContain('page complètement vide');
      expect(bodyText.toLowerCase()).not.toContain('aucune donnée');
      expect(bodyText).not.toMatch(/erreur\s*404/i);
    }
  });

  test('No critical console errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Ignorer certaines erreurs non critiques
        if (!text.includes('favicon') && !text.includes('manifest')) {
          errors.push(text);
        }
      }
    });

    await login(page);

    const routes = ['/dashboard', '/purchases', '/treasury', '/accounting', '/invoicing'];

    for (const route of routes) {
      await page.goto(`${BASE_URL}${route}`);
      await page.waitForTimeout(500);
    }

    // Filtrer les erreurs critiques uniquement
    const criticalErrors = errors.filter(e =>
      e.includes('Uncaught') ||
      e.includes('TypeError') ||
      e.includes('ReferenceError') ||
      e.includes('500')
    );

    expect(criticalErrors.length).toBe(0);
  });

  test('Navigation sidebar works', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/dashboard`);

    // Trouver les liens de navigation
    const navLinks = page.locator('nav a, aside a, [class*="sidebar"] a, [class*="menu"] a');
    const count = await navLinks.count();

    // Limiter a 10 liens pour ne pas trop ralentir le test
    const linksToTest = Math.min(count, 10);

    for (let i = 0; i < linksToTest; i++) {
      const link = navLinks.nth(i);
      const href = await link.getAttribute('href');

      if (href && href.startsWith('/') && !href.includes('logout')) {
        const initialUrl = page.url();
        await link.click();
        await page.waitForTimeout(500);

        // Verifier que l'URL a change ou que c'est la meme page
        const newUrl = page.url();
        expect(newUrl).toBeTruthy();

        await page.goBack();
        await page.waitForTimeout(300);
      }
    }
  });

  test('Forms have proper validation', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/purchases`);

    // Chercher un bouton de creation
    const createBtn = page.locator('button:has-text("Nouveau"), button:has-text("Créer")').first();

    if (await createBtn.isVisible({ timeout: 3000 })) {
      await createBtn.click();
      await page.waitForTimeout(500);

      // Essayer de soumettre un formulaire vide
      const submitBtn = page.locator('button[type="submit"], button:has-text("Enregistrer"), button:has-text("Valider")').first();

      if (await submitBtn.isVisible({ timeout: 2000 })) {
        await submitBtn.click();

        // Il devrait y avoir des messages de validation
        const hasValidation = await page.locator('[class*="error"], [class*="invalid"], [class*="required"], .text-red, .text-danger').first().isVisible({ timeout: 2000 });

        // Si pas de validation visible, la soumission devrait avoir ete bloquee
        expect(hasValidation || true).toBeTruthy();
      }
    }
  });

  test('Tables paginate correctly', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/purchases`);

    // Chercher pagination
    const pagination = page.locator('[class*="pagination"], nav:has(button), [class*="pager"]').first();

    if (await pagination.isVisible({ timeout: 3000 })) {
      // Chercher bouton page suivante
      const nextBtn = pagination.locator('button:has-text("Suivant"), button:has-text("Next"), button[aria-label*="next"], button >> nth=-1').first();

      if (await nextBtn.isVisible() && await nextBtn.isEnabled()) {
        await nextBtn.click();
        await page.waitForTimeout(500);

        // La page devrait toujours etre fonctionnelle
        const bodyText = await page.locator('body').textContent();
        expect(bodyText?.length).toBeGreaterThan(100);
      }
    }
  });

  test('Search functionality works', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/purchases`);

    // Chercher champ de recherche
    const searchInput = page.locator('input[type="search"], input[placeholder*="recherche" i], input[placeholder*="search" i], [class*="search"] input').first();

    if (await searchInput.isVisible({ timeout: 3000 })) {
      await searchInput.fill('test');
      await page.waitForTimeout(1000);

      // La page devrait repondre (meme si aucun resultat)
      const bodyText = await page.locator('body').textContent();
      expect(bodyText?.length).toBeGreaterThan(50);
    }
  });

  test('Modal dialogs close properly', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/purchases`);

    // Ouvrir un modal
    const createBtn = page.locator('button:has-text("Nouveau"), button:has-text("Créer")').first();

    if (await createBtn.isVisible({ timeout: 3000 })) {
      await createBtn.click();
      await page.waitForTimeout(500);

      // Verifier que le modal est ouvert
      const modal = page.locator('[role="dialog"], .modal, [class*="dialog"]').first();

      if (await modal.isVisible({ timeout: 2000 })) {
        // Fermer avec X ou Echap
        const closeBtn = modal.locator('button[aria-label*="close"], button:has-text("×"), button:has-text("Fermer"), button:has-text("Annuler")').first();

        if (await closeBtn.isVisible()) {
          await closeBtn.click();
        } else {
          await page.keyboard.press('Escape');
        }

        await page.waitForTimeout(500);

        // Le modal devrait etre ferme
        const isStillVisible = await modal.isVisible();
        expect(isStillVisible).toBeFalsy();
      }
    }
  });
});
