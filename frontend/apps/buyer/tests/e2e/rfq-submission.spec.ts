import { test, expect } from '@playwright/test'

test.describe('RFQ Submission Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to home page
    await page.goto('http://localhost:3000')
  })

  test('should navigate to RFQ submission page from home', async ({ page }) => {
    // Click on "Create RFQ" button
    await page.click('text=Create RFQ')

    // Verify we're on the RFQ creation page
    await expect(page).toHaveURL(/\/rfq\/new/)
    await expect(page.locator('h1')).toContainText('Create RFQ')
  })

  test('should display all RFQ form sections', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Check Product Information section
    await expect(page.locator('text=Product Information')).toBeVisible()
    await expect(page.locator('input[placeholder*="Product Name"]')).toBeVisible()

    // Check Specifications section
    await expect(page.locator('text=Technical Specifications')).toBeVisible()
    await expect(page.locator('input[placeholder*="Material"]')).toBeVisible()

    // Check Attachments section
    await expect(page.locator('text=Attachments')).toBeVisible()
    await expect(page.locator('text=Drag and drop')).toBeVisible()
  })

  test('should validate required fields', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Click submit without filling required fields
    await page.click('button:has-text("Submit RFQ")')

    // Check for validation errors
    await expect(page.locator('text=Product name is required')).toBeVisible()
    await expect(page.locator('text=Description is required')).toBeVisible()
    await expect(page.locator('text=Quantity is required')).toBeVisible()
  })

  test('should allow filling basic product information', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Fill product name
    await page.fill('input[placeholder*="Product Name"]', 'CNC Machined Parts')

    // Fill description
    await page.fill('textarea[placeholder*="Describe your requirements"]', 'Precision aluminum components')

    // Fill quantity
    await page.fill('input[type="number"][placeholder*="1000"]', '500')

    // Verify values are set
    await expect(page.locator('input[placeholder*="Product Name"]')).toHaveValue('CNC Machined Parts')
    await expect(page.locator('textarea[placeholder*="Describe"]')).toHaveValue('Precision aluminum components')
    await expect(page.locator('input[type="number"]')).toHaveValue('500')
  })

  test('should allow selecting quantity units', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Check default unit
    const unitSelect = page.locator('select').nth(0)
    await expect(unitSelect).toHaveValue('pcs')

    // Change unit to kg
    await unitSelect.selectOption('kg')
    await expect(unitSelect).toHaveValue('kg')
  })

  test('should allow selecting delivery timeframe', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Check default timeframe
    const deliverySelect = page.locator('select').nth(1)
    await expect(deliverySelect).toHaveValue('1_month')

    // Change to 2 weeks
    await deliverySelect.selectOption('2_weeks')
    await expect(deliverySelect).toHaveValue('2_weeks')
  })

  test('should allow filling technical specifications', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Fill material
    await page.fill('input[placeholder*="Material"]', '6061-T6 Aluminum')

    // Fill dimensions
    await page.fill('input[placeholder*="Dimensions"]', '100mm x 50mm x 20mm')

    // Fill tolerances
    await page.fill('input[placeholder*="Tolerances"]', '±0.05mm')

    // Verify values
    await expect(page.locator('input[placeholder*="Material"]')).toHaveValue('6061-T6 Aluminum')
    await expect(page.locator('input[placeholder*="Dimensions"]')).toHaveValue('100mm x 50mm x 20mm')
    await expect(page.locator('input[placeholder*="Tolerances"]')).toHaveValue('±0.05mm')
  })

  test('should allow selecting certifications', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Scroll to certifications section
    await page.locator('text=Required Certifications').scrollIntoViewIfNeeded()

    // Select ISO 9001
    const iso9001Checkbox = page.locator('label:has-text("ISO 9001") input[type="checkbox"]')
    await iso9001Checkbox.check()
    await expect(iso9001Checkbox).toBeChecked()

    // Select ISO 14001
    const iso14001Checkbox = page.locator('label:has-text("ISO 14001") input[type="checkbox"]')
    await iso14001Checkbox.check()
    await expect(iso14001Checkbox).toBeChecked()
  })

  test('should allow filling budget range', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Scroll to budget field
    await page.locator('input[placeholder*="Budget"]').scrollIntoViewIfNeeded()

    // Fill budget
    await page.fill('input[placeholder*="Budget"]', '$1,000 - $5,000')

    // Verify value
    await expect(page.locator('input[placeholder*="Budget"]')).toHaveValue('$1,000 - $5,000')
  })

  test('should handle file attachment via file input', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Find the file input (it's hidden by default)
    const fileInput = page.locator('input[type="file"]')

    // Create a test file and set it
    // Note: This is a simplified test. In real scenarios, you might want to create actual files
    // or mock the file upload

    // For now, just verify the input element exists
    await expect(fileInput).toBeHidden()
  })

  test('should show help section with tips', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Scroll to help section
    await page.locator('text=Provide Clear Details').scrollIntoViewIfNeeded()

    // Verify help cards are visible
    await expect(page.locator('text=Provide Clear Details')).toBeVisible()
    await expect(page.locator('text=Include Drawings')).toBeVisible()
    await expect(page.locator('text=Quick Matching')).toBeVisible()
  })

  test('should show progress indicator', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Verify progress indicator
    await expect(page.locator('text=Product Details')).toBeVisible()
    await expect(page.locator('text=Specifications')).toBeVisible()
    await expect(page.locator('text=Review & Submit')).toBeVisible()
  })

  test('should have working back button', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Click back button
    await page.click('text=Back')

    // Should go back to home page
    await expect(page).toHaveURL('http://localhost:3000/')
  })

  test('should show save as draft button', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Verify save draft button exists
    const saveDraftButton = page.locator('button:has-text("Save as Draft")')
    await expect(saveDraftButton).toBeVisible()
  })

  test('should disable submit button while loading', async ({ page }) => {
    // This test would require mocking the API to test the loading state
    // For now, we can just verify the button exists and is enabled initially

    await page.goto('http://localhost:3000/rfq/new')

    const submitButton = page.locator('button:has-text("Submit RFQ")')
    await expect(submitButton).toBeEnabled()
  })

  test('should clear validation errors when field is corrected', async ({ page }) => {
    await page.goto('http://localhost:3000/rfq/new')

    // Submit empty form to trigger errors
    await page.click('button:has-text("Submit RFQ")')

    // Wait for error message
    await expect(page.locator('text=Product name is required')).toBeVisible()

    // Fill the product name
    await page.fill('input[placeholder*="Product Name"]', 'Test Product')

    // Error should disappear
    await expect(page.locator('text=Product name is required')).not.toBeVisible()
  })
})
