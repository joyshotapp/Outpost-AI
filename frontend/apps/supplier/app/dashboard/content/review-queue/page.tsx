'use client'

/**
 * Sprint 9 — Task 9.9: Content Review Queue UI
 *
 * Centralised review interface for all AI-generated content that scored
 * below the quality threshold. Supports:
 *   - Multi-select bulk approve / reject / archive
 *   - Content type tabs (LinkedIn / SEO / Short Video)
 *   - Quick inline preview without opening full editor
 *   - Quality score badge with flag detail tooltip
 */

import React, { useState, useEffect, useCallback } from 'react'

interface ContentItem {
  id: number
  content_type: string
  title: string
  body: string
  status: string
  quality_score: number | null
  quality_checked: boolean
  review_notes: string | null
  source_video_id: number | null
  hashtags: string | null
  keywords: string | null
  short_video_url: string | null
  short_video_duration_s: number | null
}

const TYPE_ICONS: Record<string, string> = {
  linkedin_post: '💼',
  seo_article:   '📝',
  short_video:   '🎬',
}

const TYPE_LABELS: Record<string, string> = {
  linkedin_post: 'LinkedIn Post',
  seo_article:   'SEO Article',
  short_video:   'Short Video',
}

function QualityBadge({ score }: { score: number | null }) {
  if (score === null) return null
  const { bg, text } =
    score >= 70 ? { bg: 'bg-green-100', text: 'text-green-700' } :
    score >= 50 ? { bg: 'bg-yellow-100', text: 'text-yellow-700' } :
                  { bg: 'bg-red-100', text: 'text-red-600' }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${bg} ${text}`}>
      Q:{score}
    </span>
  )
}

export default function ReviewQueuePage() {
  const [items, setItems] = useState<ContentItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [typeFilter, setTypeFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [preview, setPreview] = useState<ContentItem | null>(null)
  const [bulkAction, setBulkAction] = useState<'approve' | 'reject' | 'archive'>('approve')
  const [bulkNotes, setBulkNotes] = useState('')
  const [bulkModalOpen, setBulkModalOpen] = useState(false)
  const [actionMsg, setActionMsg] = useState<string | null>(null)
  const [processing, setProcessing] = useState(false)

  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
  const PAGE_SIZE = 30

  const fetchQueue = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) })
      if (typeFilter) params.set('content_type', typeFilter)
      const res = await fetch(`${API}/content/review-queue?${params}`, { credentials: 'include' })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setItems(data.items || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
      setSelected(new Set())
    } catch {
      setActionMsg('Failed to load review queue')
    } finally {
      setLoading(false)
    }
  }, [page, typeFilter, API])

  useEffect(() => { fetchQueue() }, [fetchQueue])

  const toggleSelect = (id: number) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const selectAll = () => setSelected(new Set(items.map(i => i.id)))
  const clearAll = () => setSelected(new Set())

  const submitBulk = async () => {
    if (selected.size === 0) return
    setProcessing(true)
    try {
      const res = await fetch(`${API}/content/review-queue/bulk`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          item_ids: Array.from(selected),
          action: bulkAction,
          review_notes: bulkNotes || null,
        }),
      })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setActionMsg(`${data.updated} items set to "${data.new_status}"`)
      setBulkModalOpen(false)
      setBulkNotes('')
      fetchQueue()
    } catch {
      setActionMsg('Bulk action failed')
    } finally {
      setProcessing(false)
    }
  }

  const singleAction = async (id: number, action: string) => {
    await fetch(`${API}/content/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ status: action === 'approve' ? 'approved' : action }),
    })
    setActionMsg(`Item ${action}d`)
    fetchQueue()
  }

  const typeGroups = ['', 'linkedin_post', 'seo_article', 'short_video']

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Content Review Queue</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {total} items awaiting human review — AI quality score below threshold
            </p>
          </div>
          {selected.size > 0 && (
            <button
              onClick={() => setBulkModalOpen(true)}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg font-medium hover:bg-blue-700"
            >
              Bulk action ({selected.size} selected)
            </button>
          )}
        </div>

        {/* Type filter tabs */}
        <div className="flex gap-2 mt-4">
          {typeGroups.map(t => (
            <button
              key={t}
              onClick={() => { setTypeFilter(t); setPage(1) }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                typeFilter === t
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {t ? `${TYPE_ICONS[t]} ${TYPE_LABELS[t]}` : '📂 All Types'}
            </button>
          ))}
        </div>
      </div>

      {actionMsg && (
        <div className="mx-6 mt-4 p-3 bg-green-50 border border-green-200 rounded text-sm text-green-700 flex justify-between">
          {actionMsg}
          <button onClick={() => setActionMsg(null)}>✕</button>
        </div>
      )}

      {/* Select all / clear */}
      {items.length > 0 && (
        <div className="px-6 pt-4 flex items-center gap-3">
          <button onClick={selectAll} className="text-xs text-blue-600 hover:underline">Select all ({items.length})</button>
          {selected.size > 0 && (
            <button onClick={clearAll} className="text-xs text-gray-400 hover:text-gray-600">Clear selection</button>
          )}
          <span className="text-xs text-gray-400 ml-auto">{selected.size} selected</span>
        </div>
      )}

      {/* Queue items */}
      <div className="px-6 py-3 space-y-2">
        {loading ? (
          <div className="text-center py-16 text-gray-400">Loading…</div>
        ) : items.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            <div className="text-5xl mb-3">✅</div>
            <p className="font-medium text-lg">Review queue is empty</p>
            <p className="text-sm mt-1">All AI-generated content meets quality standards</p>
          </div>
        ) : (
          items.map(item => (
            <div
              key={item.id}
              className={`bg-white rounded-lg border p-4 flex items-start gap-3 shadow-sm transition ${
                selected.has(item.id) ? 'border-blue-400 ring-1 ring-blue-400' : 'border-gray-200'
              }`}
            >
              {/* Checkbox */}
              <input
                type="checkbox"
                checked={selected.has(item.id)}
                onChange={() => toggleSelect(item.id)}
                className="mt-1 rounded border-gray-300 text-blue-600 cursor-pointer"
              />

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm">{TYPE_ICONS[item.content_type] || '📄'}</span>
                  <span className="text-xs text-gray-500">{TYPE_LABELS[item.content_type] || item.content_type}</span>
                  <QualityBadge score={item.quality_score} />
                </div>
                <p className="font-medium text-gray-800 text-sm truncate">{item.title}</p>
                <p className="text-gray-500 text-sm mt-0.5 line-clamp-2">{item.body}</p>
                {item.review_notes && (
                  <p className="text-xs text-orange-600 mt-1 bg-orange-50 px-2 py-0.5 rounded inline-block">
                    ⚠ {item.review_notes}
                  </p>
                )}
              </div>

              {/* Actions */}
              <div className="flex flex-col gap-1.5 shrink-0">
                <button
                  onClick={() => setPreview(item)}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-600"
                >
                  Preview
                </button>
                <button
                  onClick={() => singleAction(item.id, 'approve')}
                  className="px-3 py-1 text-xs bg-green-100 hover:bg-green-200 rounded text-green-700"
                >
                  Approve
                </button>
                <button
                  onClick={() => singleAction(item.id, 'rejected')}
                  className="px-3 py-1 text-xs bg-red-50 hover:bg-red-100 rounded text-red-600"
                >
                  Reject
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex justify-center gap-2 pb-8">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 text-sm border rounded disabled:opacity-40">← Prev</button>
          <span className="text-sm text-gray-600 px-2 py-1">{page}/{pages}</span>
          <button disabled={page >= pages} onClick={() => setPage(p => p + 1)} className="px-3 py-1 text-sm border rounded disabled:opacity-40">Next →</button>
        </div>
      )}

      {/* Quick preview modal */}
      {preview && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={() => setPreview(null)}>
          <div
            className="bg-white rounded-xl shadow-2xl w-full max-w-xl max-h-[80vh] flex flex-col"
            onClick={e => e.stopPropagation()}
          >
            <div className="p-5 border-b flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span>{TYPE_ICONS[preview.content_type]}</span>
                <span className="font-semibold text-gray-900 text-sm">{preview.title}</span>
              </div>
              <button onClick={() => setPreview(null)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="p-5 overflow-y-auto flex-1">
              {preview.content_type === 'short_video' && preview.short_video_url ? (
                <video src={preview.short_video_url} controls className="w-full rounded mb-3" />
              ) : null}
              <p className="text-xs text-gray-400 mb-2">Quality score: {preview.quality_score ?? '—'}</p>
              {preview.review_notes && (
                <div className="mb-3 p-2 bg-orange-50 border border-orange-200 rounded text-xs text-orange-700">
                  {preview.review_notes}
                </div>
              )}
              <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{preview.body}</div>
              {preview.hashtags && (
                <p className="text-xs text-blue-400 mt-3">{preview.hashtags.split(',').map(h => `#${h.trim()}`).join(' ')}</p>
              )}
            </div>
            <div className="p-4 border-t flex justify-end gap-2">
              <button onClick={() => { singleAction(preview.id, 'rejected'); setPreview(null) }} className="px-3 py-1.5 text-sm bg-red-50 hover:bg-red-100 rounded text-red-600">Reject</button>
              <button onClick={() => { singleAction(preview.id, 'approve'); setPreview(null) }} className="px-3 py-1.5 text-sm bg-green-600 hover:bg-green-700 text-white rounded">Approve</button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk action modal */}
      {bulkModalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm">
            <div className="p-5 border-b flex items-center justify-between">
              <h2 className="font-semibold text-gray-900">Bulk Action — {selected.size} items</h2>
              <button onClick={() => setBulkModalOpen(false)} className="text-gray-400">✕</button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Action</label>
                <div className="flex gap-2">
                  {(['approve', 'reject', 'archive'] as const).map(a => (
                    <button
                      key={a}
                      onClick={() => setBulkAction(a)}
                      className={`flex-1 px-3 py-2 text-sm rounded capitalize font-medium border transition ${
                        bulkAction === a
                          ? a === 'approve' ? 'bg-green-600 text-white border-green-600'
                            : a === 'reject' ? 'bg-red-600 text-white border-red-600'
                            : 'bg-gray-600 text-white border-gray-600'
                          : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'
                      }`}
                    >
                      {a}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
                <textarea
                  value={bulkNotes}
                  onChange={e => setBulkNotes(e.target.value)}
                  rows={3}
                  placeholder="Rejection reason or approval note…"
                  className="w-full border rounded px-3 py-2 text-sm resize-none"
                />
              </div>
            </div>
            <div className="p-5 border-t flex justify-end gap-2">
              <button onClick={() => setBulkModalOpen(false)} className="px-4 py-2 text-sm border rounded text-gray-600">Cancel</button>
              <button
                onClick={submitBulk}
                disabled={processing}
                className={`px-4 py-2 text-sm rounded text-white font-medium disabled:opacity-50 ${
                  bulkAction === 'approve' ? 'bg-green-600 hover:bg-green-700'
                  : bulkAction === 'reject' ? 'bg-red-600 hover:bg-red-700'
                  : 'bg-gray-700 hover:bg-gray-800'
                }`}
              >
                {processing ? 'Processing…' : `${bulkAction.charAt(0).toUpperCase() + bulkAction.slice(1)} ${selected.size} items`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
