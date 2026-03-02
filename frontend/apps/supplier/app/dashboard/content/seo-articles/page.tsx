'use client'

/**
 * Sprint 9 — Task 9.7: SEO Article Management UI
 *
 * Displays AI-generated SEO articles with a rich editor, keyword suggestion
 * panel, status workflow, and scheduling to Repurpose.io.
 */

import React, { useState, useEffect, useCallback } from 'react'

interface ContentItem {
  id: number
  content_type: string
  title: string
  body: string
  keywords: string | null
  hashtags: string | null
  excerpt: string | null
  status: string
  platform: string | null
  scheduled_publish_date: string | null
  published_url: string | null
  quality_score: number | null
  quality_checked: boolean
  impressions: number
  engagements: number
  clicks: number
  source_video_id: number | null
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  draft:     { label: 'Draft',     color: 'text-gray-700',   bg: 'bg-gray-100' },
  review:    { label: 'Review',    color: 'text-yellow-800', bg: 'bg-yellow-100' },
  approved:  { label: 'Approved',  color: 'text-green-800',  bg: 'bg-green-100' },
  scheduled: { label: 'Scheduled', color: 'text-blue-800',   bg: 'bg-blue-100' },
  published: { label: 'Published', color: 'text-violet-800', bg: 'bg-violet-100' },
  rejected:  { label: 'Rejected',  color: 'text-red-800',    bg: 'bg-red-100' },
}

// Word count helper
function wordCount(text: string): number {
  return text.trim().split(/\s+/).filter(Boolean).length
}

// Extract H2s from markdown body for TOC
function extractH2s(body: string): string[] {
  return body
    .split('\n')
    .filter(line => line.startsWith('## '))
    .map(line => line.replace('## ', '').trim())
}

export default function SeoArticlesPage() {
  const [items, setItems] = useState<ContentItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedItem, setSelectedItem] = useState<ContentItem | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editBody, setEditBody] = useState('')
  const [editKeywords, setEditKeywords] = useState('')
  const [editExcerpt, setEditExcerpt] = useState('')
  const [saving, setSaving] = useState(false)
  const [actionMsg, setActionMsg] = useState<string | null>(null)
  const [scheduleModal, setScheduleModal] = useState(false)
  const [workflowId, setWorkflowId] = useState('')
  const [scheduledAt, setScheduledAt] = useState('')
  const [previewMode, setPreviewMode] = useState(false)

  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

  const fetchArticles = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ content_type: 'seo_article', page: String(page), page_size: '15' })
      if (statusFilter) params.set('status', statusFilter)
      const res = await fetch(`${API}/content?${params}`, { credentials: 'include' })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setItems(data.items || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
    } catch {
      setActionMsg('Failed to load articles')
    } finally {
      setLoading(false)
    }
  }, [page, statusFilter, API])

  useEffect(() => { fetchArticles() }, [fetchArticles])

  const openEditor = (item: ContentItem) => {
    setSelectedItem(item)
    setEditTitle(item.title)
    setEditBody(item.body)
    setEditKeywords(item.keywords || '')
    setEditExcerpt(item.excerpt || '')
    setPreviewMode(false)
  }

  const saveArticle = async () => {
    if (!selectedItem) return
    setSaving(true)
    try {
      await fetch(`${API}/content/${selectedItem.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ title: editTitle, body: editBody, keywords: editKeywords, excerpt: editExcerpt }),
      })
      setSelectedItem(null)
      setActionMsg('Article saved')
      fetchArticles()
    } catch {
      setActionMsg('Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const setStatus = async (id: number, newStatus: string) => {
    await fetch(`${API}/content/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ status: newStatus }),
    })
    setActionMsg(`Status → ${newStatus}`)
    fetchArticles()
  }

  const submitSchedule = async () => {
    if (!selectedItem || !workflowId) return
    const res = await fetch(`${API}/content/${selectedItem.id}/schedule`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ workflow_id: workflowId, scheduled_at: scheduledAt || null, platform: 'linkedin' }),
    })
    setActionMsg(res.ok ? 'Article scheduled' : 'Schedule failed')
    setScheduleModal(false)
    fetchArticles()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">SEO Articles</h1>
          <p className="text-sm text-gray-500 mt-0.5">AI-generated long-form articles — edit, optimise keywords, and publish</p>
        </div>
        <span className="text-sm text-gray-400">{total} articles</span>
      </div>

      {/* Status filters */}
      <div className="px-6 py-3 bg-white border-b flex gap-2 flex-wrap">
        {['', 'draft', 'review', 'approved', 'scheduled', 'published'].map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1) }}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition ${
              statusFilter === s ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-400'
            }`}
          >
            {s ? STATUS_CONFIG[s]?.label : 'All'}
          </button>
        ))}
      </div>

      {actionMsg && (
        <div className="mx-6 mt-4 p-3 bg-indigo-50 border border-indigo-200 rounded text-sm text-indigo-700 flex justify-between">
          {actionMsg}
          <button onClick={() => setActionMsg(null)}>✕</button>
        </div>
      )}

      {/* Articles list */}
      <div className="px-6 py-4 space-y-3">
        {loading ? (
          <div className="text-center py-16 text-gray-400">Loading…</div>
        ) : items.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <div className="text-4xl mb-3">📝</div>
            <p className="font-medium">No SEO articles yet</p>
            <p className="text-sm">Trigger the content viral pipeline from your Videos page</p>
          </div>
        ) : (
          items.map((item) => {
            const sc = STATUS_CONFIG[item.status] || STATUS_CONFIG.draft
            const h2s = extractH2s(item.body)
            return (
              <div key={item.id} className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${sc.bg} ${sc.color}`}>{sc.label}</span>
                      {item.quality_score !== null && (
                        <span className={`text-xs font-medium ${item.quality_score >= 80 ? 'text-green-600' : item.quality_score >= 60 ? 'text-yellow-600' : 'text-red-500'}`}>
                          Quality: {item.quality_score}/100
                        </span>
                      )}
                      <span className="text-xs text-gray-400">{wordCount(item.body)} words</span>
                    </div>
                    <h3 className="font-medium text-gray-900 text-sm">{item.title}</h3>
                    {item.excerpt && (
                      <p className="text-gray-500 text-sm mt-1 line-clamp-2">{item.excerpt}</p>
                    )}
                    {/* TOC preview */}
                    {h2s.length > 0 && (
                      <div className="mt-2 flex gap-2 flex-wrap">
                        {h2s.slice(0, 4).map((h, i) => (
                          <span key={i} className="text-xs bg-slate-50 border border-slate-200 rounded px-2 py-0.5 text-slate-600">{h}</span>
                        ))}
                        {h2s.length > 4 && <span className="text-xs text-gray-400">+{h2s.length - 4} more</span>}
                      </div>
                    )}
                    {item.keywords && (
                      <div className="mt-2 flex gap-1.5 flex-wrap">
                        {item.keywords.split(',').slice(0, 5).map((kw, i) => (
                          <span key={i} className="text-xs bg-green-50 border border-green-200 rounded-full px-2 py-0.5 text-green-700">{kw.trim()}</span>
                        ))}
                      </div>
                    )}
                    {item.status === 'published' && (
                      <div className="flex gap-6 mt-2 text-xs text-gray-500">
                        <span>👁 {item.impressions.toLocaleString()}</span>
                        <span>🖱 {item.clicks} clicks</span>
                        <span>💬 {item.engagements} engagements</span>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col gap-1.5 shrink-0">
                    <button
                      onClick={() => openEditor(item)}
                      className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-700"
                    >
                      Edit
                    </button>
                    {item.status === 'draft' && (
                      <button
                        onClick={() => setStatus(item.id, 'approved')}
                        className="px-3 py-1 text-xs bg-green-100 hover:bg-green-200 rounded text-green-700"
                      >
                        Approve
                      </button>
                    )}
                    {item.status === 'approved' && (
                      <button
                        onClick={() => { setSelectedItem(item); setScheduleModal(true) }}
                        className="px-3 py-1 text-xs bg-indigo-600 hover:bg-indigo-700 rounded text-white"
                      >
                        Schedule
                      </button>
                    )}
                    {['draft', 'review'].includes(item.status) && (
                      <button
                        onClick={() => setStatus(item.id, 'rejected')}
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
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 text-sm border rounded disabled:opacity-40">← Prev</button>
          <span className="px-3 py-1 text-sm text-gray-600">{page} / {pages}</span>
          <button disabled={page >= pages} onClick={() => setPage(p => p + 1)} className="px-3 py-1 text-sm border rounded disabled:opacity-40">Next →</button>
        </div>
      )}

      {/* Rich editor modal */}
      {selectedItem && !scheduleModal && (
        <div className="fixed inset-0 bg-black/40 flex items-start justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl my-8">
            <div className="p-5 border-b flex items-center justify-between">
              <h2 className="font-semibold text-gray-900">Edit SEO Article</h2>
              <div className="flex gap-2">
                <button
                  onClick={() => setPreviewMode(!previewMode)}
                  className={`px-3 py-1 text-xs rounded border ${previewMode ? 'bg-indigo-600 text-white border-indigo-600' : 'border-gray-300 text-gray-600'}`}
                >
                  {previewMode ? 'Editor' : 'Preview'}
                </button>
                <button onClick={() => setSelectedItem(null)} className="text-gray-400 hover:text-gray-600 ml-2">✕</button>
              </div>
            </div>
            <div className="p-5 grid grid-cols-3 gap-5">
              {/* Main editor / preview */}
              <div className="col-span-2 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">H1 Title</label>
                  <input
                    value={editTitle}
                    onChange={e => setEditTitle(e.target.value)}
                    className="w-full border rounded px-3 py-2 text-sm"
                  />
                </div>
                {previewMode ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Preview</label>
                    <div className="border rounded p-4 bg-slate-50 min-h-64 text-sm text-gray-800 whitespace-pre-wrap prose prose-sm max-w-none">
                      {editBody}
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Body (Markdown) — {wordCount(editBody)} words
                    </label>
                    <textarea
                      value={editBody}
                      onChange={e => setEditBody(e.target.value)}
                      rows={20}
                      className="w-full border rounded px-3 py-2 text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
                    />
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Meta Excerpt (≤280 chars)</label>
                  <textarea
                    value={editExcerpt}
                    onChange={e => setEditExcerpt(e.target.value)}
                    rows={2}
                    maxLength={280}
                    className="w-full border rounded px-3 py-2 text-sm resize-none"
                  />
                  <p className="text-xs text-gray-400 text-right">{editExcerpt.length}/280</p>
                </div>
              </div>
              {/* Sidebar */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Target Keywords</label>
                  <textarea
                    value={editKeywords}
                    onChange={e => setEditKeywords(e.target.value)}
                    rows={4}
                    placeholder="cnc machining,precision parts"
                    className="w-full border rounded px-3 py-2 text-sm resize-none"
                  />
                </div>
                {/* TOC preview */}
                <div>
                  <p className="text-xs font-medium text-gray-600 mb-1">Table of Contents</p>
                  <ul className="space-y-1">
                    {extractH2s(editBody).map((h, i) => (
                      <li key={i} className="text-xs text-indigo-600 truncate">• {h}</li>
                    ))}
                  </ul>
                </div>
                {/* Readability */}
                <div className="bg-slate-50 border rounded p-3">
                  <p className="text-xs font-medium text-gray-600 mb-2">Readability check</p>
                  <div className="space-y-1 text-xs text-gray-600">
                    <div className="flex justify-between">
                      <span>Word count</span>
                      <span className={wordCount(editBody) >= 600 ? 'text-green-600' : 'text-red-500'}>{wordCount(editBody)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>H2 headings</span>
                      <span className={extractH2s(editBody).length >= 3 ? 'text-green-600' : 'text-yellow-600'}>{extractH2s(editBody).length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Keywords set</span>
                      <span className={editKeywords ? 'text-green-600' : 'text-red-500'}>{editKeywords ? '✓' : '✗'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="p-5 border-t flex justify-end gap-2">
              <button onClick={() => setSelectedItem(null)} className="px-4 py-2 text-sm border rounded text-gray-600 hover:bg-gray-50">Cancel</button>
              <button onClick={saveArticle} disabled={saving} className="px-4 py-2 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50">
                {saving ? 'Saving…' : 'Save Article'}
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
              <h2 className="font-semibold text-gray-900">Schedule Article</h2>
              <button onClick={() => setScheduleModal(false)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Repurpose.io Workflow ID</label>
                <input value={workflowId} onChange={e => setWorkflowId(e.target.value)} placeholder="wf_blog_123" className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Publish Date/Time (optional)</label>
                <input type="datetime-local" value={scheduledAt} onChange={e => setScheduledAt(e.target.value)} className="w-full border rounded px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="p-5 border-t flex justify-end gap-2">
              <button onClick={() => setScheduleModal(false)} className="px-4 py-2 text-sm border rounded text-gray-600">Cancel</button>
              <button onClick={submitSchedule} disabled={!workflowId} className="px-4 py-2 text-sm bg-indigo-600 text-white rounded disabled:opacity-50">Confirm</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
