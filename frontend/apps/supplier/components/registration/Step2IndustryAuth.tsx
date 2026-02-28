'use client'

import React, { useState } from 'react'
import { SupplierRegistrationData } from '../RegistrationWizard'

interface Step2IndustryAuthProps {
  data: SupplierRegistrationData
  errors: Record<string, string>
  onDataChange: (data: Partial<SupplierRegistrationData>) => void
  onNext: () => void
  onPrevious: () => void
}

const INDUSTRIES = [
  'Electronics & Computing',
  'Textiles & Apparel',
  'Chemicals & Materials',
  'Machinery & Equipment',
  'Metal & Steel',
  'Plastics & Rubber',
  'Wood & Furniture',
  'Paper & Packaging',
  'Food & Beverage',
  'Energy & Power',
  'Automotive',
  'Aerospace & Defense',
  'Medical & Pharmaceutical',
  'Consumer Goods',
  'Other',
]

const CERTIFICATIONS = [
  'ISO 9001:2015 (Quality Management)',
  'ISO 14001:2015 (Environmental Management)',
  'ISO 45001:2018 (Occupational Health & Safety)',
  'ISO 50001:2018 (Energy Management)',
  'ISO/IEC 27001 (Information Security)',
  'IATF 16949 (Automotive Quality)',
  'AS9100 (Aerospace Quality)',
  'FDA Approval (Medical/Pharma)',
  'CE Marking (EU Compliance)',
  'RoHS Compliance',
  'REACH Compliance',
  'Export License',
  'Other',
]

const EMPLOYEE_COUNT_OPTIONS = [
  '1-10',
  '11-50',
  '51-100',
  '101-500',
  '501-1000',
  '1000+',
]

export default function Step2IndustryAuth({
  data,
  errors,
  onDataChange,
  onNext,
  onPrevious,
}: Step2IndustryAuthProps) {
  const [certificationInput, setCertificationInput] = useState('')
  const [showCertificationDropdown, setShowCertificationDropdown] = useState(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    onDataChange({ [name]: value })
  }

  const addCertification = (cert: string) => {
    if (!data.certifications.includes(cert)) {
      onDataChange({
        certifications: [...data.certifications, cert],
      })
    }
    setCertificationInput('')
    setShowCertificationDropdown(false)
  }

  const removeCertification = (cert: string) => {
    onDataChange({
      certifications: data.certifications.filter((c) => c !== cert),
    })
  }

  const handleAddCustomCertification = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && certificationInput.trim()) {
      e.preventDefault()
      addCertification(certificationInput.trim())
    }
  }

  const availableCertifications = CERTIFICATIONS.filter(
    (cert) =>
      !data.certifications.includes(cert) &&
      cert.toLowerCase().includes(certificationInput.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-h2 font-semibold text-gray-900 mb-2">
          Industry & Certifications
        </h2>
        <p className="text-body-sm text-gray-600">
          Tell us about your industry and certifications
        </p>
      </div>

      <div className="space-y-6">
        {/* Industry */}
        <div>
          <label htmlFor="industry" className="block text-body-sm font-medium text-gray-700 mb-2">
            Primary Industry *
          </label>
          <select
            id="industry"
            name="industry"
            value={data.industry}
            onChange={handleInputChange}
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              errors.industry
                ? 'border-red-500'
                : 'border-gray-300'
            }`}
          >
            <option value="">Select Industry</option>
            {INDUSTRIES.map((industry) => (
              <option key={industry} value={industry}>
                {industry}
              </option>
            ))}
          </select>
          {errors.industry && (
            <p className="text-body-xs text-red-600 mt-1">{errors.industry}</p>
          )}
        </div>

        {/* Main Products */}
        <div>
          <label htmlFor="mainProducts" className="block text-body-sm font-medium text-gray-700 mb-2">
            Main Products *
          </label>
          <textarea
            id="mainProducts"
            name="mainProducts"
            value={data.mainProducts}
            onChange={handleInputChange}
            placeholder="e.g. Mechanical parts, CNC machining, fasteners..."
            rows={3}
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none ${
              errors.mainProducts
                ? 'border-red-500'
                : 'border-gray-300'
            }`}
          />
          {errors.mainProducts && (
            <p className="text-body-xs text-red-600 mt-1">{errors.mainProducts}</p>
          )}
          <p className="text-body-xs text-gray-500 mt-1">
            Describe your main products or services
          </p>
        </div>

        {/* Certifications */}
        <div>
          <label className="block text-body-sm font-medium text-gray-700 mb-2">
            Certifications
          </label>
          <div className="relative">
            <input
              type="text"
              value={certificationInput}
              onChange={(e) => setCertificationInput(e.target.value)}
              onKeyDown={handleAddCustomCertification}
              onFocus={() => setShowCertificationDropdown(true)}
              onBlur={() =>
                setTimeout(() => setShowCertificationDropdown(false), 200)
              }
              placeholder="Search or enter certification..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />

            {/* Dropdown suggestions */}
            {showCertificationDropdown && availableCertifications.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto">
                {availableCertifications.map((cert) => (
                  <button
                    key={cert}
                    type="button"
                    onClick={() => addCertification(cert)}
                    className="w-full text-left px-4 py-2 text-body-sm hover:bg-primary-50 transition-colors"
                  >
                    {cert}
                  </button>
                ))}
              </div>
            )}
          </div>
          <p className="text-body-xs text-gray-500 mt-1">
            Press Enter to add custom certification
          </p>

          {/* Selected certifications */}
          {data.certifications.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {data.certifications.map((cert) => (
                <span
                  key={cert}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-primary-50 border border-primary-200 rounded-full text-body-xs text-primary-700"
                >
                  {cert}
                  <button
                    type="button"
                    onClick={() => removeCertification(cert)}
                    className="text-primary-600 hover:text-primary-900 font-medium"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Employee Count */}
        <div>
          <label htmlFor="employeeCount" className="block text-body-sm font-medium text-gray-700 mb-2">
            Employee Count
          </label>
          <select
            id="employeeCount"
            name="employeeCount"
            value={data.employeeCount}
            onChange={handleInputChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Select employee count</option>
            {EMPLOYEE_COUNT_OPTIONS.map((count) => (
              <option key={count} value={count}>
                {count}
              </option>
            ))}
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
            value={data.establishedYear}
            onChange={handleInputChange}
            min="1900"
            max={new Date().getFullYear()}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
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
            value={data.description}
            onChange={handleInputChange}
            placeholder="Tell us about your company, capabilities, and experience..."
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
          />
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between pt-6 border-t border-gray-200">
        <button
          onClick={onPrevious}
          className="px-6 py-2 text-body-sm font-medium text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 transition-colors"
        >
          Previous
        </button>
        <button
          onClick={onNext}
          className="px-6 py-2 text-body-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  )
}
