'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'

interface KPI {
  suppliers: { total: number; active: number; verified: number }
  buyers: { total: number }
  rfqs: { total: number; open: number }
  subscriptions: Record<string, number>
  mrr_usd: number
}

function StatCard({ label, value, sub, accent = false }: { label: string; value: string | number; sub?: string; accent?: boolean }) {
  return (
    <div className={`rounded-xl p-6 border ${accent ? 'bg-purple-600 text-white border-purple-500' : 'bg-white border-gray-200'}`}>
      <p className={`text-sm font-medium ${accent ? 'text-purple-200' : 'text-gray-500'}`}>{label}</p>
      <p className={`text-3xl font-bold mt-1 ${accent ? 'text-white' : 'text-gray-900'}`}>{value}</p>
      {sub && <p className={`text-xs mt-1 ${accent ? 'text-purple-200' : 'text-gray-400'}`}>{sub}</p>}
    </div>
  )
}

export default function AdminDashboardPage() {
  const router = useRouter()
  const [kpi, setKpi] = useState<KPI | null>(null)
  const [loading, setLoading] = useState(true)

  const token =
    typeof window !== 'undefined'
      ? (localStorage.getItem('token') || localStorage.getItem('auth_token') || localStorage.getItem('access_token'))
      : null

  useEffect(() => {
    const controller = new AbortController()

    const fetchKPI = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${API}/admin/kpi/overview`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          signal: controller.signal,
        })
        if (res.status === 401) {
          localStorage.removeItem('token')
          localStorage.removeItem('auth_token')
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
          router.replace('/login')
          return
        }
        if (res.ok) setKpi(await res.json())
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') return
        setKpi(null)
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    fetchKPI()
    return () => controller.abort()
  }, [token, router])

  const TIER_COLORS: Record<string, string> = {
    free: 'bg-gray-100 text-gray-600',
    starter: 'bg-blue-100 text-blue-700',
    professional: 'bg-purple-100 text-purple-700',
    enterprise: 'bg-amber-100 text-amber-700',
  }

  return (
    <>
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Platform Overview</h2>
          <p className="text-gray-500 mt-1">Real-time platform KPIs and metrics</p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
          </div>
        ) : kpi ? (
          <>
            {/* KPI Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatCard label="Total Suppliers" value={kpi.suppliers.total.toLocaleString()} sub={`${kpi.suppliers.active} active · ${kpi.suppliers.verified} verified`} />
              <StatCard label="Total Buyers" value={kpi.buyers.total.toLocaleString()} />
              <StatCard label="Total RFQs" value={kpi.rfqs.total.toLocaleString()} sub={`${kpi.rfqs.open} open`} />
              <StatCard label="Est. MRR" value={`$${kpi.mrr_usd.toLocaleString()}`} accent />
            </div>

            {/* Subscription Breakdown */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Subscription Breakdown</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {(['free', 'starter', 'professional', 'enterprise'] as const).map((tier) => (
                  <div key={tier} className="text-center">
                    <div className="text-3xl font-bold text-gray-900">{kpi.subscriptions[tier] || 0}</div>
                    <div className={`mt-1 inline-flex px-2 py-0.5 text-xs font-medium rounded-full capitalize ${TIER_COLORS[tier]}`}>
                      {tier}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: 'Review Content Queue', href: '/content', color: 'bg-yellow-50 text-yellow-700 border-yellow-200' },
                  { label: 'Approve Suppliers', href: '/suppliers', color: 'bg-blue-50 text-blue-700 border-blue-200' },
                  { label: 'Check Outbound Health', href: '/outbound', color: 'bg-green-50 text-green-700 border-green-200' },
                  { label: 'View API Costs', href: '/api-usage', color: 'bg-purple-50 text-purple-700 border-purple-200' },
                ].map((action) => (
                  <a
                    key={action.label}
                    href={action.href}
                    className={`border rounded-lg p-4 text-sm font-medium text-center transition hover:opacity-80 ${action.color}`}
                  >
                    {action.label}
                  </a>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="text-center text-gray-500 py-16">Failed to load dashboard data. Make sure you are logged in as admin.</div>
        )}
    </>
  )
}
