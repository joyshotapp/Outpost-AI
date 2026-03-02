'use client'

import { useState, useEffect, useCallback } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface ServiceUsage {
  calls: number
  cost_usd: number
  units?: number
  unit_type?: string
}

interface UsageSummary {
  period: { year: number; month: number }
  total_cost_usd: number
  per_service: Record<string, ServiceUsage>
}

const SERVICE_COLORS: Record<string, string> = {
  openai: 'bg-emerald-500',
  anthropic: 'bg-orange-500',
  heygen: 'bg-pink-500',
  stripe: 'bg-purple-500',
  clay: 'bg-blue-500',
  heyreach: 'bg-cyan-500',
  instantly: 'bg-teal-500',
  apollo: 'bg-indigo-500',
  opusclip: 'bg-rose-500',
  repurpose: 'bg-amber-500',
}

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

export default function AdminApiUsagePage() {
  const [summary, setSummary] = useState<UsageSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [year, setYear] = useState(new Date().getFullYear())
  const [month, setMonth] = useState(new Date().getMonth() + 1)

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

  const fetchSummary = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/admin/api-usage/summary?year=${year}&month=${month}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) setSummary(await res.json())
    } finally {
      setLoading(false)
    }
  }, [year, month, token])

  useEffect(() => { fetchSummary() }, [fetchSummary])

  const maxCost = summary
    ? Math.max(...Object.values(summary.per_service).map((s) => s.cost_usd), 1)
    : 1

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">API Usage Dashboard</h1>
            <p className="text-gray-500 mt-1">Monthly third-party API costs and call volumes</p>
          </div>
          <div className="flex gap-2">
            <select
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none"
            >
              {MONTHS.map((m, i) => <option key={i} value={i+1}>{m}</option>)}
            </select>
            <select
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none"
            >
              {[2025, 2026, 2027].map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
          </div>
        ) : summary ? (
          <>
            {/* Total Cost Banner */}
            <div className="bg-purple-600 text-white rounded-xl p-6 mb-6 flex items-center justify-between">
              <div>
                <p className="text-purple-200 text-sm font-medium">Total API Cost</p>
                <p className="text-4xl font-bold mt-1">${summary.total_cost_usd.toFixed(2)}</p>
                <p className="text-purple-200 text-sm mt-1">{MONTHS[summary.period.month - 1]} {summary.period.year}</p>
              </div>
              <div className="text-right">
                <p className="text-purple-200 text-sm">Services tracked</p>
                <p className="text-3xl font-bold mt-1">{Object.keys(summary.per_service).length}</p>
              </div>
            </div>

            {/* Per-Service Breakdown */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost by Service</h3>
              <div className="space-y-4">
                {Object.entries(summary.per_service)
                  .sort(([, a], [, b]) => b.cost_usd - a.cost_usd)
                  .map(([service, usage]) => (
                    <div key={service}>
                      <div className="flex items-center justify-between text-sm mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className={`w-2.5 h-2.5 rounded-full ${SERVICE_COLORS[service] || 'bg-gray-400'}`} />
                          <span className="font-medium text-gray-900 capitalize">{service}</span>
                          <span className="text-gray-400">
                            {usage.calls.toLocaleString()} calls
                            {usage.units ? ` · ${usage.units.toLocaleString()} ${usage.unit_type || 'units'}` : ''}
                          </span>
                        </div>
                        <span className="font-semibold">${usage.cost_usd.toFixed(4)}</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${SERVICE_COLORS[service] || 'bg-gray-400'}`}
                          style={{ width: `${Math.max(1, (usage.cost_usd / maxCost) * 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    {['Service', 'Calls', 'Units', 'Cost (USD)', '% of Total'].map((h) => (
                      <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {Object.entries(summary.per_service)
                    .sort(([, a], [, b]) => b.cost_usd - a.cost_usd)
                    .map(([service, usage]) => (
                      <tr key={service} className="hover:bg-gray-50">
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-2">
                            <span className={`w-2.5 h-2.5 rounded-full ${SERVICE_COLORS[service] || 'bg-gray-400'}`} />
                            <span className="text-sm font-medium text-gray-900 capitalize">{service}</span>
                          </div>
                        </td>
                        <td className="px-5 py-3 text-sm text-gray-600">{usage.calls.toLocaleString()}</td>
                        <td className="px-5 py-3 text-sm text-gray-600">
                          {usage.units ? `${usage.units.toLocaleString()} ${usage.unit_type || ''}` : '—'}
                        </td>
                        <td className="px-5 py-3 text-sm font-semibold text-gray-900">${usage.cost_usd.toFixed(4)}</td>
                        <td className="px-5 py-3 text-sm text-gray-500">
                          {summary.total_cost_usd > 0 ? `${((usage.cost_usd / summary.total_cost_usd) * 100).toFixed(1)}%` : '—'}
                        </td>
                      </tr>
                    ))}
                  <tr className="bg-gray-50 font-semibold">
                    <td className="px-5 py-3 text-sm text-gray-900">Total</td>
                    <td colSpan={2} />
                    <td className="px-5 py-3 text-sm text-gray-900">${summary.total_cost_usd.toFixed(4)}</td>
                    <td className="px-5 py-3 text-sm text-gray-500">100%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <div className="text-center text-gray-500 py-16">Failed to load API usage data</div>
        )}
      </div>
    </div>
  )
}
