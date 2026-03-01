'use client'

import React, { useState } from 'react'

export interface VideoLanguageOption {
  code: string
  label: string
  video_url?: string | null
  cdn_url?: string | null
  subtitle_url?: string | null
  localization_status?: string
}

interface VideoPlayerWithLanguageSwitcherProps {
  videoTitle: string
  /** Source (original) video URL */
  sourceVideoUrl: string
  /** All available language versions including the original */
  languageVersions: VideoLanguageOption[]
  className?: string
}

const LANGUAGE_NAMES: Record<string, string> = {
  en: 'English',
  de: 'Deutsch',
  ja: '日本語',
  zh: '中文',
  es: 'Español',
  fr: 'Français',
  ko: '한국어',
  pt: 'Português',
  it: 'Italiano',
  ar: 'العربية',
}

function getLanguageLabel(code: string): string {
  return LANGUAGE_NAMES[code.toLowerCase()] ?? code.toUpperCase()
}

export default function VideoPlayerWithLanguageSwitcher({
  videoTitle,
  sourceVideoUrl,
  languageVersions,
  className = '',
}: VideoPlayerWithLanguageSwitcherProps) {
  const [selectedCode, setSelectedCode] = useState<string>(() => {
    // Default to first completed version if available, else source
    const first = languageVersions.find((v) => v.localization_status === 'completed')
    return first?.code ?? 'original'
  })

  const currentVersion =
    selectedCode === 'original'
      ? null
      : languageVersions.find((v) => v.code === selectedCode) ?? null

  // Resolve active URL: prefer cdn_url, then video_url, then fallback to source
  const activeVideoUrl =
    currentVersion?.cdn_url ??
    currentVersion?.video_url ??
    sourceVideoUrl

  const activeSubtitleUrl = currentVersion?.subtitle_url ?? null

  // Available options: original always first, then completed versions
  const completedVersions = languageVersions.filter(
    (v) => v.localization_status === 'completed' || !v.localization_status
  )

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Video Player */}
      <div className="relative w-full bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
        <video
          key={activeVideoUrl}
          controls
          className="w-full h-full"
          preload="metadata"
          crossOrigin="anonymous"
        >
          <source src={activeVideoUrl} />
          {activeSubtitleUrl && (
            <track
              kind="subtitles"
              src={activeSubtitleUrl}
              srcLang={selectedCode === 'original' ? 'en' : selectedCode}
              label={selectedCode === 'original' ? 'Original' : getLanguageLabel(selectedCode)}
              default
            />
          )}
          Your browser does not support the video tag.
        </video>

        {/* Language badge overlay */}
        <div className="absolute top-3 left-3">
          <span className="bg-black bg-opacity-60 text-white text-xs font-medium px-2 py-1 rounded">
            {selectedCode === 'original' ? 'Original' : getLanguageLabel(selectedCode)}
          </span>
        </div>
      </div>

      {/* Language Switcher */}
      {(completedVersions.length > 0 || languageVersions.length > 0) && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-gray-500 font-medium shrink-0">Language:</span>

          {/* Original */}
          <button
            onClick={() => setSelectedCode('original')}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              selectedCode === 'original'
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Original
          </button>

          {/* Localised versions */}
          {completedVersions.map((v) => (
            <button
              key={v.code}
              onClick={() => setSelectedCode(v.code)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                selectedCode === v.code
                  ? 'bg-primary-600 text-white'
                  : 'bg-primary-50 text-primary-700 hover:bg-primary-100'
              }`}
            >
              {v.label || getLanguageLabel(v.code)}
            </button>
          ))}

          {/* Pending/processing hint */}
          {languageVersions.some((v) => v.localization_status === 'processing' || v.localization_status === 'pending') && (
            <span className="text-xs text-gray-400 italic">
              More languages coming soon…
            </span>
          )}
        </div>
      )}
    </div>
  )
}
