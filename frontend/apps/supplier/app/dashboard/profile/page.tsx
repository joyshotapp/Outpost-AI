'use client'

import React, { useState } from 'react'
import ProfileBasicInfo from '@/components/profile/ProfileBasicInfo'
import ProfileContactInfo from '@/components/profile/ProfileContactInfo'
import ProfileImages from '@/components/profile/ProfileImages'

type TabType = 'basic' | 'contact' | 'images'

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState<TabType>('basic')
  const [isSaving, setIsSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const tabs = [
    { id: 'basic', label: 'Basic Information' },
    { id: 'contact', label: 'Contact & Business' },
    { id: 'images', label: 'Images & Media' },
  ] as const

  const handleSave = () => {
    setIsSaving(true)
    setTimeout(() => {
      setIsSaving(false)
      setSuccessMessage('Profile updated successfully!')
      setTimeout(() => setSuccessMessage(null), 3000)
    }, 1000)
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-h1 font-bold text-gray-900">Company Profile</h1>
        <p className="text-body-lg text-gray-600 mt-2">
          Manage your company information and media
        </p>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
          <svg
            className="w-5 h-5 text-green-600 flex-shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          <p className="text-body-sm text-green-800">{successMessage}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 flex">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`flex-1 py-4 px-4 text-center font-medium text-body-sm border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'text-primary-600 border-primary-600'
                  : 'text-gray-600 border-transparent hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'basic' && (
            <ProfileBasicInfo onSave={handleSave} isSaving={isSaving} />
          )}
          {activeTab === 'contact' && (
            <ProfileContactInfo onSave={handleSave} isSaving={isSaving} />
          )}
          {activeTab === 'images' && (
            <ProfileImages onSave={handleSave} isSaving={isSaving} />
          )}
        </div>
      </div>
    </div>
  )
}
