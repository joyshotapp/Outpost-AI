'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

// ── Types ─────────────────────────────────────────────────────────────────────

interface RFQSummary {
  id: number
  title: string
  status: string
  supplier_name?: string
  created_at?: string
  lead_grade?: string
}

interface DashboardStats {
  total_rfqs: number
  active_rfqs: number
  replies_received: number
  saved_suppliers: number
  unread_messages: number
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-600',
  submitted: 'bg-blue-50 text-blue-700',
  quoted: 'bg-amber-50 text-amber-700',
  accepted: 'bg-green-50 text-green-700',
  rejected: 'bg-red-50 text-red-600',
  closed: 'bg-gray-100 text-gray-500',
}

const GRADE_COLORS: Record<string, string> = {
  A: 'bg-green-100 text-green-800',
  B: 'bg-blue-100 text-blue-800',
  C: 'bg-yellow-100 text-yellow-800',
  D: 'bg-red-100 text-red-700',
}

// ── Demo data ──────────────────────────────────────────────────────────────────

const DEMO_STATS: DashboardStats = {
  total_rfqs: 8,
  active_rfqs: 3,
  replies_received: 12,
  saved_suppliers: 5,
  unread_messages: 2,
}

const DEMO_RFQS: RFQSummary[] = [
  { id: 1, title: 'CNC Machined Aluminium Housing × 500', status: 'quoted', supplier_name: 'Precision Parts Co', created_at: '2025-01-15', lead_grade: 'A' },
  { id: 2, title: 'Injection Moulded ABS Cover Panels', status: 'submitted', supplier_name: 'AutoPlast Taiwan', created_at: '2025-01-20', lead_grade: 'B' },
  { id: 3, title: 'M6 Stainless Steel Fasteners × 10,000', status: 'active', supplier_name: undefined, created_at: '2025-01-22' },
  { id: 4, title: 'PCB Assembly — 4-Layer SMD', status: 'accepted', supplier_name: 'TechForge GmbH', created_at: '2025-01-10', lead_grade: 'A' },
  { id: 5, title: 'Silicone Gaskets — FDA Grade', status: 'draft', created_at: '2025-01-25' },
]

// ── Stat Card ─────────────────────────────────────────────────────────────────

function StatCard({ label, value, color, href }: { label: string; value: number; color: string; href?: string }) {
  const inner = (
    <div className={`bg-white rounded-xl border p-5 hover:shadow-md transition-shadow ${href ? 'cursor-pointer' : ''}`}>
      <div className={`text-3xl font-extrabold ${color}`}>{value}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </div>
  )
  return href ? <Link href={href}>{inner}</Link> : inner
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [stats] = useState<DashboardStats>(DEMO_STATS)
  const [rfqs] = useState<RFQSummary[]>(DEMO_RFQS)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Nav */}
      <header className="bg-white border-b sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-5">
            <Link href="/" className="font-bold text-primary-700 text-lg">Factory Insider</Link>
            <nav className="flex items-center gap-4 text-sm text-gray-600">
              <Link href="/suppliers" className="hover:text-primary-700">Find Suppliers</Link>
              <Link href="/rfq/new" className="hover:text-primary-700">Post RFQ</Link>
              <Link href="/dashboard" className="text-primary-700 font-medium border-b-2 border-primary-700 pb-0.5">Dashboard</Link>
              <Link href="/dashboard/messages" className="hover:text-primary-700 flex items-center gap-1">
                Messages
                {stats.unread_messages > 0 && (
                  <span className="w-4 h-4 text-xs font-bold bg-red-500 text-white rounded-full flex items-center justify-center">{stats.unread_messages}</span>
                )}
              </Link>
            </nav>
          </div>
          <div className="text-sm text-gray-500">Demo Buyer Account</div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Buyer Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">Your sourcing activity at a glance</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <StatCard label="Total RFQs" value={stats.total_rfqs} color="text-primary-700" href="/rfq" />
          <StatCard label="Active RFQs" value={stats.active_rfqs} color="text-blue-600" href="/rfq" />
          <StatCard label="Replies Received" value={stats.replies_received} color="text-green-600" />
          <StatCard label="Saved Suppliers" value={stats.saved_suppliers} color="text-amber-600" href="/dashboard/saved" />
          <StatCard label="Unread Messages" value={stats.unread_messages} color="text-red-600" href="/dashboard/messages" />
        </div>

        {/* RFQ Table */}
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h2 className="font-semibold text-gray-900">My RFQs</h2>
            <Link href="/rfq/new" className="px-4 py-1.5 bg-primary-700 text-white rounded-lg text-sm font-medium hover:bg-primary-600">
              + New RFQ
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 uppercase border-b">
                  <th className="text-left px-6 py-3 font-medium">Title</th>
                  <th className="text-left px-6 py-3 font-medium">Status</th>
                  <th className="text-left px-6 py-3 font-medium">Supplier</th>
                  <th className="text-left px-6 py-3 font-medium">Grade</th>
                  <th className="text-left px-6 py-3 font-medium">Date</th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {rfqs.map(rfq => (
                  <tr key={rfq.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-3 font-medium text-gray-800 max-w-xs truncate">{rfq.title}</td>
                    <td className="px-6 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[rfq.status] || 'bg-gray-100 text-gray-600'}`}>
                        {rfq.status}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-gray-600">{rfq.supplier_name || '—'}</td>
                    <td className="px-6 py-3">
                      {rfq.lead_grade && (
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${GRADE_COLORS[rfq.lead_grade] || ''}`}>
                          {rfq.lead_grade}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-3 text-gray-500">{rfq.created_at}</td>
                    <td className="px-6 py-3">
                      <Link href={`/rfq/${rfq.id}`} className="text-primary-600 hover:text-primary-700 font-medium text-xs">View →</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
