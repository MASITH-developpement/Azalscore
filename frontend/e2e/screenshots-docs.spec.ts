/**
 * AZALSCORE - Screenshots pour Documentation
 *
 * Ce fichier genere les captures d'ecran pour la documentation
 * de vente et le rapport de valorisation 200K.
 *
 * Usage: npx playwright test screenshots-docs.spec.ts
 */

import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const SCREENSHOTS_DIR = path.join(__dirname, '../../docs/screenshots');

// Credentials de test
const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'admin@azalscore.com',
  password: process.env.TEST_USER_PASSWORD || ''  // Set via environment variable
};

// URL de production si definie
const BASE_URL = process.env.BASE_URL || 'https://azalscore.com';

test.describe('Documentation Screenshots', () => {

  test.beforeAll(async () => {
    // Creer le dossier screenshots s'il n'existe pas
    if (!fs.existsSync(SCREENSHOTS_DIR)) {
      fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
    }
  });

  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Remplir le formulaire de connexion
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const passwordInput = page.locator('input[type="password"], input[name="password"]');

    if (await emailInput.isVisible()) {
      await emailInput.fill(TEST_USER.email);
      await passwordInput.fill(TEST_USER.password);
      await page.click('button[type="submit"]');
      await page.waitForURL('**/cockpit**', { timeout: 10000 }).catch(() => {
        // Si pas de redirection vers cockpit, continuer quand meme
      });
    }

    await page.waitForLoadState('networkidle');
  });

  test('01 - Cockpit Dashboard Overview', async ({ page }) => {
    await page.goto('/cockpit');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Attendre le chargement des KPIs

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '01-cockpit-dashboard.png'),
      fullPage: true
    });
  });

  test('02 - Strategic KPIs Section', async ({ page }) => {
    await page.goto('/cockpit');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Essayer de localiser la section KPIs strategiques
    const strategicSection = page.locator('.azals-cockpit-strategic');

    if (await strategicSection.isVisible()) {
      await strategicSection.screenshot({
        path: path.join(SCREENSHOTS_DIR, '02-strategic-kpis.png')
      });
    } else {
      // Screenshot de la zone superieure du cockpit
      await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, '02-strategic-kpis.png'),
        clip: { x: 0, y: 0, width: 1280, height: 600 }
      });
    }
  });

  test('03 - Cockpit Alerts Panel', async ({ page }) => {
    await page.goto('/cockpit');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    const alertsPanel = page.locator('[class*="alert"], [class*="Alert"]').first();

    if (await alertsPanel.isVisible()) {
      await alertsPanel.screenshot({
        path: path.join(SCREENSHOTS_DIR, '03-cockpit-alerts.png')
      });
    }
  });

  test('04 - BI Module Query Editor', async ({ page }) => {
    await page.goto('/bi');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '04-bi-module.png'),
      fullPage: false
    });
  });

  test('05 - CRM Pipeline View', async ({ page }) => {
    await page.goto('/crm');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '05-crm-pipeline.png'),
      fullPage: false
    });
  });

  test('06 - Sales Module (Devis/Factures)', async ({ page }) => {
    await page.goto('/ventes');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '06-ventes-module.png'),
      fullPage: false
    });
  });

  test('07 - Purchases Module', async ({ page }) => {
    await page.goto('/achats');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '07-achats-module.png'),
      fullPage: false
    });
  });

  test('08 - Mobile Responsive View', async ({ page }) => {
    // Simuler un ecran mobile
    await page.setViewportSize({ width: 375, height: 812 });

    await page.goto('/cockpit');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '08-mobile-cockpit.png'),
      fullPage: true
    });
  });

  test('09 - Tablet Responsive View', async ({ page }) => {
    // Simuler une tablette
    await page.setViewportSize({ width: 768, height: 1024 });

    await page.goto('/cockpit');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '09-tablet-cockpit.png'),
      fullPage: false
    });
  });

  test('10 - Login Page', async ({ page }) => {
    // Deconnexion d'abord
    await page.goto('/logout');
    await page.waitForTimeout(1000);

    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '10-login-page.png'),
      fullPage: false
    });
  });

});

// Test standalone pour verification rapide
test('Quick verification - Cockpit loads', async ({ page }) => {
  await page.goto('/cockpit');
  const title = await page.title();
  console.log(`Page title: ${title}`);

  // Verifier que la page charge sans erreur
  const hasError = await page.locator('text=Error').isVisible().catch(() => false);
  expect(hasError).toBeFalsy();
});
