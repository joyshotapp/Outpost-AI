'use client'

/**
 * Sprint 9 — Task 9.6: LinkedIn Post Management UI
 *
 * Displays AI-generated LinkedIn posts for the supplier, with inline editing,
 * quality score badge, status filter, and one-click schedule to Repurpose.io.
 */

import React, { useState, useEffect, useCallback } from 'react'

// ─── Types ────────────────────────────────────────────────────────────────────

interface ContentItem {
  id: number
  content_type: 'linkedin_post' | 'seo_article' | 'short_video'
  title: string
  body: string
  keywords: string | null
  hashtags: string | null
  excerpt: string | null
  status: string
  platform: string | null
  scheduled_publish_date: string | null
  published_at: string | null
  published_url: string | null
  quality_score: number | null
  quality_checked: boolean
  impressions: number
  engagements: number
  clicks: number
  likes: number
  shares: number
  comments: number
  source_video_id: number | null
  created_at?: string
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  draft:     { label: 'Draft',     color: 'text-gray-700', bg: 'bg-gray-100' },
  review:    { label: 'Review',    color: 'text-yellow-800', bg: 'bg-yellow-100' },
  approved:  { label: 'Approved',  color: 'text-green-800', bg: 'bg-green-100' },
  scheduled: { label: 'Scheduled', color: 'text-blue-800', bg: 'bg-blue-100' },
  published: { label: 'Published', color: 'text-violet-800', bg: 'bg-violet-100' },
  rejected:  { label: 'Rejected',  color: 'text-red-800',  bg: 'bg-red-100' },
  archived:  { label: 'Archived',  color: 'text-slate-600', bg: 'bg-slate-100' },
}

function qualityColor(score: number | null): string {
  if (score === null) return 'text-gray-400'
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-yellow-600'
  return 'text-red-500'
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function LinkedInPostsPage() {
  const [items, setItems] = useState<ContentItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [selectedItem, setSelectedItem] = useState<ContentItem | null>(null)
  const [editBody, setEditBody] = useState('')
  const [editTitle, setEditTitle] = useState('')
  const [editHashtags, setEditHashtags] = useState('')
  const [saving, setSaving] = useState(false)
  const [scheduleModal, setScheduleModal] = useState(false)
  const [workflowId, setWorkflowId] = useState('')
  const [scheduledAt, setScheduledAt] = useState('')
  const [actionMsg, setActionMsg] = useState<string | null>(null)

  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

  const fetchPosts = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        content_type: 'linkedin_post',
        page: String(page),
        page_size: '20',
      })
      if (statusFilter) params.set('status', statusFilter)
      const res = await fetch(`${API}/content?${params}`, { credentials: 'include' })
      if (!res.ok) throw new Error('Failed to load')
      const data = await res.json()
      setItems(data.items || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
    } catch {
      setActionMsg('Failed to load posts')
    } finally {
      setLoading(false)
    }
  }, [page, statusFilter, API])

  useEffect(() => { fetchPosts() }, [fetchPosts])

  const openEdit = (item: ContentItem) => {
    setSelectedItem(item)
    setEditBody(item.body)
    setEditTitle(item.title)
    setEditHashtags(item.hashtags || '')
  }

  const saveEdit = async () => {
    if (!selectedItem) return
    setSaving(true)
    try {
      const res = await fetch(`${API}/content/${selectedItem.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ title: editTitle, body: editBody, hashtags: editHashtags }),
      })
      if (!res.ok) throw new Error()
      setSelectedItem(null)
      setActionMsg('Post updated')
      fetchPosts()
    } catch {
      setActionMsg('Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const approveItem = async (id: number) => {
    await fetch(`${API}/content/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ status: 'approved' }),
    })
    setActionMsg('Approved')
    fetchPosts()
  }

  const rejectItem = async (id: number) => {
    await fetch(`${API}/content/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ status: 'rejected' }),
    })
    setActionMsg('Rejected')
    fetchPosts()
  }

  const openSchedule = (item: ContentItem) => {
    setSelectedItem(item)
    setScheduleModal(true)
  }

  const submitSchedule = async () => {
    if (!selectedItem || !workflowId) return
    const res = await fetch(`${API}/content/${selectedItem.id}/schedule`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ workflow_id: workflowId, scheduled_at: scheduledAt || null, platform: 'linkedin' }),
    })
    if (res.ok) {
      setActionMsg('Post scheduled for publishing')
      setScheduleModal(false)
      fetchPosts()
    } else {
      setActionMsg('Scheduling failed')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">LinkedIn Posts</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            AI-generated posts from your videos — review, edit, and schedule
          </p>
        </div>
        <span className="text-sm text-gray-400">{total} posts total</span>
      </div>

      {/* Filters */}
      <div className="px-6 py-4 bg-white border-b flex gap-3 flex-wrap">
        {['', 'draft', 'review', 'approved', 'scheduled', 'published'].map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1) }}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition ${
              statusFilter === s
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-600 border-gray-200 hover:border-blue-400'
            }`}
          >
            {s ? STATUS_CONFIG[s]?.label : 'All'}
          </button>
        ))}
      </div>

      {/* Toast */}
      {actionMsg && (
        <div className="mx-6 mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700 flex justify-between">
          {actionMsg}
          <button onClick={() => setActionMsg(null)} className="text-blue-400 hover:text-blue-600">✕</button>
        </div>
      )}

      {/* Post list */}
      <div className="px-6 py-4 space-y-3">
        {loading ? (
          <div className="text-center py-16 text-gray-400">Loading…</div>
        ) : items.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <div className="text-4xl mb-3">💼</div>
            <p className="font-medium">No LinkedIn posts yet</p>
            <p className="text-sm">Trigger a content viral pipeline from your Videos page</p>
          </div>
        ) : (
          items.map((item) => {
            const sc = STATUS_CONFIG[item.status] || STATUS_CONFIG.draft
            return (
              <div key={item.id} className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${sc.bg} ${sc.color}`}>
                        {sc.label}
                      </span>
                      {item.quality_score !== null && (
                        <span className={`text-xs font-medium ${qualityColor(item.quality_score)}`}>
                          Q: {item.quality_score}
                        </span>
                      )}
                    </div>
                    <p className="font-medium text-gray-800 text-sm truncate">{item.title}</p>
                    <p className="text-gray-500 text-sm mt-1 line-clamp-2">{item.body}</p>
                    {item.hashtags && (
                      <p className="text-blue-400 text-xs mt-1">{item.hashtags.split(',').map(h => `#${h.trim()}`).join(' ')}</p>
                    )}
                    {item.status === 'published' && (
                      <div className="flex gap-4 mt-2 text-xs text-gray-500">
                        <span>👁 {item.impressions.toLocaleString()}</span>
                        <span>👍 {item.likes}</span>
                        <span>💬 {item.comments}</span>
                        <span>↗ {item.shares}</span>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col gap-1.5 shrink-0">
                    <button
                      onClick={() => openEdit(item)}
                      className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-700"
                    >
                      Edit
                    </button>
                    {item.status === 'draft' && (
                      <button
                        onClick={() => approveItem(item.id)}
                        className="px-3 py-1 text-xs bg-green-100 hover:bg-green-200 rounded text-green-700"
                      >
                        Approve
                      </button>
                    )}
                    {item.status === 'approved' && (
                      <button
                        onClick={() => openSchedule(item)}
                        className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 rounded text-white"
                      >
                        Schedule
                      </button>
                    )}
                    {['draft', 'review'].includes(item.status) && (
                      <button
                        onClick={() => rejectItem(item.id)}
                        className="px-3 py-1 text-xs bg-red-50 hover:bg-red-100 rounded text-red-600"
                      >
                        Reject
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex justify-center gap-2 pb-8">
          <button
            disabled={page <= 1}
            onClick={() => setPage(p => p - 1)}
            className="px-3 py-1 text-sm border rounded disabled:opacity-40"
          >
            ← Prev
          </button>
          <span className="px-3 py-1 text-sm text-gray-600">{page} / {pages}</span>
          <button
            disabled={page >= pages}
            onClick={() => setPage(p => p + 1)}
            className="px-3 py-1 text-sm border rounded disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      )}

      {/* Edit modal */}
      {selectedItem && !scheduleModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
            <div className="p-5 border-b flex items-center justify-between">
              <h2 className="font-semibold text-gray-900">Edit LinkedIn Post</h2>
              <button onClick={() => setSelectedItem(null)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="p-5 flex-1 overflow-y-auto space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title / Hook</label>
                <input
                  value={editTitle}
                  onChange={e => setEditTitle(e.target.value)}
                  className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Post Body</label>
                <textarea
                  value={editBody}
                  onChange={e => setEditBody(e.target.value)}
                  rows={12}
                  className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
                />
                <p className="text-xs text-gray-400 mt-1">{editBody.length} chars · LinkedIn optimal: 150-250 words</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Hashtags (comma-separated)</label>
                <input
                  value={editHashtags}
                  onChange={e => setEditHashtags(e.target.value)}
                  placeholder="manufacturing,quality,precision"
                  className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
              </div>
              {/* Live preview */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Preview</label>
                <div className="bg-slate-50 border rounded p-4 text-sm text-gray-700 whitespace-pre-wrap">
                  {editBody}
                </div>
              </div>
            </div>
            <div className="p-5 border-t flex justify-end gap-2">
              <button
                onClick={() => setSelectedItem(null)}
                className="px-4 py-2 text-sm border rounded text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={saveEdit}
                disabled={saving}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Schedule modal */}
      {scheduleModal && selectedItem && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="p-5 border-b flex items-center justify-between">
              <h2 className="font-semibold text-gray-900">Schedule Post</h2>
              <button onClick={() => setScheduleModal(false)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Repurpose.io Workflow ID</label>
                <input
                  value={workflowId}
                  onChange={e => setWorkflowId(e.target.value)}
                  placeholder="wf_linkedin_123"
                  className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Schedule Date/Time (optional)</label>
                <input
                  type="datetime-local"
                  value={scheduledAt}
                  onChange={e => setScheduledAt(e.target.value)}
                  className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
                <p className="text-xs text-gray-400 mt-1">Leave blank to post immediately</p>
              </div>
            </div>
            <div className="p-5 border-t flex justify-end gap-2">
              <button
                onClick={() => setScheduleModal(false)}
                className="px-4 py-2 text-sm border rounded text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={submitSchedule}
                disabled={!workflowId}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Confirm Schedule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
