/**
 * AZALSCORE - Global Setup
 *
 * Execute une seule fois AVANT tous les tests.
 * Effectue le login et sauvegarde l'etat d'authentification.
 */

import { test as setup, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// ES Module compatibility
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const AUTH_FILE = path.join(__dirname, '.auth/user.json');
const BASE_URL = process.env.BASE_URL || 'https://azalscore.com';

// Credentials
const CREDENTIALS = {
  tenant: process.env.TEST_TENANT || 'masith',
  email: process.env.TEST_USER || 'contact@masith.fr',
  password: process.env.TEST_PASSWORD || 'Azals2026!'
};

setup('Authentification globale', async ({ page }) => {
  // Creer le dossier .auth si necessaire
  const authDir = path.dirname(AUTH_FILE);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  console.log(`[SETUP] Login sur ${BASE_URL}...`);

  // Aller sur la page de login
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded' });

  // Attendre le formulaire
  await page.waitForSelector('#tenant, input[name="tenant"]', { timeout: 15000 });

  // Remplir les credentials
  await page.fill('#tenant', CREDENTIALS.tenant);
  await page.fill('#email', CREDENTIALS.email);
  await page.fill('#password', CREDENTIALS.password);

  // Soumettre
  await page.click('button[type="submit"]');

  // Attendre que l'authentification reussisse
  // On verifie plusieurs indicateurs possibles
  await Promise.race([
    page.waitForSelector('.azals-unified-header__selector', { timeout: 20000 }),
    page.waitForSelector('button:has-text("Nouvelle saisie")', { timeout: 20000 }),
    page.waitForURL(/\/(cockpit|dashboard|home|app)/, { timeout: 20000 })
  ]).catch(async () => {
    // Debug: afficher le contenu de la page en cas d'echec
    const bodyText = await page.locator('body').textContent();
    console.log('[SETUP] Echec login. Contenu page:', bodyText?.substring(0, 500));
    throw new Error('Login failed - impossible de detecter une session authentifiee');
  });

  console.log('[SETUP] Login reussi, sauvegarde de la session...');

  // Sauvegarder l'etat d'authentification (cookies + localStorage)
  await page.context().storageState({ path: AUTH_FILE });

  console.log(`[SETUP] Session sauvegardee dans ${AUTH_FILE}`);
});
