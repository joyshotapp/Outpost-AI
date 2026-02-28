'use client'

import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'

interface RFQListItemProps {
  id: number
  product_name: string
  buyer_company?: string
  lead_grade: 'A' | 'B' | 'C'
  lead_score: number
  description: string
  quantity: string
  created_at: string
  status?: 'new' | 'viewed' | 'replied' | 'archived'
}

const GRADE_COLORS = {
  A: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300' },
  B: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300' },
  C: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300' },
}

const GRADE_LABELS = {
  A: 'High Quality',
  B: 'Medium Quality',
  C: 'Low Quality',
}

export function RFQListItem({
  id,
  product_name,
  buyer_company,
  lead_grade,
  lead_score,
  description,
  quantity,
  created_at,
  status = 'new',
}: RFQListItemProps) {
  const colors = GRADE_COLORS[lead_grade]
  const timeAgo = formatDistanceToNow(new Date(created_at), { addSuffix: true })

  return (
    <Link href={`/dashboard/rfq/${id}`}>
      <div className={`border border-gray-200 rounded-lg p-6 hover:shadow-md hover:border-primary-300 transition-all cursor-pointer ${
        status === 'new' ? 'bg-blue-50' : 'bg-white'
      }`}>
        {/* Header Row */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 hover:text-primary-700">
              {product_name}
            </h3>
            {buyer_company && (
              <p className="text-sm text-gray-600 mt-1">
                from <span className="font-medium">{buyer_company}</span>
              </p>
            )}
          </div>

          {/* Status Badge */}
          <div className="flex gap-2 ml-4">
            {status === 'new' && (
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-xs font-medium">
                <span className="w-2 h-2 bg-blue-600 rounded-full"></span>
                New
              </span>
            )}
          </div>
        </div>

        {/* Description Preview */}
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
          {description}
        </p>

        {/* Details Row */}
        <div className="flex flex-wrap items-center gap-4 mb-4 text-sm">
          <div>
            <span className="text-gray-600">Quantity: </span>
            <span className="font-medium text-gray-900">{quantity}</span>
          </div>
          <div className="w-px h-4 bg-gray-300"></div>
          <div>
            <span className="text-gray-600">Score: </span>
            <span className="font-medium text-gray-900">{lead_score}/100</span>
          </div>
          <div className="w-px h-4 bg-gray-300"></div>
          <div className="text-gray-600">{timeAgo}</div>
        </div>

        {/* Grade Badge */}
        <div className="flex items-center justify-between">
          <div>
            <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full font-medium text-sm border ${colors.bg} ${colors.text} ${colors.border}`}>
              <span className="w-2 h-2 rounded-full bg-current"></span>
              Grade {lead_grade} - {GRADE_LABELS[lead_grade]}
            </span>
          </div>
          <span className="text-sm font-medium text-primary-600 hover:text-primary-700">
            View Details →
          </span>
        </div>
      </div>
    </Link>
  )
}
