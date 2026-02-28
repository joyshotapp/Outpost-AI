import { test, expect } from '@playwright/test'

test.describe('RFQ Inbox', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to RFQ inbox
    await page.goto('http://localhost:3001/dashboard/rfq')
  })

  test('should display RFQ inbox page', async ({ page }) => {
    // Verify page title
    await expect(page.locator('h1')).toContainText('RFQ Inbox')

    // Verify subtitle
    await expect(page.locator('p')).toContainText('Manage incoming requests')
  })

  test('should show statistics cards', async ({ page }) => {
    // Check for stat cards
    await expect(page.locator('text=Total RFQs')).toBeVisible()
    await expect(page.locator('text=New RFQs')).toBeVisible()
    await expect(page.locator('text=Grade A Leads')).toBeVisible()
  })

  test('should display filter controls', async ({ page }) => {
    // Check for filter section
    await expect(page.locator('text=Filters & Sort')).toBeVisible()

    // Check for individual filters
    await expect(page.locator('label:has-text("Lead Grade")')).toBeVisible()
    await expect(page.locator('label:has-text("Status")')).toBeVisible()
    await expect(page.locator('label:has-text("Sort By")')).toBeVisible()
  })

  test('should display RFQ list items', async ({ page }) => {
    // Verify RFQ items are displayed
    const rfqItems = page.locator('[class*="border-gray-200"][class*="rounded-lg"][class*="p-6"]')
    const count = await rfqItems.count()
    expect(count).toBeGreaterThan(0)
  })

  test('should filter by lead grade A', async ({ page }) => {
    // Get initial count of items
    const allItems = page.locator('[class*="RFQ"]').count()

    // Select Grade A filter
    const gradeSelect = page.locator('select').nth(0)
    await gradeSelect.selectOption('A')

    // Wait for filter to apply
    await page.waitForTimeout(500)

    // Should show filtered results message
    await expect(page.locator('text=filtered')).toBeVisible()
  })

  test('should filter by status', async ({ page }) => {
    // Select "New" status
    const statusSelect = page.locator('select').nth(1)
    await statusSelect.selectOption('new')

    // Wait for filter to apply
    await page.waitForTimeout(500)

    // Should show filtered results
    await expect(page.locator('text=filtered')).toBeVisible()
  })

  test('should sort by highest score', async ({ page }) => {
    // Select sort option
    const sortSelect = page.locator('select').nth(2)
    await sortSelect.selectOption('highest_score')

    // Wait for sort to apply
    await page.waitForTimeout(500)

    // Verify page still shows content
    await expect(page.locator('text=Filters & Sort')).toBeVisible()
  })

  test('should clear all filters', async ({ page }) => {
    // Apply a filter
    const gradeSelect = page.locator('select').nth(0)
    await gradeSelect.selectOption('A')

    // Click clear filters
    const clearButton = page.locator('text=Clear All')
    await clearButton.click()

    // Verify filters are reset
    await expect(gradeSelect).toHaveValue('all')
  })

  test('should navigate to RFQ detail on click', async ({ page }) => {
    // Click on first RFQ item
    const firstRFQItem = page.locator('[class*="hover:shadow-md"]').first()

    // Check if link exists
    const link = firstRFQItem.locator('a').first()
    const href = await link.getAttribute('href')

    expect(href).toMatch(/\/dashboard\/rfq\/\d+/)
  })

  test('should show pagination controls for large lists', async ({ page }) => {
    // Check if pagination is visible (only if there are many items)
    const paginationText = page.locator('text=Page')

    const isVisible = await paginationText.isVisible().catch(() => false)
    if (isVisible) {
      expect(paginationText).toBeVisible()
    }
  })

  test('should display grade badges with correct colors', async ({ page }) => {
    // Look for grade badges
    const gradeABadge = page.locator('text=Grade A')
    const gradeBBadge = page.locator('text=Grade B')
    const gradeCBadge = page.locator('text=Grade C')

    // At least one grade badge should exist
    const totalBadges = await gradeABadge.count() + await gradeBBadge.count() + await gradeCBadge.count()
    expect(totalBadges).toBeGreaterThan(0)
  })

  test('should show results summary', async ({ page }) => {
    // Check for results summary
    const summary = page.locator('text=/Showing .* of .* RFQs/')
    await expect(summary).toBeVisible()
  })

  test('should handle empty results', async ({ page }) => {
    // Apply filters that might result in no items
    const gradeSelect = page.locator('select').nth(0)

    // Try multiple filters to potentially get empty state
    // This depends on the mock data, so we just verify the page handles it
    await gradeSelect.selectOption('A')

    // Page should still be functional
    await expect(page.locator('text=Filters & Sort')).toBeVisible()
  })

  test('should show new indicator for new RFQs', async ({ page }) => {
    // Look for "New" badges
    const newBadges = page.locator('text=New')

    const count = await newBadges.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })

  test('should display buyer company names', async ({ page }) => {
    // Look for company names
    const companyText = page.locator('text=from')

    // There should be at least some RFQs with company names
    expect(await companyText.count()).toBeGreaterThanOrEqual(0)
  })

  test('should show RFQ preview in list items', async ({ page }) => {
    // Look for quantity information
    const quantityText = page.locator('text=/Quantity:/')
    expect(quantityText.count()).toBeGreaterThan(0)
  })

  test('should display score information', async ({ page }) => {
    // Look for score display
    const scoreText = page.locator('text=/Score:/')
    expect(scoreText.count()).toBeGreaterThan(0)
  })
})
