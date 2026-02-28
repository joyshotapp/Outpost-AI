'use client'

import Link from 'next/link'

export default function RegistrationSuccessPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-blue-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md text-center">
        {/* Success Icon */}
        <div className="mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full">
            <svg
              className="w-8 h-8 text-green-600"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        </div>

        {/* Message */}
        <h1 className="text-h1 font-bold text-gray-900 mb-2">
          Registration Successful!
        </h1>
        <p className="text-body-lg text-gray-600 mb-6">
          Thank you for joining Factory Insider. Our team will review your
          information and contact you within 24 hours.
        </p>

        {/* Next Steps */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8 text-left space-y-4">
          <h2 className="text-body-lg font-semibold text-gray-900 text-center">
            What's Next?
          </h2>
          <div className="space-y-3">
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold text-sm">
                1
              </div>
              <div>
                <p className="text-body-sm font-medium text-gray-900">
                  Account Verification
                </p>
                <p className="text-body-xs text-gray-600">
                  We'll verify your company information
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold text-sm">
                2
              </div>
              <div>
                <p className="text-body-sm font-medium text-gray-900">
                  Profile Setup
                </p>
                <p className="text-body-xs text-gray-600">
                  Add company logo, images, and product videos
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold text-sm">
                3
              </div>
              <div>
                <p className="text-body-sm font-medium text-gray-900">
                  Start Trading
                </p>
                <p className="text-body-xs text-gray-600">
                  Respond to buyer inquiries and grow your business
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <Link
            href="/dashboard"
            className="block w-full px-6 py-3 text-body-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors text-center"
          >
            Go to Dashboard
          </Link>
          <Link
            href="/"
            className="block w-full px-6 py-3 text-body-sm font-medium text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 transition-colors text-center"
          >
            Back to Home
          </Link>
        </div>

        {/* Contact Info */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <p className="text-body-xs text-gray-600">
            Questions? Contact us at{' '}
            <a
              href="mailto:support@factoryinsider.com"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              support@factoryinsider.com
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
