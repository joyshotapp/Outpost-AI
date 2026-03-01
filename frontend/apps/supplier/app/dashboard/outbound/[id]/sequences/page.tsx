'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'

interface Sequence {
  id: number
  campaign_id: number
  contact_id: number
  sequence_status: string
  current_day: number
  total_days: number
  is_hot_lead: boolean
  connection_sent_at: string | null
  connection_accepted_at: string | null
  replied_at: string | null
  reply_content: string | null
  hot_lead_flagged_at: string | null
  created_at: string
}

interface Campaign {
  id: number
  campaign_name: string
  status: string
  contacts_reached: number
  responses_received: number
  hot_leads: number
  safety_paused: number
  daily_connections_sent: number
  daily_messages_sent: number
}

const SEQ_STATUS_BADGE: Record<string, string> = {
  queued: 'bg-gray-100 text-gray-600',
  active: 'bg-blue-100 text-blue-700',
  replied: 'bg-green-100 text-green-700',
  declined: 'bg-red-100 text-red-600',
  completed: 'bg-purple-100 text-purple-700',
  paused: 'bg-yellow-100 text-yellow-700',
  failed: 'bg-red-100 text-red-600',
}

const SEQ_LABELS: Record<string, string> = {
  queued: '排隊中',
  active: '進行中',
  replied: '已回覆',
  declined: '已拒絕',
  completed: '已完成',
  paused: '已暫停',
  failed: '失敗',
}

const STATUS_FILTERS = [
  { value: '', label: '全部' },
  { value: 'active', label: '進行中' },
  { value: 'replied', label: '已回覆' },
  { value: 'queued', label: '排隊中' },
  { value: 'completed', label: '已完成' },
  { value: 'declined', label: '已拒絕' },
]

function DayProgressBar({ current, total }: { current: number; total: number }) {
  const pct = Math.min(100, Math.round((current / total) * 100))
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 w-12 text-right">
        {current}/{total}
      </span>
    </div>
  )
}

export default function SequencesPage() {
  const params = useParams()
  const campaignId = params.id as string

  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [sequences, setSequences] = useState<Sequence[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 50

  const token = () => localStorage.getItem('access_token')

  const fetchCampaign = useCallback(async () => {
    const res = await fetch(`/api/v1/outbound/campaigns/${campaignId}`, {
      headers: { Authorization: `Bearer ${token()}` },
    })
    if (res.ok) setCampaign(await res.json())
  }, [campaignId])

  const fetchSequences = useCallback(async () => {
    setLoading(true)
    try {
      const qp = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
      if (statusFilter) qp.set('status', statusFilter)
      const res = await fetch(
        `/api/v1/outbound/campaigns/${campaignId}/sequences?${qp}`,
        { headers: { Authorization: `Bearer ${token()}` } },
      )
      if (res.ok) {
        const data = await res.json()
        setSequences(data.sequences || [])
        setTotal(data.total || 0)
      }
    } finally {
      setLoading(false)
    }
  }, [campaignId, page, statusFilter])

  useEffect(() => { fetchCampaign(); fetchSequences() }, [fetchCampaign, fetchSequences])

  const handlePause = async () => {
    if (!confirm('確定要暫停此活動的 LinkedIn 序列嗎？')) return
    await fetch(`/api/v1/outbound/campaigns/${campaignId}/pause`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token()}` },
    })
    fetchCampaign()
  }

  const handleResume = async () => {
    await fetch(`/api/v1/outbound/campaigns/${campaignId}/resume`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token()}` },
    })
    fetchCampaign()
  }

  const hotLeads = sequences.filter((s) => s.is_hot_lead)
  const replied = sequences.filter((s) => s.sequence_status === 'replied')
  const active = sequences.filter((s) => s.sequence_status === 'active')

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/dashboard/outbound" className="hover:text-gray-700">Outbound 活動</Link>
        <span>/</span>
        <span className="font-medium text-gray-900">{campaign?.campaign_name ?? `活動 #${campaignId}`}</span>
        <span>/</span>
        <span>LinkedIn 序列</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">LinkedIn 序列管理</h1>
          <p className="text-gray-500 mt-1">Day 1–25 序列進度、回覆追蹤與熱線索標記</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href={`/dashboard/outbound/${campaignId}/contacts`}
            className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium"
          >
            ← 回聯絡人名單
          </Link>
          {campaign?.status === 'running' ? (
            <button
              onClick={handlePause}
              className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 text-sm font-semibold"
            >
              ⏸ 暫停活動
            </button>
          ) : campaign?.status === 'paused' ? (
            <button
              onClick={handleResume}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-semibold"
            >
              ▶ 恢復活動
            </button>
          ) : null}
        </div>
      </div>

      {/* Safety paused alert */}
      {campaign?.safety_paused ? (
        <div className="flex items-center gap-3 p-4 bg-yellow-50 border border-yellow-300 rounded-xl text-yellow-800">
          <span className="text-lg">🔒</span>
          <div>
            <p className="font-semibold">LinkedIn 安全防護已觸發</p>
            <p className="text-sm mt-0.5">
              今日連結請求 {campaign.daily_connections_sent} 次，訊息 {campaign.daily_messages_sent} 次。
              序列已自動暫停以保護帳號，明日零時自動重置計數器後可恢復。
            </p>
          </div>
        </div>
      ) : null}

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: '總序列數', value: total, icon: '📋' },
          { label: '進行中', value: active.length, icon: '▶' },
          { label: '已回覆', value: replied.length, icon: '💬' },
          { label: '🔥 熱線索', value: hotLeads.length, icon: '' },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-100 p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900">{s.value}</div>
            <div className="text-sm text-gray-500 mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Hot leads panel */}
      {hotLeads.length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-5">
          <h2 className="font-semibold text-orange-900 mb-3">🔥 熱線索回覆（{hotLeads.length} 筆）</h2>
          <div className="space-y-3">
            {hotLeads.slice(0, 5).map((s) => (
              <div
                key={s.id}
                className="bg-white rounded-lg border border-orange-100 p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">聯絡人 #{s.contact_id}</p>
                    {s.reply_content && (
                      <p className="text-sm text-gray-600 mt-1 line-clamp-3">&ldquo;{s.reply_content}&rdquo;</p>
                    )}
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-xs text-gray-400">Day {s.current_day}</div>
                    {s.replied_at && (
                      <div className="text-xs text-gray-400 mt-0.5">
                        {new Date(s.replied_at).toLocaleDateString('zh-TW')}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          {hotLeads.length > 5 && (
            <button
              onClick={() => setStatusFilter('replied')}
              className="mt-3 text-sm text-orange-700 hover:underline"
            >
              查看全部 {hotLeads.length} 筆熱線索 →
            </button>
          )}
        </div>
      )}

      {/* Status filter */}
      <div className="flex items-center gap-3 bg-white p-4 rounded-xl border border-gray-200">
        <span className="text-sm font-medium text-gray-700">篩選：</span>
        <div className="flex gap-2 flex-wrap">
          {STATUS_FILTERS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => { setStatusFilter(opt.value); setPage(1) }}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                statusFilter === opt.value
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'border border-gray-200 text-gray-600 hover:border-blue-300 hover:text-blue-600'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Sequences table */}
      {loading ? (
        <div className="flex justify-center py-16 text-gray-400">載入中…</div>
      ) : sequences.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-16 text-center">
          <p className="text-gray-500">尚無符合條件的序列記錄</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                {['聯絡人', '序列狀態', 'Day 進度', '連結請求', '已接受', '回覆'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {sequences.map((s) => (
                <tr key={s.id} className={`hover:bg-gray-50 transition-colors ${s.is_hot_lead ? 'bg-orange-50 hover:bg-orange-100' : ''}`}>
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">
                      {s.is_hot_lead && '🔥 '}聯絡人 #{s.contact_id}
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      {new Date(s.created_at).toLocaleDateString('zh-TW')}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${SEQ_STATUS_BADGE[s.sequence_status] ?? 'bg-gray-100 text-gray-600'}`}>
                      {SEQ_LABELS[s.sequence_status] ?? s.sequence_status}
                    </span>
                  </td>
                  <td className="px-4 py-3 w-40">
                    <DayProgressBar current={s.current_day} total={s.total_days} />
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {s.connection_sent_at
                      ? new Date(s.connection_sent_at).toLocaleDateString('zh-TW')
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {s.connection_accepted_at
                      ? <span className="text-green-600">✓ {new Date(s.connection_accepted_at).toLocaleDateString('zh-TW')}</span>
                      : '—'}
                  </td>
                  <td className="px-4 py-3 max-w-xs">
                    {s.reply_content ? (
                      <div className="text-xs text-gray-700 line-clamp-2 bg-green-50 rounded p-2 border border-green-100">
                        {s.reply_content}
                      </div>
                    ) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {total > pageSize && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
              <span className="text-sm text-gray-500">{total} 筆總計</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 border border-gray-200 rounded text-sm disabled:opacity-40"
                >
                  上一頁
                </button>
                <span className="px-3 py-1 text-sm text-gray-700">第 {page} 頁</span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page * pageSize >= total}
                  className="px-3 py-1 border border-gray-200 rounded text-sm disabled:opacity-40"
                >
                  下一頁
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
