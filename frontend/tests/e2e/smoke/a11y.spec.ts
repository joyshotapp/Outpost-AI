import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

const targets = [
  { name: 'buyer-home', url: 'http://localhost:3004/' },
  { name: 'supplier-login', url: 'http://localhost:3001/login' },
  { name: 'admin-home', url: 'http://localhost:3002/' },
]

test.describe('Accessibility quick scan (axe)', () => {
  for (const target of targets) {
    test(`${target.name} has no critical accessibility violations`, async ({ page }) => {
      await page.goto(target.url)
      await page.waitForLoadState('domcontentloaded')

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze()

      const critical = results.violations.filter(v => v.impact === 'critical')
      expect(critical, `${target.name} should have 0 critical a11y issues`).toEqual([])
    })
  }
})
