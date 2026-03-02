'use client'

/**
 * Sprint 9 — Task 9.8: Short Video Management UI
 *
 * Shows OpusClip-generated short clips with preview player, highlights score,
 * status badges, and schedule-to-YouTube/LinkedIn controls.
 */

import React, { useState, useEffect, useCallback } from 'react'

interface ContentItem {
  id: number
  content_type: string
  title: string
  body: string
  status: string
  platform: string | null
  scheduled_publish_date: string | null
  published_url: string | null
  quality_score: number | null
  impressions: number
  engagements: number
  views?: number
  opusclip_job_id: string | null
  short_video_url: string | null
  short_video_duration_s: number | null
  opusclip_highlights_score: number | null
  source_video_id: number | null
  review_notes: string | null
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  draft:      { label: 'Ready',      color: 'text-gray-700',   bg: 'bg-gray-100' },
  processing: { label: 'Processing', color: 'text-yellow-800', bg: 'bg-yellow-100' },
  review:     { label: 'Review',     color: 'text-orange-800', bg: 'bg-orange-100' },
  approved:   { label: 'Approved',   color: 'text-green-800',  bg: 'bg-green-100' },
  scheduled:  { label: 'Scheduled',  color: 'text-blue-800',   bg: 'bg-blue-100' },
  published:  { label: 'Published',  color: 'text-violet-800', bg: 'bg-violet-100' },
  rejected:   { label: 'Rejected',   color: 'text-red-800',    bg: 'bg-red-100' },
  archived:   { label: 'Archived',   color: 'text-slate-600',  bg: 'bg-slate-100' },
}

function durationStr(s: number | null): string {
  if (!s) return '—'
  const m = Math.floor(s / 60)
  const sec = s % 60
  return m > 0 ? `${m}m ${sec}s` : `${sec}s`
}

function highlightBadge(score: number | null): React.ReactNode {
  if (score === null) return null
  const color = score >= 80 ? 'text-green-600 bg-green-50' : score >= 60 ? 'text-yellow-700 bg-yellow-50' : 'text-gray-500 bg-gray-100'
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${color}`}>⚡ {score}</span>
}

type Platform = 'linkedin' | 'youtube' | 'instagram'

export default function ShortVideosPage() {
  const [items, setItems] = useState<ContentItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [previewItem, setPreviewItem] = useState<ContentItem | null>(null)
  const [scheduleModal, setScheduleModal] = useState(false)
  const [scheduleTarget, setScheduleTarget] = useState<ContentItem | null>(null)
  const [workflowId, setWorkflowId] = useState('')
  const [scheduledAt, setScheduledAt] = useState('')
  const [platform, setPlatform] = useState<Platform>('youtube')
  const [actionMsg, setActionMsg] = useState<string | null>(null)

  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

  const fetchClips = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ content_type: 'short_video', page: String(page), page_size: '20' })
      if (statusFilter) params.set('status', statusFilter)
      const res = await fetch(`${API}/content?${params}`, { credentials: 'include' })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setItems(data.items || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
    } catch {
      setActionMsg('Failed to load clips')
    } finally {
      setLoading(false)
    }
  }, [page, statusFilter, API])

  useEffect(() => { fetchClips() }, [fetchClips])

  const approveItem = async (id: number) => {
    await fetch(`${API}/content/${id}/status`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
      body: JSON.stringify({ status: 'approved' }),
    })
    setActionMsg('Approved')
    fetchClips()
  }

  const submitSchedule = async () => {
    if (!scheduleTarget || !workflowId) return
    const res = await fetch(`${API}/content/${scheduleTarget.id}/schedule`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
      body: JSON.stringify({ workflow_id: workflowId, scheduled_at: scheduledAt || null, platform }),
    })
    setActionMsg(res.ok ? 'Clip scheduled' : 'Schedule failed')
    setScheduleModal(false)
    fetchClips()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Short Videos</h1>
          <p className="text-sm text-gray-500 mt-0.5">AI-selected highlights from your long-form videos — preview and publish</p>
        </div>
        <span className="text-sm text-gray-400">{total} clips</span>
      </div>

      {/* Filter tabs */}
      <div className="px-6 py-3 bg-white border-b flex gap-2 flex-wrap">
        {['', 'processing', 'draft', 'approved', 'scheduled', 'published'].map(s => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1) }}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition ${
              statusFilter === s ? 'bg-violet-600 text-white border-violet-600' : 'bg-white text-gray-600 border-gray-200 hover:border-violet-400'
            }`}
          >
            {s ? STATUS_CONFIG[s]?.label : 'All'}
          </button>
        ))}
      </div>

      {actionMsg && (
        <div className="mx-6 mt-4 p-3 bg-violet-50 border border-violet-200 rounded text-sm text-violet-700 flex justify-between">
          {actionMsg}
          <button onClick={() => setActionMsg(null)}>✕</button>
        </div>
      )}

      {/* Grid of clips */}
      <div className="px-6 py-4">
        {loading ? (
          <div className="text-center py-16 text-gray-400">Loading…</div>
        ) : items.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <div className="text-5xl mb-3">🎬</div>
            <p className="font-medium">No short clips yet</p>
            <p className="text-sm">Clips are generated automatically when you trigger the content viral pipeline</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {items.map(item => {
              const sc = STATUS_CONFIG[item.status] || STATUS_CONFIG.draft
              return (
                <div key={item.id} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                  {/* Thumbnail / video area */}
                  <div
                    className="relative bg-gradient-to-br from-gray-900 to-gray-700 flex items-center justify-center cursor-pointer"
                    style={{ paddingTop: '56.25%' }}
                    onClick={() => setPreviewItem(item)}
                  >
                    <div className="absolute inset-0 flex flex-col items-center justify-center gap-1 text-white">
                      {item.status === 'processing' ? (
                        <div className="animate-pulse text-yellow-400">
                          <div className="text-3xl">⏳</div>
                          <div className="text-xs mt-1">Processing</div>
                        </div>
                      ) : item.short_video_url ? (
                        <>
                          <div className="text-5xl">▶</div>
                          <div className="text-xs opacity-70 mt-1">{durationStr(item.short_video_duration_s)}</div>
                        </>
                      ) : (
                        <div className="text-gray-400 text-3xl">🎬</div>
                      )}
                    </div>
                    <div className="absolute top-2 right-2 flex gap-1">
                      {highlightBadge(item.opusclip_highlights_score)}
                    </div>
                    <div className="absolute top-2 left-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${sc.bg} ${sc.color}`}>{sc.label}</span>
                    </div>
                  </div>
                  {/* Card body */}
                  <div className="p-3">
                    <p className="text-sm font-medium text-gray-800 truncate">{item.title}</p>
                    {item.body && item.status !== 'processing' && (
                      <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{item.body}</p>
                    )}
                    {item.status === 'published' && (
                      <div className="flex gap-3 mt-2 text-xs text-gray-500">
                        <span>👁 {item.impressions.toLocaleString()}</span>
                        <span>💬 {item.engagements}</span>
                      </div>
                    )}
                    {/* Actions */}
                    <div className="flex gap-2 mt-3">
                      {item.short_video_url && (
                        <button
                          onClick={() => setPreviewItem(item)}
                          className="flex-1 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-700"
                        >
                          Preview
                        </button>
                      )}
                      {item.status === 'draft' && (
                        <button
                          onClick={() => approveItem(item.id)}
                          className="flex-1 px-2 py-1 text-xs bg-green-100 hover:bg-green-200 rounded text-green-700"
                        >
                          Approve
                        </button>
                      )}
                      {item.status === 'approved' && (
                        <button
                          onClick={() => { setScheduleTarget(item); setScheduleModal(true) }}
                          className="flex-1 px-2 py-1 text-xs bg-violet-600 hover:bg-violet-700 rounded text-white"
                        >
                          Schedule
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
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

      {/* Preview modal */}
      {previewItem && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setPreviewItem(null)}>
          <div className="bg-black rounded-2xl shadow-2xl max-w-2xl w-full" onClick={e => e.stopPropagation()}>
            <div className="p-4 flex items-center justify-between text-white">
              <span className="font-medium">{previewItem.title}</span>
              <button onClick={() => setPreviewItem(null)} className="text-gray-400 hover:text-white">✕</button>
            </div>
            {previewItem.short_video_url ? (
              <video
                src={previewItem.short_video_url}
                controls
                autoPlay
                className="w-full rounded-b-2xl"
                style={{ maxHeight: '70vh' }}
              />
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">Video URL not available</div>
            )}
            <div className="p-4 text-xs text-gray-400 flex gap-4">
              <span>Duration: {durationStr(previewItem.short_video_duration_s)}</span>
              {previewItem.opusclip_highlights_score !== null && (
                <span>Highlight score: {previewItem.opusclip_highlights_score}/100</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Schedule modal */}
      {scheduleModal && scheduleTarget && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="p-5 border-b flex items-center justify-between">
              <h2 className="font-semibold text-gray-900">Schedule Short Clip</h2>
              <button onClick={() => setScheduleModal(false)} className="text-gray-400">✕</button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Platform</label>
                <select value={platform} onChange={e => setPlatform(e.target.value as Platform)} className="w-full border rounded px-3 py-2 text-sm">
                  <option value="youtube">YouTube</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="instagram">Instagram</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Workflow ID</label>
                <input value={workflowId} onChange={e => setWorkflowId(e.target.value)} placeholder="wf_youtube_123" className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Publish Date/Time (optional)</label>
                <input type="datetime-local" value={scheduledAt} onChange={e => setScheduledAt(e.target.value)} className="w-full border rounded px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="p-5 border-t flex justify-end gap-2">
              <button onClick={() => setScheduleModal(false)} className="px-4 py-2 text-sm border rounded text-gray-600">Cancel</button>
              <button onClick={submitSchedule} disabled={!workflowId} className="px-4 py-2 text-sm bg-violet-600 text-white rounded disabled:opacity-50">Confirm</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
