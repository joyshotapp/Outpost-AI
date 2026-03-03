'use client'

import { useState, useCallback } from 'react'
import { useTranslations } from 'next-intl'

interface RFQFormData {
  product_name: string
  description: string
  quantity: string
  unit: string
  delivery_timeframe: string
  specifications: {
    material?: string
    dimensions?: string
    tolerances?: string
    certifications?: string
    special_requirements?: string
  }
  budget_range?: string
  attachment_url?: string
}

interface RFQFormProps {
  onSubmit?: (data: RFQFormData) => Promise<void>
  loading?: boolean
}

const QUANTITY_UNITS = [
  { value: 'pcs', label: 'Pieces' },
  { value: 'kg', label: 'Kilograms' },
  { value: 'lbs', label: 'Pounds' },
  { value: 'm', label: 'Meters' },
  { value: 'm2', label: 'Square Meters' },
  { value: 'l', label: 'Liters' },
  { value: 'boxes', label: 'Boxes' },
]

const DELIVERY_OPTIONS = [
  { value: '1_week', label: '1 Week' },
  { value: '2_weeks', label: '2 Weeks' },
  { value: '1_month', label: '1 Month' },
  { value: '2_months', label: '2 Months' },
  { value: '3_months', label: '3 Months' },
  { value: 'flexible', label: 'Flexible' },
]

const CERTIFICATIONS = [
  { value: 'iso9001', label: 'ISO 9001' },
  { value: 'iso14001', label: 'ISO 14001' },
  { value: 'iso45001', label: 'ISO 45001' },
  { value: 'ce', label: 'CE Marking' },
  { value: 'fda', label: 'FDA Approved' },
  { value: 'rohs', label: 'RoHS Compliant' },
]

export function RFQForm({ onSubmit, loading = false }: RFQFormProps) {
  const t = useTranslations('rfq')
  const [formData, setFormData] = useState<RFQFormData>({
    product_name: '',
    description: '',
    quantity: '',
    unit: 'pcs',
    delivery_timeframe: '1_month',
    specifications: {},
    attachment_url: undefined,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [attachmentFile, setAttachmentFile] = useState<File | null>(null)
  const [attachmentProgress, setAttachmentProgress] = useState(0)

  const handleFieldChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const handleSpecificationChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      specifications: {
        ...prev.specifications,
        [field]: value,
      },
    }))
  }

  const handleFileAttach = useCallback((file: File | null) => {
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        setErrors(prev => ({ ...prev, attachment: 'File size must be less than 10MB' }))
        return
      }
      if (!file.type.includes('pdf') && !file.type.includes('image')) {
        setErrors(prev => ({ ...prev, attachment: 'Only PDF and image files are supported' }))
        return
      }
      setAttachmentFile(file)
      setErrors(prev => ({ ...prev, attachment: '' }))
    } else {
      setAttachmentFile(null)
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileAttach(files[0])
    }
  }, [handleFileAttach])

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.product_name.trim()) {
      newErrors.product_name = 'Product name is required'
    }
    if (!formData.description.trim()) {
      newErrors.description = 'Description is required'
    }
    if (!formData.quantity.trim()) {
      newErrors.quantity = 'Quantity is required'
    }
    if (isNaN(Number(formData.quantity))) {
      newErrors.quantity = 'Quantity must be a number'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    if (onSubmit) {
      try {
        await onSubmit(formData)
      } catch (error) {
        setErrors(prev => ({
          ...prev,
          submit: error instanceof Error ? error.message : 'Failed to submit RFQ',
        }))
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Product Information Section */}
      <div className="space-y-6">
        <h2 className="text-h3 font-semibold text-gray-900">Product Information</h2>

        {/* Product Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Product Name *
          </label>
          <input
            type="text"
            value={formData.product_name}
            onChange={e => handleFieldChange('product_name', e.target.value)}
            placeholder="e.g., CNC Machined Aluminum Parts"
            className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              errors.product_name ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.product_name && (
            <p className="mt-1 text-sm text-red-600">{errors.product_name}</p>
          )}
        </div>

        {/* Description with Rich Text */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description *
          </label>
          <div className="border border-gray-300 rounded-md overflow-hidden focus-within:ring-2 focus-within:ring-primary-500">
            {/* Simple Rich Text Editor Toolbar */}
            <div className="bg-gray-50 border-b border-gray-300 p-2 flex gap-1 flex-wrap">
              <button
                type="button"
                className="p-2 hover:bg-gray-200 rounded text-sm font-bold"
                title="Bold"
                onClick={() => document.execCommand('bold')}
              >
                B
              </button>
              <button
                type="button"
                className="p-2 hover:bg-gray-200 rounded text-sm italic"
                title="Italic"
                onClick={() => document.execCommand('italic')}
              >
                I
              </button>
              <button
                type="button"
                className="p-2 hover:bg-gray-200 rounded text-sm underline"
                title="Underline"
                onClick={() => document.execCommand('underline')}
              >
                U
              </button>
              <div className="w-px bg-gray-300"></div>
              <button
                type="button"
                className="p-2 hover:bg-gray-200 rounded text-sm"
                title="Bullet List"
                onClick={() => document.execCommand('insertUnorderedList')}
              >
                • List
              </button>
              <button
                type="button"
                className="p-2 hover:bg-gray-200 rounded text-sm"
                title="Numbered List"
                onClick={() => document.execCommand('insertOrderedList')}
              >
                1. List
              </button>
            </div>
            {/* Editor Area */}
            <textarea
              value={formData.description}
              onChange={e => handleFieldChange('description', e.target.value)}
              placeholder="Describe your requirements, technical specifications, and any special requirements..."
              className="w-full h-40 p-4 resize-none focus:outline-none"
            />
          </div>
          {errors.description && (
            <p className="mt-1 text-sm text-red-600">{errors.description}</p>
          )}
        </div>
      </div>

      {/* Quantity Section */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quantity *
          </label>
          <input
            type="number"
            value={formData.quantity}
            onChange={e => handleFieldChange('quantity', e.target.value)}
            placeholder="e.g., 1000"
            min="1"
            step="1"
            className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              errors.quantity ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.quantity && (
            <p className="mt-1 text-sm text-red-600">{errors.quantity}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Unit
          </label>
          <select
            value={formData.unit}
            onChange={e => handleFieldChange('unit', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {QUANTITY_UNITS.map(unit => (
              <option key={unit.value} value={unit.value}>
                {unit.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Delivery Timeframe */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Required Delivery Timeframe
        </label>
        <select
          value={formData.delivery_timeframe}
          onChange={e => handleFieldChange('delivery_timeframe', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {DELIVERY_OPTIONS.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Technical Specifications */}
      <div className="space-y-6">
        <h2 className="text-h3 font-semibold text-gray-900">Technical Specifications</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Material */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Material
            </label>
            <input
              type="text"
              value={formData.specifications.material || ''}
              onChange={e => handleSpecificationChange('material', e.target.value)}
              placeholder="e.g., 6061-T6 Aluminum"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Dimensions */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dimensions
            </label>
            <input
              type="text"
              value={formData.specifications.dimensions || ''}
              onChange={e => handleSpecificationChange('dimensions', e.target.value)}
              placeholder="e.g., 100mm x 50mm x 20mm"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Tolerances */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tolerances
            </label>
            <input
              type="text"
              value={formData.specifications.tolerances || ''}
              onChange={e => handleSpecificationChange('tolerances', e.target.value)}
              placeholder="e.g., ±0.05mm"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Special Requirements */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Special Requirements
            </label>
            <input
              type="text"
              value={formData.specifications.special_requirements || ''}
              onChange={e => handleSpecificationChange('special_requirements', e.target.value)}
              placeholder="e.g., Anodized finish, RoHS compliant"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        {/* Certifications */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Required Certifications
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {CERTIFICATIONS.map(cert => (
              <label key={cert.value} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.specifications.certifications?.includes(cert.value) || false}
                  onChange={e => {
                    let certs = formData.specifications.certifications?.split(',') || []
                    if (e.target.checked) {
                      certs.push(cert.value)
                    } else {
                      certs = certs.filter(c => c !== cert.value)
                    }
                    handleSpecificationChange('certifications', certs.join(','))
                  }}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">{cert.label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* File Attachment */}
      <div className="space-y-4">
        <h2 className="text-h3 font-semibold text-gray-900">Attachments</h2>

        <div
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-500 hover:bg-primary-50 transition-colors cursor-pointer"
        >
          <div className="space-y-4">
            <div className="text-4xl">📎</div>
            <div>
              <p className="text-sm font-medium text-gray-900">
                Drag and drop your files or
              </p>
              <label className="text-primary-600 hover:text-primary-700 font-medium cursor-pointer">
                click to select
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={e => handleFileAttach(e.target.files?.[0] || null)}
                  className="hidden"
                />
              </label>
            </div>
            <p className="text-xs text-gray-500">
              PDF, JPG, or PNG • Max 10MB
            </p>
          </div>
        </div>

        {attachmentFile && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-2xl">✓</div>
              <div>
                <p className="font-medium text-gray-900">{attachmentFile.name}</p>
                <p className="text-sm text-gray-600">
                  {(attachmentFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => handleFileAttach(null)}
              className="text-red-600 hover:text-red-700 font-medium"
            >
              Remove
            </button>
          </div>
        )}

        {errors.attachment && (
          <p className="text-sm text-red-600">{errors.attachment}</p>
        )}
      </div>

      {/* Budget Range (Optional) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Budget Range (Optional)
        </label>
        <input
          type="text"
          value={formData.budget_range || ''}
          onChange={e => handleFieldChange('budget_range', e.target.value)}
          placeholder="e.g., $1,000 - $5,000"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* Submit Error */}
      {errors.submit && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-600">{errors.submit}</p>
        </div>
      )}

      {/* Submit Button */}
      <div className="flex gap-4 pt-4">
        <button
          type="submit"
          disabled={loading}
          className="flex-1 px-6 py-3 bg-primary-700 text-white rounded-md hover:bg-primary-600 disabled:bg-gray-400 font-semibold transition-colors"
        >
          {loading ? 'Submitting RFQ...' : 'Submit RFQ'}
        </button>
        <button
          type="button"
          className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-semibold transition-colors"
        >
          Save as Draft
        </button>
      </div>
    </form>
  )
}
