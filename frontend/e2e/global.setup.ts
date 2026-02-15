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
  console.log(`[SETUP] Credentials: tenant=${CREDENTIALS.tenant}, email=${CREDENTIALS.email}`);

  // Aller sur la page de login
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });

  // Attendre que le formulaire soit completement charge
  const tenantInput = page.locator('#tenant');
  const emailInput = page.locator('#email');
  const passwordInput = page.locator('#password');
  const submitButton = page.locator('button[type="submit"]');

  // Attendre que tous les champs soient visibles
  await tenantInput.waitFor({ state: 'visible', timeout: 15000 });
  await emailInput.waitFor({ state: 'visible', timeout: 5000 });
  await passwordInput.waitFor({ state: 'visible', timeout: 5000 });

  console.log('[SETUP] Formulaire de login detecte');

  // Vider les champs au cas ou ils auraient des valeurs pre-remplies
  await tenantInput.clear();
  await emailInput.clear();
  await passwordInput.clear();

  // Remplir les credentials avec des delais pour les inputs React
  await tenantInput.fill(CREDENTIALS.tenant);
  await page.waitForTimeout(100); // Laisser React mettre a jour le state

  await emailInput.fill(CREDENTIALS.email);
  await page.waitForTimeout(100);

  await passwordInput.fill(CREDENTIALS.password);
  await page.waitForTimeout(100);

  // Verifier que les valeurs sont bien remplies
  const tenantValue = await tenantInput.inputValue();
  const emailValue = await emailInput.inputValue();
  const passwordValue = await passwordInput.inputValue();

  console.log(`[SETUP] Valeurs remplies: tenant="${tenantValue}", email="${emailValue}", password="${passwordValue ? '***' : 'VIDE'}"`);

  if (!tenantValue || !emailValue || !passwordValue) {
    // Retry avec type() au lieu de fill()
    console.log('[SETUP] Retry avec type()...');
    await tenantInput.clear();
    await tenantInput.type(CREDENTIALS.tenant, { delay: 50 });

    await emailInput.clear();
    await emailInput.type(CREDENTIALS.email, { delay: 50 });

    await passwordInput.clear();
    await passwordInput.type(CREDENTIALS.password, { delay: 50 });
  }

  // Soumettre le formulaire
  console.log('[SETUP] Soumission du formulaire...');
  await submitButton.click();

  // Attendre que l'authentification reussisse
  // On verifie plusieurs indicateurs possibles
  try {
    await Promise.race([
      page.waitForSelector('.azals-unified-header__selector', { timeout: 20000 }),
      page.waitForSelector('button:has-text("Nouvelle saisie")', { timeout: 20000 }),
      page.waitForSelector('[class*="sidebar"]', { timeout: 20000 }),
      page.waitForSelector('[class*="dashboard"]', { timeout: 20000 }),
      page.waitForURL(/\/(cockpit|dashboard|home|app)/, { timeout: 20000 })
    ]);
  } catch {
    // Debug: afficher le contenu de la page en cas d'echec
    const currentUrl = page.url();
    const bodyText = await page.locator('body').textContent();
    console.log(`[SETUP] Echec login. URL: ${currentUrl}`);
    console.log('[SETUP] Contenu page:', bodyText?.substring(0, 800));

    // Verifier s'il y a une erreur affichee
    const errorElement = page.locator('.azals-login__error, .azals-alert--error, [class*="error"]');
    if (await errorElement.isVisible().catch(() => false)) {
      const errorText = await errorElement.textContent();
      console.log(`[SETUP] Erreur affichee: ${errorText}`);
    }

    throw new Error('Login failed - impossible de detecter une session authentifiee');
  }

  console.log('[SETUP] Login reussi, sauvegarde de la session...');

  // Sauvegarder l'etat d'authentification (cookies + localStorage)
  await page.context().storageState({ path: AUTH_FILE });

  console.log(`[SETUP] Session sauvegardee dans ${AUTH_FILE}`);
});
