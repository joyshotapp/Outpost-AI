import { useCallback, useEffect, useMemo, useRef } from 'react'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const CONSENT_KEY = 'fi_cookie_consent'
const SESSION_KEY = 'fi_visitor_session_id'

interface TrackEventInput {
  eventType: string
  pageUrl?: string
  eventData?: Record<string, unknown>
}

interface UseVisitorTrackingOptions {
  supplierId: number
  enabled?: boolean
}

export function useVisitorTracking({ supplierId, enabled = true }: UseVisitorTrackingOptions) {
  const mountedAtRef = useRef<number>(Date.now())

  const hasConsent = useMemo(() => {
    if (typeof window === 'undefined') return false
    return localStorage.getItem(CONSENT_KEY) === 'accepted'
  }, [])

  const visitorSessionId = useMemo(() => {
    if (typeof window === 'undefined') {
      return ''
    }
    const existing = window.localStorage.getItem(SESSION_KEY)
    if (existing) {
      return existing
    }
    const generated = `visitor-${crypto.randomUUID()}`
    window.localStorage.setItem(SESSION_KEY, generated)
    return generated
  }, [])

  const trackEvent = useCallback(
    async ({ eventType, pageUrl, eventData }: TrackEventInput) => {
      if (!enabled || !hasConsent || !visitorSessionId || !supplierId) {
        return
      }

      const sessionDurationSeconds = Math.max(
        0,
        Math.round((Date.now() - mountedAtRef.current) / 1000)
      )

      try {
        await fetch(`${API_BASE_URL}/api/v1/visitor-intent/events`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            supplier_id: supplierId,
            visitor_session_id: visitorSessionId,
            event_type: eventType,
            page_url: pageUrl || (typeof window !== 'undefined' ? window.location.pathname : ''),
            event_data: eventData || null,
            session_duration_seconds: sessionDurationSeconds,
            consent_given: true,
          }),
        })
      } catch {
        // Intentionally swallow tracking failures to avoid impacting UI interactions.
      }
    },
    [enabled, hasConsent, visitorSessionId, supplierId]
  )

  useEffect(() => {
    if (!enabled || !hasConsent) {
      return
    }

    trackEvent({
      eventType: 'page_view',
      pageUrl: typeof window !== 'undefined' ? window.location.pathname : '',
    })
  }, [enabled, hasConsent, trackEvent])

  return {
    hasConsent,
    trackEvent,
    visitorSessionId,
  }
}
