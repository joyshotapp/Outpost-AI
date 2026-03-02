'use client'

import { useState, useEffect, useCallback } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

const NAV_ITEMS = [
  { label: 'Dashboard', href: '/', icon: '📊' },
  { label: 'Suppliers', href: '/suppliers', icon: '🏭' },
  { label: 'Buyers', href: '/buyers', icon: '👤' },
  { label: 'Content Review', href: '/content', icon: '✍️' },
  { label: 'Outbound Health', href: '/outbound', icon: '📡' },
  { label: 'API Usage', href: '/api-usage', icon: '⚡' },
  { label: 'Settings', href: '/settings', icon: '⚙️' },
]

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
  const [kpi, setKpi] = useState<KPI | null>(null)
  const [loading, setLoading] = useState(true)

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

  const fetchKPI = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/admin/kpi/overview`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (res.ok) setKpi(await res.json())
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => { fetchKPI() }, [fetchKPI])

  const TIER_COLORS: Record<string, string> = {
    free: 'bg-gray-100 text-gray-600',
    starter: 'bg-blue-100 text-blue-700',
    professional: 'bg-purple-100 text-purple-700',
    enterprise: 'bg-amber-100 text-amber-700',
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-gray-200 min-h-screen flex flex-col py-6">
        <div className="px-6 mb-8">
          <h1 className="text-lg font-bold text-gray-900">Factory Insider</h1>
          <p className="text-xs text-purple-600 font-medium mt-0.5">Admin Console</p>
        </div>
        <nav className="flex-1 px-3 space-y-1">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                item.label === 'Dashboard'
                  ? 'bg-purple-50 text-purple-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
            </a>
          ))}
        </nav>
        <div className="px-6 pt-4 border-t border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white text-xs font-bold">A</div>
            <div>
              <p className="text-sm font-medium text-gray-900">Admin</p>
              <p className="text-xs text-gray-400">Super Admin</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 p-8">
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
      </main>
    </div>
  )
}


      {/* Sidebar + Content */}
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 min-h-screen p-6">
          <nav className="space-y-2">
            {[
              { label: "Dashboard", active: true },
              { label: "Suppliers", badge: 245 },
              { label: "Buyers", badge: 1230 },
              { label: "RFQ Inquiries", badge: 89 },
              { label: "Analytics" },
              { label: "Settings" },
            ].map((item, index) => (
              <a
                key={index}
                href="#"
                className={`block px-4 py-2 rounded-md font-medium transition-colors flex justify-between items-center ${
                  item.active
                    ? "bg-primary-100 text-primary-700"
                    : "text-gray-700 hover:bg-gray-100"
                }`}
              >
                {item.label}
                {item.badge && (
                  <span className="text-body-sm bg-primary-700 text-white px-2 py-1 rounded-full">
                    {item.badge}
                  </span>
                )}
              </a>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <div className="flex-1 p-8">
          <h1 className="text-h2 font-bold mb-6">Platform Overview</h1>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[
              { label: "Total Users", value: "1,475", change: "+12%" },
              { label: "Active Suppliers", value: "245", change: "+5%" },
              { label: "Monthly Revenue", value: "$156,230", change: "+23%" },
              { label: "Platform Health", value: "99.8%", change: "✓" },
            ].map((kpi, index) => (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-lg p-6"
              >
                <p className="text-body-sm text-gray-600 mb-2">{kpi.label}</p>
                <p className="text-h2 font-bold text-gray-900 mb-2">{kpi.value}</p>
                <p className={`text-body-sm font-medium ${
                  kpi.change.includes("+") ? "text-success-700" : "text-primary-700"
                }`}>
                  {kpi.change}
                </p>
              </div>
            ))}
          </div>

          {/* System Status */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Services Health */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-h3 font-semibold mb-4">Services Health</h2>
              <div className="space-y-3">
                {[
                  { service: "API", status: "healthy" },
                  { service: "Database", status: "healthy" },
                  { service: "Redis", status: "healthy" },
                  { service: "Elasticsearch", status: "healthy" },
                ].map((item, index) => (
                  <div
                    key={index}
                    className="flex justify-between items-center p-3 bg-gray-50 rounded"
                  >
                    <span className="font-medium">{item.service}</span>
                    <span className="text-body-sm px-3 py-1 bg-success-100 text-success-700 rounded-full">
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 lg:col-span-2">
              <h2 className="text-h3 font-semibold mb-4">Recent Activity</h2>
              <div className="space-y-3">
                {[
                  "New supplier registered: ABC Manufacturing",
                  "RFQ inquiries exceeded 50 for the day",
                  "Platform maintenance scheduled for 2026-03-01",
                  "New API integration: HubSpot CRM",
                ].map((activity, index) => (
                  <div
                    key={index}
                    className="p-3 bg-gray-50 rounded border-l-4 border-primary-700"
                  >
                    <p className="text-body text-gray-700">{activity}</p>
                    <p className="text-body-sm text-gray-500 mt-1">2 hours ago</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
