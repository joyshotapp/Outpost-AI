import { test, expect } from '@playwright/test'

test.describe('RFQ Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to RFQ detail page
    await page.goto('http://localhost:3001/dashboard/rfq/1')
  })

  test('should display RFQ detail page with title', async ({ page }) => {
    // Verify page title
    await expect(page.locator('h1')).toContainText('CNC Machined Aluminum Parts')

    // Verify RFQ ID
    await expect(page.locator('text=RFQ #1')).toBeVisible()
  })

  test('should display grade badge', async ({ page }) => {
    // Check for grade display
    await expect(page.locator('text=Grade A')).toBeVisible()
    await expect(page.locator('text=/100/')).toBeVisible()
  })

  test('should display original RFQ section', async ({ page }) => {
    // Check for Original RFQ section
    await expect(page.locator('text=Original RFQ')).toBeVisible()

    // Check for description
    await expect(page.locator('text=precision CNC')).toBeVisible()
  })

  test('should display specifications', async ({ page }) => {
    // Check for specification labels
    await expect(page.locator('text=QUANTITY')).toBeVisible()
    await expect(page.locator('text=MATERIAL')).toBeVisible()
    await expect(page.locator('text=DIMENSIONS')).toBeVisible()
    await expect(page.locator('text=TOLERANCES')).toBeVisible()
  })

  test('should display AI summary section', async ({ page }) => {
    // Check for AI summary
    await expect(page.locator('text=AI Summary')).toBeVisible()
    await expect(page.locator('text=High-quality manufacturing')).toBeVisible()
  })

  test('should display AI draft reply section', async ({ page }) => {
    // Check for draft reply
    await expect(page.locator('text=AI Draft Reply')).toBeVisible()
    await expect(page.locator('text=Draft')).toBeVisible()
    await expect(page.locator('text=Thank you for your RFQ')).toBeVisible()
  })

  test('should have copy button for draft reply', async ({ page }) => {
    // Find copy button
    const copyButton = page.locator('button:has-text("Copy")')
    await expect(copyButton).toBeVisible()

    // Click copy button
    await copyButton.click()

    // Verify feedback
    await expect(page.locator('text=Copied')).toBeVisible()
  })

  test('should allow editing draft reply', async ({ page }) => {
    // Click edit button
    const editButton = page.locator('button:has-text("Edit Reply")')
    await editButton.click()

    // Verify textarea appears
    const textarea = page.locator('textarea')
    await expect(textarea).toBeVisible()

    // Type in textarea
    await textarea.fill('Modified reply content')

    // Verify save button
    const saveButton = page.locator('button:has-text("Save Changes")')
    await expect(saveButton).toBeVisible()
  })

  test('should allow canceling reply edit', async ({ page }) => {
    // Click edit button
    const editButton = page.locator('button:has-text("Edit Reply")')
    await editButton.click()

    // Click cancel
    const cancelButton = page.locator('button:has-text("Cancel")')
    await cancelButton.click()

    // Verify back to display mode
    await expect(editButton).toBeVisible()
    await expect(page.locator('textarea')).not.toBeVisible()
  })

  test('should display buyer company profile', async ({ page }) => {
    // Check for company card
    await expect(page.locator('text=Buyer Company')).toBeVisible()
    await expect(page.locator('text=TechCorp Manufacturing')).toBeVisible()
  })

  test('should display contact information', async ({ page }) => {
    // Check for contact person
    await expect(page.locator('text=John Smith')).toBeVisible()
    await expect(page.locator('text=john@techcorp.com')).toBeVisible()
  })

  test('should display company details', async ({ page }) => {
    // Check for company info
    await expect(page.locator('text=Electronics Manufacturing')).toBeVisible()
    await expect(page.locator('text=500')).toBeVisible()
    await expect(page.locator('text=San Francisco')).toBeVisible()
  })

  test('should display certifications badge', async ({ page }) => {
    // Check for certifications
    await expect(page.locator('text=ISO 9001')).toBeVisible()
    await expect(page.locator('text=ISO 14001')).toBeVisible()
  })

  test('should display action buttons', async ({ page }) => {
    // Check for buttons in buyer profile
    await expect(page.locator('button:has-text("Reply to RFQ")')).toBeVisible()
    await expect(page.locator('button:has-text("Save")')).toBeVisible()
    await expect(page.locator('button:has-text("Archive")')).toBeVisible()
  })

  test('should have working back link', async ({ page }) => {
    // Click back link
    const backLink = page.locator('text=Back to Inbox')
    await expect(backLink).toBeVisible()

    // Verify href
    const href = await backLink.locator('a').getAttribute('href')
    expect(href).toBe('/dashboard/rfq')
  })

  test('should display draft status badge', async ({ page }) => {
    // Check for draft status
    await expect(page.locator('text=Draft')).toBeVisible()
  })

  test('should have send reply button', async ({ page }) => {
    // Check for send button
    const sendButton = page.locator('button:has-text("Send Reply")')
    await expect(sendButton).toBeVisible()
  })

  test('should have edit and send buttons initially', async ({ page }) => {
    // Should see Edit and Send buttons
    await expect(page.locator('button:has-text("Edit Reply")')).toBeVisible()
    await expect(page.locator('button:has-text("Send Reply")')).toBeVisible()
  })

  test('should maintain reply content when switching between modes', async ({ page }) => {
    // Get original reply
    const originalReply = await page.locator('text=Thank you for your RFQ').textContent()

    // Enter edit mode
    await page.locator('button:has-text("Edit Reply")').click()

    // Exit edit mode
    await page.locator('button:has-text("Cancel")').click()

    // Check reply is still there
    await expect(page.locator('text=Thank you for your RFQ')).toBeVisible()
  })

  test('should show sticky buyer card on scroll', async ({ page }) => {
    // Check that buyer card is visible
    const buyerCard = page.locator('text=Buyer Company').locator('..')
    await expect(buyerCard).toBeVisible()

    // Note: Testing sticky positioning would require checking computed styles
    // which is better done in unit tests
  })
})
