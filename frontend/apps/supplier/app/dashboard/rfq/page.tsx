'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { RFQInboxList } from '@/components/rfq/RFQInboxList'

interface RFQData {
  id: number
  product_name: string
  buyer_company?: string
  lead_grade: 'A' | 'B' | 'C'
  lead_score: number
  description: string
  quantity: string
  created_at: string
  status: 'new' | 'viewed' | 'replied' | 'archived'
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'

function mapApiRFQ(rfq: Record<string, unknown>): RFQData {
  return {
    id: rfq.id as number,
    product_name: rfq.title as string,
    buyer_company: undefined,
    lead_grade: ((rfq.lead_grade as string) || 'C') as 'A' | 'B' | 'C',
    lead_score: (rfq.lead_score as number) || 0,
    description: (rfq.description as string) || '',
    quantity: rfq.quantity
      ? `${rfq.quantity} ${rfq.unit || 'pcs'}`
      : 'N/A',
    created_at: rfq.created_at as string,
    status: ((rfq.status as string) || 'new') as 'new' | 'viewed' | 'replied' | 'archived',
  }
}

export default function RFQInboxPage() {
  const t = useTranslations('rfq')
  const [rfqs, setRfqs] = useState<RFQData[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    total: 0,
    new: 0,
    gradeA: 0,
  })

  useEffect(() => {
    const fetchRFQs = async () => {
      setLoading(true)
      try {
        const token = localStorage.getItem('access_token')
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        }

        const listResponse = await fetch(`${API_BASE_URL}/rfqs`, { headers })
        if (!listResponse.ok) {
          throw new Error(`Failed to fetch RFQs: ${listResponse.statusText}`)
        }
        const listData = await listResponse.json()

        // Fetch full RFQ details in parallel to get description and quantity
        const detailPromises = listData.map((r: { id: number }) =>
          fetch(`${API_BASE_URL}/rfqs/${r.id}`, { headers }).then(res => res.json())
        )
        const details = await Promise.all(detailPromises)

        const rfqData = details.map(mapApiRFQ)
        setRfqs(rfqData)
        setStats({
          total: rfqData.length,
          new: rfqData.filter(r => r.status === 'new').length,
          gradeA: rfqData.filter(r => r.lead_grade === 'A').length,
        })
      } catch (error) {
        console.error('Failed to fetch RFQs:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchRFQs()
  }, [])

  const handleLoadMore = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      }

      const skip = rfqs.length
      const response = await fetch(
        `${API_BASE_URL}/rfqs?skip=${skip}&limit=20`,
        { headers }
      )

      if (!response.ok) {
        throw new Error(`Failed to load more RFQs: ${response.statusText}`)
      }

      const listData = await response.json()
      if (listData.length === 0) return

      const detailPromises = listData.map((r: { id: number }) =>
        fetch(`${API_BASE_URL}/rfqs/${r.id}`, { headers }).then(res => res.json())
      )
      const details = await Promise.all(detailPromises)
      const newRFQData = details.map(mapApiRFQ)
      setRfqs(prev => [...prev, ...newRFQData])
    } catch (error) {
      console.error('Failed to load more RFQs:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex-1">
      {/* Page Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-h2 font-bold text-gray-900">RFQ Inbox</h1>
            <p className="mt-1 text-sm text-gray-600">
              Manage incoming requests for quotation from buyers worldwide
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">Total RFQs</p>
                <p className="text-h3 font-bold text-gray-900 mt-1">{stats.total}</p>
              </div>
              <div className="text-4xl">📨</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">New RFQs</p>
                <p className="text-h3 font-bold text-blue-600 mt-1">{stats.new}</p>
              </div>
              <div className="text-4xl">✨</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">Grade A Leads</p>
                <p className="text-h3 font-bold text-green-600 mt-1">{stats.gradeA}</p>
              </div>
              <div className="text-4xl">🎯</div>
            </div>
          </div>
        </div>

        {/* RFQ List with Filters */}
        <RFQInboxList
          initialRFQs={rfqs}
          loading={loading}
          onLoadMore={handleLoadMore}
        />
      </div>
    </main>
  )
}
