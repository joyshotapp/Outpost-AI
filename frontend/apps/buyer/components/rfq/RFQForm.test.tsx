import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RFQForm } from './RFQForm'

// Mock next-intl
jest.mock('next-intl', () => ({
  useTranslations: () => (key: string) => key,
}))

describe('RFQForm Component', () => {
  const mockOnSubmit = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('renders all required fields', () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    expect(screen.getByText('Product Information')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Product Name/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Description/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Quantity/i)).toBeInTheDocument()
    expect(screen.getByText('Unit')).toBeInTheDocument()
    expect(screen.getByText('Required Delivery Timeframe')).toBeInTheDocument()
  })

  test('renders technical specifications section', () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    expect(screen.getByText('Technical Specifications')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Material/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Dimensions/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Tolerances/i)).toBeInTheDocument()
  })

  test('renders certification checkboxes', () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    expect(screen.getByLabelText(/ISO 9001/)).toBeInTheDocument()
    expect(screen.getByLabelText(/ISO 14001/)).toBeInTheDocument()
    expect(screen.getByLabelText(/CE Marking/)).toBeInTheDocument()
  })

  test('renders file attachment section', () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    expect(screen.getByText('Attachments')).toBeInTheDocument()
    expect(screen.getByText(/Drag and drop/)).toBeInTheDocument()
  })

  test('renders submit button', () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    expect(screen.getByText('Submit RFQ')).toBeInTheDocument()
    expect(screen.getByText('Save as Draft')).toBeInTheDocument()
  })

  test('validates required fields on submit', async () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    const submitButton = screen.getByText('Submit RFQ')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Product name is required/)).toBeInTheDocument()
      expect(screen.getByText(/Description is required/)).toBeInTheDocument()
      expect(screen.getByText(/Quantity is required/)).toBeInTheDocument()
    })

    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  test('accepts valid form data', async () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    const productInput = screen.getByPlaceholderText(/Product Name/i)
    const descriptionInput = screen.getByPlaceholderText(/Description/i)
    const quantityInput = screen.getByPlaceholderText(/Quantity/i)

    await userEvent.type(productInput, 'CNC Parts')
    await userEvent.type(descriptionInput, 'Aluminum parts needed')
    await userEvent.type(quantityInput, '1000')

    const submitButton = screen.getByText('Submit RFQ')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled()
    })
  })

  test('validates quantity as number', async () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    const productInput = screen.getByPlaceholderText(/Product Name/i)
    const descriptionInput = screen.getByPlaceholderText(/Description/i)
    const quantityInput = screen.getByPlaceholderText(/Quantity/i)

    await userEvent.type(productInput, 'Test Product')
    await userEvent.type(descriptionInput, 'Test description')
    await userEvent.type(quantityInput, 'invalid')

    const submitButton = screen.getByText('Submit RFQ')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Quantity must be a number/)).toBeInTheDocument()
    })

    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  test('handles field changes', async () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    const productInput = screen.getByPlaceholderText(/Product Name/i) as HTMLInputElement
    expect(productInput.value).toBe('')

    await userEvent.type(productInput, 'New Product')
    expect(productInput.value).toBe('New Product')
  })

  test('handles quantity unit selection', async () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    const unitSelect = screen.getByDisplayValue('Pieces')
    expect(unitSelect).toBeInTheDocument()

    await userEvent.selectOptions(unitSelect, 'kg')
    expect(unitSelect).toHaveValue('kg')
  })

  test('handles delivery timeframe selection', async () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    const deliverySelect = screen.getByDisplayValue('1 Month')
    expect(deliverySelect).toBeInTheDocument()

    await userEvent.selectOptions(deliverySelect, '2_weeks')
    expect(deliverySelect).toHaveValue('2_weeks')
  })

  test('clears error messages when field is corrected', async () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    const productInput = screen.getByPlaceholderText(/Product Name/i)

    // Trigger validation
    const submitButton = screen.getByText('Submit RFQ')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Product name is required/)).toBeInTheDocument()
    })

    // Fix the field
    await userEvent.type(productInput, 'Product')

    await waitFor(() => {
      expect(screen.queryByText(/Product name is required/)).not.toBeInTheDocument()
    })
  })

  test('displays loading state', () => {
    render(<RFQForm onSubmit={mockOnSubmit} loading={true} />)

    const submitButton = screen.getByText(/Submitting RFQ/)
    expect(submitButton).toBeDisabled()
  })

  test('handles specification fields', async () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    const materialInput = screen.getByPlaceholderText(/Material/i)
    const dimensionsInput = screen.getByPlaceholderText(/Dimensions/i)

    await userEvent.type(materialInput, 'Aluminum')
    await userEvent.type(dimensionsInput, '100x50x20')

    // These fields should be populated
    expect(materialInput).toHaveValue('Aluminum')
    expect(dimensionsInput).toHaveValue('100x50x20')
  })

  test('handles certification checkboxes', async () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    const iso9001 = screen.getByLabelText(/ISO 9001/)
    const iso14001 = screen.getByLabelText(/ISO 14001/)

    expect(iso9001).not.toBeChecked()
    expect(iso14001).not.toBeChecked()

    await userEvent.click(iso9001)
    expect(iso9001).toBeChecked()

    await userEvent.click(iso14001)
    expect(iso14001).toBeChecked()
  })

  test('handles optional budget range field', async () => {
    render(<RFQForm onSubmit={mockOnSubmit} />)

    const budgetInput = screen.getByPlaceholderText(/Budget Range/)
    expect(budgetInput).toBeInTheDocument()

    await userEvent.type(budgetInput, '$1000-$5000')
    expect(budgetInput).toHaveValue('$1000-$5000')
  })
})
