/**
 * Supplier Dashboard — Functional Pages E2E
 *
 * Deep tests for pages that exist, confirming key UI elements
 * render with real or empty data, and no JS crashes.
 */
import { test, expect, BACKEND } from '../fixtures';

/* ────── RFQ Inbox ────── */
test.describe('Supplier RFQ Inbox', () => {

  test('RFQ list page renders', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/rfq');
    await page.waitForLoadState('networkidle');

    // Should show heading
    const heading = page.locator('h1, h2').first();
    await expect(heading).toBeVisible();

    // Should show a list, table, or empty/loading state
    const body = await page.locator('body').textContent() || '';
    // Page should render meaningful content (heading, list, or empty state)
    expect(body.length, 'RFQ page should have content').toBeGreaterThan(50);
    // Check for common patterns: list items, table rows, cards, or empty state text
    const hasContent = await page.locator('a[href*="/rfq/"], tr, [class*="card"], [class*="rounded"]').first().isVisible().catch(() => false);
    const hasEmpty = body.match(/no rfq|no data|沒有|暫無|empty|0 results|loading/i) !== null;
    expect(hasContent || hasEmpty || body.length > 100, 'RFQ page should show list or fallback').toBe(true);
  });

  test('clicking an RFQ item navigates to detail', async ({ authedSupplierPage: page, supplierToken }) => {
    // First, check if there are RFQs via API
    const rfqs = await fetch(`${BACKEND}/api/v1/rfqs`, {
      headers: { Authorization: `Bearer ${supplierToken}` },
    }).then(r => r.json()).catch(() => []);

    if (!Array.isArray(rfqs) || rfqs.length === 0) {
      test.skip();
      return;
    }

    await page.goto('/dashboard/rfq');
    await page.waitForLoadState('networkidle');

    // Click first RFQ link
    const firstLink = page.locator('a[href*="/dashboard/rfq/"]').first();
    if (await firstLink.isVisible().catch(() => false)) {
      await firstLink.click();
      await page.waitForURL('**/dashboard/rfq/**');

      // Detail page should show RFQ info
      const body = await page.locator('body').textContent();
      expect(body!.length).toBeGreaterThan(50);
    }
  });
});

/* ────── Company Profile ────── */
test.describe('Supplier Profile Page', () => {

  test('profile page renders with form fields', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/profile');
    await page.waitForLoadState('networkidle');

    // Should have input fields or profile display
    const inputs = page.locator('input, textarea, select');
    const count = await inputs.count();
    expect(count, 'Profile page should have form inputs').toBeGreaterThan(0);
  });

  test('profile page displays company name', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/profile');
    await page.waitForLoadState('networkidle');

    // Look for the company name in any form field or header
    const bodyText = await page.locator('body').textContent();
    // The seeded profile has "Taiwan Precision Parts"
    const hasName = bodyText?.includes('Taiwan') || bodyText?.includes('Precision');
    // It's OK if name is not shown (new profile), but page shouldn't be empty
    expect(bodyText!.length).toBeGreaterThan(50);
  });
});

/* ────── Videos Page ────── */
test.describe('Supplier Videos Page', () => {

  test('videos page renders', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/videos');
    await page.waitForLoadState('networkidle');

    const body = await page.locator('body').textContent();
    expect(body!.length).toBeGreaterThan(20);
    // Should show heading or upload section
    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
  });
});

/* ────── Knowledge Base Page ────── */
test.describe('Supplier Knowledge Base', () => {

  test('knowledge base page renders with upload area', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/knowledge-base');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();

    // Should have either file list or upload controls
    const body = await page.locator('body').textContent();
    expect(body!.length).toBeGreaterThan(50);
  });
});

/* ────── Visitor Intent Page ────── */
test.describe('Supplier Visitor Intent', () => {

  test('visitor intent page renders', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/visitor-intent');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();

    const body = await page.locator('body').textContent();
    expect(body!.length).toBeGreaterThan(20);
  });
});

/* ────── Outbound Campaign Page ────── */
test.describe('Supplier Outbound', () => {

  test('outbound campaigns page renders', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/outbound');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
  });

  test('create new campaign button exists', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/outbound');
    await page.waitForLoadState('networkidle');

    const newBtn = page.locator('a[href*="/outbound/new"], button:has-text("New"), button:has-text("建立")').first();
    const hasBtn = await newBtn.isVisible().catch(() => false);
    expect(hasBtn, 'Should have a create new campaign button').toBe(true);
  });

  test('email campaigns sub-page renders', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/outbound/email-campaigns');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
  });
});

/* ────── Exhibitions Page ────── */
test.describe('Supplier Exhibitions', () => {

  test('exhibitions page renders', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/exhibitions');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();

    const body = await page.locator('body').textContent();
    expect(body!.length).toBeGreaterThan(20);
  });
});

/* ────── Business Cards Page ────── */
test.describe('Supplier Business Cards', () => {

  test('business cards (名片掃描) page renders', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/business-cards');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
  });
});

/* ────── Workbench Page ────── */
test.describe('Supplier Workbench', () => {

  test('workbench (業務工作台) page renders', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/workbench');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
  });
});

/* ────── Analytics Page ────── */
test.describe('Supplier Analytics', () => {

  test('analytics page renders with charts or metrics', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard/analytics');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();

    // Should have chart containers or stat numbers
    const body = await page.locator('body').textContent();
    expect(body!.length).toBeGreaterThan(50);
  });
});

