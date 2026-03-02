'use client'

/**
 * Sprint 8 — Task 8.2: Email Sequence Management UI
 *
 * Shows all email campaigns with per-contact sequence progress:
 * - 4-step progress tracker
 * - open / reply / bounce counters
 * - Hot lead badge + instant Slack alert indicator
 * - Safety-pause banner when bounce rate exceeds threshold
 */

import React, { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'

// ─── Types ────────────────────────────────────────────────────────────────────

interface EmailCampaign {
  id: number
  campaign_name: string
  status: string
  email_safety_paused: boolean
  bounce_rate: number
  email_sent_count: number
  email_opened_count: number
  email_reply_count: number
  email_bounce_count: number
  instantly_campaign_id: string | null
  created_at: string
}

interface EmailSequence {
  id: number
  email: string
  full_name: string | null
  company_name: string | null
  status: string
  current_step: number
  total_steps: number
  emails_sent: number
  emails_opened: number
  reply_received: boolean
  replied_at: string | null
  is_bounced: boolean
  bounce_type: string | null
  is_unsubscribed: boolean
  is_hot_lead: boolean
  hot_lead_reason: string | null
  hubspot_synced: boolean
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const STATUS_BADGE: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-600',
  importing: 'bg-yellow-100 text-yellow-700',
  active: 'bg-green-100 text-green-700',
  paused: 'bg-orange-100 text-orange-700',
  completed: 'bg-blue-100 text-blue-700',
  replied: 'bg-purple-100 text-purple-700',
  bounced: 'bg-red-100 text-red-700',
  unsubscribed: 'bg-gray-100 text-gray-500',
}

const STEP_LABELS = ['Step 1', 'Step 2', 'Step 3', 'Step 4']

function StepIndicator({ current, total }: { current: number; total: number }) {
  const steps = Math.max(total, 4)
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: steps }).map((_, i) => (
        <React.Fragment key={i}>
          <div
            className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
              i < current
                ? 'bg-blue-600 text-white'
                : i === current
                ? 'bg-blue-200 text-blue-700 ring-2 ring-blue-400'
                : 'bg-gray-100 text-gray-400'
            }`}
          >
            {i < current ? (
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <span>{i + 1}</span>
            )}
          </div>
          {i < steps - 1 && (
            <div className={`flex-1 h-0.5 w-4 ${i < current - 1 ? 'bg-blue-600' : 'bg-gray-200'}`} />
          )}
        </React.Fragment>
      ))}
    </div>
  )
}

// ─── Campaign Card ─────────────────────────────────────────────────────────────

function CampaignCard({
  campaign,
  onSelect,
  selectedId,
}: {
  campaign: EmailCampaign
  onSelect: (id: number) => void
  selectedId: number | null
}) {
  const openRate =
    campaign.email_sent_count > 0
      ? Math.round((campaign.email_opened_count / campaign.email_sent_count) * 100)
      : 0
  const replyRate =
    campaign.email_sent_count > 0
      ? Math.round((campaign.email_reply_count / campaign.email_sent_count) * 100)
      : 0

  return (
    <button
      onClick={() => onSelect(campaign.id)}
      className={`w-full text-left p-4 rounded-xl border transition-all ${
        selectedId === campaign.id
          ? 'border-blue-500 bg-blue-50 shadow-sm'
          : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-gray-50'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0 mr-2">
          <p className="font-semibold text-gray-900 truncate">{campaign.campaign_name}</p>
          {campaign.instantly_campaign_id && (
            <p className="text-xs text-gray-400 mt-0.5 font-mono truncate">
              {campaign.instantly_campaign_id}
            </p>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span
            className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
              STATUS_BADGE[campaign.status] ?? 'bg-gray-100 text-gray-600'
            }`}
          >
            {campaign.status}
          </span>
          {campaign.email_safety_paused && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              Safety Paused
            </span>
          )}
        </div>
      </div>

      {campaign.email_safety_paused && (
        <div className="mt-2 mb-3 p-2 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
          ⚠ Bounce rate {(campaign.bounce_rate * 100).toFixed(1)}% exceeds 2% threshold. Campaign
          auto-paused to protect sender reputation.
        </div>
      )}

      <div className="grid grid-cols-4 gap-2 text-center mt-3">
        {[
          { label: 'Sent', value: campaign.email_sent_count, color: 'text-gray-700' },
          { label: 'Open %', value: `${openRate}%`, color: 'text-blue-600' },
          { label: 'Reply %', value: `${replyRate}%`, color: 'text-green-600' },
          { label: 'Bounced', value: campaign.email_bounce_count, color: 'text-red-500' },
        ].map((m) => (
          <div key={m.label} className="bg-gray-50 rounded-lg py-2">
            <p className={`text-base font-bold ${m.color}`}>{m.value}</p>
            <p className="text-xs text-gray-400">{m.label}</p>
          </div>
        ))}
      </div>
    </button>
  )
}

// ─── Sequence Row ──────────────────────────────────────────────────────────────

function SequenceRow({ seq }: { seq: EmailSequence }) {
  return (
    <tr className="hover:bg-gray-50 transition-colors">
      <td className="px-4 py-3">
        <div className="flex flex-col">
          <span className="font-medium text-gray-900 text-sm">
            {seq.full_name || seq.email}
          </span>
          {seq.full_name && (
            <span className="text-xs text-gray-400">{seq.email}</span>
          )}
          {seq.company_name && (
            <span className="text-xs text-gray-500">{seq.company_name}</span>
          )}
        </div>
      </td>
      <td className="px-4 py-3">
        <StepIndicator current={seq.current_step} total={seq.total_steps} />
      </td>
      <td className="px-4 py-3">
        <span
          className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${
            STATUS_BADGE[seq.status] ?? 'bg-gray-100 text-gray-600'
          }`}
        >
          {seq.status}
        </span>
      </td>
      <td className="px-4 py-3 text-center">
        <span className="text-sm font-semibold text-gray-700">{seq.emails_sent}</span>
        <span className="text-xs text-gray-400 ml-1">/ {seq.total_steps}</span>
      </td>
      <td className="px-4 py-3 text-center">
        <span className="text-sm text-gray-700">{seq.emails_opened}</span>
      </td>
      <td className="px-4 py-3 text-center">
        {seq.reply_received ? (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            Replied
          </span>
        ) : (
          <span className="text-xs text-gray-300">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-center">
        {seq.is_hot_lead ? (
          <span className="inline-flex items-center gap-1 text-xs font-bold text-orange-700 bg-orange-100 px-2 py-0.5 rounded-full">
            🔥 Hot
          </span>
        ) : (
          <span className="text-xs text-gray-300">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-center">
        {seq.is_bounced ? (
          <span className="text-xs text-red-500 font-medium">
            {seq.bounce_type === 'hard' ? 'Hard' : 'Soft'} bounce
          </span>
        ) : seq.is_unsubscribed ? (
          <span className="text-xs text-gray-400">Unsubscribed</span>
        ) : (
          <span className="text-xs text-gray-300">—</span>
        )}
      </td>
    </tr>
  )
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export default function EmailCampaignsPage() {
  const [campaigns, setCampaigns] = useState<EmailCampaign[]>([])
  const [selectedCampaignId, setSelectedCampaignId] = useState<number | null>(null)
  const [sequences, setSequences] = useState<EmailSequence[]>([])
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [seqLoading, setSeqLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)

  const token = () =>
    typeof window !== 'undefined' ? localStorage.getItem('access_token') ?? '' : ''

  const fetchCampaigns = useCallback(async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/v1/outbound/campaigns?campaign_type=email', {
        headers: { Authorization: `Bearer ${token()}` },
      })
      if (res.ok) {
        const data = await res.json()
        const emailCampaigns = (data.campaigns || []).filter(
          (c: EmailCampaign) => true // All campaigns returned already filtered by type
        )
        setCampaigns(emailCampaigns)
        if (emailCampaigns.length > 0 && !selectedCampaignId) {
          setSelectedCampaignId(emailCampaigns[0].id)
        }
      }
    } finally {
      setLoading(false)
    }
  }, [selectedCampaignId])

  const fetchSequences = useCallback(
    async (campaignId: number) => {
      try {
        setSeqLoading(true)
        const url = `/api/v1/outbound/campaigns/${campaignId}/email-sequences${
          statusFilter ? `?status=${statusFilter}` : ''
        }`
        const res = await fetch(url, {
          headers: { Authorization: `Bearer ${token()}` },
        })
        if (res.ok) {
          const data = await res.json()
          setSequences(data.sequences || [])
        }
      } finally {
        setSeqLoading(false)
      }
    },
    [statusFilter]
  )

  const handleSyncAnalytics = async () => {
    if (!selectedCampaignId) return
    setSyncing(true)
    try {
      await fetch(`/api/v1/outbound/campaigns/${selectedCampaignId}/sync-analytics`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token()}` },
      })
      // Refresh after a short delay to pick up updated stats
      setTimeout(() => {
        fetchCampaigns()
        fetchSequences(selectedCampaignId)
        setSyncing(false)
      }, 2000)
    } catch {
      setSyncing(false)
    }
  }

  useEffect(() => {
    fetchCampaigns()
  }, [])

  useEffect(() => {
    if (selectedCampaignId) fetchSequences(selectedCampaignId)
  }, [selectedCampaignId, statusFilter])

  const selectedCampaign = campaigns.find((c) => c.id === selectedCampaignId)

  return (
    <div className="flex gap-6 h-[calc(100vh-7rem)]">
      {/* ── Left sidebar: campaign list ── */}
      <aside className="w-80 shrink-0 flex flex-col gap-3 overflow-y-auto pr-1">
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-gray-800 text-lg">Email 活動</h2>
          <Link
            href="/dashboard/outbound/new"
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            + 新建
          </Link>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-36 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : campaigns.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <svg
              className="w-12 h-12 mx-auto mb-3 text-gray-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            <p className="text-sm font-medium">沒有 Email 活動</p>
            <p className="text-xs mt-1">建立第一個 Email 外發活動</p>
          </div>
        ) : (
          campaigns.map((c) => (
            <CampaignCard
              key={c.id}
              campaign={c}
              onSelect={setSelectedCampaignId}
              selectedId={selectedCampaignId}
            />
          ))
        )}
      </aside>

      {/* ── Main: sequence list ── */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {!selectedCampaign ? (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <p>選擇左側活動以檢視序列進度</p>
          </div>
        ) : (
          <>
            {/* ── Toolbar ── */}
            <div className="flex items-center justify-between mb-4 shrink-0">
              <div>
                <h1 className="text-xl font-bold text-gray-900">{selectedCampaign.campaign_name}</h1>
                <p className="text-sm text-gray-500 mt-0.5">
                  Email 序列進度 — {sequences.length} 個聯絡人
                </p>
              </div>
              <div className="flex items-center gap-3">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">所有狀態</option>
                  <option value="active">Active</option>
                  <option value="replied">Replied</option>
                  <option value="bounced">Bounced</option>
                  <option value="unsubscribed">Unsubscribed</option>
                  <option value="completed">Completed</option>
                </select>
                <button
                  onClick={handleSyncAnalytics}
                  disabled={syncing}
                  className="flex items-center gap-2 px-4 py-1.5 bg-white border border-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
                >
                  <svg
                    className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`}
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
                  {syncing ? '同步中…' : '同步分析'}
                </button>
              </div>
            </div>

            {/* ── Safety pause banner ── */}
            {selectedCampaign.email_safety_paused && (
              <div className="mb-4 shrink-0 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
                <svg
                  className="w-5 h-5 text-red-500 shrink-0 mt-0.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <div>
                  <p className="font-semibold text-red-800 text-sm">活動已自動暫停</p>
                  <p className="text-red-600 text-sm mt-0.5">
                    Bounce rate 達 {(selectedCampaign.bounce_rate * 100).toFixed(1)}%，已超過 2% 安全閾值。
                    請清理名單後手動恢復活動。
                  </p>
                </div>
              </div>
            )}

            {/* ── Table ── */}
            <div className="flex-1 overflow-auto rounded-xl border border-gray-200 bg-white">
              {seqLoading ? (
                <div className="flex items-center justify-center h-48">
                  <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
                </div>
              ) : sequences.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-48 text-gray-400">
                  <p className="text-sm">沒有符合的序列記錄</p>
                </div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      {[
                        '聯絡人',
                        '進度',
                        '狀態',
                        '已發送',
                        '已開信',
                        '回覆',
                        'Hot Lead',
                        '異常',
                      ].map((h) => (
                        <th
                          key={h}
                          className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {sequences.map((s) => (
                      <SequenceRow key={s.id} seq={s} />
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  )
}
