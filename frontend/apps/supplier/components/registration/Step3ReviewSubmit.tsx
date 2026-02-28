'use client'

import React, { useState } from 'react'
import { SupplierRegistrationData } from '../RegistrationWizard'

interface Step3ReviewSubmitProps {
  data: SupplierRegistrationData
  onSubmit: (data: SupplierRegistrationData) => void
  onPrevious: () => void
}

export default function Step3ReviewSubmit({
  data,
  onSubmit,
  onPrevious,
}: Step3ReviewSubmitProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    setIsSubmitting(true)
    try {
      onSubmit(data)
    } finally {
      setIsSubmitting(false)
    }
  }

  const InfoSection = ({
    title,
    items,
  }: {
    title: string
    items: Array<{ label: string; value: string | string[] | number | undefined }>
  }) => (
    <div className="space-y-3">
      <h3 className="text-body-lg font-semibold text-gray-900">{title}</h3>
      <div className="space-y-2">
        {items.map(({ label, value }) => (
          <div key={label} className="flex justify-between py-2 border-b border-gray-200">
            <span className="text-body-sm text-gray-600">{label}</span>
            <span className="text-body-sm font-medium text-gray-900">
              {Array.isArray(value) ? value.join(', ') : value || '—'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-h2 font-semibold text-gray-900 mb-2">
          Review & Submit
        </h2>
        <p className="text-body-sm text-gray-600">
          Please review your information before submission
        </p>
      </div>

      {/* Company Information Review */}
      <div className="bg-gray-50 rounded-lg p-6 space-y-6">
        <InfoSection
          title="Company Information"
          items={[
            { label: 'Company Name', value: data.companyName },
            { label: 'Company Slug', value: data.companySlug },
            { label: 'Website', value: data.website },
            { label: 'Phone', value: data.phone },
            { label: 'Email', value: data.email },
            { label: 'Country', value: data.country },
            { label: 'City', value: data.city },
          ]}
        />

        <div className="border-t border-gray-300" />

        <InfoSection
          title="Industry & Certifications"
          items={[
            { label: 'Industry', value: data.industry },
            { label: 'Main Products', value: data.mainProducts },
            { label: 'Certifications', value: data.certifications },
            { label: 'Employee Count', value: data.employeeCount },
            { label: 'Year Established', value: data.establishedYear },
            { label: 'Description', value: data.description },
          ]}
        />
      </div>

      {/* Important Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <svg
              className="w-5 h-5 text-blue-600"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zm-11-1a1 1 0 11-2 0 1 1 0 012 0zM8 8a1 1 0 000 2h6a1 1 0 100-2H8zm0 3a1 1 0 000 2h3a1 1 0 100-2H8z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div>
            <h4 className="text-body-sm font-semibold text-blue-900 mb-1">
              Next Steps
            </h4>
            <p className="text-body-sm text-blue-800">
              After submitting, our team will review your information and contact
              you within 24 hours. You can also add company logo and product videos
              to your profile after registration.
            </p>
          </div>
        </div>
      </div>

      {/* Terms & Conditions */}
      <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
        <input
          id="terms"
          type="checkbox"
          className="w-4 h-4 mt-1 text-primary-600 border-gray-300 rounded focus:ring-primary-500 cursor-pointer"
        />
        <label htmlFor="terms" className="cursor-pointer">
          <span className="text-body-sm text-gray-700">
            I agree to the{' '}
            <a
              href="/terms"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Terms of Service
            </a>
            {' '}and{' '}
            <a
              href="/privacy"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Privacy Policy
            </a>
          </span>
        </label>
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between pt-6 border-t border-gray-200">
        <button
          onClick={onPrevious}
          disabled={isSubmitting}
          className="px-6 py-2 text-body-sm font-medium text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="px-6 py-2 text-body-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isSubmitting ? (
            <>
              <svg
                className="w-4 h-4 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
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
              Submitting...
            </>
          ) : (
            'Submit Registration'
          )}
        </button>
      </div>
    </div>
  )
}
