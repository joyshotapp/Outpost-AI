'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  AreaChart,
  Area,
  XAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { ApiError, apiFetch } from '@/lib/api'
import { SkeletonCard, SkeletonChart } from '@/components/ui/Skeleton'

interface KpiData {
  rfq: { total: number; by_grade: Record<string, number> }
  visitors: { total: number; high_intent: number }
  outbound: { contacts: number; replies: number; reply_rate_pct: number }
  content: { items: number; total_reach: number }
  conversion_rate_pct: number
}
interface TrendPoint { date: string; count: number }

export default function DashboardPage() {
  const router = useRouter()
  const [kpi, setKpi] = useState<KpiData | null>(null)
  const [trend, setTrend] = useState<TrendPoint[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    ;(async () => {
      try {
        const [kpiRes, trendRes] = await Promise.all([
          apiFetch<KpiData>('/analytics/kpi?window_days=30'),
          apiFetch<{ series: TrendPoint[] }>('/analytics/rfq-trend?window_days=30'),
        ])
        setKpi(kpiRes)
        setTrend(trendRes.series)
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('access_token')
          localStorage.removeItem('token')
          router.replace('/login')
          return
        }
        // silently fall back to null — UI handles empty state
      } finally {
        setLoading(false)
      }
    })()
  }, [router])

  const stats = kpi
    ? [
        {
          label: 'RFQ 詢價單',
          value: kpi.rfq.total,
          sub: `等級 A: ${kpi.rfq.by_grade?.A ?? 0} 筆`,
          href: '/dashboard/inquiries',
          color: 'text-primary-700',
          bg: 'bg-primary-50',
          icon: (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2.5 3A1.5 1.5 0 001 4.5v.793c.026.009.051.02.076.032a.75.75 0 00.658.482 60.456 60.456 0 014.064-.053.75.75 0 00.658-.482c.025-.012.05-.023.076-.032V4.5A1.5 1.5 0 002.5 3zM1 7.75V19.5A1.5 1.5 0 002.5 21h15A1.5 1.5 0 0019 19.5V7.75c-.345.104-.681.227-1 .367V19.5H2.5V7.75c-.319-.14-.655-.263-1-.367z" />
            </svg>
          ),
        },
        {
          label: '訪客總數',
          value: kpi.visitors.total,
          sub: `高意圖 ${kpi.visitors.high_intent} 位`,
          href: '/dashboard/analytics',
          color: 'text-indigo-700',
          bg: 'bg-indigo-50',
          icon: (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
            </svg>
          ),
        },
        {
          label: 'Outbound 回覆率',
          value: `${kpi.outbound.reply_rate_pct}%`,
          sub: `${kpi.outbound.replies}/${kpi.outbound.contacts} 筆`,
          href: '/dashboard/analytics',
          color: 'text-emerald-700',
          bg: 'bg-emerald-50',
          icon: (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
              <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
            </svg>
          ),
        },
        {
          label: '內容觸及',
          value: kpi.content.total_reach.toLocaleString(),
          sub: `${kpi.content.items} 篇內容`,
          href: '/dashboard/analytics',
          color: 'text-amber-700',
          bg: 'bg-amber-50',
          icon: (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
            </svg>
          ),
        },
      ]
    : []

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-h1 font-bold text-gray-900">Dashboard</h1>
        <p className="text-body-lg text-gray-600 mt-2">
          Welcome back! Here's what's happening with your business today.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-white rounded-xl shadow p-6">
                <SkeletonCard />
              </div>
            ))
          : stats.map((stat) => (
              <Link
                key={stat.label}
                href={stat.href ?? '#'}
                className="bg-white rounded-xl shadow hover:shadow-lg transition-shadow p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`${stat.color} ${stat.bg} p-3 rounded-lg`}>
                    {stat.icon}
                  </div>
                  {stat.sub && (
                    <span className="text-xs font-medium px-2 py-1 rounded-full bg-gray-50 text-gray-500">
                      {stat.sub}
                    </span>
                  )}
                </div>
                <p className="text-body-sm text-gray-500 mb-1">{stat.label}</p>
                <p className="text-h2 font-bold text-gray-900">{stat.value}</p>
              </Link>
            ))}
      </div>

      {/* RFQ Trend chart + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Mini RFQ trend */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-h3 font-semibold text-gray-900">RFQ 趨勢（近 30 天）</h2>
            <Link
              href="/dashboard/analytics"
              className="text-primary-600 text-body-sm font-medium hover:text-primary-700"
            >
              查看詳細 →
            </Link>
          </div>
          {loading ? (
            <SkeletonChart height={200} />
          ) : trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={trend} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                <defs>
                  <linearGradient id="rfqGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2B7FA3" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#2B7FA3" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: '#9ca3af' }}
                  tickFormatter={(d: string) => d.slice(5)}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
                  labelFormatter={(l: string) => `日期: ${l}`}
                  formatter={(v: number) => [v, 'RFQ']}
                />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="#2B7FA3"
                  strokeWidth={2}
                  fill="url(#rfqGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
              尚無趨勢數據
            </div>
          )}
        </div>

        {/* Quick Links */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-h3 font-semibold text-gray-900 mb-6">
            Quick Actions
          </h2>
          <div className="space-y-3">
            <Link
              href="/dashboard/profile"
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
            >
              <div className="text-primary-600 group-hover:text-primary-700">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <p className="text-body-sm font-medium text-gray-900">Edit Profile</p>
                <p className="text-body-xs text-gray-500">Update company info</p>
              </div>
            </Link>

            <Link
              href="/dashboard/videos"
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
            >
              <div className="text-primary-600 group-hover:text-primary-700">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm4 2v4h8V8H6z" />
                </svg>
              </div>
              <div>
                <p className="text-body-sm font-medium text-gray-900">Upload Video</p>
                <p className="text-body-xs text-gray-500">Add product videos</p>
              </div>
            </Link>

            <Link
              href="/dashboard/inquiries"
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
            >
              <div className="text-primary-600 group-hover:text-primary-700">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2.5 3A1.5 1.5 0 001 4.5v.793c.026.009.051.02.076.032a.75.75 0 00.658.482 60.456 60.456 0 014.064-.053.75.75 0 00.658-.482c.025-.012.05-.023.076-.032V4.5A1.5 1.5 0 002.5 3zM1 7.75V19.5A1.5 1.5 0 002.5 21h15A1.5 1.5 0 0019 19.5V7.75c-.345.104-.681.227-1 .367V19.5H2.5V7.75c-.319-.14-.655-.263-1-.367z" />
                </svg>
              </div>
              <div>
                <p className="text-body-sm font-medium text-gray-900">View Inquiries</p>
                <p className="text-body-xs text-gray-500">Check buyer requests</p>
              </div>
            </Link>

            <Link
              href="/dashboard/analytics"
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
            >
              <div className="text-primary-600 group-hover:text-primary-700">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                </svg>
              </div>
              <div>
                <p className="text-body-sm font-medium text-gray-900">KPI 儀表板</p>
                <p className="text-body-xs text-gray-500">View analytics</p>
              </div>
            </Link>
          </div>
        </div>
      </div>

      {/* Announcement Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <svg className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zm-11-1a1 1 0 11-2 0 1 1 0 012 0zM8 8a1 1 0 000 2h6a1 1 0 100-2H8zm0 3a1 1 0 000 2h3a1 1 0 100-2H8z" clipRule="evenodd" />
          </svg>
          <div className="flex-1">
            <h3 className="text-body-lg font-semibold text-blue-900">最新功能</h3>
            <p className="text-body-sm text-blue-800 mt-1">
              我們已推出完整的業績分析功能！查看詢價趨勢、訪客分析、外發成效等詳細數據。
            </p>
            <Link
              href="/dashboard/analytics"
              className="inline-block mt-3 text-body-sm font-medium text-blue-600 hover:text-blue-700"
            >
              前往 KPI 儀表板 →
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
