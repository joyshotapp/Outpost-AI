'use client'

import { useState, useEffect, useCallback } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'

interface Supplier {
  id: number
  company_name: string
  company_slug: string
  country: string
  industry: string
  is_active: boolean
  is_verified: boolean
  subscription_tier: string
  created_at: string
}

const TIER_BADGE: Record<string, string> = {
  free: 'bg-gray-100 text-gray-600',
  starter: 'bg-blue-100 text-blue-700',
  professional: 'bg-purple-100 text-purple-700',
  enterprise: 'bg-amber-100 text-amber-700',
}

export default function AdminSuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterVerified, setFilterVerified] = useState<boolean | null>(null)
  const [filterActive, setFilterActive] = useState<boolean | null>(null)
  const [filterTier, setFilterTier] = useState('')
  const [actionLoading, setActionLoading] = useState<number | null>(null)

  const token = typeof window !== 'undefined' ? (localStorage.getItem('token') || localStorage.getItem('auth_token')) : null

  const fetchSuppliers = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({ page: String(page), page_size: '20' })
    if (search) params.set('search', search)
    if (filterVerified !== null) params.set('is_verified', String(filterVerified))
    if (filterActive !== null) params.set('is_active', String(filterActive))
    if (filterTier) params.set('plan_tier', filterTier)
    try {
      const res = await fetch(`${API}/admin/suppliers?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      setSuppliers(data.suppliers || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
    } finally {
      setLoading(false)
    }
  }, [page, search, filterVerified, filterActive, filterTier, token])

  useEffect(() => { fetchSuppliers() }, [fetchSuppliers])

  async function toggleVerified(id: number, current: boolean) {
    setActionLoading(id)
    try {
      await fetch(`${API}/admin/suppliers/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ is_verified: !current }),
      })
      await fetchSuppliers()
    } finally {
      setActionLoading(null)
    }
  }

  async function toggleActive(id: number, current: boolean) {
    setActionLoading(id)
    try {
      await fetch(`${API}/admin/suppliers/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ is_active: !current }),
      })
      await fetchSuppliers()
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Supplier Management</h1>
            <p className="text-gray-500 mt-1">{total.toLocaleString()} total suppliers</p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 flex flex-wrap gap-3 items-center">
          <input
            type="text"
            placeholder="Search by company name…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <select
            value={filterVerified === null ? '' : String(filterVerified)}
            onChange={(e) => setFilterVerified(e.target.value === '' ? null : e.target.value === 'true')}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none"
          >
            <option value="">All Verification</option>
            <option value="true">Verified</option>
            <option value="false">Unverified</option>
          </select>
          <select
            value={filterActive === null ? '' : String(filterActive)}
            onChange={(e) => setFilterActive(e.target.value === '' ? null : e.target.value === 'true')}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none"
          >
            <option value="">All Status</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
          <select
            value={filterTier}
            onChange={(e) => setFilterTier(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none"
          >
            <option value="">All Plans</option>
            {['free', 'starter', 'professional', 'enterprise'].map((t) => (
              <option key={t} value={t} className="capitalize">{t.charAt(0).toUpperCase() + t.slice(1)}</option>
            ))}
          </select>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {['Company', 'Country', 'Industry', 'Plan', 'Verified', 'Active', 'Actions'].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {suppliers.length === 0 ? (
                  <tr><td colSpan={7} className="text-center py-12 text-gray-400">No suppliers found</td></tr>
                ) : suppliers.map((s) => (
                  <tr key={s.id} className="hover:bg-gray-50 transition">
                    <td className="px-5 py-4">
                      <div className="font-medium text-gray-900 text-sm">{s.company_name}</div>
                      <div className="text-xs text-gray-400">{s.company_slug}</div>
                    </td>
                    <td className="px-5 py-4 text-sm text-gray-600">{s.country}</td>
                    <td className="px-5 py-4 text-sm text-gray-600">{s.industry || '—'}</td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full capitalize ${TIER_BADGE[s.subscription_tier] || TIER_BADGE.free}`}>
                        {s.subscription_tier}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex items-center gap-1 text-xs font-medium ${s.is_verified ? 'text-green-600' : 'text-gray-400'}`}>
                        {s.is_verified ? '✓ Verified' : '○ Unverified'}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex text-xs font-medium ${s.is_active ? 'text-green-600' : 'text-red-500'}`}>
                        {s.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => toggleVerified(s.id, s.is_verified)}
                          disabled={actionLoading === s.id}
                          className={`text-xs px-2.5 py-1 rounded font-medium transition ${
                            s.is_verified
                              ? 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                              : 'bg-green-50 hover:bg-green-100 text-green-700'
                          }`}
                        >
                          {s.is_verified ? 'Unverify' : 'Verify'}
                        </button>
                        <button
                          onClick={() => toggleActive(s.id, s.is_active)}
                          disabled={actionLoading === s.id}
                          className={`text-xs px-2.5 py-1 rounded font-medium transition ${
                            s.is_active
                              ? 'bg-red-50 hover:bg-red-100 text-red-700'
                              : 'bg-blue-50 hover:bg-blue-100 text-blue-700'
                          }`}
                        >
                          {s.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex justify-center items-center gap-2 mt-4">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
              className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40 hover:bg-gray-100">← Prev</button>
            <span className="text-sm text-gray-600">Page {page} of {pages}</span>
            <button onClick={() => setPage(p => Math.min(pages, p + 1))} disabled={page === pages}
              className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40 hover:bg-gray-100">Next →</button>
          </div>
        )}
      </div>
    </div>
  )
}
