'use client'

import React, { useState } from 'react'
import Step1CompanyInfo from './registration/Step1CompanyInfo'
import Step2IndustryAuth from './registration/Step2IndustryAuth'
import Step3ReviewSubmit from './registration/Step3ReviewSubmit'

interface RegistrationWizardProps {
  currentStep: number
  onNext: () => void
  onPrevious: () => void
  onComplete: (data: SupplierRegistrationData) => void
}

export interface SupplierRegistrationData {
  companyName: string
  companySlug: string
  website?: string
  phone: string
  email: string
  country: string
  city: string
  industry: string
  certifications: string[]
  employeeCount?: string
  establishedYear?: number
  mainProducts: string
  description?: string
}

export default function RegistrationWizard({
  currentStep,
  onNext,
  onPrevious,
  onComplete,
}: RegistrationWizardProps) {
  const [formData, setFormData] = useState<SupplierRegistrationData>({
    companyName: '',
    companySlug: '',
    website: '',
    phone: '',
    email: '',
    country: '',
    city: '',
    industry: '',
    certifications: [],
    employeeCount: '',
    establishedYear: new Date().getFullYear(),
    mainProducts: '',
    description: '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const updateFormData = (data: Partial<SupplierRegistrationData>) => {
    setFormData((prev) => ({ ...prev, ...data }))
  }

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {}

    if (step === 1) {
      if (!formData.companyName.trim())
        newErrors.companyName = 'Company name is required'
      if (!formData.companySlug.trim())
        newErrors.companySlug = 'Company slug is required'
      if (!formData.phone.trim()) newErrors.phone = 'Phone is required'
      if (!formData.email.trim()) newErrors.email = 'Email is required'
      if (!formData.country) newErrors.country = 'Country is required'
      if (!formData.city.trim()) newErrors.city = 'City is required'
    } else if (step === 2) {
      if (!formData.industry) newErrors.industry = 'Industry is required'
      if (!formData.mainProducts.trim())
        newErrors.mainProducts = 'Main products are required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleNext = () => {
    if (validateStep(currentStep)) {
      onNext()
    }
  }

  return (
    <div className="w-full">
      {currentStep === 1 && (
        <Step1CompanyInfo
          data={formData}
          errors={errors}
          onDataChange={updateFormData}
          onNext={handleNext}
          onPrevious={onPrevious}
        />
      )}

      {currentStep === 2 && (
        <Step2IndustryAuth
          data={formData}
          errors={errors}
          onDataChange={updateFormData}
          onNext={handleNext}
          onPrevious={onPrevious}
        />
      )}

      {currentStep === 3 && (
        <Step3ReviewSubmit
          data={formData}
          onSubmit={onComplete}
          onPrevious={onPrevious}
        />
      )}
    </div>
  )
}
