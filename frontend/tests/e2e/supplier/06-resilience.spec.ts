import { test, expect } from '../fixtures'

test.describe('Supplier UI Resilience Scenarios', () => {
  test('Outbound page handles 500 from campaigns endpoint gracefully', async ({ authedSupplierPage: page }) => {
    await page.route('**/api/v1/outbound/campaigns**', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Injected internal error' }),
        })
        return
      }
      await route.continue()
    })

    await page.goto('/dashboard/outbound')
    await page.waitForLoadState('networkidle')

    await expect(page.locator('h1')).toContainText('Outbound')
    const bodyText = (await page.locator('body').textContent()) || ''
    expect(bodyText.length).toBeGreaterThan(30)
  })

  test('Outbound page remains usable when API is slow', async ({ authedSupplierPage: page }) => {
    await page.route('**/api/v1/outbound/campaigns**', async route => {
      if (route.request().method() === 'GET') {
        await page.waitForTimeout(1200)
      }
      await route.continue()
    })

    await page.goto('/dashboard/outbound')
    await expect(page.locator('h1')).toContainText('Outbound')
    await page.waitForLoadState('networkidle')

    const createButton = page.locator('a[href*="/dashboard/outbound/new"]').first()
    await expect(createButton).toBeVisible()
  })

  test('Outbound page handles empty dataset response', async ({ authedSupplierPage: page }) => {
    await page.route('**/api/v1/outbound/campaigns**', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        })
        return
      }
      await route.continue()
    })

    await page.goto('/dashboard/outbound')
    await page.waitForLoadState('networkidle')

    const bodyText = (await page.locator('body').textContent()) || ''
    expect(bodyText.length, 'Outbound page should still render with empty data').toBeGreaterThan(20)
  })
})
