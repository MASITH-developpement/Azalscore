/**
 * AZALSCORE - Smoke Tests (Ultra-rapides)
 *
 * Tests minimaux pour validation rapide.
 * Pas d'authentification requise - teste juste que les pages chargent.
 *
 * Usage: npx playwright test --project=smoke
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'https://azalscore.com';

test.describe('Smoke Tests - Health Check', () => {
  test.describe.configure({ mode: 'parallel' });

  test('Page login accessible', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/login`);
    expect(response?.status()).toBeLessThan(500);

    // Formulaire de login present
    await expect(page.locator('#tenant, input[name="tenant"]')).toBeVisible({ timeout: 10000 });
  });

  test('Assets chargent correctement', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Pas d'erreur de chargement critique
    const failedRequests: string[] = [];
    page.on('requestfailed', request => {
      const url = request.url();
      if (url.includes('.js') || url.includes('.css')) {
        failedRequests.push(url);
      }
    });

    await page.waitForLoadState('networkidle');
    expect(failedRequests.length).toBe(0);
  });

  test('Pas d\'erreur console critique', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (text.includes('TypeError') || text.includes('ReferenceError')) {
          errors.push(text);
        }
      }
    });

    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');

    expect(errors.length).toBe(0);
  });

  test('Redirect HTTPS fonctionne', async ({ page }) => {
    // Tester que HTTP redirige vers HTTPS
    if (BASE_URL.startsWith('https://')) {
      const httpUrl = BASE_URL.replace('https://', 'http://');
      await page.goto(httpUrl);
      expect(page.url()).toMatch(/^https:\/\//);
    }
  });
});
