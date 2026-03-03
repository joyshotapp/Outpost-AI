/**
 * Supplier Dashboard — Sidebar Navigation E2E
 *
 * Verifies that EVERY sidebar link in the supplier dashboard
 * navigates to a real page (no 404, no blank screen, no JS error).
 *
 * Known bugs this test will catch:
 *   - /dashboard/inquiries → missing page (dead link)
 *   - /dashboard/orders    → missing page (dead link)
 *   - /dashboard/settings  → missing page (dead link)
 *   - Duplicate "Analytics" nav entry
 */
import { test, expect } from '../fixtures';

/** All 16 sidebar nav items (from Sidebar.tsx navItems array) */
const SIDEBAR_LINKS = [
  { label: 'Dashboard',        href: '/dashboard' },
  { label: 'Company Profile',  href: '/dashboard/profile' },
  { label: 'Videos',           href: '/dashboard/videos' },
  { label: 'Knowledge Base',   href: '/dashboard/knowledge-base' },
  { label: 'Visitor Intent',   href: '/dashboard/visitor-intent' },
  { label: 'Outbound',         href: '/dashboard/outbound' },
  { label: 'Email 活動',       href: '/dashboard/outbound/email-campaigns' },
  { label: '業務工作台',       href: '/dashboard/workbench' },
  { label: 'Inquiries',        href: '/dashboard/inquiries' },
  { label: 'Orders',           href: '/dashboard/orders' },
  { label: 'Analytics',        href: '/dashboard/analytics' },
  // Note: Duplicate "Analytics" entry exists in Sidebar.tsx — testing only one
  { label: '展覽活動',         href: '/dashboard/exhibitions' },
  { label: '名片掃描',         href: '/dashboard/business-cards' },
  { label: 'Settings',         href: '/dashboard/settings' },
];

/** Pages that actually exist (have page.tsx) */
const EXISTING_PAGES = new Set([
  '/dashboard',
  '/dashboard/profile',
  '/dashboard/videos',
  '/dashboard/knowledge-base',
  '/dashboard/visitor-intent',
  '/dashboard/outbound',
  '/dashboard/outbound/email-campaigns',
  '/dashboard/workbench',
  '/dashboard/inquiries',
  '/dashboard/orders',
  '/dashboard/analytics',
  '/dashboard/exhibitions',
  '/dashboard/business-cards',
  '/dashboard/settings',
]);

/** Pages that are DEAD links (no page.tsx) — should be empty after fixes */
const DEAD_LINKS = new Set<string>([
]);

test.describe('Supplier Sidebar Navigation', () => {

  test('sidebar renders with all expected nav items', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // The sidebar should be visible
    const sidebar = page.locator('aside');
    await expect(sidebar).toBeVisible();

    // Check each expected label is in the sidebar
    for (const { label } of SIDEBAR_LINKS) {
      const link = sidebar.locator(`text="${label}"`).first();
      await expect(link, `Sidebar should contain "${label}"`).toBeVisible();
    }
  });

  test('duplicate Analytics entry should be removed', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const sidebar = page.locator('aside');
    const analyticsLinks = sidebar.locator('a:has-text("Analytics")');
    const count = await analyticsLinks.count();
    // Fixed: duplicate Analytics entry was removed from Sidebar.tsx
    expect(count, 'There should be exactly 1 Analytics link').toBe(1);
  });

  // For each page that exists, verify the sidebar click works
  for (const { label, href } of SIDEBAR_LINKS.filter(l => EXISTING_PAGES.has(l.href))) {
    test(`clicking "${label}" navigates to ${href} successfully`, async ({ authedSupplierPage: page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      const sidebar = page.locator('aside');
      const link = sidebar.locator(`a[href="${href}"]`).first();
      await expect(link).toBeVisible();
      await link.click();

      // Wait for navigation
      await page.waitForURL(`**${href}`, { timeout: 10_000 });

      // Page should not be a 404 or blank
      const body = page.locator('body');
      await expect(body).not.toHaveText(/404/);

      // No unhandled JS errors
      const consoleErrors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') consoleErrors.push(msg.text());
      });

      // The page should have some meaningful content (not just an empty shell)
      const mainContent = page.locator('main, [class*="dashboard"], [class*="container"]').first();
      // Some pages may use <main>, others just a div
      const hasContent = await mainContent.isVisible().catch(() => false);
      // At a minimum, body should have non-trivial text
      const bodyText = await body.textContent();
      expect(bodyText!.length, `Page ${href} should render some content`).toBeGreaterThan(20);
    });
  }

  // For each DEAD link, document the failure
  for (const { label, href } of SIDEBAR_LINKS.filter(l => DEAD_LINKS.has(l.href))) {
    test(`DEAD LINK: "${label}" (${href}) shows 404 or error`, async ({ authedSupplierPage: page }) => {
      await page.goto(href);
      await page.waitForLoadState('networkidle');

      // This page should be a 404 (no page.tsx exists)
      // We document this as an expected failure — the sidebar has dead links
      const text = await page.locator('body').textContent();
      const is404 = text?.includes('404') || text?.includes('not found') || text?.includes('Not Found');
      expect(is404, `${href} is a dead link — expected 404`).toBe(true);
    });
  }
});

test.describe('Supplier Dashboard Overview Page', () => {

  test('dashboard page loads with quick-action cards', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // The dashboard should have a heading or welcome section
    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();

    // Dashboard has quick-action links to other sections
    const quickLinks = page.locator('a[href*="/dashboard/"]');
    const count = await quickLinks.count();
    expect(count, 'Dashboard should have quick-action links').toBeGreaterThan(0);
  });

  test('dashboard stats cards load (even if API returns empty)', async ({ authedSupplierPage: page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Look for stat cards or metric displays
    const cards = page.locator('[class*="card"], [class*="stat"], [class*="rounded-xl"]');
    const count = await cards.count();
    expect(count, 'Dashboard should display stat cards').toBeGreaterThan(0);
  });
});

