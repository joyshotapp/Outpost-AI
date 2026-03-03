'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { SkeletonChart } from '@/components/ui/Skeleton'
import { ApiError, apiFetch, apiDownload } from '@/lib/api'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface KpiData {
  window_days: number
  rfq: { total: number; by_grade: Record<string, number> }
  visitors: { total: number; high_intent: number }
  outbound: { contacts: number; replies: number; reply_rate_pct: number }
  content: { items: number; total_reach: number }
  conversion_rate_pct: number
}

interface TrendPoint { date: string; count: number }
interface VisitorPoint { date: string; total: number; high_intent: number }
interface GradeBucket { grade: string; count: number; pct: number }
interface PlatformRow { platform: string; items: number; reach: number; engagement: number }
interface OutboundData { contacts: number; emails_sent: number; open_rate_pct: number; click_rate_pct: number; reply_rate_pct: number; bounce_rate_pct: number }

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function KpiCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">{label}</p>
      <p className={`text-3xl font-bold ${color ?? 'text-gray-800'}`}>{value}</p>
      {sub && <p className="mt-1 text-sm text-gray-500">{sub}</p>}
    </div>
  )
}

const GRADE_COLORS: Record<string, string> = {
  A: '#22c55e',
  B: '#f59e0b',
  C: '#ef4444',
  unscored: '#9ca3af',
}

// ─────────────────────────────────────────────────────────────────────────────
// API alias — `get` calls delegated to lib/api.ts
// ─────────────────────────────────────────────────────────────────────────────

const get = apiFetch

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const router = useRouter()
  const [window_days, setWindowDays] = useState(30)
  const [kpi, setKpi] = useState<KpiData | null>(null)
  const [rfqTrend, setRfqTrend] = useState<TrendPoint[]>([])
  const [visitorTrend, setVisitorTrend] = useState<VisitorPoint[]>([])
  const [gradeDist, setGradeDist] = useState<GradeBucket[]>([])
  const [outbound, setOutbound] = useState<OutboundData | null>(null)
  const [contentPlatforms, setContentPlatforms] = useState<PlatformRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async (days: number) => {
    setLoading(true)
    setError(null)
    try {
      const [_kpi, _rfqTrend, _visitorTrend, _gradeDist, _outbound, _content] = await Promise.all([
        get<KpiData>(`/analytics/kpi?window_days=${days}`),
        get<{ series: TrendPoint[] }>(`/analytics/rfq-trend?window_days=${days}`),
        get<{ series: VisitorPoint[] }>(`/analytics/visitor-trend?window_days=${Math.min(days, 90)}`),
        get<{ distribution: GradeBucket[] }>(`/analytics/lead-score-distribution?window_days=${days}`),
        get<{ email: OutboundData }>(`/analytics/outbound-performance?window_days=${days}`),
        get<{ by_platform: PlatformRow[] }>(`/analytics/content-reach?window_days=${days}`),
      ])
      setKpi(_kpi)
      setRfqTrend(_rfqTrend.series)
      setVisitorTrend(_visitorTrend.series)
      setGradeDist(_gradeDist.distribution)
      setOutbound(_outbound.email)
      setContentPlatforms(_content.by_platform)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('access_token')
        localStorage.removeItem('token')
        router.replace('/login')
        return
      }

      setError('Failed to load analytics data. Using demo data.')
      // Stub fallback so charts still render
      setKpi({
        window_days: days,
        rfq: { total: 24, by_grade: { A: 6, B: 10, C: 8 } },
        visitors: { total: 342, high_intent: 58 },
        outbound: { contacts: 180, replies: 27, reply_rate_pct: 15.0 },
        content: { items: 12, total_reach: 8400 },
        conversion_rate_pct: 7.0,
      })
      setRfqTrend(Array.from({ length: days }, (_, i) => ({
        date: new Date(Date.now() - (days - i) * 86400000).toISOString().slice(0, 10),
        count: Math.floor(Math.random() * 4),
      })))
      setVisitorTrend(Array.from({ length: Math.min(days, 30) }, (_, i) => ({
        date: new Date(Date.now() - (Math.min(days, 30) - i) * 86400000).toISOString().slice(0, 10),
        total: Math.floor(Math.random() * 20) + 5,
        high_intent: Math.floor(Math.random() * 5),
      })))
      setGradeDist([
        { grade: 'A', count: 6, pct: 25 },
        { grade: 'B', count: 10, pct: 41.7 },
        { grade: 'C', count: 8, pct: 33.3 },
      ])
      setOutbound({ contacts: 180, emails_sent: 540, open_rate_pct: 28.5, click_rate_pct: 7.2, reply_rate_pct: 15.0, bounce_rate_pct: 2.1 })
      setContentPlatforms([
        { platform: 'linkedin', items: 8, reach: 4200, engagement: 315 },
        { platform: 'email', items: 4, reach: 2100, engagement: 189 },
        { platform: 'website', items: 3, reach: 2100, engagement: 42 },
      ])
    } finally {
      setLoading(false)
    }
  }, [router])

  useEffect(() => { load(window_days) }, [load, window_days])

  const handleExport = async (type: 'leads' | 'rfqs' | 'analytics', fmt: 'csv' | 'json') => {
    try {
      await apiDownload(`/analytics/export/${type}?fmt=${fmt}&window_days=${window_days}`, `${type}.${fmt}`)
    } catch (err) {
      const message = err instanceof Error ? err.message : '匯出失敗，請稍後再試。'
      setError(message)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📊 KPI 儀表板</h1>
          <p className="text-sm text-gray-500 mt-1">供應商業務指標總覽</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {/* Window selector */}
          <select
            value={window_days}
            onChange={e => setWindowDays(Number(e.target.value))}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white shadow-sm focus:ring-2 focus:ring-blue-500 outline-none"
          >
            {[7, 30, 90, 180, 365].map(d => (
              <option key={d} value={d}>最近 {d} 天</option>
            ))}
          </select>
          {/* Export buttons */}
          <div className="relative group">
            <button className="text-sm bg-white border border-gray-200 rounded-lg px-3 py-2 shadow-sm hover:bg-gray-50 flex items-center gap-1">
              ⬇ 匯出
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
            <div className="absolute right-0 mt-1 w-44 bg-white border border-gray-200 rounded-lg shadow-lg z-10 hidden group-hover:block">
              {(['leads', 'rfqs', 'analytics'] as const).map(type =>
                (['csv', 'json'] as const).map(fmt => (
                  <button
                    key={`${type}-${fmt}`}
                    onClick={() => handleExport(type, fmt)}
                    className="block w-full text-left px-4 py-2 text-sm hover:bg-gray-50 capitalize"
                  >
                    {type} ({fmt.toUpperCase()})
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="text-sm text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2">
          ⚠ {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="lg:col-span-2 bg-white rounded-xl border border-gray-100 p-5"><SkeletonChart height={220} /></div>
          <div className="bg-white rounded-xl border border-gray-100 p-5"><SkeletonChart height={220} /></div>
          <div className="bg-white rounded-xl border border-gray-100 p-5"><SkeletonChart height={220} /></div>
        </div>
      ) : kpi ? (
        <>
          {/* ── KPI cards ──────────────────────────────────────────────── */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            <KpiCard label="RFQ 總數" value={kpi.rfq.total} color="text-blue-600" />
            <KpiCard label="訪客總數" value={kpi.visitors.total} sub={`高意圖: ${kpi.visitors.high_intent}`} />
            <KpiCard label="Outbound 回覆率" value={`${kpi.outbound.reply_rate_pct}%`} sub={`${kpi.outbound.replies}/${kpi.outbound.contacts}`} color="text-green-600" />
            <KpiCard label="內容觸及" value={kpi.content.total_reach.toLocaleString()} sub={`${kpi.content.items} 篇內容`} />
            <KpiCard label="轉換率" value={`${kpi.conversion_rate_pct}%`} sub="訪客→RFQ" color={kpi.conversion_rate_pct >= 5 ? 'text-green-600' : 'text-amber-600'} />
          </div>

          {/* ── RFQ Trend ─────────────────────────────────────────────── */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">RFQ 提交趨勢</h2>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={rfqTrend}>
                <defs>
                  <linearGradient id="rfqGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => d.slice(5)} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Area type="monotone" dataKey="count" stroke="#3b82f6" fill="url(#rfqGrad)" name="RFQ" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* ── Visitor Trend + Lead Grade ────────────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Visitor Trend */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">訪客趨勢</h2>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={visitorTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => d.slice(5)} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="total" stroke="#6366f1" fill="#6366f120" name="所有訪客" />
                  <Area type="monotone" dataKey="high_intent" stroke="#ec4899" fill="#ec489920" name="高意圖" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Lead Grade Distribution */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Lead 等級分佈</h2>
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <ResponsiveContainer width="100%" height={180}>
                    <PieChart>
                      <Pie
                        data={gradeDist}
                        dataKey="count"
                        nameKey="grade"
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={85}
                        label={({ grade, pct }) => `${grade} ${pct}%`}
                        labelLine={false}
                      >
                        {gradeDist.map((entry) => (
                          <Cell key={entry.grade} fill={GRADE_COLORS[entry.grade] ?? '#9ca3af'} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v: number) => [`${v} 筆`, '數量']} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-2 text-sm min-w-[100px]">
                  {gradeDist.map(b => (
                    <div key={b.grade} className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: GRADE_COLORS[b.grade] ?? '#9ca3af' }} />
                      <span className="font-medium">{b.grade}</span>
                      <span className="text-gray-500">{b.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* ── Outbound Performance ─────────────────────────────────── */}
          {outbound && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Outbound 成效</h2>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {[
                  { label: '聯絡人', value: outbound.contacts },
                  { label: '已送出', value: outbound.emails_sent },
                  { label: '開信率', value: `${outbound.open_rate_pct}%` },
                  { label: '點擊率', value: `${outbound.click_rate_pct}%` },
                  { label: '回覆率', value: `${outbound.reply_rate_pct}%` },
                ].map(item => (
                  <div key={item.label} className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-lg font-bold text-gray-800">{item.value}</p>
                    <p className="text-xs text-gray-500 mt-1">{item.label}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Content Reach by Platform ─────────────────────────────── */}
          {contentPlatforms.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">內容觸及 (by Platform)</h2>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={contentPlatforms} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis dataKey="platform" type="category" tick={{ fontSize: 11 }} width={70} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="reach" fill="#3b82f6" name="觸及人數" radius={[0, 4, 4, 0]} />
                  <Bar dataKey="engagement" fill="#22c55e" name="互動數" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      ) : null}
    </div>
  )
}
