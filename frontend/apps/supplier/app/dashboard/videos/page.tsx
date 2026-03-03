'use client'

import React, { useState } from 'react'
import VideoUploader from '@/components/videos/VideoUploader'
import VideoList from '@/components/videos/VideoList'

type ViewMode = 'upload' | 'list'

interface Video {
  id: string
  title: string
  type: 'product-demo' | 'company-intro' | 'testimonial' | 'other'
  duration: number
  thumbnail?: string
  uploadedAt: Date
  isPublished: boolean
  languages: Array<{
    code: string
    title: string
    subtitle?: string
    dubbed?: boolean
  }>
}

interface VideoRecord {
  id: number
  title: string
  video_type: string | null
  thumbnail_url: string | null
  is_published: boolean
  created_at: string
}

const mockVideos: Video[] = [
  {
    id: '1',
    title: 'Product Demo - CNC Machining',
    type: 'product-demo',
    duration: 180,
    thumbnail: 'https://via.placeholder.com/300x200',
    uploadedAt: new Date('2024-02-20'),
    isPublished: true,
    languages: [
      { code: 'en', title: 'Product Demo - CNC Machining' },
      { code: 'zh', title: '产品演示 - 数控加工' },
      { code: 'es', title: 'Demostración de Producto - Mecanizado CNC' },
    ],
  },
  {
    id: '2',
    title: 'Company Overview',
    type: 'company-intro',
    duration: 240,
    uploadedAt: new Date('2024-02-15'),
    isPublished: true,
    languages: [
      { code: 'en', title: 'Company Overview' },
      { code: 'zh', title: '公司概览' },
    ],
  },
  {
    id: '3',
    title: 'Production Facility Tour',
    type: 'product-demo',
    duration: 420,
    uploadedAt: new Date('2024-02-10'),
    isPublished: false,
    languages: [{ code: 'en', title: 'Production Facility Tour' }],
  },
]

export default function VideosPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [videos, setVideos] = useState<Video[]>(mockVideos)

  const mapVideoType = (videoType: string | null): Video['type'] => {
    if (videoType === 'product-demo' || videoType === 'company-intro' || videoType === 'testimonial' || videoType === 'other') {
      return videoType
    }
    return 'other'
  }

  const handleVideoUploaded = (newVideo: VideoRecord) => {
    const mappedVideo: Video = {
      id: String(newVideo.id),
      title: newVideo.title,
      type: mapVideoType(newVideo.video_type),
      duration: 0,
      thumbnail: newVideo.thumbnail_url || undefined,
      uploadedAt: new Date(newVideo.created_at),
      isPublished: newVideo.is_published,
      languages: [{ code: 'en', title: newVideo.title }],
    }
    setVideos((prev) => [mappedVideo, ...prev])
    setViewMode('list')
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-h1 font-bold text-gray-900">Product Videos</h1>
          <p className="text-body-lg text-gray-600 mt-2">
            Upload and manage videos to showcase your products and company
          </p>
        </div>
        {viewMode === 'list' && (
          <button
            onClick={() => setViewMode('upload')}
            className="px-6 py-2 text-body-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5.5 13a3.5 3.5 0 01-.369-6.98 4 4 0 117.753-1.3A4.5 4.5 0 1113.5 13H11V9.413l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13H5.5z" />
            </svg>
            Upload New Video
          </button>
        )}
      </div>

      {/* Content */}
      {viewMode === 'upload' ? (
        <VideoUploader
          supplierId={1}
          onSuccess={handleVideoUploaded}
          onCancel={() => setViewMode('list')}
        />
      ) : (
        <VideoList videos={videos} />
      )}
    </div>
  )
}
