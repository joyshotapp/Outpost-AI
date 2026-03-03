import { test, expect } from '@playwright/test'

test.describe('Mobile viewport smoke', () => {
  test('buyer home is usable on mobile', async ({ page }) => {
    await page.goto('http://localhost:3004/')
    await page.waitForLoadState('domcontentloaded')

    await expect(page.locator('body')).toBeVisible()
    const menuOrNav = page.locator('header, nav').first()
    await expect(menuOrNav).toBeVisible()

    const searchInput = page.locator('input[type="text"], input[type="search"]').first()
    await expect(searchInput).toBeVisible()
  })

  test('supplier login is usable on mobile', async ({ page }) => {
    await page.goto('http://localhost:3001/login')
    await page.waitForLoadState('domcontentloaded')

    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
  })

  test('admin home shell loads on mobile viewport', async ({ page }) => {
    await page.goto('http://localhost:3002/')
    await page.waitForLoadState('domcontentloaded')

    const bodyText = (await page.locator('body').textContent()) || ''
    expect(bodyText.length).toBeGreaterThan(20)
  })
})
