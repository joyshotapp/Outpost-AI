'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import RegistrationWizard, { SupplierRegistrationData } from '@/components/RegistrationWizard'
import ProgressBar from '@/components/ProgressBar'

export default function RegisterPage() {
  const [currentStep, setCurrentStep] = useState(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()
  const totalSteps = 3

  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = async (data: SupplierRegistrationData) => {
    setIsSubmitting(true)
    setError(null)

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('You must be logged in to register a supplier')
      }

      const response = await fetch('/api/v1/suppliers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          company_name: data.companyName,
          company_slug: data.companySlug,
          website: data.website || null,
          phone: data.phone,
          email: data.email,
          country: data.country,
          city: data.city,
          industry: data.industry,
          certifications: data.certifications,
          number_of_employees: data.employeeCount ? parseInt(data.employeeCount, 10) : null,
          established_year: data.establishedYear || null,
          main_products: data.mainProducts,
          company_description: data.description || null,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to register supplier')
      }

      router.push('/register/success')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred'
      setError(message)
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-blue-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-h1 font-bold text-gray-900 mb-2">
            Supplier Registration
          </h1>
          <p className="text-body-lg text-gray-600">
            Join Factory Insider and expand your business opportunities
          </p>
        </div>

        {/* Progress Bar */}
        <ProgressBar currentStep={currentStep} totalSteps={totalSteps} />

        {/* Error Message */}
        {error && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex gap-3">
              <svg
                className="w-5 h-5 text-red-600 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <div>
                <p className="text-body-sm font-medium text-red-900">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Registration Wizard */}
        <div className="bg-white rounded-lg shadow-lg p-8 mt-8">
          <RegistrationWizard
            currentStep={currentStep}
            onNext={handleNext}
            onPrevious={handlePrevious}
            onComplete={handleComplete}
          />
        </div>

        {/* Footer */}
        <div className="text-center mt-6 text-body-sm text-gray-600">
          <p>
            Already have an account?{' '}
            <a href="/login" className="text-primary-600 font-medium hover:text-primary-700">
              Login here
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
