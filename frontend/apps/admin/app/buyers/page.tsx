'use client'

import { useState, useEffect, useCallback } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface Buyer {
  id: number
  company_name: string
  country: string
  is_active: boolean
  created_at: string
}

export default function AdminBuyersPage() {
  const [buyers, setBuyers] = useState<Buyer[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterActive, setFilterActive] = useState<boolean | null>(null)
  const [actionLoading, setActionLoading] = useState<number | null>(null)

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

  const fetchBuyers = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({ page: String(page), page_size: '20' })
    if (search) params.set('search', search)
    if (filterActive !== null) params.set('is_active', String(filterActive))
    try {
      const res = await fetch(`${API}/admin/buyers?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      setBuyers(data.buyers || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
    } finally {
      setLoading(false)
    }
  }, [page, search, filterActive, token])

  useEffect(() => { fetchBuyers() }, [fetchBuyers])

  async function toggleBlock(id: number, currentActive: boolean) {
    setActionLoading(id)
    try {
      await fetch(`${API}/admin/buyers/${id}/block`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ is_active: !currentActive }),
      })
      await fetchBuyers()
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Buyer Management</h1>
          <p className="text-gray-500 mt-1">{total.toLocaleString()} registered buyers</p>
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
            value={filterActive === null ? '' : String(filterActive)}
            onChange={(e) => setFilterActive(e.target.value === '' ? null : e.target.value === 'true')}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none"
          >
            <option value="">All Status</option>
            <option value="true">Active</option>
            <option value="false">Blocked</option>
          </select>
          <div className="ml-auto">
            <span className={`inline-flex px-3 py-1 text-xs font-medium rounded-full ${filterActive === false ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
              {buyers.filter(b => b.is_active).length} active · {buyers.filter(b => !b.is_active).length} blocked (this page)
            </span>
          </div>
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
                  {['#', 'Company', 'Country', 'Status', 'Joined', 'Actions'].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {buyers.length === 0 ? (
                  <tr><td colSpan={6} className="text-center py-12 text-gray-400">No buyers found</td></tr>
                ) : buyers.map((b) => (
                  <tr key={b.id} className="hover:bg-gray-50 transition">
                    <td className="px-5 py-4 text-sm text-gray-400">{b.id}</td>
                    <td className="px-5 py-4">
                      <div className="font-medium text-gray-900 text-sm">{b.company_name}</div>
                    </td>
                    <td className="px-5 py-4 text-sm text-gray-600">{b.country || '—'}</td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                        b.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {b.is_active ? 'Active' : 'Blocked'}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-sm text-gray-500">
                      {new Date(b.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-4">
                      <button
                        onClick={() => toggleBlock(b.id, b.is_active)}
                        disabled={actionLoading === b.id}
                        className={`text-xs px-3 py-1.5 rounded font-medium transition ${
                          b.is_active
                            ? 'bg-red-50 hover:bg-red-100 text-red-700'
                            : 'bg-green-50 hover:bg-green-100 text-green-700'
                        }`}
                      >
                        {actionLoading === b.id ? '…' : b.is_active ? 'Block' : 'Unblock'}
                      </button>
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
