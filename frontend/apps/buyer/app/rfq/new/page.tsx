'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { RFQForm } from '@/components/rfq/RFQForm'

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

export default function NewRFQPage() {
  const t = useTranslations('rfq')
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const handleSubmitRFQ = async (formData: RFQFormData) => {
    setIsLoading(true)
    try {
      // Call the backend API to create RFQ
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/rfqs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          description: formData.description,
          specifications: formData.specifications,
        }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const result = await response.json()
      setSuccessMessage('RFQ submitted successfully!')

      // Redirect to RFQ detail page after a delay
      setTimeout(() => {
        router.push(`/dashboard/rfq/${result.id}`)
      }, 1500)
    } catch (error) {
      console.error('Failed to submit RFQ:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-h2 font-bold text-gray-900">Create RFQ</h1>
            <p className="mt-1 text-sm text-gray-600">
              Submit a request for quotation to find the right suppliers
            </p>
          </div>
          <button
            onClick={() => router.back()}
            className="text-gray-600 hover:text-gray-900 font-medium"
          >
            ← Back
          </button>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {successMessage && (
          <div className="mb-8 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">✓</span>
              <div>
                <p className="font-medium text-green-900">{successMessage}</p>
                <p className="text-sm text-green-700">Redirecting to dashboard...</p>
              </div>
            </div>
          </div>
        )}

        {/* Progress Indicator */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold">
                1
              </div>
              <span className="text-sm font-medium text-gray-900">Product Details</span>
            </div>
            <div className="flex-1 h-1 bg-gray-200 mx-4"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gray-300 text-white rounded-full flex items-center justify-center font-bold">
                2
              </div>
              <span className="text-sm font-medium text-gray-500">Specifications</span>
            </div>
            <div className="flex-1 h-1 bg-gray-200 mx-4"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gray-300 text-white rounded-full flex items-center justify-center font-bold">
                3
              </div>
              <span className="text-sm font-medium text-gray-500">Review & Submit</span>
            </div>
          </div>
        </div>

        {/* Form */}
        <div className="bg-white rounded-lg shadow-sm p-8">
          <RFQForm onSubmit={handleSubmitRFQ} loading={isLoading} />
        </div>

        {/* Help Section */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="text-3xl mb-4">📝</div>
            <h3 className="font-semibold text-gray-900 mb-2">Provide Clear Details</h3>
            <p className="text-sm text-gray-600">
              The more specific you are about your requirements, the better quotes you'll receive from suppliers.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="text-3xl mb-4">📎</div>
            <h3 className="font-semibold text-gray-900 mb-2">Include Drawings</h3>
            <p className="text-sm text-gray-600">
              Attach PDF drawings, images, or specifications to help suppliers understand your exact needs.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="text-3xl mb-4">⚡</div>
            <h3 className="font-semibold text-gray-900 mb-2">Quick Matching</h3>
            <p className="text-sm text-gray-600">
              Our AI will match your RFQ with verified suppliers who can meet your requirements.
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
