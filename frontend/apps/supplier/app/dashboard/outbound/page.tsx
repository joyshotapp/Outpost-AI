'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'

interface Campaign {
  id: number
  campaign_name: string
  campaign_type: string
  status: string
  clay_enrichment_status: string
  target_count: number
  contacts_reached: number
  hot_leads: number
  responses_received: number
  safety_paused: number
  created_at: string
}

const STATUS_BADGE: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  running: 'bg-green-100 text-green-800',
  paused: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-blue-100 text-blue-800',
}

const ENRICH_BADGE: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-500',
  running: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
}

export default function OutboundCampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchCampaigns = async () => {
      try {
        const token = localStorage.getItem('access_token')
        const res = await fetch('/api/v1/outbound/campaigns', {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.ok) {
          const data = await res.json()
          setCampaigns(data.campaigns || [])
        }
      } catch {
        // silently fail in dev
      } finally {
        setLoading(false)
      }
    }
    fetchCampaigns()
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Outbound 活動</h1>
          <p className="text-gray-500 mt-1">
            Clay ICP 名單富化 + HeyReach LinkedIn 自動序列
          </p>
        </div>
        <Link
          href="/dashboard/outbound/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          新建活動
        </Link>
      </div>

      {/* Campaign cards */}
      {loading ? (
        <div className="flex items-center justify-center h-48 text-gray-400">載入中…</div>
      ) : campaigns.length === 0 ? (
        <div className="border-2 border-dashed border-gray-200 rounded-xl p-12 text-center">
          <svg
            className="w-12 h-12 text-gray-300 mx-auto mb-4"
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-700 mb-2">尚無 Outbound 活動</h3>
          <p className="text-gray-500 mb-6">設定 ICP 條件，讓 Clay 自動建立目標名單</p>
          <Link
            href="/dashboard/outbound/new"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            建立第一個活動
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {campaigns.map((c) => (
            <div key={c.id} className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-semibold text-gray-900 text-lg truncate">{c.campaign_name}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_BADGE[c.status] ?? 'bg-gray-100 text-gray-700'}`}>
                        {c.status}
                        {c.safety_paused ? ' 🔒 安全暫停' : ''}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <span>LinkedIn</span>
                      <span>·</span>
                      <span>Clay 富化：
                        <span className={`ml-1 px-1.5 py-0.5 rounded text-xs font-medium ${ENRICH_BADGE[c.clay_enrichment_status] ?? ''}`}>
                          {c.clay_enrichment_status}
                        </span>
                      </span>
                      <span>·</span>
                      <span>{new Date(c.created_at).toLocaleDateString('zh-TW')}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Link
                      href={`/dashboard/outbound/${c.id}/contacts`}
                      className="text-sm px-3 py-1.5 border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      名單
                    </Link>
                    <Link
                      href={`/dashboard/outbound/${c.id}/sequences`}
                      className="text-sm px-3 py-1.5 border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      序列
                    </Link>
                  </div>
                </div>

                {/* Stats row */}
                <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-100">
                  {[
                    { label: '目標聯絡人', value: c.target_count },
                    { label: '已接觸', value: c.contacts_reached },
                    { label: '回覆', value: c.responses_received },
                    { label: '🔥 熱線索', value: c.hot_leads },
                  ].map((s) => (
                    <div key={s.label} className="text-center">
                      <div className="text-xl font-bold text-gray-900">{s.value}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{s.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
