import { test, expect } from '@playwright/test'

const APPS = [
  { name: 'buyer-home', url: 'http://localhost:3004/' },
  { name: 'buyer-suppliers', url: 'http://localhost:3004/suppliers' },
  { name: 'supplier-login', url: 'http://localhost:3001/login' },
  { name: 'admin-home', url: 'http://localhost:3002/' },
]

test.describe('Cross-browser smoke', () => {
  for (const app of APPS) {
    test(`${app.name} renders key shell`, async ({ page }) => {
      await page.goto(app.url)
      await page.waitForLoadState('domcontentloaded')

      const body = page.locator('body')
      await expect(body).toBeVisible()
      const text = (await body.textContent()) || ''
      expect(text.length, `${app.name} should render visible content`).toBeGreaterThan(20)

      const runtimeError = await page
        .locator('text=Unhandled Runtime Error, text=Application error, text=500')
        .first()
        .isVisible()
        .catch(() => false)
      expect(runtimeError, `${app.name} should not crash at shell level`).toBe(false)
    })
  }
})
