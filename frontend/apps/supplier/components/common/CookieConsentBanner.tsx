'use client'

import { useEffect, useState } from 'react'

const CONSENT_KEY = 'fi_cookie_consent'

interface CookieConsentBannerProps {
  onConsentChange?: (accepted: boolean) => void
}

export default function CookieConsentBanner({ onConsentChange }: CookieConsentBannerProps) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const value = localStorage.getItem(CONSENT_KEY)
    const hasChoice = value === 'accepted' || value === 'rejected'
    setVisible(!hasChoice)
    if (hasChoice) {
      onConsentChange?.(value === 'accepted')
    }
  }, [onConsentChange])

  const setConsent = (accepted: boolean) => {
    localStorage.setItem(CONSENT_KEY, accepted ? 'accepted' : 'rejected')
    onConsentChange?.(accepted)
    setVisible(false)
  }

  if (!visible) {
    return null
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:max-w-md z-50 rounded-lg border border-gray-200 bg-white shadow-xl p-4">
      <h3 className="text-sm font-semibold text-gray-900">Cookie Consent</h3>
      <p className="text-sm text-gray-600 mt-2">
        We use cookies to track page interactions for visitor intent analysis. You can accept or reject analytics tracking.
      </p>
      <div className="mt-4 flex gap-2 justify-end">
        <button
          onClick={() => setConsent(false)}
          className="px-3 py-2 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
        >
          Reject
        </button>
        <button
          onClick={() => setConsent(true)}
          className="px-3 py-2 text-sm rounded-lg bg-primary-600 text-white hover:bg-primary-700"
        >
          Accept
        </button>
      </div>
    </div>
  )
}
