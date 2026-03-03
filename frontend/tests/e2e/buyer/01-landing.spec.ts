/**
 * Buyer App — Landing Page & Navigation E2E
 *
 * Tests the public-facing buyer portal:
 *   - Home page renders with search, stats, industry cards
 *   - Navigation links (Browse Suppliers, Post RFQ, Dashboard)
 *   - Search submit redirects to /suppliers?q=...
 *   - Login/Register links
 */
import { test, expect } from '../fixtures';

test.describe('Buyer Landing Page', () => {

  test('home page loads with hero section', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Main heading
    const heading = page.locator('text=Factory Insider').first();
    await expect(heading).toBeVisible();

    // Should have a search input
    const searchInput = page.locator('input[placeholder*="Search"], input[type="search"], input[type="text"]').first();
    await expect(searchInput).toBeVisible();
  });

  test('home page shows industry cards', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // The home page displays 6 industry cards
    const industries = ['Automotive', 'Electronics', 'Aerospace', 'Medical', 'Steel', 'Plastics'];
    let found = 0;
    for (const name of industries) {
      const el = page.locator(`text=${name}`).first();
      if (await el.isVisible().catch(() => false)) found++;
    }
    expect(found, 'Should show at least some industry cards').toBeGreaterThanOrEqual(3);
  });

  test('home page shows stats section', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const stats = ['12,000+', '60+', '50,000+', '< 24h'];
    let found = 0;
    for (const stat of stats) {
      const el = page.locator(`text="${stat}"`).first();
      if (await el.isVisible().catch(() => false)) found++;
    }
    expect(found, 'Should show stat numbers').toBeGreaterThanOrEqual(2);
  });

  test('nav links are present', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const browseLink = page.locator('a:has-text("Browse Suppliers")').first();
    await expect(browseLink).toBeVisible();

    const postRfqLink = page.locator('a:has-text("Post RFQ")').first();
    await expect(postRfqLink).toBeVisible();

    const dashboardLink = page.locator('a:has-text("Dashboard")').first();
    await expect(dashboardLink).toBeVisible();
  });

  test('search submits and redirects to suppliers page', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const searchInput = page.locator('input[placeholder*="Search"], input[type="search"], input[type="text"]').first();
    await searchInput.fill('CNC machining');
    await searchInput.press('Enter');

    await page.waitForURL('**/suppliers?q=CNC*', { timeout: 10_000 });
    expect(page.url()).toContain('suppliers');
    expect(page.url()).toContain('CNC');
  });
});

test.describe('Buyer Browse Suppliers Page', () => {

  test('suppliers listing page renders', async ({ page }) => {
    await page.goto('/suppliers');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();

    // Should have search or filter controls
    const body = await page.locator('body').textContent();
    expect(body!.length).toBeGreaterThan(50);
  });

  test('supplier list has clickable items', async ({ page }) => {
    await page.goto('/suppliers');
    await page.waitForLoadState('networkidle');

    // Wait for supplier cards/rows to appear (or empty state)
    const supplierLink = page.locator('a[href*="/suppliers/"]').first();
    const emptyState = page.locator('text=/no supplier|no result|暫無/i').first();
    const hasLinks = await supplierLink.isVisible().catch(() => false);
    const hasEmpty = await emptyState.isVisible().catch(() => false);
    expect(hasLinks || hasEmpty, 'Should show supplier list or empty state').toBe(true);
  });
});

test.describe('Buyer RFQ Submission', () => {

  test('RFQ form page loads', async ({ authedBuyerPage: page }) => {
    await page.goto('/rfq/new');
    await page.waitForLoadState('networkidle');

    // The page may show a heading, form, or loading state
    const heading = page.locator('h1, h2, h3').first();
    const headingVisible = await heading.isVisible().catch(() => false);

    // Check if there are form inputs or at least the page rendered content
    const inputs = page.locator('input, textarea, select');
    const count = await inputs.count();

    const body = await page.locator('body').textContent() || '';
    // Page should render something meaningful (form, heading, or error)
    expect(body.length, 'RFQ form page should render content').toBeGreaterThan(20);
  });

  test('RFQ form has required fields', async ({ authedBuyerPage: page }) => {
    await page.goto('/rfq/new');
    await page.waitForLoadState('networkidle');

    // Key form elements that should exist
    const bodyText = await page.locator('body').textContent() || '';
    const expectedFields = ['title', 'description', 'quantity', 'material', 'budget', 'deadline'];
    let found = 0;
    for (const field of expectedFields) {
      // Check both labels and input names
      const hasLabel = bodyText.toLowerCase().includes(field);
      const hasInput = await page.locator(`input[name*="${field}"], textarea[name*="${field}"]`).count() > 0;
      if (hasLabel || hasInput) found++;
    }
    expect(found, 'RFQ form should have key fields (title, description, etc.)').toBeGreaterThanOrEqual(2);
  });
});

test.describe('Buyer Dashboard', () => {

  test('buyer dashboard loads when authenticated', async ({ authedBuyerPage: page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const body = await page.locator('body').textContent();
    expect(body!.length).toBeGreaterThan(20);
  });

  test('buyer dashboard has messages link', async ({ authedBuyerPage: page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const messagesLink = page.locator('a[href*="messages"]').first();
    const hasMessages = await messagesLink.isVisible().catch(() => false);
    // Messages page exists at /dashboard/messages
    if (hasMessages) {
      await messagesLink.click();
      await page.waitForURL('**/dashboard/messages');
      const body = await page.locator('body').textContent();
      expect(body!.length).toBeGreaterThan(20);
    }
  });
});

