'use client'

import React, { useState, useRef } from 'react'

interface VideoUploaderProps {
  onSuccess: (video: any) => void
  onCancel: () => void
}

interface Language {
  code: string
  title: string
  subtitle?: string
  dubbed?: boolean
}

export default function VideoUploader({
  onSuccess,
  onCancel,
}: VideoUploaderProps) {
  const [dragActive, setDragActive] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [videoTitle, setVideoTitle] = useState('')
  const [videoType, setVideoType] = useState<'product-demo' | 'company-intro' | 'testimonial' | 'other'>('product-demo')
  const [languages, setLanguages] = useState<Language[]>([
    { code: 'en', title: '' },
  ])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const availableLanguages = [
    { code: 'en', label: 'English' },
    { code: 'zh', label: 'Chinese' },
    { code: 'es', label: 'Spanish' },
    { code: 'fr', label: 'French' },
    { code: 'de', label: 'German' },
    { code: 'ja', label: 'Japanese' },
  ]

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile?.type.startsWith('video/')) {
      setFile(droppedFile)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile?.type.startsWith('video/')) {
      setFile(selectedFile)
    }
  }

  const addLanguage = () => {
    const unusedLang = availableLanguages.find(
      (l) => !languages.find((lang) => lang.code === l.code)
    )
    if (unusedLang) {
      setLanguages([...languages, { code: unusedLang.code, title: '' }])
    }
  }

  const removeLanguage = (code: string) => {
    if (code !== 'en') {
      setLanguages(languages.filter((l) => l.code !== code))
    }
  }

  const updateLanguage = (code: string, field: string, value: string | boolean) => {
    setLanguages(
      languages.map((l) =>
        l.code === code ? { ...l, [field]: value } : l
      )
    )
  }

  const handleUpload = async () => {
    if (!file || !videoTitle) {
      alert('Please select a video and enter a title')
      return
    }

    setIsUploading(true)

    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 95) {
          clearInterval(interval)
          return 95
        }
        return prev + Math.random() * 20
      })
    }, 500)

    // Simulate upload completion
    setTimeout(() => {
      setUploadProgress(100)
      clearInterval(interval)
      setIsUploading(false)

      // Call success callback
      onSuccess({
        id: Math.random().toString(),
        title: videoTitle,
        type: videoType,
        duration: 0,
        uploadedAt: new Date(),
        isPublished: false,
        languages,
      })
    }, 3000)
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-6">
      {/* File Upload */}
      <div>
        <h2 className="text-h2 font-semibold text-gray-900 mb-4">Upload Video</h2>

        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            dragActive
              ? 'border-primary-600 bg-primary-50'
              : 'border-gray-300 bg-gray-50'
          } ${file ? 'border-green-500 bg-green-50' : ''}`}
        >
          {file ? (
            <div className="space-y-2">
              <svg
                className="w-12 h-12 text-green-600 mx-auto"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="text-body-lg font-medium text-green-900">{file.name}</p>
              <p className="text-body-sm text-green-700">
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </p>
              <button
                onClick={() => setFile(null)}
                className="text-primary-600 text-body-sm font-medium hover:text-primary-700"
              >
                Choose Different Video
              </button>
            </div>
          ) : (
            <>
              <svg
                className="w-12 h-12 text-gray-400 mx-auto mb-4"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M2 6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm4 2v4h8V8H6z" />
              </svg>
              <p className="text-body-lg font-medium text-gray-900 mb-1">
                Drag and drop your video here
              </p>
              <p className="text-body-sm text-gray-600 mb-4">
                or click the button below (MP4, WebM, MOV - max 2GB)
              </p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-primary-600 text-white text-body-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
              >
                Choose Video
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                onChange={handleFileSelect}
                className="hidden"
              />
            </>
          )}
        </div>
      </div>

      {/* Video Details */}
      {file && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Video Title */}
            <div>
              <label htmlFor="title" className="block text-body-sm font-medium text-gray-700 mb-2">
                Video Title *
              </label>
              <input
                id="title"
                type="text"
                value={videoTitle}
                onChange={(e) => setVideoTitle(e.target.value)}
                placeholder="e.g. CNC Machining Process"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            {/* Video Type */}
            <div>
              <label htmlFor="type" className="block text-body-sm font-medium text-gray-700 mb-2">
                Video Type
              </label>
              <select
                id="type"
                value={videoType}
                onChange={(e) => setVideoType(e.target.value as any)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="product-demo">Product Demo</option>
                <option value="company-intro">Company Introduction</option>
                <option value="testimonial">Customer Testimonial</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          {/* Language Versions */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-body-lg font-semibold text-gray-900">
                Language Versions
              </h3>
              <button
                onClick={addLanguage}
                disabled={languages.length >= availableLanguages.length}
                className="px-3 py-1 text-body-sm font-medium text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                + Add Language
              </button>
            </div>

            <div className="space-y-4">
              {languages.map((lang) => (
                <div key={lang.code} className="border border-gray-200 rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-gray-900">
                      {availableLanguages.find((l) => l.code === lang.code)?.label}
                    </h4>
                    {lang.code !== 'en' && (
                      <button
                        onClick={() => removeLanguage(lang.code)}
                        className="text-red-600 text-body-sm font-medium hover:text-red-700"
                      >
                        Remove
                      </button>
                    )}
                  </div>

                  <input
                    type="text"
                    value={lang.title}
                    onChange={(e) =>
                      updateLanguage(lang.code, 'title', e.target.value)
                    }
                    placeholder="Video title in this language"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />

                  <input
                    type="text"
                    value={lang.subtitle || ''}
                    onChange={(e) =>
                      updateLanguage(lang.code, 'subtitle', e.target.value)
                    }
                    placeholder="Subtitle file URL (optional)"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />

                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={lang.dubbed || false}
                      onChange={(e) =>
                        updateLanguage(lang.code, 'dubbed', e.target.checked)
                      }
                      className="w-4 h-4 text-primary-600 rounded"
                    />
                    <span className="text-body-sm text-gray-700">
                      Has dubbed audio for this language
                    </span>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Upload Progress */}
          {isUploading && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-body-sm font-medium text-gray-900">
                  Uploading...
                </p>
                <span className="text-body-sm font-medium text-gray-600">
                  {Math.round(uploadProgress)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
            <button
              onClick={onCancel}
              disabled={isUploading}
              className="px-6 py-2 text-body-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              onClick={handleUpload}
              disabled={isUploading || !videoTitle}
              className="px-6 py-2 text-body-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isUploading && (
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
              {isUploading ? 'Uploading...' : 'Upload Video'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
