'use client'

import React from 'react'
import { SupplierRegistrationData } from '../RegistrationWizard'

interface Step1CompanyInfoProps {
  data: SupplierRegistrationData
  errors: Record<string, string>
  onDataChange: (data: Partial<SupplierRegistrationData>) => void
  onNext: () => void
  onPrevious: () => void
}

const COUNTRIES = [
  'China',
  'Vietnam',
  'India',
  'Thailand',
  'Indonesia',
  'Malaysia',
  'Philippines',
  'Myanmar',
  'Cambodia',
  'Laos',
  'Taiwan',
  'Japan',
  'South Korea',
]

const CITIES_BY_COUNTRY: Record<string, string[]> = {
  China: [
    'Shanghai',
    'Beijing',
    'Guangzhou',
    'Shenzhen',
    'Chongqing',
    'Hangzhou',
    'Wuhan',
    'Xiamen',
    'Suzhou',
    'Ningbo',
  ],
  Vietnam: [
    'Ho Chi Minh City',
    'Hanoi',
    'Hai Phong',
    'Da Nang',
    'Can Tho',
    'Bien Hoa',
  ],
  India: [
    'Delhi',
    'Mumbai',
    'Bangalore',
    'Hyderabad',
    'Chennai',
    'Pune',
    'Kolkata',
    'Ahmedabad',
  ],
  Thailand: ['Bangkok', 'Chiang Mai', 'Phuket', 'Pattaya', 'Rayong'],
  Indonesia: ['Jakarta', 'Surabaya', 'Bandung', 'Medan', 'Semarang'],
  Malaysia: ['Kuala Lumpur', 'Penang', 'Johor Bahru', 'Selangor'],
  Philippines: ['Manila', 'Cebu', 'Davao', 'Quezon City'],
  Myanmar: ['Yangon', 'Mandalay', 'Naypyidaw'],
  Cambodia: ['Phnom Penh', 'Siem Reap'],
  Laos: ['Vientiane'],
  Taiwan: ['Taipei', 'Kaohsiung', 'Taichung'],
  Japan: ['Tokyo', 'Osaka', 'Yokohama', 'Nagoya'],
  'South Korea': ['Seoul', 'Busan', 'Incheon', 'Daegu'],
}

export default function Step1CompanyInfo({
  data,
  errors,
  onDataChange,
  onNext,
  onPrevious,
}: Step1CompanyInfoProps) {
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    onDataChange({ [name]: value })
  }

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '-')
      .replace(/[^\w-]/g, '')
  }

  const handleCompanyNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const name = e.target.value
    onDataChange({
      companyName: name,
      companySlug: generateSlug(name),
    })
  }

  const cities = data.country ? CITIES_BY_COUNTRY[data.country] || [] : []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-h2 font-semibold text-gray-900 mb-2">
          Company Information
        </h2>
        <p className="text-body-sm text-gray-600">
          Provide basic details about your company
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Company Name */}
        <div>
          <label htmlFor="companyName" className="block text-body-sm font-medium text-gray-700 mb-2">
            Company Name *
          </label>
          <input
            id="companyName"
            type="text"
            name="companyName"
            value={data.companyName}
            onChange={handleCompanyNameChange}
            placeholder="e.g. ABC Manufacturing"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              errors.companyName
                ? 'border-red-500'
                : 'border-gray-300'
            }`}
          />
          {errors.companyName && (
            <p className="text-body-xs text-red-600 mt-1">{errors.companyName}</p>
          )}
        </div>

        {/* Company Slug */}
        <div>
          <label htmlFor="companySlug" className="block text-body-sm font-medium text-gray-700 mb-2">
            Company Slug *
          </label>
          <input
            id="companySlug"
            type="text"
            name="companySlug"
            value={data.companySlug}
            onChange={handleInputChange}
            placeholder="auto-generated"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              errors.companySlug
                ? 'border-red-500'
                : 'border-gray-300'
            }`}
          />
          {errors.companySlug && (
            <p className="text-body-xs text-red-600 mt-1">{errors.companySlug}</p>
          )}
          <p className="text-body-xs text-gray-500 mt-1">
            Used for company profile URL
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
            value={data.website}
            onChange={handleInputChange}
            placeholder="https://example.com"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Phone */}
        <div>
          <label htmlFor="phone" className="block text-body-sm font-medium text-gray-700 mb-2">
            Phone *
          </label>
          <input
            id="phone"
            type="tel"
            name="phone"
            value={data.phone}
            onChange={handleInputChange}
            placeholder="+86 10 1234 5678"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              errors.phone
                ? 'border-red-500'
                : 'border-gray-300'
            }`}
          />
          {errors.phone && (
            <p className="text-body-xs text-red-600 mt-1">{errors.phone}</p>
          )}
        </div>

        {/* Email */}
        <div>
          <label htmlFor="email" className="block text-body-sm font-medium text-gray-700 mb-2">
            Email *
          </label>
          <input
            id="email"
            type="email"
            name="email"
            value={data.email}
            onChange={handleInputChange}
            placeholder="contact@company.com"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              errors.email
                ? 'border-red-500'
                : 'border-gray-300'
            }`}
          />
          {errors.email && (
            <p className="text-body-xs text-red-600 mt-1">{errors.email}</p>
          )}
        </div>

        {/* Country */}
        <div>
          <label htmlFor="country" className="block text-body-sm font-medium text-gray-700 mb-2">
            Country *
          </label>
          <select
            id="country"
            name="country"
            value={data.country}
            onChange={handleInputChange}
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              errors.country
                ? 'border-red-500'
                : 'border-gray-300'
            }`}
          >
            <option value="">Select Country</option>
            {COUNTRIES.map((country) => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>
          {errors.country && (
            <p className="text-body-xs text-red-600 mt-1">{errors.country}</p>
          )}
        </div>

        {/* City */}
        <div>
          <label htmlFor="city" className="block text-body-sm font-medium text-gray-700 mb-2">
            City *
          </label>
          {data.country && cities.length > 0 ? (
            <select
              id="city"
              name="city"
              value={data.city}
              onChange={handleInputChange}
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.city
                  ? 'border-red-500'
                  : 'border-gray-300'
              }`}
            >
              <option value="">Select City</option>
              {cities.map((city) => (
                <option key={city} value={city}>
                  {city}
                </option>
              ))}
            </select>
          ) : (
            <input
              id="city"
              type="text"
              name="city"
              value={data.city}
              onChange={handleInputChange}
              placeholder="Enter city"
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.city
                  ? 'border-red-500'
                  : 'border-gray-300'
              }`}
            />
          )}
          {errors.city && (
            <p className="text-body-xs text-red-600 mt-1">{errors.city}</p>
          )}
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between pt-6 border-t border-gray-200">
        <button
          onClick={onPrevious}
          disabled
          className="px-6 py-2 text-body-sm font-medium text-gray-500 bg-gray-100 rounded-lg cursor-not-allowed"
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
