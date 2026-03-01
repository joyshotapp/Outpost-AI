'use client'

import React from 'react'

export type LocalizationStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'skipped'

export interface LanguageVersionStatus {
  language_code: string
  localization_status: LocalizationStatus
  provider_job_id?: string | null
  cdn_url?: string | null
  compression_ratio?: number | null
  error_message?: string | null
  subtitle_url?: string | null
  voice_url?: string | null
}

interface StatusBadgeProps {
  status: LocalizationStatus
}

const STATUS_CONFIG: Record<LocalizationStatus, { label: string; classes: string; icon: React.ReactNode }> = {
  pending: {
    label: 'Pending',
    classes: 'bg-yellow-50 text-yellow-700 border border-yellow-200',
    icon: (
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  processing: {
    label: 'Processing',
    classes: 'bg-blue-50 text-blue-700 border border-blue-200',
    icon: (
      <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
  },
  completed: {
    label: 'Completed',
    classes: 'bg-green-50 text-green-700 border border-green-200',
    icon: (
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
  },
  failed: {
    label: 'Failed',
    classes: 'bg-red-50 text-red-700 border border-red-200',
    icon: (
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
  },
  skipped: {
    label: 'Skipped',
    classes: 'bg-gray-100 text-gray-500 border border-gray-200',
    icon: (
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.classes}`}>
      {config.icon}
      {config.label}
    </span>
  )
}

interface LocalizationStatusPanelProps {
  versions: LanguageVersionStatus[]
  /** Optional: show a "Retry" button per failed version */
  onRetry?: (languageCode: string) => void
}

const LANGUAGE_NAMES: Record<string, string> = {
  en: 'English',
  de: 'German',
  ja: 'Japanese',
  zh: 'Chinese',
  es: 'Spanish',
  fr: 'French',
  ko: 'Korean',
  pt: 'Portuguese',
  it: 'Italian',
  ar: 'Arabic',
}

function getLanguageLabel(code: string): string {
  return LANGUAGE_NAMES[code.toLowerCase()] ?? code.toUpperCase()
}

export default function LocalizationStatusPanel({ versions, onRetry }: LocalizationStatusPanelProps) {
  if (versions.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 p-4 text-center text-sm text-gray-500">
        No language versions yet. Use the Localize button to generate multilingual versions.
      </div>
    )
  }

  const completed = versions.filter((v) => v.localization_status === 'completed').length
  const total = versions.length

  return (
    <div className="space-y-3">
      {/* Summary bar */}
      <div className="flex items-center justify-between text-xs text-gray-600 px-1">
        <span>{total} language version{total !== 1 ? 's' : ''}</span>
        <span className="text-green-600 font-medium">{completed}/{total} completed</span>
      </div>

      {/* Per-language rows */}
      {versions.map((v) => {
        const config = STATUS_CONFIG[v.localization_status] ?? STATUS_CONFIG.pending
        return (
          <div
            key={v.language_code}
            className="border border-gray-200 rounded-lg p-4 space-y-2"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm text-gray-900">
                  {getLanguageLabel(v.language_code)}
                </span>
                <span className="text-xs text-gray-400 uppercase">{v.language_code}</span>
              </div>
              <StatusBadge status={v.localization_status} />
            </div>

            {/* De compression ratio */}
            {v.compression_ratio != null && (
              <p className="text-xs text-gray-500">
                DE compression ratio: <span className="font-medium">{v.compression_ratio.toFixed(2)}</span>
              </p>
            )}

            {/* Provider job ID */}
            {v.provider_job_id && (
              <p className="text-xs text-gray-400 truncate">
                Job: <code className="font-mono">{v.provider_job_id}</code>
              </p>
            )}

            {/* Error message */}
            {v.localization_status === 'failed' && v.error_message && (
              <p className="text-xs text-red-600 bg-red-50 rounded p-2 mt-1">
                {v.error_message}
              </p>
            )}

            {/* Asset links */}
            {v.localization_status === 'completed' && (v.subtitle_url || v.voice_url || v.cdn_url) && (
              <div className="flex gap-3 pt-1">
                {v.cdn_url && (
                  <a
                    href={v.cdn_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-primary-600 hover:underline"
                  >
                    Watch ↗
                  </a>
                )}
                {v.subtitle_url && (
                  <a
                    href={v.subtitle_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-primary-600 hover:underline"
                  >
                    Subtitles ↗
                  </a>
                )}
                {v.voice_url && (
                  <a
                    href={v.voice_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-primary-600 hover:underline"
                  >
                    Dubbed audio ↗
                  </a>
                )}
              </div>
            )}

            {/* Retry button for failed */}
            {v.localization_status === 'failed' && onRetry && (
              <button
                onClick={() => onRetry(v.language_code)}
                className="text-xs font-medium text-red-600 border border-red-300 px-3 py-1 rounded hover:bg-red-50 transition-colors"
              >
                Retry
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}
