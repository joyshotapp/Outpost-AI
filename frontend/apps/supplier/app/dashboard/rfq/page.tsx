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

// Mock data - in production this would come from the API
const MOCK_RFQS: RFQData[] = [
  {
    id: 1,
    product_name: 'CNC Machined Aluminum Parts',
    buyer_company: 'TechCorp Manufacturing',
    lead_grade: 'A',
    lead_score: 85,
    description: 'High precision aluminum components with tight tolerances, ISO 9001 required',
    quantity: '1000 pieces',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    status: 'new',
  },
  {
    id: 2,
    product_name: 'Stainless Steel Fasteners',
    buyer_company: 'Auto Parts Inc',
    lead_grade: 'B',
    lead_score: 68,
    description: 'M8 and M10 stainless steel bolts with regular tolerances',
    quantity: '5000 pieces',
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    status: 'viewed',
  },
  {
    id: 3,
    product_name: 'Plastic Injection Molded Parts',
    buyer_company: 'Consumer Goods Ltd',
    lead_grade: 'C',
    lead_score: 45,
    description: 'Generic plastic components, standard quality acceptable',
    quantity: '10000 pieces',
    created_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
    status: 'replied',
  },
  {
    id: 4,
    product_name: 'Medical Device Components',
    buyer_company: 'MedTech Solutions',
    lead_grade: 'A',
    lead_score: 92,
    description: 'FDA approved medical-grade titanium implants with biocompatible coating',
    quantity: '500 pieces',
    created_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    status: 'new',
  },
  {
    id: 5,
    product_name: 'Electronics Circuit Boards',
    buyer_company: 'TechGear Electronics',
    lead_grade: 'B',
    lead_score: 72,
    description: '4-layer PCB boards with RoHS compliance',
    quantity: '2000 pieces',
    created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    status: 'new',
  },
]

export default function RFQInboxPage() {
  const t = useTranslations('rfq')
  const [rfqs, setRfqs] = useState<RFQData[]>(MOCK_RFQS)
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({
    total: MOCK_RFQS.length,
    new: MOCK_RFQS.filter(r => r.status === 'new').length,
    gradeA: MOCK_RFQS.filter(r => r.lead_grade === 'A').length,
  })

  // In production, fetch RFQs from API
  useEffect(() => {
    // Mock API call
    // const fetchRFQs = async () => {
    //   try {
    //     const response = await fetch('/api/v1/rfqs', {
    //       headers: {
    //         'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    //       }
    //     })
    //     const data = await response.json()
    //     setRfqs(data)
    //   } catch (error) {
    //     console.error('Failed to fetch RFQs:', error)
    //   }
    // }
    // fetchRFQs()
  }, [])

  const handleLoadMore = async () => {
    setLoading(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    setLoading(false)
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
