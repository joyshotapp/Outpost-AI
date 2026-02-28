'use client'

import React, { useState, useEffect } from 'react'
import { useSupplier } from '@/hooks/useSupplier'

interface ProfileContactInfoProps {
  onSave: () => void
  isSaving: boolean
  supplierId?: string
}

export default function ProfileContactInfo({
  onSave,
  isSaving: parentIsSaving,
  supplierId,
}: ProfileContactInfoProps) {
  const { supplier, loading, updateSupplier } = useSupplier()
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    industry: 'Electronics & Computing',
    mainProducts: 'Mechanical parts, CNC machining, fasteners',
    description: 'Leading manufacturer of precision mechanical parts for industrial applications.',
    employeeCount: '51-100',
    establishedYear: '2010',
    certifications: 'ISO 9001, ISO 14001, IATF 16949',
    businessLicense: 'License #12345678',
    taxId: 'Tax ID #87654321',
    bankDetails: 'Available upon request',
  })

  useEffect(() => {
    if (supplier) {
      setFormData({
        industry: supplier.industry || '',
        mainProducts: supplier.mainProducts || '',
        description: supplier.description || '',
        employeeCount: supplier.employeeCount || '',
        establishedYear: supplier.establishedYear?.toString() || '',
        certifications: supplier.certifications?.join(', ') || '',
        businessLicense: supplier.businessLicense || '',
        taxId: supplier.taxId || '',
        bankDetails: supplier.bankDetails || '',
      })
    }
  }, [supplier])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSave = async () => {
    setIsSaving(true)
    setError(null)
    try {
      await updateSupplier({
        ...formData,
        certifications: formData.certifications.split(',').map((c) => c.trim()),
        establishedYear: parseInt(formData.establishedYear),
      })
      onSave()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save changes')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Industry */}
        <div>
          <label htmlFor="industry" className="block text-body-sm font-medium text-gray-700 mb-2">
            Primary Industry
          </label>
          <select
            id="industry"
            name="industry"
            value={formData.industry}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option>Electronics & Computing</option>
            <option>Textiles & Apparel</option>
            <option>Chemicals & Materials</option>
            <option>Machinery & Equipment</option>
            <option>Metal & Steel</option>
          </select>
        </div>

        {/* Employee Count */}
        <div>
          <label htmlFor="employeeCount" className="block text-body-sm font-medium text-gray-700 mb-2">
            Employee Count
          </label>
          <select
            id="employeeCount"
            name="employeeCount"
            value={formData.employeeCount}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option>1-10</option>
            <option>11-50</option>
            <option>51-100</option>
            <option>101-500</option>
            <option>501-1000</option>
            <option>1000+</option>
          </select>
        </div>

        {/* Established Year */}
        <div>
          <label htmlFor="establishedYear" className="block text-body-sm font-medium text-gray-700 mb-2">
            Year Established
          </label>
          <input
            id="establishedYear"
            type="number"
            name="establishedYear"
            value={formData.establishedYear}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Certifications */}
        <div>
          <label htmlFor="certifications" className="block text-body-sm font-medium text-gray-700 mb-2">
            Certifications
          </label>
          <input
            id="certifications"
            type="text"
            name="certifications"
            value={formData.certifications}
            onChange={handleChange}
            placeholder="ISO 9001, ISO 14001, etc."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Business License */}
        <div>
          <label htmlFor="businessLicense" className="block text-body-sm font-medium text-gray-700 mb-2">
            Business License
          </label>
          <input
            id="businessLicense"
            type="text"
            name="businessLicense"
            value={formData.businessLicense}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Tax ID */}
        <div>
          <label htmlFor="taxId" className="block text-body-sm font-medium text-gray-700 mb-2">
            Tax ID
          </label>
          <input
            id="taxId"
            type="text"
            name="taxId"
            value={formData.taxId}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      {/* Full Width Fields */}
      <div className="space-y-6">
        {/* Main Products */}
        <div>
          <label htmlFor="mainProducts" className="block text-body-sm font-medium text-gray-700 mb-2">
            Main Products
          </label>
          <textarea
            id="mainProducts"
            name="mainProducts"
            value={formData.mainProducts}
            onChange={handleChange}
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
          />
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-body-sm font-medium text-gray-700 mb-2">
            Company Description
          </label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={4}
            placeholder="Tell potential buyers about your company, capabilities, and what makes you unique..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
          />
          <p className="text-body-xs text-gray-500 mt-1">
            This description will appear on your public profile
          </p>
        </div>

        {/* Bank Details */}
        <div>
          <label htmlFor="bankDetails" className="block text-body-sm font-medium text-gray-700 mb-2">
            Bank Details (Optional)
          </label>
          <textarea
            id="bankDetails"
            name="bankDetails"
            value={formData.bankDetails}
            onChange={handleChange}
            rows={2}
            placeholder="Add bank information for payments (visible only to verified buyers)"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
          />
          <p className="text-body-xs text-gray-500 mt-1">
            Only shared with verified buyers when negotiating orders
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-body-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
        <button className="px-6 py-2 text-body-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={isSaving || loading}
          className="px-6 py-2 text-body-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {(isSaving || loading) && (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          )}
          {isSaving || loading ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}
