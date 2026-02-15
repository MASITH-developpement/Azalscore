/**
 * AZALSCORE - Auth Fixture
 *
 * Gere l'authentification partagee entre tous les tests E2E.
 * Utilise storageState pour eviter de se reconnecter a chaque test.
 */

import { test as base, expect, type Page, type BrowserContext } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// ES Module compatibility
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const BASE_URL = process.env.BASE_URL || 'https://azalscore.com';
const AUTH_FILE = path.join(__dirname, '../.auth/user.json');

// Credentials
const CREDENTIALS = {
  tenant: process.env.TEST_TENANT || 'masith',
  email: process.env.TEST_USER || 'contact@masith.fr',
  password: process.env.TEST_PASSWORD || 'Azals2026!'
};

/**
 * Login et sauvegarde l'etat d'authentification
 */
export async function globalLogin(page: Page): Promise<void> {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded' });

  // Attendre le formulaire
  await page.waitForSelector('#tenant, input[name="tenant"]', { timeout: 10000 });

  // Remplir les champs
  await page.fill('#tenant', CREDENTIALS.tenant);
  await page.fill('#email', CREDENTIALS.email);
  await page.fill('#password', CREDENTIALS.password);

  // Soumettre
  await page.click('button[type="submit"]');

  // Attendre authentification reussie
  await Promise.race([
    page.waitForSelector('.azals-unified-header__selector', { timeout: 15000 }),
    page.waitForSelector('button:has-text("Nouvelle saisie")', { timeout: 15000 }),
    page.waitForURL(/\/(cockpit|dashboard|home)/, { timeout: 15000 })
  ]);
}

/**
 * Verifie si l'utilisateur est connecte
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  try {
    const header = page.locator('.azals-unified-header__selector, button:has-text("Nouvelle saisie")').first();
    return await header.isVisible({ timeout: 2000 });
  } catch {
    return false;
  }
}

/**
 * Type pour les fixtures personnalisees
 */
type AuthFixtures = {
  authenticatedPage: Page;
  baseURL: string;
};

/**
 * Test avec authentification automatique
 */
export const test = base.extend<AuthFixtures>({
  baseURL: BASE_URL,

  authenticatedPage: async ({ page, context }, use) => {
    // Verifier si on a deja un etat auth sauvegarde
    if (fs.existsSync(AUTH_FILE)) {
      try {
        const authState = JSON.parse(fs.readFileSync(AUTH_FILE, 'utf-8'));
        await context.addCookies(authState.cookies || []);
      } catch {
        // Fichier corrompu, on se reconnecte
      }
    }

    // Aller sur la page d'accueil
    await page.goto(BASE_URL);

    // Verifier si on est connecte
    if (!(await isLoggedIn(page))) {
      await globalLogin(page);

      // Sauvegarder l'etat
      const cookies = await context.cookies();
      const dir = path.dirname(AUTH_FILE);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(AUTH_FILE, JSON.stringify({ cookies }));
    }

    await use(page);
  }
});

export { expect };
export { BASE_URL, CREDENTIALS };
