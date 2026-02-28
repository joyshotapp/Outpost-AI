'use client'

import React, { useState, useEffect } from 'react'
import { useSupplier } from '@/hooks/useSupplier'

interface ProfileBasicInfoProps {
  onSave: () => void
  isSaving: boolean
  supplierId?: string
}

export default function ProfileBasicInfo({
  onSave,
  isSaving: parentIsSaving,
  supplierId,
}: ProfileBasicInfoProps) {
  const { supplier, loading, updateSupplier } = useSupplier()
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    companyName: 'ABC Manufacturing',
    companySlug: 'abc-manufacturing',
    website: 'https://abc-mfg.com',
    phone: '+86 10 1234 5678',
    email: 'contact@abc-mfg.com',
    country: 'China',
    city: 'Shanghai',
    address: '123 Industrial Park, Pudong District',
    postalCode: '200000',
  })

  useEffect(() => {
    if (supplier) {
      setFormData({
        companyName: supplier.companyName || '',
        companySlug: supplier.companySlug || '',
        website: supplier.website || '',
        phone: supplier.phone || '',
        email: supplier.email || '',
        country: supplier.country || '',
        city: supplier.city || '',
        address: supplier.address || '',
        postalCode: supplier.postalCode || '',
      })
    }
  }, [supplier])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSave = async () => {
    setIsSaving(true)
    setError(null)
    try {
      await updateSupplier(formData)
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
        {/* Company Name */}
        <div>
          <label htmlFor="companyName" className="block text-body-sm font-medium text-gray-700 mb-2">
            Company Name
          </label>
          <input
            id="companyName"
            type="text"
            name="companyName"
            value={formData.companyName}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Company Slug */}
        <div>
          <label htmlFor="companySlug" className="block text-body-sm font-medium text-gray-700 mb-2">
            Company Slug
          </label>
          <input
            id="companySlug"
            type="text"
            name="companySlug"
            value={formData.companySlug}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <p className="text-body-xs text-gray-500 mt-1">
            Used in your profile URL: factoryinsider.com/{formData.companySlug}
          </p>
        </div>

        {/* Website */}
        <div>
          <label htmlFor="website" className="block text-body-sm font-medium text-gray-700 mb-2">
            Website
          </label>
          <input
            id="website"
            type="url"
            name="website"
            value={formData.website}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Phone */}
        <div>
          <label htmlFor="phone" className="block text-body-sm font-medium text-gray-700 mb-2">
            Phone
          </label>
          <input
            id="phone"
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Email */}
        <div>
          <label htmlFor="email" className="block text-body-sm font-medium text-gray-700 mb-2">
            Email
          </label>
          <input
            id="email"
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Country */}
        <div>
          <label htmlFor="country" className="block text-body-sm font-medium text-gray-700 mb-2">
            Country
          </label>
          <select
            id="country"
            name="country"
            value={formData.country}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option>China</option>
            <option>Vietnam</option>
            <option>India</option>
            <option>Thailand</option>
          </select>
        </div>

        {/* City */}
        <div>
          <label htmlFor="city" className="block text-body-sm font-medium text-gray-700 mb-2">
            City
          </label>
          <input
            id="city"
            type="text"
            name="city"
            value={formData.city}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Address */}
        <div>
          <label htmlFor="address" className="block text-body-sm font-medium text-gray-700 mb-2">
            Address
          </label>
          <input
            id="address"
            type="text"
            name="address"
            value={formData.address}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Postal Code */}
        <div>
          <label htmlFor="postalCode" className="block text-body-sm font-medium text-gray-700 mb-2">
            Postal Code
          </label>
          <input
            id="postalCode"
            type="text"
            name="postalCode"
            value={formData.postalCode}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
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
