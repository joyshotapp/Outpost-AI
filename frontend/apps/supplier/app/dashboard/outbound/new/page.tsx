'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'

// ── ICP option data ───────────────────────────────────────────────────────────

const INDUSTRIES = [
  'Automotive', 'Aerospace & Defense', 'Electronics Manufacturing',
  'Medical Devices', 'Industrial Machinery', 'Consumer Goods',
  'Chemical', 'Food & Beverage', 'Textile & Apparel',
  'Plastics & Rubber', 'Metal Fabrication', 'Packaging',
]

const COUNTRIES = [
  'Germany', 'United States', 'United Kingdom', 'France', 'Japan',
  'South Korea', 'Netherlands', 'Sweden', 'Italy', 'Switzerland',
  'Canada', 'Australia', 'Singapore', 'Taiwan', 'Denmark',
]

const JOB_TITLES = [
  'Procurement Manager', 'Sourcing Manager', 'Supply Chain Manager',
  'Operations Manager', 'Manufacturing Director', 'VP Operations',
  'Head of Procurement', 'Purchasing Director', 'CPO',
  'Plant Manager', 'Production Manager', 'Quality Manager',
]

const COMPANY_SIZES = [
  '1-10', '11-50', '51-200', '201-500', '501-1000', '1000+',
]

const SENIORITY_LEVELS = [
  'Entry', 'Manager', 'Director', 'VP', 'C-Suite',
]

// ── Component ─────────────────────────────────────────────────────────────────

interface IcpCriteria {
  industries: string[]
  countries: string[]
  job_titles: string[]
  company_sizes: string[]
  seniority_levels: string[]
  limit: number
}

function FilterChip({
  label,
  selected,
  onToggle,
}: {
  label: string
  selected: boolean
  onToggle: () => void
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-all ${
        selected
          ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
          : 'bg-white text-gray-700 border-gray-200 hover:border-blue-300 hover:text-blue-600'
      }`}
    >
      {label}
    </button>
  )
}

function FilterSection({
  title,
  options,
  selected,
  onToggle,
}: {
  title: string
  options: string[]
  selected: string[]
  onToggle: (v: string) => void
}) {
  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-gray-800">{title}</h3>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <FilterChip
            key={opt}
            label={opt}
            selected={selected.includes(opt)}
            onToggle={() => onToggle(opt)}
          />
        ))}
      </div>
    </div>
  )
}

function toggle(arr: string[], val: string): string[] {
  return arr.includes(val) ? arr.filter((v) => v !== val) : [...arr, val]
}

export default function NewCampaignPage() {
  const router = useRouter()
  const [campaignName, setCampaignName] = useState('')
  const [icp, setIcp] = useState<IcpCriteria>({
    industries: [],
    countries: [],
    job_titles: [],
    company_sizes: [],
    seniority_levels: [],
    limit: 500,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const totalSelected =
    icp.industries.length +
    icp.countries.length +
    icp.job_titles.length +
    icp.company_sizes.length +
    icp.seniority_levels.length

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!campaignName.trim()) { setError('請輸入活動名稱'); return }
    if (totalSelected === 0) { setError('請至少選擇一個 ICP 條件'); return }
    setError(null)
    setLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch('/api/v1/outbound/campaigns', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          campaign_name: campaignName,
          campaign_type: 'linkedin',
          icp_criteria: icp,
        }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '建立失敗')
      }

      const campaign = await res.json()
      router.push(`/dashboard/outbound/${campaign.id}/contacts`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '建立失敗，請稍後再試')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <nav className="text-sm text-gray-500 mb-3">
          <button onClick={() => router.back()} className="hover:text-gray-700">
            ← 返回活動列表
          </button>
        </nav>
        <h1 className="text-2xl font-bold text-gray-900">建立 Outbound 活動</h1>
        <p className="text-gray-500 mt-1">
          設定理想客戶輪廓 (ICP)，Clay 會自動搜尋符合的聯絡人並進行瀑布式富化
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Campaign name */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h2 className="font-semibold text-gray-900 text-lg">基本資訊</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              活動名稱 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
              placeholder="例：Q1 2026 歐洲採購負責人外展"
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* ICP Filters */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 text-lg">ICP 條件設定</h2>
            {totalSelected > 0 && (
              <span className="text-sm text-blue-600 font-medium">
                已選 {totalSelected} 個條件
              </span>
            )}
          </div>

          <FilterSection
            title="🏭 產業"
            options={INDUSTRIES}
            selected={icp.industries}
            onToggle={(v) => setIcp((p) => ({ ...p, industries: toggle(p.industries, v) }))}
          />
          <FilterSection
            title="🌍 目標國家"
            options={COUNTRIES}
            selected={icp.countries}
            onToggle={(v) => setIcp((p) => ({ ...p, countries: toggle(p.countries, v) }))}
          />
          <FilterSection
            title="💼 職稱"
            options={JOB_TITLES}
            selected={icp.job_titles}
            onToggle={(v) => setIcp((p) => ({ ...p, job_titles: toggle(p.job_titles, v) }))}
          />
          <FilterSection
            title="🏢 公司規模（人數）"
            options={COMPANY_SIZES}
            selected={icp.company_sizes}
            onToggle={(v) => setIcp((p) => ({ ...p, company_sizes: toggle(p.company_sizes, v) }))}
          />
          <FilterSection
            title="⭐ 職級"
            options={SENIORITY_LEVELS}
            selected={icp.seniority_levels}
            onToggle={(v) => setIcp((p) => ({ ...p, seniority_levels: toggle(p.seniority_levels, v) }))}
          />

          {/* Contact limit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              最多搜尋聯絡人數
            </label>
            <input
              type="number"
              min={50}
              max={2000}
              value={icp.limit}
              onChange={(e) => setIcp((p) => ({ ...p, limit: Number(e.target.value) }))}
              className="w-32 px-4 py-2 border border-gray-200 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-400 mt-1">建議 500–1000 筆，每筆需 Clay 額度</p>
          </div>
        </div>

        {/* Info box */}
        <div className="flex gap-3 p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <svg className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="text-sm text-blue-700">
            <p className="font-medium mb-1">建立後的流程</p>
            <ol className="list-decimal list-inside space-y-1 text-blue-600">
              <li>Clay 自動搜尋符合 ICP 的聯絡人（約 3–10 分鐘）</li>
              <li>在名單管理頁審核並批准/排除聯絡人</li>
              <li>Claude AI 為每位聯絡人生成個人化開場白</li>
              <li>一鍵匯入 HeyReach，啟動 Day 1–25 LinkedIn 序列</li>
            </ol>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Submit */}
        <div className="flex items-center gap-4">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '建立中…Clay 正在搜尋名單' : '建立活動 → 開始 Clay 富化'}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="px-6 py-3 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
          >
            取消
          </button>
        </div>
      </form>
    </div>
  )
}
