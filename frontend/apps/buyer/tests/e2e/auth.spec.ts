import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('user can register and login', async ({ page }) => {
    // Navigate to registration page
    await page.goto('/');
    await page.click('a:has-text("Register")');

    // Register new user
    await page.fill('input[type="email"]', `test-${Date.now()}@example.com`);
    await page.fill('input[type="password"]', 'SecurePassword123!');
    await page.fill('input[name="fullName"]', 'Test User');
    await page.selectOption('select[name="role"]', 'buyer');

    // Submit registration
    await page.click('button:has-text("Register")');

    // Verify redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('text=Welcome')).toBeVisible();
  });

  test('user can login with existing credentials', async ({ page, context }) => {
    // Create API context for authentication
    const apiContext = await context.request.newContext();

    // Login via API to get tokens
    const response = await apiContext.post('/api/v1/auth/login', {
      data: {
        email: 'buyer@example.com',
        password: 'password123'
      }
    });

    const { access_token } = await response.json();

    // Navigate to dashboard with token
    await page.goto('/', {
      extraHTTPHeaders: {
        'Authorization': `Bearer ${access_token}`
      }
    });

    // Verify authenticated
    await expect(page.locator('text=Dashboard')).toBeVisible();
  });

  test('invalid credentials show error', async ({ page }) => {
    await page.goto('/');
    await page.click('a:has-text("Login")');

    // Enter invalid credentials
    await page.fill('input[type="email"]', 'invalid@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');

    // Submit
    await page.click('button:has-text("Login")');

    // Verify error message
    await expect(page.locator('text=Invalid email or password')).toBeVisible();
  });
});

test.describe('RFQ Workflow', () => {
  test.beforeEach(async ({ page, context }) => {
    // Login before each test
    const apiContext = await context.request.newContext();
    const response = await apiContext.post('/api/v1/auth/login', {
      data: {
        email: 'buyer@example.com',
        password: 'password123'
      }
    });

    const { access_token } = await response.json();

    await page.goto('/', {
      extraHTTPHeaders: {
        'Authorization': `Bearer ${access_token}`
      }
    });
  });

  test('buyer can submit RFQ', async ({ page }) => {
    // Navigate to RFQ creation
    await page.click('a:has-text("Create RFQ")');

    // Fill RFQ form
    await page.fill('input[name="title"]', 'Aluminum Brackets');
    await page.fill('textarea[name="description"]', 'Need 1000 units of aluminum brackets');
    await page.fill('input[name="quantity"]', '1000');
    await page.selectOption('select[name="unit"]', 'pcs');
    await page.fill('input[name="deliveryDate"]', '2026-04-28');

    // Submit
    await page.click('button:has-text("Submit RFQ")');

    // Verify RFQ created
    await expect(page).toHaveURL(/\/rfq\/\d+/);
    await expect(page.locator('text=RFQ Created Successfully')).toBeVisible();
  });

  test('buyer can view RFQ responses', async ({ page }) => {
    // Navigate to RFQs
    await page.click('a:has-text("My RFQs")');

    // Click on first RFQ
    await page.click('tr:first-child a:has-text("View")');

    // Verify responses are shown
    await expect(page.locator('text=Responses')).toBeVisible();
    await expect(page.locator('text=Total Suppliers')).toBeVisible();
  });
});
