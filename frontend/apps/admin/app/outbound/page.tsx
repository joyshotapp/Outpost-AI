'use client'

import { useState, useEffect, useCallback } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'

interface OutboundHealth {
  linkedin: {
    total_contacts: number
    connected: number
    blocked: number
    ban_rate: number
    daily_limit: number
    alert: boolean
  }
  email: {
    total_sequences: number
    active: number
    bounced: number
    bounce_rate: number
    daily_limit: number
    alert: boolean
  }
}

function MetricBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium">{value.toLocaleString()} / {max.toLocaleString()}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function AlertBadge({ triggered, label }: { triggered: boolean; label: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium ${
      triggered ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
    }`}>
      <span>{triggered ? '⚠️' : '✓'}</span>
      {triggered ? `Alert: ${label}` : `OK: ${label}`}
    </span>
  )
}

export default function AdminOutboundHealthPage() {
  const [health, setHealth] = useState<OutboundHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const token = typeof window !== 'undefined' ? (localStorage.getItem('token') || localStorage.getItem('auth_token')) : null

  const fetchHealth = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/admin/outbound/health`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        setHealth(await res.json())
        setLastRefresh(new Date())
      }
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => { fetchHealth() }, [fetchHealth])

  return (
    <div>
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Outbound System Health</h1>
            <p className="text-gray-500 mt-1">LinkedIn and Email outbound performance metrics</p>
          </div>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center gap-2"
          >
            {loading ? <span className="animate-spin">⟳</span> : '⟳'} Refresh
          </button>
        </div>
        {lastRefresh && <p className="text-xs text-gray-400 mb-6">Last updated: {lastRefresh.toLocaleTimeString()}</p>}

        {loading && !health ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
          </div>
        ) : health ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* LinkedIn Panel */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <span>💼</span> LinkedIn Outbound
                </h2>
                <AlertBadge triggered={health.linkedin.alert} label={health.linkedin.alert ? 'High ban rate' : 'Healthy'} />
              </div>

              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{health.linkedin.total_contacts.toLocaleString()}</div>
                  <div className="text-xs text-gray-500 mt-0.5">Total Contacts</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{health.linkedin.connected.toLocaleString()}</div>
                  <div className="text-xs text-gray-500 mt-0.5">Connected</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${health.linkedin.blocked > 0 ? 'text-red-600' : 'text-gray-400'}`}>
                    {health.linkedin.blocked.toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">Blocked</div>
                </div>
              </div>

              <div className="space-y-4">
                <MetricBar
                  label="Connected rate"
                  value={health.linkedin.connected}
                  max={health.linkedin.total_contacts}
                  color="bg-green-500"
                />
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Ban rate</span>
                    <span className={`font-medium ${health.linkedin.alert ? 'text-red-600' : 'text-gray-900'}`}>
                      {(health.linkedin.ban_rate * 100).toFixed(2)}%
                    </span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${health.linkedin.alert ? 'bg-red-500' : 'bg-green-500'}`}
                      style={{ width: `${Math.min(100, health.linkedin.ban_rate * 100 * 20)}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-1">Alert threshold: 5%</p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100 text-sm text-gray-500">
                Daily connection limit: <span className="font-medium text-gray-900">{health.linkedin.daily_limit}</span>
              </div>
            </div>

            {/* Email Panel */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <span>📧</span> Email Outbound
                </h2>
                <AlertBadge triggered={health.email.alert} label={health.email.alert ? 'High bounce rate' : 'Healthy'} />
              </div>

              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{health.email.total_sequences.toLocaleString()}</div>
                  <div className="text-xs text-gray-500 mt-0.5">Total Sequences</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{health.email.active.toLocaleString()}</div>
                  <div className="text-xs text-gray-500 mt-0.5">Active</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${health.email.bounced > 0 ? 'text-red-600' : 'text-gray-400'}`}>
                    {health.email.bounced.toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">Bounced</div>
                </div>
              </div>

              <div className="space-y-4">
                <MetricBar
                  label="Active sequences"
                  value={health.email.active}
                  max={health.email.total_sequences}
                  color="bg-blue-500"
                />
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Bounce rate</span>
                    <span className={`font-medium ${health.email.alert ? 'text-red-600' : 'text-gray-900'}`}>
                      {(health.email.bounce_rate * 100).toFixed(2)}%
                    </span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${health.email.alert ? 'bg-red-500' : 'bg-green-500'}`}
                      style={{ width: `${Math.min(100, health.email.bounce_rate * 100 * 50)}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-1">Alert threshold: 2%</p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100 text-sm text-gray-500">
                Daily send limit: <span className="font-medium text-gray-900">{health.email.daily_limit}</span>
              </div>
            </div>

            {/* Overall Health Summary */}
            <div className="md:col-span-2 bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Health Summary</h3>
              <div className="flex gap-4 flex-wrap">
                <AlertBadge triggered={health.linkedin.alert} label="LinkedIn ban rate" />
                <AlertBadge triggered={health.email.alert} label="Email bounce rate" />
                <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium ${
                  !health.linkedin.alert && !health.email.alert ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {!health.linkedin.alert && !health.email.alert
                    ? '✓ All systems operational'
                    : '⚠️ Action required — review alerts above'}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-500 py-16">Failed to load outbound health data</div>
        )}
      </div>
    </div>
  )
}
