'use client'

import React, { useState } from 'react'
import Image from 'next/image'

interface ProfileImagesProps {
  onSave: () => void
  isSaving: boolean
}

export default function ProfileImages({
  onSave,
  isSaving,
}: ProfileImagesProps) {
  const [logo, setLogo] = useState<string | null>(null)
  const [coverImage, setCoverImage] = useState<string | null>(null)
  const [galleryImages, setGalleryImages] = useState<string[]>([])
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      simulateUpload(file, 'logo', setLogo)
    }
  }

  const handleCoverChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      simulateUpload(file, 'cover', setCoverImage)
    }
  }

  const handleGalleryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files) {
      Array.from(files).forEach((file, index) => {
        simulateUpload(file, `gallery-${index}`, (url) => {
          setGalleryImages((prev) => [...prev, url])
        })
      })
    }
  }

  const simulateUpload = (
    file: File,
    key: string,
    callback: (url: string) => void
  ) => {
    setUploadProgress((prev) => ({ ...prev, [key]: 0 }))

    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        const current = prev[key] || 0
        const next = Math.min(current + Math.random() * 30, 95)
        if (next >= 95) {
          clearInterval(interval)
          setUploadProgress((p) => ({ ...p, [key]: 100 }))
          callback(URL.createObjectURL(file))
          setTimeout(() => {
            setUploadProgress((p) => {
              const { [key]: _, ...rest } = p
              return rest
            })
          }, 500)
        }
        return { ...prev, [key]: next }
      })
    }, 200)
  }

  const removeGalleryImage = (index: number) => {
    setGalleryImages((prev) => prev.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-8">
      {/* Logo Upload */}
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
        <div className="text-center">
          {logo ? (
            <div className="mb-4 flex justify-center">
              <div className="relative w-32 h-32 bg-gray-100 rounded-lg overflow-hidden">
                <Image
                  src={logo}
                  alt="Company Logo"
                  fill
                  className="object-cover"
                />
              </div>
            </div>
          ) : (
            <svg
              className="w-12 h-12 text-gray-400 mx-auto mb-4"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
                clipRule="evenodd"
              />
            </svg>
          )}

          <h3 className="text-body-lg font-semibold text-gray-900 mb-1">
            Company Logo
          </h3>
          <p className="text-body-sm text-gray-600 mb-4">
            Upload your company logo (PNG, JPG, max 5MB)
          </p>

          <label className="inline-block px-4 py-2 bg-primary-600 text-white text-body-sm font-medium rounded-lg hover:bg-primary-700 cursor-pointer transition-colors">
            Choose Logo
            <input
              type="file"
              accept="image/*"
              onChange={handleLogoChange}
              className="hidden"
            />
          </label>

          {uploadProgress.logo !== undefined && (
            <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all"
                style={{ width: `${uploadProgress.logo}%` }}
              />
            </div>
          )}
        </div>
      </div>

      {/* Cover Image Upload */}
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
        <div className="text-center">
          {coverImage ? (
            <div className="mb-4 flex justify-center">
              <div className="relative w-full h-40 bg-gray-100 rounded-lg overflow-hidden">
                <Image
                  src={coverImage}
                  alt="Cover Image"
                  fill
                  className="object-cover"
                />
              </div>
            </div>
          ) : (
            <svg
              className="w-12 h-12 text-gray-400 mx-auto mb-4"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
                clipRule="evenodd"
              />
            </svg>
          )}

          <h3 className="text-body-lg font-semibold text-gray-900 mb-1">
            Cover Image
          </h3>
          <p className="text-body-sm text-gray-600 mb-4">
            Upload a cover image for your profile (PNG, JPG, max 10MB)
          </p>

          <label className="inline-block px-4 py-2 bg-primary-600 text-white text-body-sm font-medium rounded-lg hover:bg-primary-700 cursor-pointer transition-colors">
            Choose Cover
            <input
              type="file"
              accept="image/*"
              onChange={handleCoverChange}
              className="hidden"
            />
          </label>

          {uploadProgress.cover !== undefined && (
            <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all"
                style={{ width: `${uploadProgress.cover}%` }}
              />
            </div>
          )}
        </div>
      </div>

      {/* Gallery Images */}
      <div>
        <h3 className="text-body-lg font-semibold text-gray-900 mb-4">
          Product Gallery
        </h3>

        {galleryImages.length > 0 && (
          <div className="mb-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {galleryImages.map((image, index) => (
              <div key={index} className="relative group">
                <div className="relative w-full h-32 bg-gray-100 rounded-lg overflow-hidden">
                  <Image
                    src={image}
                    alt={`Gallery image ${index + 1}`}
                    fill
                    className="object-cover"
                  />
                </div>
                <button
                  onClick={() => removeGalleryImage(index)}
                  className="absolute top-2 right-2 p-1 bg-red-600 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <svg
            className="w-12 h-12 text-gray-400 mx-auto mb-4"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
              clipRule="evenodd"
            />
          </svg>

          <p className="text-body-sm text-gray-600 mb-4">
            Upload product photos to showcase your capabilities
          </p>

          <label className="inline-block px-4 py-2 bg-primary-600 text-white text-body-sm font-medium rounded-lg hover:bg-primary-700 cursor-pointer transition-colors">
            Add Images
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={handleGalleryChange}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
        <button className="px-6 py-2 text-body-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          Cancel
        </button>
        <button
          onClick={onSave}
          disabled={isSaving}
          className="px-6 py-2 text-body-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isSaving && (
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
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}
