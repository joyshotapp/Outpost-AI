'use client'

import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '@/lib/api'
import { SkeletonTable } from '@/components/ui/Skeleton'
import EmptyState from '@/components/ui/EmptyState'

interface Inquiry {
  id: number
  buyer_company: string
  subject: string
  message: string
  status: 'new' | 'read' | 'replied'
  created_at: string
}

const STATUS_STYLES: Record<Inquiry['status'], string> = {
  new: 'bg-blue-100 text-blue-700',
  read: 'bg-gray-100 text-gray-600',
  replied: 'bg-green-100 text-green-700',
}

const STATUS_LABELS: Record<Inquiry['status'], string> = {
  new: '新詢問',
  read: '已讀',
  replied: '已回覆',
}

export default function InquiriesPage() {
  const [inquiries, setInquiries] = useState<Inquiry[]>([])
  const [loading, setLoading] = useState(true)

  const fetchInquiries = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch<Inquiry[]>('/supplier/inquiries')
      setInquiries(data)
    } catch {
      setInquiries([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchInquiries() }, [fetchInquiries])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-h1 font-bold text-gray-900">Buyer Inquiries</h1>
          <p className="text-body-sm text-gray-500 mt-1">
            {loading ? '載入中…' : `共 ${inquiries.length} 筆詢問`}
          </p>
        </div>
        <button
          onClick={fetchInquiries}
          className="text-sm px-4 py-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 transition-colors"
        >
          ↻ 重新整理
        </button>
      </div>

      {loading ? (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <SkeletonTable rows={5} />
        </div>
      ) : inquiries.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200">
          <EmptyState type="rfq" />
        </div>
      ) : (
        <div className="space-y-3">
          {inquiries.map((inq) => (
            <div
              key={inq.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 truncate">{inq.subject}</h3>
                  <p className="text-sm text-gray-500 mt-0.5">
                    <span className="font-medium text-gray-600">{inq.buyer_company}</span>
                  </p>
                  <p className="text-sm text-gray-600 mt-2 line-clamp-2">{inq.message}</p>
                </div>
                <div className="flex flex-col items-end gap-2 flex-shrink-0">
                  <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${STATUS_STYLES[inq.status]}`}>
                    {STATUS_LABELS[inq.status]}
                  </span>
                  <p className="text-xs text-gray-400">
                    {new Date(inq.created_at).toLocaleDateString('zh-TW', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
