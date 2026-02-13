/**
 * AZALSCORE - E2E Test Helpers
 *
 * Fonctions utilitaires optimisees pour les tests E2E.
 * Evite les waitForTimeout en faveur de vraies conditions.
 */

import { type Page, type Locator, expect } from '@playwright/test';

// Timeouts optimises
export const TIMEOUTS = {
  short: 2000,
  medium: 5000,
  long: 10000,
  spinner: 6000
};

// Selecteurs AZALSCORE
export const SELECTORS = {
  // Loading states
  loadingState: '.azals-state--loading',
  errorState: '.azals-state--error',
  emptyState: '.azals-state--empty',
  spinner: '.azals-spinner, .animate-spin, .azals-app-init__spinner',

  // Header
  header: '.azals-unified-header',
  moduleSelector: '.azals-unified-header__selector',
  moduleDropdown: '.azals-unified-header__dropdown',
  moduleItem: '.azals-unified-header__item',

  // Common UI
  table: 'table, [class*="table"], [class*="data-grid"]',
  card: '[class*="card"]',
  form: 'form',
  modal: '[role="dialog"], .modal, [class*="dialog"]',
  pagination: '[class*="pagination"], [class*="pager"]',

  // Buttons
  createBtn: 'button:has-text("Nouveau"), button:has-text("Créer"), button:has-text("Ajouter")',
  submitBtn: 'button[type="submit"], button:has-text("Enregistrer"), button:has-text("Valider")',
  cancelBtn: 'button:has-text("Annuler"), button:has-text("Fermer")',
};

/**
 * Attend que les spinners disparaissent (smart wait)
 */
export async function waitForLoadingComplete(page: Page, timeout = TIMEOUTS.spinner): Promise<void> {
  // Attendre que TOUS les indicateurs de chargement disparaissent
  await Promise.all([
    page.locator(SELECTORS.loadingState).waitFor({ state: 'hidden', timeout }).catch(() => {}),
    page.locator(SELECTORS.spinner).first().waitFor({ state: 'hidden', timeout }).catch(() => {})
  ]);
}

/**
 * Attend qu'un contenu significatif soit visible
 */
export async function waitForContent(page: Page, timeout = TIMEOUTS.medium): Promise<void> {
  // Attendre soit une table, soit des cards, soit un etat (error/empty)
  await page.locator(`${SELECTORS.table}, ${SELECTORS.card}, ${SELECTORS.errorState}, ${SELECTORS.emptyState}`).first().waitFor({ state: 'visible', timeout }).catch(() => {});
}

/**
 * Verifie qu'aucun spinner n'est actif apres le timeout
 */
export async function assertNoActiveSpinners(page: Page, context: string): Promise<void> {
  await waitForLoadingComplete(page);

  // Verifier chaque type de spinner
  const spinnerTypes = [
    { selector: SELECTORS.loadingState, name: 'LoadingState' },
    { selector: '.azals-app-init__spinner', name: 'InitSpinner' },
    { selector: '.azals-spinner', name: 'BareSpinner' },
    { selector: '.animate-spin', name: 'TailwindSpin' }
  ];

  for (const { selector, name } of spinnerTypes) {
    const isVisible = await page.locator(selector).first().isVisible().catch(() => false);
    expect(isVisible, `${name} encore actif sur [${context}]`).toBe(false);
  }
}

/**
 * Verifie qu'on n'a pas d'erreur 404 ou page blanche
 */
export async function assertNoPageError(page: Page, context: string): Promise<void> {
  const bodyText = await page.locator('body').textContent() || '';

  // Pas de 404
  expect(bodyText, `Page 404 sur [${context}]`).not.toMatch(/erreur\s*404|page\s*non\s*trouvée/i);

  // Contenu minimum
  expect(bodyText.length, `Page vide sur [${context}]`).toBeGreaterThan(100);
}

/**
 * Navigue vers un module et attend le chargement
 */
export async function navigateToModule(page: Page, route: string): Promise<void> {
  const baseURL = process.env.BASE_URL || 'https://azalscore.com';
  await page.goto(`${baseURL}${route}`);
  await waitForLoadingComplete(page);
  await waitForContent(page);
}

/**
 * Navigue via le dropdown du header
 */
export async function navigateViaHeader(page: Page, menuLabel: string): Promise<void> {
  // Ouvrir le dropdown
  await page.click(SELECTORS.moduleSelector);
  await page.waitForSelector(SELECTORS.moduleDropdown, { timeout: TIMEOUTS.short });

  // Cliquer sur l'item
  await page.click(`${SELECTORS.moduleItem}:has-text("${menuLabel}")`);

  // Attendre fermeture et chargement
  await page.locator(SELECTORS.moduleDropdown).waitFor({ state: 'hidden', timeout: TIMEOUTS.short }).catch(() => {});
  await waitForLoadingComplete(page);
}

/**
 * Ouvre un formulaire de creation
 */
export async function openCreateForm(page: Page): Promise<boolean> {
  const createBtn = page.locator(SELECTORS.createBtn).first();

  if (await createBtn.isVisible({ timeout: TIMEOUTS.short })) {
    await createBtn.click();
    const hasForm = await page.locator(`${SELECTORS.form}, ${SELECTORS.modal}`).first().isVisible({ timeout: TIMEOUTS.short });
    return hasForm;
  }
  return false;
}

/**
 * Ferme un modal/dialog
 */
export async function closeModal(page: Page): Promise<void> {
  const modal = page.locator(SELECTORS.modal).first();

  if (await modal.isVisible({ timeout: TIMEOUTS.short })) {
    // Essayer le bouton fermer
    const closeBtn = modal.locator('button[aria-label*="close"], button:has-text("×"), button:has-text("Fermer")').first();

    if (await closeBtn.isVisible()) {
      await closeBtn.click();
    } else {
      await page.keyboard.press('Escape');
    }

    await modal.waitFor({ state: 'hidden', timeout: TIMEOUTS.short }).catch(() => {});
  }
}

/**
 * Collecte les erreurs console critiques
 */
export function setupConsoleErrorCollector(page: Page): string[] {
  const errors: string[] = [];

  page.on('console', msg => {
    if (msg.type() === 'error') {
      const text = msg.text();
      // Ignorer les erreurs non critiques
      if (!text.includes('favicon') &&
          !text.includes('manifest') &&
          !text.includes('Failed to load resource')) {
        errors.push(text);
      }
    }
  });

  return errors;
}

/**
 * Filtre les erreurs critiques
 */
export function getCriticalErrors(errors: string[]): string[] {
  return errors.filter(e =>
    e.includes('Uncaught') ||
    e.includes('TypeError') ||
    e.includes('ReferenceError') ||
    e.includes('SyntaxError')
  );
}
