import { defineConfig, devices } from '@playwright/test';

/**
 * Factory Insider — E2E Test Configuration
 *
 * Three apps under test:
 *   Buyer    → http://localhost:3004
 *   Supplier → http://localhost:3001
 *   Admin    → http://localhost:3002
 *   Backend  → http://localhost:8001
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  timeout: 30_000,
  expect: { timeout: 8_000 },
  globalSetup: './tests/e2e/global-setup.ts',
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['list'],
  ],

  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000,
  },

  /* Don't auto-start servers — they are already running */

  projects: [
    /* ── Supplier App ─────────────────────────────────── */
    {
      name: 'supplier',
      testDir: './tests/e2e/supplier',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: 'http://localhost:3001',
      },
    },
    /* ── Admin App ────────────────────────────────────── */
    {
      name: 'admin',
      testDir: './tests/e2e/admin',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: 'http://localhost:3002',
      },
    },
    /* ── Buyer App ────────────────────────────────────── */
    {
      name: 'buyer',
      testDir: './tests/e2e/buyer',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: 'http://localhost:3004',
      },
    },
    /* ── Cross-browser smoke suites ──────────────────── */
    {
      name: 'smoke-firefox',
      testDir: './tests/e2e/smoke',
      testMatch: '**/cross-browser.spec.ts',
      use: {
        ...devices['Desktop Firefox'],
      },
    },
    {
      name: 'smoke-webkit',
      testDir: './tests/e2e/smoke',
      testMatch: '**/cross-browser.spec.ts',
      use: {
        ...devices['Desktop Safari'],
      },
    },
    /* ── Mobile viewport smoke suite ─────────────────── */
    {
      name: 'smoke-mobile',
      testDir: './tests/e2e/smoke',
      testMatch: '**/mobile.spec.ts',
      use: {
        ...devices['Pixel 5'],
      },
    },
    /* ── Accessibility quick scan suite ──────────────── */
    {
      name: 'smoke-a11y',
      testDir: './tests/e2e/smoke',
      testMatch: '**/a11y.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
      },
    },
  ],
});
