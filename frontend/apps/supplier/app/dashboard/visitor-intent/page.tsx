'use client'

import { useCallback, useEffect, useState } from 'react'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'
const AUTO_REFRESH_MS = 60_000

interface VisitorSummary {
  supplier_id: number
  total_events: number
  high_intent_count: number
  medium_intent_count: number
  avg_intent_score: number
  latest_event_at?: string | null
  generated_at: string
}

interface VisitorEvent {
  id: number
  visitor_session_id: string
  visitor_email?: string | null
  visitor_company?: string | null
  visitor_country?: string | null
  event_type: string
  page_url?: string | null
  session_duration_seconds?: number | null
  intent_score?: number | null
  intent_level?: string | null
  created_at: string
}

interface OpsMetrics {
  supplier_id: number
  window_hours: number
  total_events: number
  high_intent_events: number
  medium_intent_events: number
  unread_high_intent_notifications: number
  avg_intent_score: number
  alert_high_intent_spike: boolean
  alert_unread_backlog: boolean
  generated_at: string
}

export default function VisitorIntentPage() {
  const [summary, setSummary] = useState<VisitorSummary | null>(null)
  const [events, setEvents] = useState<VisitorEvent[]>([])
  const [opsMetrics, setOpsMetrics] = useState<OpsMetrics | null>(null)
  const [levelFilter, setLevelFilter] = useState<string>('all')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const getHeaders = useCallback(() => {
    const token = localStorage.getItem('access_token')
    return { Authorization: `Bearer ${token}` }
  }, [])

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const eventsUrl = levelFilter !== 'all'
        ? `${API_BASE_URL}/visitor-intent/events?limit=50&level=${levelFilter}`
        : `${API_BASE_URL}/visitor-intent/events?limit=50`

      const [summaryRes, eventsRes, opsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/visitor-intent/summary`, { headers: getHeaders() }),
        fetch(eventsUrl, { headers: getHeaders() }),
        fetch(`${API_BASE_URL}/visitor-intent/ops-metrics?hours=24`, { headers: getHeaders() }),
      ])

      if (!summaryRes.ok || !eventsRes.ok) {
        throw new Error('Failed to load visitor intent data')
      }

      setSummary(await summaryRes.json())
      setEvents(await eventsRes.json())
      if (opsRes.ok) setOpsMetrics(await opsRes.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load visitor intent data')
    } finally {
      setLoading(false)
    }
  }, [getHeaders, levelFilter])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    const id = setInterval(loadData, AUTO_REFRESH_MS)
    return () => clearInterval(id)
  }, [loadData])

  const levelBadge = (level?: string | null) => {
    if (level === 'high') return 'bg-red-100 text-red-700'
    if (level === 'medium') return 'bg-yellow-100 text-yellow-700'
    return 'bg-gray-100 text-gray-700'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-h1 font-bold text-gray-900">Visitor Intent Dashboard</h1>
          <p className="text-body-lg text-gray-600 mt-2">
            Track visitor behavior and identify high-intent opportunities.
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 rounded-lg border border-gray-300 text-sm text-gray-700 hover:bg-gray-50"
        >
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Ops Metrics — 24h monitoring panel */}
      {opsMetrics && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Monitoring · Last 24 h
            </h2>
            <div className="flex gap-2">
              {opsMetrics.alert_high_intent_spike && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">
                  ⚠ High-intent spike
                </span>
              )}
              {opsMetrics.alert_unread_backlog && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 font-medium">
                  ⚠ Unread backlog
                </span>
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div>
              <p className="text-xs text-gray-500">Total Events</p>
              <p className="text-lg font-bold text-gray-900">{opsMetrics.total_events}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">High Intent</p>
              <p className="text-lg font-bold text-red-600">{opsMetrics.high_intent_events}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Medium Intent</p>
              <p className="text-lg font-bold text-yellow-600">{opsMetrics.medium_intent_events}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Unread Alerts</p>
              <p className="text-lg font-bold text-orange-600">{opsMetrics.unread_high_intent_notifications}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Avg Score</p>
              <p className="text-lg font-bold text-primary-600">{opsMetrics.avg_intent_score}</p>
            </div>
          </div>
        </div>
      )}

      {/* Summary KPI cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600">Total Events</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{summary.total_events}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600">High Intent</p>
            <p className="text-2xl font-bold text-red-600 mt-1">{summary.high_intent_count}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600">Medium Intent</p>
            <p className="text-2xl font-bold text-yellow-600 mt-1">{summary.medium_intent_count}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600">Avg Intent Score</p>
            <p className="text-2xl font-bold text-primary-600 mt-1">{summary.avg_intent_score}</p>
          </div>
        </div>
      )}

      {/* Event list with level filter */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-h2 font-semibold text-gray-900">Recent Visitor Events</h2>
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 text-gray-700 bg-white"
          >
            <option value="all">All levels</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        {loading ? (
          <p className="text-sm text-gray-600">Loading…</p>
        ) : events.length === 0 ? (
          <p className="text-sm text-gray-600">No visitor events yet.</p>
        ) : (
          <div className="space-y-3">
            {events.map((event) => (
              <div key={event.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900">
                    {event.event_type} · session {event.visitor_session_id.slice(0, 12)}…
                  </p>
                  <span className={`text-xs px-2 py-1 rounded ${levelBadge(event.intent_level)}`}>
                    {event.intent_level || 'pending'}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {event.visitor_company || 'Unknown company'}{event.visitor_country ? ` · ${event.visitor_country}` : ''}
                </p>
                <p className="text-sm text-gray-600">
                  score: {event.intent_score ?? '–'} · duration: {event.session_duration_seconds ?? 0}s
                </p>
                {event.page_url && <p className="text-xs text-gray-500 mt-1">{event.page_url}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
