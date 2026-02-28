'use client'

import React, { useState } from 'react'
import Image from 'next/image'

interface Language {
  code: string
  title: string
  subtitle?: string
  dubbed?: boolean
}

interface Video {
  id: string
  title: string
  type: 'product-demo' | 'company-intro' | 'testimonial' | 'other'
  duration: number
  thumbnail?: string
  uploadedAt: Date
  isPublished: boolean
  languages: Language[]
}

interface VideoListProps {
  videos: Video[]
}

const typeLabels = {
  'product-demo': 'Product Demo',
  'company-intro': 'Company Introduction',
  testimonial: 'Testimonial',
  other: 'Other',
}

const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`
}

const formatDate = (date: Date) => {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export default function VideoList({ videos }: VideoListProps) {
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null)
  const [editingLanguages, setEditingLanguages] = useState<boolean>(false)

  if (videos.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <svg
          className="w-12 h-12 text-gray-400 mx-auto mb-4"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M2 6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm4 2v4h8V8H6z" />
        </svg>
        <h3 className="text-body-lg font-semibold text-gray-900 mb-2">
          No videos yet
        </h3>
        <p className="text-body-sm text-gray-600">
          Upload your first video to get started
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Videos Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {videos.map((video) => (
          <div
            key={video.id}
            className="bg-white rounded-lg shadow overflow-hidden hover:shadow-lg transition-shadow"
          >
            {/* Video Thumbnail */}
            <div className="relative w-full h-40 bg-gray-900 flex items-center justify-center group cursor-pointer">
              {video.thumbnail ? (
                <Image
                  src={video.thumbnail}
                  alt={video.title}
                  fill
                  className="object-cover"
                />
              ) : (
                <svg
                  className="w-12 h-12 text-gray-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M2 6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm4 2v4h8V8H6z" />
                </svg>
              )}

              {/* Play button overlay */}
              <button className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all">
                <svg
                  className="w-12 h-12 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                </svg>
              </button>

              {/* Duration badge */}
              {video.duration > 0 && (
                <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-body-xs font-medium px-2 py-1 rounded">
                  {formatDuration(video.duration)}
                </div>
              )}

              {/* Published badge */}
              {video.isPublished && (
                <div className="absolute top-2 right-2 bg-green-500 text-white text-body-xs font-medium px-2 py-1 rounded">
                  Published
                </div>
              )}
            </div>

            {/* Video Info */}
            <div className="p-4 space-y-3">
              <div>
                <h3 className="text-body-sm font-semibold text-gray-900 truncate">
                  {video.title}
                </h3>
                <p className="text-body-xs text-gray-500 mt-1">
                  {typeLabels[video.type]} • {formatDate(video.uploadedAt)}
                </p>
              </div>

              {/* Languages */}
              <div className="space-y-1">
                <p className="text-body-xs font-medium text-gray-700">Languages:</p>
                <div className="flex flex-wrap gap-1">
                  {video.languages.slice(0, 3).map((lang) => (
                    <span
                      key={lang.code}
                      className="inline-block px-2 py-1 bg-primary-50 text-primary-700 text-body-xs rounded"
                    >
                      {lang.code.toUpperCase()}
                    </span>
                  ))}
                  {video.languages.length > 3 && (
                    <span className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-body-xs rounded">
                      +{video.languages.length - 3}
                    </span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-2 border-t border-gray-200">
                <button
                  onClick={() => setSelectedVideo(video)}
                  className="flex-1 px-3 py-2 text-body-xs font-medium text-primary-600 border border-primary-600 rounded hover:bg-primary-50 transition-colors"
                >
                  Edit
                </button>
                <button className="flex-1 px-3 py-2 text-body-xs font-medium text-red-600 border border-red-600 rounded hover:bg-red-50 transition-colors">
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Video Details Modal */}
      {selectedVideo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
              <h2 className="text-h2 font-semibold text-gray-900">
                {selectedVideo.title}
              </h2>
              <button
                onClick={() => setSelectedVideo(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Video Details */}
              <div className="space-y-4">
                <div>
                  <label className="text-body-sm font-medium text-gray-700">
                    Type
                  </label>
                  <p className="text-body-sm text-gray-900 mt-1">
                    {typeLabels[selectedVideo.type]}
                  </p>
                </div>
                <div>
                  <label className="text-body-sm font-medium text-gray-700">
                    Uploaded
                  </label>
                  <p className="text-body-sm text-gray-900 mt-1">
                    {formatDate(selectedVideo.uploadedAt)}
                  </p>
                </div>
                <div>
                  <label className="text-body-sm font-medium text-gray-700">
                    Status
                  </label>
                  <p className="text-body-sm mt-1">
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-body-xs font-medium ${
                        selectedVideo.isPublished
                          ? 'bg-green-50 text-green-700'
                          : 'bg-yellow-50 text-yellow-700'
                      }`}
                    >
                      {selectedVideo.isPublished ? 'Published' : 'Draft'}
                    </span>
                  </p>
                </div>
              </div>

              {/* Language Versions */}
              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-body-lg font-semibold text-gray-900 mb-4">
                  Language Versions
                </h3>
                <div className="space-y-3">
                  {selectedVideo.languages.map((lang) => (
                    <div
                      key={lang.code}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">
                          {lang.code.toUpperCase()}
                        </h4>
                        {lang.dubbed && (
                          <span className="text-body-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                            Dubbed
                          </span>
                        )}
                      </div>
                      <p className="text-body-sm text-gray-700">{lang.title}</p>
                      {lang.subtitle && (
                        <p className="text-body-xs text-gray-500 mt-1">
                          Subtitles: {lang.subtitle}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="border-t border-gray-200 pt-6 flex gap-3">
                <button className="flex-1 px-4 py-2 text-body-sm font-medium text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 transition-colors">
                  Publish
                </button>
                <button className="flex-1 px-4 py-2 text-body-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                  Edit Languages
                </button>
                <button className="px-4 py-2 text-body-sm font-medium text-red-600 border border-red-600 rounded-lg hover:bg-red-50 transition-colors">
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
