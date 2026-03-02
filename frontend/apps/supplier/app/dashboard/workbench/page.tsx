'use client'

/**
 * Sprint 8 — Task 8.6: Business Workbench (統一業務工作台)
 *
 * Shows unified leads from ALL inbound sources (RFQ / LinkedIn / Email /
 * Visitor / Chat / Manual) with AI-grade badge, source icon, and one-click
 * draft reply panel for B/A-grade leads.
 */

import React, { useState, useEffect, useCallback } from 'react'

// ─── Types ────────────────────────────────────────────────────────────────────

interface UnifiedLead {
  id: number
  email: string
  full_name: string | null
  company_name: string | null
  job_title: string | null
  source: string
  source_ref_id: string | null
  lead_score: number
  lead_grade: 'A' | 'B' | 'C' | string
  status: string
  recommended_action: string | null
  is_hot_lead: boolean
  auto_reply_sent: boolean
  draft_reply_body: string | null
  draft_reply_sent: boolean
  hubspot_synced: boolean
  created_at: string
  updated_at: string
}

interface LeadDetail extends UnifiedLead {
  company_domain: string | null
  phone: string | null
  linkedin_url: string | null
  score_breakdown: Record<string, unknown>
  hot_lead_reason: string | null
  auto_reply_type: string | null
  draft_reply_generated_at: string | null
  draft_reply_sent_at: string | null
  hubspot_contact_id: string | null
  hubspot_deal_id: string | null
  raw_payload: Record<string, unknown>
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const GRADE_CONFIG: Record<string, { label: string; color: string; bg: string; ring: string }> = {
  A: { label: 'Grade A', color: 'text-green-800', bg: 'bg-green-100', ring: 'ring-green-400' },
  B: { label: 'Grade B', color: 'text-blue-800', bg: 'bg-blue-100', ring: 'ring-blue-400' },
  C: { label: 'Grade C', color: 'text-gray-600', bg: 'bg-gray-100', ring: 'ring-gray-300' },
}

const SOURCE_ICON: Record<string, string> = {
  rfq: '📋',
  linkedin: '💼',
  email: '✉️',
  visitor: '👀',
  chat: '💬',
  manual: '✍️',
}

const STATUS_BADGE: Record<string, string> = {
  new: 'bg-blue-50 text-blue-700',
  contacted: 'bg-purple-50 text-purple-700',
  replied: 'bg-green-50 text-green-700',
  converted: 'bg-emerald-50 text-emerald-700',
  lost: 'bg-gray-100 text-gray-500',
}

function GradeBadge({ grade }: { grade: string }) {
  const cfg = GRADE_CONFIG[grade] ?? GRADE_CONFIG['C']
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${cfg.bg} ${cfg.color} ring-1 ${cfg.ring}`}
    >
      {grade}
    </span>
  )
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.min(100, Math.max(0, score))
  const color =
    pct >= 80 ? 'bg-green-500' : pct >= 50 ? 'bg-blue-500' : 'bg-gray-300'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold text-gray-600 w-6 text-right">{score}</span>
    </div>
  )
}

// ─── Draft Panel ──────────────────────────────────────────────────────────────

function DraftPanel({
  lead,
  onRefresh,
}: {
  lead: LeadDetail
  onRefresh: () => void
}) {
  const [sending, setSending] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [error, setError] = useState('')

  const token = () => localStorage.getItem('access_token') ?? ''

  const handleSend = async () => {
    setSending(true)
    setError('')
    try {
      const res = await fetch(`/api/v1/outbound/leads/${lead.id}/send-draft`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token()}` },
      })
      if (!res.ok) {
        const body = await res.json()
        setError(body.detail || '發送失敗')
      } else {
        onRefresh()
      }
    } finally {
      setSending(false)
    }
  }

  const handleRegenerate = async () => {
    setRegenerating(true)
    setError('')
    try {
      const res = await fetch(`/api/v1/outbound/leads/${lead.id}/regenerate-draft`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token()}` },
      })
      if (!res.ok) {
        const body = await res.json()
        setError(body.detail || '重新生成失敗')
      } else {
        // Poll for draft completion
        setTimeout(onRefresh, 4000)
      }
    } finally {
      setRegenerating(false)
    }
  }

  if (lead.draft_reply_sent) {
    return (
      <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-xl">
        <div className="flex items-center gap-2 text-green-700">
          <svg className="w-5 h-5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          <span className="text-sm font-semibold">草稿已發送</span>
        </div>
        {lead.draft_reply_sent_at && (
          <p className="text-xs text-green-600 mt-1">
            {new Date(lead.draft_reply_sent_at).toLocaleString('zh-TW')}
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-semibold text-gray-700">AI 草稿回覆</p>
        <div className="flex gap-2">
          <button
            onClick={handleRegenerate}
            disabled={regenerating || sending}
            className="text-xs text-gray-500 hover:text-gray-700 disabled:opacity-50 flex items-center gap-1"
          >
            <svg
              className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            {regenerating ? '生成中…' : '重新生成'}
          </button>
        </div>
      </div>

      {lead.draft_reply_body ? (
        <>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm text-gray-700 whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed">
            {lead.draft_reply_body}
          </div>
          {lead.draft_reply_generated_at && (
            <p className="text-xs text-gray-400 mt-1">
              由 Claude AI 生成 · {new Date(lead.draft_reply_generated_at).toLocaleString('zh-TW')}
            </p>
          )}
          {error && <p className="text-xs text-red-500 mt-2">{error}</p>}
          <button
            onClick={handleSend}
            disabled={sending}
            className="mt-3 w-full flex items-center justify-center gap-2 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {sending ? (
              <>
                <svg
                  className="w-4 h-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v1m0 14v1m-7-7H4m14 0h1M6.343 6.343l-.707-.707m12.728 12.728l-.707-.707M6.343 17.657l-.707.707M17.657 6.343l-.707.707"
                  />
                </svg>
                發送中…
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
                確認發送草稿
              </>
            )}
          </button>
        </>
      ) : (
        <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-4 text-center text-sm text-gray-400">
          {regenerating ? (
            <div className="flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-blue-200 border-t-blue-500 rounded-full animate-spin" />
              <p>Claude AI 正在生成草稿…</p>
            </div>
          ) : (
            <p>尚無草稿。點擊「重新生成」以使用 AI 建立草稿</p>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Lead Card ────────────────────────────────────────────────────────────────

function LeadCard({
  lead,
  selected,
  onClick,
}: {
  lead: UnifiedLead
  selected: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-xl border transition-all ${
        selected
          ? 'border-blue-500 bg-blue-50 shadow-sm'
          : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-gray-50'
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center shrink-0 text-sm font-bold text-blue-700">
          {(lead.full_name?.[0] ?? lead.email[0]).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="font-semibold text-gray-900 text-sm truncate">
              {lead.full_name || lead.email}
            </p>
            {lead.is_hot_lead && <span className="shrink-0 text-sm">🔥</span>}
          </div>
          {lead.company_name && (
            <p className="text-xs text-gray-500 truncate">{lead.company_name}</p>
          )}
          <div className="flex items-center gap-2 mt-1.5">
            <span className="text-sm">{SOURCE_ICON[lead.source] ?? '📌'}</span>
            <span className="text-xs text-gray-400">{lead.source}</span>
          </div>
        </div>
        <div className="shrink-0">
          <GradeBadge grade={lead.lead_grade} />
        </div>
      </div>
      <div className="mt-2">
        <ScoreBar score={lead.lead_score} />
      </div>
      <div className="flex items-center justify-between mt-2">
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded-full ${
            STATUS_BADGE[lead.status] ?? 'bg-gray-100 text-gray-500'
          }`}
        >
          {lead.status}
        </span>
        <span className="text-xs text-gray-400">
          {new Date(lead.created_at).toLocaleDateString('zh-TW')}
        </span>
      </div>
    </button>
  )
}

// ─── Lead Detail Panel ────────────────────────────────────────────────────────

function LeadDetailPanel({
  leadId,
  onRefresh,
}: {
  leadId: number
  onRefresh: () => void
}) {
  const [lead, setLead] = useState<LeadDetail | null>(null)
  const [loading, setLoading] = useState(true)

  const token = () => localStorage.getItem('access_token') ?? ''

  const fetchDetail = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/v1/outbound/leads/${leadId}`, {
        headers: { Authorization: `Bearer ${token()}` },
      })
      if (res.ok) setLead(await res.json())
    } finally {
      setLoading(false)
    }
  }, [leadId])

  useEffect(() => {
    fetchDetail()
  }, [fetchDetail])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      </div>
    )
  }

  if (!lead) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <p>載入失敗，請重試</p>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-100 to-indigo-200 flex items-center justify-center text-lg font-bold text-blue-700 shrink-0">
            {(lead.full_name?.[0] ?? lead.email[0]).toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">{lead.full_name || lead.email}</h2>
            {lead.job_title && lead.company_name && (
              <p className="text-sm text-gray-500 mt-0.5">
                {lead.job_title} · {lead.company_name}
              </p>
            )}
            <div className="flex items-center gap-2 mt-2">
              <GradeBadge grade={lead.lead_grade} />
              {lead.is_hot_lead && (
                <span className="inline-flex items-center gap-1 bg-orange-100 text-orange-700 text-xs font-bold px-2.5 py-1 rounded-full">
                  🔥 Hot Lead
                </span>
              )}
              <span
                className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                  STATUS_BADGE[lead.status] ?? 'bg-gray-100 text-gray-500'
                }`}
              >
                {lead.status}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Score */}
      <section className="mb-5 p-4 bg-gray-50 rounded-xl">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-semibold text-gray-700">AI 評分</p>
          <span className="text-2xl font-black text-gray-900">{lead.lead_score}</span>
        </div>
        <ScoreBar score={lead.lead_score} />
        {lead.recommended_action && (
          <p className="text-xs text-gray-500 mt-2">
            建議行動: <span className="font-medium text-gray-700">{lead.recommended_action}</span>
          </p>
        )}
        {lead.hot_lead_reason && (
          <p className="text-xs text-orange-600 mt-1">🔥 {lead.hot_lead_reason}</p>
        )}
      </section>

      {/* Contact Info */}
      <section className="mb-5">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">聯絡資訊</p>
        <div className="space-y-1.5">
          {[
            { label: 'Email', value: lead.email },
            { label: 'Phone', value: lead.phone },
            { label: 'LinkedIn', value: lead.linkedin_url },
            { label: 'Domain', value: lead.company_domain },
            { label: 'Source', value: `${SOURCE_ICON[lead.source] ?? '📌'} ${lead.source}` },
            { label: 'Source Ref', value: lead.source_ref_id },
          ]
            .filter((f) => f.value)
            .map((f) => (
              <div key={f.label} className="flex gap-3 text-sm">
                <span className="w-20 shrink-0 text-gray-400 text-xs pt-0.5">{f.label}</span>
                <span className="text-gray-700 break-all">{f.value}</span>
              </div>
            ))}
        </div>
      </section>

      {/* Automation status */}
      <section className="mb-5">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">自動化狀態</p>
        <div className="flex flex-wrap gap-2">
          {[
            { label: 'Auto Reply', done: lead.auto_reply_sent },
            { label: 'HubSpot Sync', done: lead.hubspot_synced },
            { label: 'Draft Ready', done: !!lead.draft_reply_body },
            { label: 'Draft Sent', done: lead.draft_reply_sent },
          ].map((item) => (
            <span
              key={item.label}
              className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium ${
                item.done
                  ? 'bg-green-50 text-green-700'
                  : 'bg-gray-100 text-gray-400'
              }`}
            >
              {item.done ? (
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <span className="w-3 h-3 rounded-full border border-gray-300" />
              )}
              {item.label}
            </span>
          ))}
        </div>
      </section>

      {/* Draft Panel (only B/A grade) */}
      {(lead.lead_grade === 'A' || lead.lead_grade === 'B') && (
        <section>
          <DraftPanel
            lead={lead}
            onRefresh={() => {
              fetchDetail()
              onRefresh()
            }}
          />
        </section>
      )}
    </div>
  )
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export default function WorkbenchPage() {
  const [leads, setLeads] = useState<UnifiedLead[]>([])
  const [total, setTotal] = useState(0)
  const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)

  // Filters
  const [gradeFilter, setGradeFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [hotOnly, setHotOnly] = useState(false)

  const token = () => localStorage.getItem('access_token') ?? ''

  const fetchLeads = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (gradeFilter) params.set('lead_grade', gradeFilter)
      if (sourceFilter) params.set('source', sourceFilter)
      if (statusFilter) params.set('status', statusFilter)
      if (hotOnly) params.set('is_hot_lead', 'true')
      params.set('page', String(page))
      params.set('page_size', '30')

      const res = await fetch(`/api/v1/outbound/leads?${params}`, {
        headers: { Authorization: `Bearer ${token()}` },
      })
      if (res.ok) {
        const data = await res.json()
        setLeads(data.leads || [])
        setTotal(data.total || 0)
        if (!selectedLeadId && data.leads?.length > 0) {
          setSelectedLeadId(data.leads[0].id)
        }
      }
    } finally {
      setLoading(false)
    }
  }, [gradeFilter, sourceFilter, statusFilter, hotOnly, page, selectedLeadId])

  useEffect(() => {
    fetchLeads()
  }, [gradeFilter, sourceFilter, statusFilter, hotOnly, page])

  return (
    <div className="flex gap-0 h-[calc(100vh-7rem)] -mx-6 -mt-4">
      {/* ── Left: Filters + Lead list ── */}
      <aside className="w-80 shrink-0 flex flex-col border-r border-gray-200 bg-white">
        {/* Filters bar */}
        <div className="p-4 border-b border-gray-100 space-y-3">
          <h2 className="font-bold text-gray-800 text-base">業務工作台</h2>
          <p className="text-xs text-gray-400">
            {total} 條線索 · 所有進線來源
          </p>

          <div className="grid grid-cols-2 gap-2">
            <select
              value={gradeFilter}
              onChange={(e) => { setGradeFilter(e.target.value); setPage(1) }}
              className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              <option value="">所有等級</option>
              <option value="A">Grade A</option>
              <option value="B">Grade B</option>
              <option value="C">Grade C</option>
            </select>

            <select
              value={sourceFilter}
              onChange={(e) => { setSourceFilter(e.target.value); setPage(1) }}
              className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              <option value="">所有來源</option>
              <option value="rfq">📋 RFQ</option>
              <option value="linkedin">💼 LinkedIn</option>
              <option value="email">✉️ Email</option>
              <option value="visitor">👀 Visitor</option>
              <option value="chat">💬 Chat</option>
              <option value="manual">✍️ Manual</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
              className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              <option value="">所有狀態</option>
              <option value="new">New</option>
              <option value="contacted">Contacted</option>
              <option value="replied">Replied</option>
              <option value="converted">Converted</option>
              <option value="lost">Lost</option>
            </select>

            <button
              onClick={() => { setHotOnly(!hotOnly); setPage(1) }}
              className={`text-xs font-medium px-2 py-1.5 rounded-lg border transition-colors ${
                hotOnly
                  ? 'bg-orange-500 text-white border-orange-500'
                  : 'border-gray-200 text-gray-600 hover:bg-orange-50 hover:border-orange-200'
              }`}
            >
              🔥 Hot Only
            </button>
          </div>
        </div>

        {/* Lead list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {loading ? (
            <div className="space-y-3 pt-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-28 bg-gray-100 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : leads.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full pt-16 text-gray-400">
              <svg
                className="w-12 h-12 text-gray-300 mb-3"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <p className="text-sm">沒有符合的線索</p>
            </div>
          ) : (
            leads.map((lead) => (
              <LeadCard
                key={lead.id}
                lead={lead}
                selected={selectedLeadId === lead.id}
                onClick={() => setSelectedLeadId(lead.id)}
              />
            ))
          )}

          {/* Pagination */}
          {total > 30 && (
            <div className="flex items-center justify-center gap-2 pt-3 pb-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="px-3 py-1.5 text-xs border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
              >
                上一頁
              </button>
              <span className="text-xs text-gray-500">
                {page} / {Math.ceil(total / 30)}
              </span>
              <button
                disabled={page >= Math.ceil(total / 30)}
                onClick={() => setPage(page + 1)}
                className="px-3 py-1.5 text-xs border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
              >
                下一頁
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* ── Right: Lead detail ── */}
      <div className="flex-1 bg-white overflow-hidden">
        {selectedLeadId ? (
          <LeadDetailPanel leadId={selectedLeadId} onRefresh={fetchLeads} />
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-3">
            <svg
              className="w-14 h-14 text-gray-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
              />
            </svg>
            <p className="text-sm font-medium">選擇線索以查看詳細資訊</p>
            <p className="text-xs">包含 AI 草稿回覆與自動化狀態</p>
          </div>
        )}
      </div>
    </div>
  )
}
