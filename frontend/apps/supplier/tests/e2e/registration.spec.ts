import { test, expect } from '@playwright/test'

test.describe('Supplier Registration Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register')
  })

  test('should display registration page with progress bar', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Factory Insider/)

    // Check main heading
    await expect(page.locator('h1')).toContainText('Supplier Registration')

    // Check progress bar exists
    await expect(page.locator('div:has-text("Company Info")')).toBeVisible()
  })

  test('should complete step 1 with company information', async ({ page }) => {
    // Fill in company name
    await page.fill('input[name="companyName"]', 'Test Manufacturing Co.')
    await page.fill('input[name="phone"]', '+86 10 1234 5678')
    await page.fill('input[name="email"]', 'contact@testmfg.com')

    // Select country
    await page.selectOption('select[name="country"]', 'China')

    // Company slug should auto-populate
    const slugValue = await page.inputValue('input[name="companySlug"]')
    expect(slugValue).toBe('test-manufacturing-co.')

    // Click next button
    await page.click('button:has-text("Next")')

    // Should move to step 2
    await expect(page.locator('text=Industry & Certs')).toBeVisible()
  })

  test('should validate required fields on step 1', async ({ page }) => {
    // Try to submit without filling required fields
    await page.click('button:has-text("Next")')

    // Error messages should appear
    await expect(page.locator('text=Company name is required')).toBeVisible()
    await expect(page.locator('text=Email is required')).toBeVisible()
  })

  test('should complete step 2 with industry information', async ({ page }) => {
    // Complete step 1
    await page.fill('input[name="companyName"]', 'Test Manufacturing')
    await page.fill('input[name="phone"]', '+86 10 1234 5678')
    await page.fill('input[name="email"]', 'contact@test.com')
    await page.selectOption('select[name="country"]', 'China')
    await page.fill('input[name="city"]', 'Shanghai')
    await page.click('button:has-text("Next")')

    // Step 2: Select industry
    await page.selectOption('select[name="industry"]', 'Electronics & Computing')

    // Add main products
    await page.fill(
      'textarea[name="mainProducts"]',
      'CNC machining parts, fasteners'
    )

    // Add certifications
    await page.fill('input[placeholder*="Search or enter certification"]', 'ISO')
    await page.click('text=ISO 9001:2015')

    // Click next
    await page.click('button:has-text("Next")')

    // Should move to step 3
    await expect(page.locator('text=Review & Submit')).toBeVisible()
  })

  test('should display review page with all information', async ({ page }) => {
    // Fill and navigate through all steps
    await page.fill('input[name="companyName"]', 'ABC Corporation')
    await page.fill('input[name="phone"]', '+86 10 1234 5678')
    await page.fill('input[name="email"]', 'contact@abc.com')
    await page.selectOption('select[name="country"]', 'China')
    await page.fill('input[name="city"]', 'Shanghai')
    await page.click('button:has-text("Next")')

    await page.selectOption('select[name="industry"]', 'Textiles & Apparel')
    await page.fill('textarea[name="mainProducts"]', 'Cotton fabrics')
    await page.click('button:has-text("Next")')

    // Verify review page shows company name
    await expect(page.locator('text=ABC Corporation')).toBeVisible()
    await expect(page.locator('text=Shanghai')).toBeVisible()
  })

  test('should successfully submit registration', async ({ page }) => {
    // Fill all steps
    await page.fill('input[name="companyName"]', 'Success Test Company')
    await page.fill('input[name="phone"]', '+86 10 9999 8888')
    await page.fill('input[name="email"]', 'success@test.com')
    await page.selectOption('select[name="country"]', 'China')
    await page.fill('input[name="city"]', 'Beijing')
    await page.click('button:has-text("Next")')

    await page.selectOption('select[name="industry"]', 'Machinery & Equipment')
    await page.fill('textarea[name="mainProducts"]', 'Industrial machinery')
    await page.click('button:has-text("Next")')

    // Agree to terms
    const termsCheckbox = page.locator('input[type="checkbox"]').first()
    await termsCheckbox.check()

    // Submit
    await page.click('button:has-text("Submit Registration")')

    // Wait for success page
    await page.waitForURL('**/register/success')
    await expect(page.locator('text=Registration Successful')).toBeVisible()
  })

  test('should navigate back using previous button', async ({ page }) => {
    // Go to step 2
    await page.fill('input[name="companyName"]', 'Test')
    await page.fill('input[name="phone"]', '+86 10 1234 5678')
    await page.fill('input[name="email"]', 'test@test.com')
    await page.selectOption('select[name="country"]', 'China')
    await page.fill('input[name="city"]', 'Shanghai')
    await page.click('button:has-text("Next")')

    // Go back
    await page.click('button:has-text("Previous")')

    // Should be back on step 1
    await expect(page.locator('input[name="companyName"]')).toHaveValue('Test')
  })
})
