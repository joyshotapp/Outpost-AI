'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'

interface Contact {
  id: number
  full_name: string | null
  email: string | null
  linkedin_url: string | null
  company_name: string | null
  company_industry: string | null
  company_size: string | null
  company_country: string | null
  job_title: string | null
  seniority: string | null
  status: string
  is_hot_lead: boolean
  linkedin_opener: string | null
  sequence_day: number | null
  lead_score: number | null
  created_at: string
}

interface Campaign {
  id: number
  campaign_name: string
  clay_enrichment_status: string
  status: string
  target_count: number
}

const STATUS_OPTS = [
  { value: '', label: '全部' },
  { value: 'enriched', label: '已富化' },
  { value: 'approved', label: '已批准' },
  { value: 'excluded', label: '已排除' },
  { value: 'in_sequence', label: '序列中' },
  { value: 'replied', label: '已回覆' },
]

const STATUS_BADGE: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-600',
  enriched: 'bg-blue-100 text-blue-700',
  approved: 'bg-green-100 text-green-700',
  excluded: 'bg-red-100 text-red-600',
  in_sequence: 'bg-purple-100 text-purple-700',
  replied: 'bg-yellow-100 text-yellow-700',
  hot_lead: 'bg-orange-100 text-orange-700',
}

export default function ContactsPage() {
  const params = useParams()
  const router = useRouter()
  const campaignId = params.id as string

  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [startingSequence, setStartingSequence] = useState(false)
  const pageSize = 50

  const token = () => localStorage.getItem('access_token')

  const fetchCampaign = useCallback(async () => {
    const res = await fetch(`/api/v1/outbound/campaigns/${campaignId}`, {
      headers: { Authorization: `Bearer ${token()}` },
    })
    if (res.ok) setCampaign(await res.json())
  }, [campaignId])

  const fetchContacts = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      })
      if (statusFilter) params.set('status', statusFilter)

      const res = await fetch(
        `/api/v1/outbound/campaigns/${campaignId}/contacts?${params}`,
        { headers: { Authorization: `Bearer ${token()}` } },
      )
      if (res.ok) {
        const data = await res.json()
        setContacts(data.contacts || [])
        setTotal(data.total || 0)
      }
    } finally {
      setLoading(false)
    }
  }, [campaignId, page, statusFilter])

  useEffect(() => { fetchCampaign(); fetchContacts() }, [fetchCampaign, fetchContacts])

  const handleApprove = async (contactId: number) => {
    await fetch(`/api/v1/outbound/contacts/${contactId}/approve`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token()}` },
    })
    fetchContacts()
  }

  const handleExclude = async (contactId: number) => {
    await fetch(`/api/v1/outbound/contacts/${contactId}/exclude`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token()}` },
    })
    fetchContacts()
  }

  const handleStartSequence = async () => {
    if (!confirm('確定要為所有「已批准」的聯絡人生成開場白並啟動 HeyReach 序列嗎？')) return
    setStartingSequence(true)
    try {
      await fetch(`/api/v1/outbound/campaigns/${campaignId}/start-sequence`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token()}` },
      })
      alert('序列已開始排程！AI 正在生成個人化開場白，完成後自動匯入 HeyReach。')
      router.push(`/dashboard/outbound/${campaignId}/sequences`)
    } finally {
      setStartingSequence(false)
    }
  }

  const enrichingStatus = campaign?.clay_enrichment_status
  const approvedCount = contacts.filter((c) => c.status === 'approved').length

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/dashboard/outbound" className="hover:text-gray-700">Outbound 活動</Link>
        <span>/</span>
        <span className="font-medium text-gray-900">{campaign?.campaign_name ?? `活動 #${campaignId}`}</span>
        <span>/</span>
        <span>聯絡人名單</span>
      </div>

      {/* Page header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">目標名單管理</h1>
          <p className="text-gray-500 mt-1">
            審核 Clay 富化的聯絡人，批准後一鍵啟動 LinkedIn 外展序列
          </p>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          <Link
            href={`/dashboard/outbound/${campaignId}/sequences`}
            className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium"
          >
            查看序列進度
          </Link>
          {approvedCount > 0 && (
            <button
              onClick={handleStartSequence}
              disabled={startingSequence}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-semibold disabled:opacity-50"
            >
              {startingSequence ? '啟動中…' : `🚀 啟動序列 (${approvedCount} 人)`}
            </button>
          )}
        </div>
      </div>

      {/* Enrichment status banner */}
      {enrichingStatus && enrichingStatus !== 'completed' && (
        <div className={`flex items-center gap-3 p-4 rounded-xl border ${
          enrichingStatus === 'running'
            ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
            : enrichingStatus === 'failed'
            ? 'bg-red-50 border-red-200 text-red-800'
            : 'bg-gray-50 border-gray-200 text-gray-700'
        }`}>
          {enrichingStatus === 'running' && (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
          <span className="font-medium">
            Clay 富化狀態：{enrichingStatus === 'running' ? '正在搜尋並富化聯絡人，請稍候…' : enrichingStatus}
          </span>
        </div>
      )}

      {/* Summary bar */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: '總聯絡人', value: total, color: 'text-gray-900' },
          { label: '已批准', value: contacts.filter((c) => c.status === 'approved').length, color: 'text-green-700' },
          { label: '已排除', value: contacts.filter((c) => c.status === 'excluded').length, color: 'text-red-600' },
          { label: '🔥 熱線索', value: contacts.filter((c) => c.is_hot_lead).length, color: 'text-orange-700' },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-100 p-4 text-center shadow-sm">
            <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-sm text-gray-500 mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-3 bg-white p-4 rounded-xl border border-gray-200">
        <span className="text-sm font-medium text-gray-700">篩選狀態：</span>
        <div className="flex gap-2 flex-wrap">
          {STATUS_OPTS.map((opt) => (
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

      {/* Contact table */}
      {loading ? (
        <div className="flex justify-center py-16 text-gray-400">載入中…</div>
      ) : contacts.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-16 text-center">
          <p className="text-gray-500">
            {enrichingStatus === 'running'
              ? 'Clay 正在富化名單，完成後聯絡人將自動顯示'
              : '尚無符合條件的聯絡人'}
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                {['姓名 / 職稱', '公司', '地區', 'LinkedIn 開場白', '狀態', '操作'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {contacts.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{c.full_name || '—'}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{c.job_title || '—'}</div>
                    {c.is_hot_lead && <span className="text-xs text-orange-600 font-medium">🔥 熱線索</span>}
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-700">{c.company_name || '—'}</div>
                    <div className="text-xs text-gray-400">{c.company_industry || ''}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {[c.company_country, c.company_size].filter(Boolean).join(' · ') || '—'}
                  </td>
                  <td className="px-4 py-3 max-w-xs">
                    {c.linkedin_opener ? (
                      <div className="text-xs text-gray-600 line-clamp-2 bg-gray-50 rounded p-2 border border-gray-100">
                        {c.linkedin_opener}
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400 italic">AI 開場白生成中…</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${STATUS_BADGE[c.status] ?? 'bg-gray-100 text-gray-600'}`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {c.status === 'enriched' || c.status === 'pending' ? (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleApprove(c.id)}
                          className="px-2.5 py-1 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700"
                        >
                          批准
                        </button>
                        <button
                          onClick={() => handleExclude(c.id)}
                          className="px-2.5 py-1 border border-red-200 text-red-600 text-xs rounded-lg hover:bg-red-50"
                        >
                          排除
                        </button>
                      </div>
                    ) : c.linkedin_url ? (
                      <a
                        href={c.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 text-xs hover:underline"
                      >
                        LinkedIn ↗
                      </a>
                    ) : null}
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
