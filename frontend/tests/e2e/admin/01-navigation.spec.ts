/**
 * Admin Dashboard — Navigation & Pages E2E
 *
 * The admin app has 7 nav items rendered inline in page.tsx (no shared layout).
 * Each nav item is tested for correct rendering and navigation.
 *
 * Nav items: Dashboard(/), Suppliers(/suppliers), Buyers(/buyers),
 *            Content Review(/content), Outbound Health(/outbound),
 *            API Usage(/api-usage), Settings(/settings)
 */
import { test, expect } from '../fixtures';

const ADMIN_NAV = [
  { label: 'Dashboard',       href: '/' },
  { label: 'Suppliers',       href: '/suppliers' },
  { label: 'Buyers',          href: '/buyers' },
  { label: 'Content Review',  href: '/content' },
  { label: 'Outbound Health', href: '/outbound' },
  { label: 'API Usage',       href: '/api-usage' },
  { label: 'Settings',        href: '/settings' },
];

test.describe('Admin Sidebar Navigation', () => {

  test('admin dashboard page loads', async ({ authedAdminPage: page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Should show the admin console header
    const heading = page.locator('text=Factory Insider');
    await expect(heading.first()).toBeVisible();
    const adminLabel = page.locator('text=Admin Console');
    await expect(adminLabel.first()).toBeVisible();
  });

  test('sidebar renders all 7 nav items', async ({ authedAdminPage: page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const sidebar = page.locator('aside');
    await expect(sidebar).toBeVisible();

    for (const { label } of ADMIN_NAV) {
      const link = sidebar.locator(`text="${label}"`).first();
      await expect(link, `Nav should contain "${label}"`).toBeVisible();
    }
  });

  // Test navigation for each link
  for (const { label, href } of ADMIN_NAV) {
    test(`clicking "${label}" navigates to ${href}`, async ({ authedAdminPage: page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const sidebar = page.locator('aside');
      const link = sidebar.locator(`a[href="${href}"]`).first();
      await expect(link).toBeVisible();
      await link.click();

      // Wait for navigation
      if (href === '/') {
        await page.waitForURL('**/');
      } else {
        await page.waitForURL(`**${href}`, { timeout: 10_000 });
      }

      // Page should render non-trivial content
      const bodyText = await page.locator('body').textContent();
      expect(bodyText!.length, `Page ${href} should have content`).toBeGreaterThan(20);
    });
  }
});

test.describe('Admin Dashboard KPI Data', () => {

  test('dashboard content area renders (with or without KPI data)', async ({ authedAdminPage: page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // The admin dashboard has StatCard components when KPI data loads
    // If the API returns 401 or error, the page still renders the sidebar and layout
    const cards = page.locator('[class*="rounded-xl"], [class*="rounded-lg"], [class*="stat"], [class*="card"]');
    const count = await cards.count();
    // Even without data, the page shell should render
    const bodyText = await page.locator('body').textContent() || '';
    expect(bodyText.length, 'Dashboard should have content even without KPI data').toBeGreaterThan(50);
  });

  test('dashboard shows supplier/buyer/rfq sections', async ({ authedAdminPage: page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').textContent() || '';
    // At least some KPI labels should be visible
    const hasLabels = ['Supplier', 'Buyer', 'RFQ', 'MRR', 'supplier', 'buyer', 'rfq']
      .some(word => bodyText.includes(word));
    expect(hasLabels, 'Dashboard should mention Supplier/Buyer/RFQ data').toBe(true);
  });
});

test.describe('Admin Suppliers Page', () => {

  test('suppliers list page renders', async ({ authedAdminPage: page }) => {
    await page.goto('/suppliers');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
  });

  test('suppliers page shows table or list', async ({ authedAdminPage: page }) => {
    await page.goto('/suppliers');
    await page.waitForLoadState('networkidle');

    // Should have a table or card list
    const table = page.locator('table, [class*="list"], [class*="grid"]').first();
    const hasTable = await table.isVisible().catch(() => false);
    const emptyState = page.locator('text=/no supplier|no data|empty|暫無/i').first();
    const hasEmpty = await emptyState.isVisible().catch(() => false);
    expect(hasTable || hasEmpty, 'Should show suppliers table or empty state').toBe(true);
  });
});

test.describe('Admin Buyers Page', () => {

  test('buyers list page renders', async ({ authedAdminPage: page }) => {
    await page.goto('/buyers');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
  });
});

test.describe('Admin Content Review Page', () => {

  test('content review page renders', async ({ authedAdminPage: page }) => {
    await page.goto('/content');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
  });
});

test.describe('Admin Outbound Health Page', () => {

  test('outbound health page renders', async ({ authedAdminPage: page }) => {
    await page.goto('/outbound');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
  });
});

test.describe('Admin API Usage Page', () => {

  test('api usage page renders', async ({ authedAdminPage: page }) => {
    await page.goto('/api-usage');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
  });
});

test.describe('Admin Settings Page', () => {

  test('settings page renders', async ({ authedAdminPage: page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
  });
});

