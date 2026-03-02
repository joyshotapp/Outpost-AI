'use client'

import { useState, useEffect, useCallback } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface ContentItem {
  id: number
  supplier_id: number
  content_type: string
  title: string
  body_preview: string
  review_status: string
  review_note: string | null
  created_at: string
}

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  flagged: 'bg-orange-100 text-orange-700',
}

const TYPE_STYLES: Record<string, string> = {
  linkedin_post: 'bg-blue-50 text-blue-600',
  seo_article: 'bg-purple-50 text-purple-600',
  short_video: 'bg-pink-50 text-pink-600',
}

export default function AdminContentReviewPage() {
  const [items, setItems] = useState<ContentItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState('pending')
  const [actionLoading, setActionLoading] = useState<number | null>(null)
  const [reviewNote, setReviewNote] = useState('')
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

  const fetchItems = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({ page: String(page), page_size: '20' })
    if (filterStatus) params.set('review_status', filterStatus)
    try {
      const res = await fetch(`${API}/admin/content/review-queue?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      setItems(data.items || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
    } finally {
      setLoading(false)
    }
  }, [page, filterStatus, token])

  useEffect(() => { fetchItems() }, [fetchItems])

  async function reviewItem(id: number, status: string, note?: string) {
    setActionLoading(id)
    try {
      await fetch(`${API}/admin/content/${id}/review`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ review_status: status, review_note: note || null }),
      })
      setExpandedId(null)
      setReviewNote('')
      await fetchItems()
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">AI Content Review Queue</h1>
          <p className="text-gray-500 mt-1">Review and approve AI-generated content before publishing · {total.toLocaleString()} items</p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 flex gap-2">
          {(['pending', 'approved', 'rejected', 'flagged'] as const).map((s) => (
            <button
              key={s}
              onClick={() => { setFilterStatus(s); setPage(1) }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition capitalize ${
                filterStatus === s ? STATUS_STYLES[s] + ' ring-2 ring-offset-1 ring-current' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Cards */}
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-16 text-gray-400 bg-white rounded-xl border border-gray-200">
            No {filterStatus} content items
          </div>
        ) : (
          <div className="space-y-4">
            {items.map((item) => (
              <div key={item.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${TYPE_STYLES[item.content_type] || 'bg-gray-100 text-gray-600'}`}>
                          {item.content_type.replace(/_/g, ' ')}
                        </span>
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${STATUS_STYLES[item.review_status] || STATUS_STYLES.pending}`}>
                          {item.review_status}
                        </span>
                        <span className="text-xs text-gray-400">Supplier #{item.supplier_id}</span>
                        <span className="text-xs text-gray-400">{new Date(item.created_at).toLocaleDateString()}</span>
                      </div>
                      <h3 className="font-semibold text-gray-900 truncate">{item.title}</h3>
                      <p className="text-sm text-gray-500 mt-1 line-clamp-2">{item.body_preview}</p>
                      {item.review_note && (
                        <p className="text-xs text-orange-600 mt-1 italic">Note: {item.review_note}</p>
                      )}
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button
                        onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                        className="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium"
                      >
                        {expandedId === item.id ? 'Close' : 'Review'}
                      </button>
                      {item.review_status !== 'approved' && (
                        <button
                          onClick={() => reviewItem(item.id, 'approved')}
                          disabled={actionLoading === item.id}
                          className="text-xs px-3 py-1.5 bg-green-50 hover:bg-green-100 text-green-700 rounded-lg font-medium"
                        >
                          ✓ Approve
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Expanded review panel */}
                  {expandedId === item.id && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Review Note (optional)</label>
                      <textarea
                        value={reviewNote}
                        onChange={(e) => setReviewNote(e.target.value)}
                        placeholder="Add a note for the supplier…"
                        rows={2}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                      <div className="flex gap-2 mt-3">
                        <button
                          onClick={() => reviewItem(item.id, 'approved', reviewNote)}
                          disabled={actionLoading === item.id}
                          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => reviewItem(item.id, 'flagged', reviewNote)}
                          disabled={actionLoading === item.id}
                          className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-medium rounded-lg"
                        >
                          Flag
                        </button>
                        <button
                          onClick={() => reviewItem(item.id, 'rejected', reviewNote)}
                          disabled={actionLoading === item.id}
                          className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-medium rounded-lg"
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex justify-center items-center gap-2 mt-6">
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
