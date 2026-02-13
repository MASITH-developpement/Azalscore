/**
 * AZALSCORE - Configuration Playwright E2E Tests (Optimisee)
 *
 * Optimisations:
 * - Setup projet pour auth unique
 * - storageState pour persistance session
 * - Timeouts ajustes
 * - Parallelisation maximale
 */

import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// ES Module compatibility
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Chemins
const AUTH_FILE = join(__dirname, 'e2e/.auth/user.json');

// URL de base
const BASE_URL = process.env.BASE_URL || 'https://azalscore.com';
const IS_CI = !!process.env.CI;
const IS_PRODUCTION = BASE_URL.includes('azalscore.com');

export default defineConfig({
  testDir: './e2e',

  // Parallelisation
  fullyParallel: true,
  workers: IS_CI ? 2 : 4,  // Plus de workers en local

  // Retries
  retries: IS_CI ? 2 : 0,  // Pas de retry en local pour feedback rapide
  forbidOnly: IS_CI,

  // Timeouts optimises
  timeout: IS_PRODUCTION ? 45000 : 30000,  // Plus long pour prod (latence reseau)
  expect: {
    timeout: IS_PRODUCTION ? 8000 : 5000,
  },

  // Reporters
  reporter: IS_CI
    ? [['github'], ['html', { open: 'never' }], ['json', { outputFile: 'playwright-report/results.json' }]]
    : [['list'], ['html', { open: 'on-failure' }]],

  // Options globales
  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: IS_CI ? 'retain-on-failure' : 'off',
    headless: true,

    // Optimisations reseau
    actionTimeout: 10000,
    navigationTimeout: 20000,

    // Viewport standard
    viewport: { width: 1280, height: 720 },
  },

  // Projets avec setup auth
  projects: [
    // Setup: Login une seule fois
    {
      name: 'setup',
      testMatch: /global\.setup\.ts/,
      teardown: 'cleanup',
    },

    // Cleanup: Nettoyer apres
    {
      name: 'cleanup',
      testMatch: /global\.teardown\.ts/,
    },

    // Tests principaux (Chromium) - dependant du setup
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: AUTH_FILE,
      },
      dependencies: ['setup'],
    },

    // Tests rapides smoke (sans auth) - pour CI rapide
    {
      name: 'smoke',
      testMatch: /smoke\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },

    // Firefox (optionnel, CI seulement)
    ...(IS_CI ? [{
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        storageState: AUTH_FILE,
      },
      dependencies: ['setup'],
    }] : []),

    // Mobile (optionnel)
    {
      name: 'mobile',
      testMatch: /mobile\.spec\.ts/,
      use: {
        ...devices['iPhone 13'],
        storageState: AUTH_FILE,
      },
      dependencies: ['setup'],
    },
  ],

  // Serveur de dev (local seulement)
  webServer: (IS_PRODUCTION || process.env.SKIP_WEBSERVER) ? undefined : {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
    timeout: 60000,
  },

  // Output
  outputDir: 'test-results',
});
