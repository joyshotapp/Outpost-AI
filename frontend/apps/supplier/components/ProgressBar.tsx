import React from 'react'

interface ProgressBarProps {
  currentStep: number
  totalSteps: number
}

export default function ProgressBar({ currentStep, totalSteps }: ProgressBarProps) {
  const steps = Array.from({ length: totalSteps }, (_, i) => i + 1)

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        {steps.map((step) => (
          <div key={step} className="flex items-center flex-1">
            {/* Step circle */}
            <div
              className={`flex items-center justify-center w-10 h-10 rounded-full font-medium text-sm transition-colors ${
                step < currentStep
                  ? 'bg-green-500 text-white'
                  : step === currentStep
                  ? 'bg-primary-600 text-white ring-2 ring-primary-300'
                  : 'bg-gray-200 text-gray-600'
              }`}
            >
              {step < currentStep ? (
                <svg
                  className="w-6 h-6"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                step
              )}
            </div>

            {/* Connector line */}
            {step < totalSteps && (
              <div
                className={`flex-1 h-1 mx-2 rounded-full transition-colors ${
                  step < currentStep ? 'bg-green-500' : 'bg-gray-300'
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step labels */}
      <div className="flex justify-between text-xs text-gray-600 mt-2">
        <div>Company Info</div>
        <div>Industry & Certs</div>
        <div>Review & Submit</div>
      </div>
    </div>
  )
}
