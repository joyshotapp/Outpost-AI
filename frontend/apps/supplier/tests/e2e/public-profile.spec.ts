import { test, expect } from '@playwright/test'

test.describe('Public Supplier Profile', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/suppliers/abc-manufacturing')
  })

  test('should display supplier profile header', async ({ page }) => {
    // Check company name
    await expect(page.locator('h1:has-text("ABC Manufacturing")')).toBeVisible()

    // Check verified badge
    await expect(page.locator('text=Verified')).toBeVisible()

    // Check main products
    await expect(
      page.locator('text=Mechanical parts, CNC machining, fasteners')
    ).toBeVisible()
  })

  test('should display contact statistics', async ({ page }) => {
    // Check profile views
    await expect(page.locator('text=Profile Views')).toBeVisible()
    await expect(page.locator('text=1234')).toBeVisible()

    // Check response rate
    await expect(page.locator('text=Response Rate')).toBeVisible()
    await expect(page.locator('text=92%')).toBeVisible()

    // Check response time
    await expect(page.locator('text=Avg Response')).toBeVisible()
    await expect(page.locator('text=2 hours')).toBeVisible()
  })

  test('should display send inquiry button', async ({ page }) => {
    const inquiryButton = page.locator('button:has-text("Send Inquiry")')
    await expect(inquiryButton).toBeVisible()
  })

  test('should display overview tab content', async ({ page }) => {
    // Check about section
    await expect(page.locator('text=About ABC Manufacturing')).toBeVisible()

    // Check company information grid
    await expect(page.locator('text=Electronics & Computing')).toBeVisible()
    await expect(page.locator('text=2010')).toBeVisible()
    await expect(page.locator('text=51-100')).toBeVisible()

    // Check certifications
    await expect(page.locator('text=ISO 9001:2015')).toBeVisible()
  })

  test('should display contact information in sidebar', async ({ page }) => {
    // Check email
    const emailLink = page.locator('a[href="mailto:contact@abc-mfg.com"]')
    await expect(emailLink).toBeVisible()

    // Check phone
    const phoneLink = page.locator('a[href^="tel:"]')
    await expect(phoneLink).toBeVisible()

    // Check website link
    await expect(page.locator('a:has-text("Visit Website")')).toBeVisible()
  })

  test('should display supplier ratings in sidebar', async ({ page }) => {
    // Check rating title
    await expect(page.locator('text=Supplier Rating')).toBeVisible()

    // Check quality rating
    await expect(page.locator('text=Quality')).toBeVisible()
    await expect(page.locator('text=4.8/5')).toBeVisible()

    // Check reliability rating
    await expect(page.locator('text=Reliability')).toBeVisible()
    await expect(page.locator('text=4.9/5')).toBeVisible()
  })

  test('should switch between tabs', async ({ page }) => {
    // Click on Videos tab
    await page.click('button:has-text("Videos")')
    await expect(page.locator('text=Product Videos')).toBeVisible()

    // Click on Products tab
    await page.click('button:has-text("Products & Services")')
    await expect(page.locator('text=Products & Services')).toBeVisible()

    // Click on Reviews tab
    await page.click('button:has-text("Reviews")')
    await expect(page.locator('text=Customer Reviews')).toBeVisible()
  })

  test('should display product videos on videos tab', async ({ page }) => {
    // Switch to videos tab
    await page.click('button:has-text("Videos")')

    // Check for video titles
    await expect(page.locator('text=Company Overview')).toBeVisible()
    await expect(page.locator('text=CNC Machining Process')).toBeVisible()
    await expect(page.locator('text=Quality Control')).toBeVisible()
  })

  test('should display customer reviews on reviews tab', async ({ page }) => {
    // Switch to reviews tab
    await page.click('button:has-text("Reviews")')

    // Check for review element
    await expect(page.locator('text=Verified Purchase')).toBeVisible()
    await expect(
      page.locator('text=Great quality products and fast shipping')
    ).toBeVisible()
  })

  test('should be responsive on mobile', async ({ page }) => {
    // Resize to mobile
    await page.setViewportSize({ width: 375, height: 812 })

    // Verify key elements still visible
    await expect(page.locator('h1:has-text("ABC Manufacturing")')).toBeVisible()
    await expect(page.locator('button:has-text("Send Inquiry")')).toBeVisible()

    // Check that layout adjusted properly
    await expect(page.locator('text=Profile Views')).toBeVisible()
  })

  test('should have proper link functionality', async ({ page, context }) => {
    // Create new page to track navigation
    const [popup] = await Promise.all([
      context.waitForEvent('page'),
      page.click('a:has-text("Visit Website")'),
    ])

    // Verify popup opened (would be actual website in production)
    // In test environment, just verify the action was triggered
  })
})
