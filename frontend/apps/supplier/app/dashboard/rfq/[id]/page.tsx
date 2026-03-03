'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import Link from 'next/link'

interface RFQDetail {
  id: number
  title: string
  description: string
  specifications: string | null
  quantity: number | null
  unit: string | null
  required_delivery_date: string | null
  attachment_url: string | null
  status: string
  lead_score: number | null
  lead_grade: 'A' | 'B' | 'C' | null
  parsed_data: string | null
  pdf_vision_data: string | null
  ai_summary: string | null
  draft_reply: string | null
  created_at: string
  updated_at: string
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'

const GRADE_COLORS = {
  A: { bg: 'bg-green-100', text: 'text-green-800' },
  B: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
  C: { bg: 'bg-red-100', text: 'text-red-800' },
}

export default function RFQDetailPage({ params }: { params: { id: string } }) {
  const t = useTranslations('rfq')
  const [rfq, setRfq] = useState<RFQDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showReplyEditor, setShowReplyEditor] = useState(false)
  const [editedReply, setEditedReply] = useState('')
  const [saving, setSaving] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const fetchRFQ = async () => {
      setLoading(true)
      setError(null)
      try {
        const token = localStorage.getItem('access_token')
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        }

        const response = await fetch(`${API_BASE_URL}/rfqs/${params.id}`, { headers })
        if (!response.ok) {
          throw new Error(`Failed to fetch RFQ: ${response.statusText}`)
        }

        const data: RFQDetail = await response.json()
        setRfq(data)
        setEditedReply(data.draft_reply || '')
      } catch (err) {
        console.error('Failed to fetch RFQ:', err)
        setError('Failed to load RFQ details. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    fetchRFQ()
  }, [params.id])

  const handleCopyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleSaveReply = async () => {
    setSaving(true)
    try {
      const token = localStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      }

      // Persist the edited reply to the backend
      await fetch(`${API_BASE_URL}/rfqs/${params.id}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ draft_reply: editedReply }),
      })

      setRfq(prev => prev ? { ...prev, draft_reply: editedReply } : prev)
      setShowReplyEditor(false)
    } catch (err) {
      console.error('Failed to save reply:', err)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <main className="flex-1 flex items-center justify-center">
        <div className="text-gray-500">Loading RFQ details...</div>
      </main>
    )
  }

  if (error || !rfq) {
    return (
      <main className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'RFQ not found'}</p>
          <Link href="/dashboard/rfq" className="text-primary-600 hover:text-primary-700">
            ← Back to Inbox
          </Link>
        </div>
      </main>
    )
  }

  const grade = rfq.lead_grade || 'C'
  const colors = GRADE_COLORS[grade]

  // Parse specifications JSON if present
  let specifications: Record<string, string> = {}
  if (rfq.specifications) {
    try {
      specifications = JSON.parse(rfq.specifications)
    } catch {
      // specifications stored as plain text
    }
  }

  // Parse parsed_data JSON if present
  let parsedData: Record<string, unknown> = {}
  if (rfq.parsed_data) {
    try {
      parsedData = JSON.parse(rfq.parsed_data)
    } catch {
      // ignore parse errors
    }
  }

  const parsedMaterials = parsedData.materials
  const parsedCertifications = parsedData.certifications
  const hasParsedMaterials = Array.isArray(parsedMaterials)
    ? parsedMaterials.length > 0
    : Boolean(parsedMaterials)
  const hasParsedCertifications = Array.isArray(parsedCertifications)
    ? parsedCertifications.length > 0
    : Boolean(parsedCertifications)

  return (
    <main className="flex-1">
      {/* Page Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <Link href="/dashboard/rfq" className="text-primary-600 hover:text-primary-700 mb-2 inline-block">
              ← Back to Inbox
            </Link>
            <h1 className="text-h2 font-bold text-gray-900">{rfq.title}</h1>
            <p className="text-sm text-gray-600 mt-1">RFQ #{rfq.id}</p>
          </div>
          {rfq.lead_grade && (
            <div className={`px-4 py-2 rounded-lg font-semibold ${colors.bg} ${colors.text}`}>
              Grade {rfq.lead_grade} ({rfq.lead_score}/100)
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Main Content Grid */}
        <div className="grid grid-cols-3 gap-6">
          {/* Left Column - RFQ Details (2 columns) */}
          <div className="col-span-2 space-y-6">
            {/* Original RFQ Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-h3 font-bold text-gray-900 mb-4">Original RFQ</h2>
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {rfq.description}
                  </p>
                </div>

                {/* Specifications */}
                <div className="grid grid-cols-2 gap-4">
                  {rfq.quantity && (
                    <div>
                      <label className="text-xs font-semibold text-gray-600 uppercase">Quantity</label>
                      <p className="text-gray-900 font-medium">
                        {rfq.quantity} {rfq.unit || ''}
                      </p>
                    </div>
                  )}
                  {specifications.material && (
                    <div>
                      <label className="text-xs font-semibold text-gray-600 uppercase">Material</label>
                      <p className="text-gray-900 font-medium">{specifications.material}</p>
                    </div>
                  )}
                  {specifications.dimensions && (
                    <div>
                      <label className="text-xs font-semibold text-gray-600 uppercase">Dimensions</label>
                      <p className="text-gray-900 font-medium">{specifications.dimensions}</p>
                    </div>
                  )}
                  {specifications.tolerances && (
                    <div>
                      <label className="text-xs font-semibold text-gray-600 uppercase">Tolerances</label>
                      <p className="text-gray-900 font-medium">{specifications.tolerances}</p>
                    </div>
                  )}
                  {rfq.required_delivery_date && (
                    <div>
                      <label className="text-xs font-semibold text-gray-600 uppercase">Delivery</label>
                      <p className="text-gray-900 font-medium">{rfq.required_delivery_date}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* AI Summary Section */}
            {rfq.ai_summary && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <div className="flex items-start gap-3">
                  <div className="text-2xl">🤖</div>
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-900 mb-2">AI Summary</h3>
                    <p className="text-gray-700 text-sm leading-relaxed">
                      {rfq.ai_summary}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Draft Reply Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <h3 className="text-h3 font-bold text-gray-900">AI Draft Reply</h3>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    Draft
                  </span>
                </div>
                {rfq.draft_reply && (
                  <button
                    onClick={() => handleCopyToClipboard(editedReply || rfq.draft_reply || '')}
                    className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {copied ? '✓ Copied' : 'Copy'}
                  </button>
                )}
              </div>

              {!rfq.draft_reply ? (
                <div className="text-center py-8 text-gray-500">
                  <p>AI draft reply is being generated...</p>
                </div>
              ) : !showReplyEditor ? (
                <div>
                  <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap font-mono leading-relaxed">
                      {rfq.draft_reply}
                    </p>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setShowReplyEditor(true)}
                      className="flex-1 px-4 py-2 bg-primary-700 text-white rounded-md hover:bg-primary-600 font-medium text-sm"
                    >
                      Edit Reply
                    </button>
                    <button className="flex-1 px-4 py-2 border-2 border-primary-300 text-primary-700 rounded-md hover:bg-primary-50 font-medium text-sm">
                      Send Reply
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <textarea
                    value={editedReply}
                    onChange={e => setEditedReply(e.target.value)}
                    className="w-full h-48 p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none mb-4 font-mono text-sm"
                  />
                  <div className="flex gap-3">
                    <button
                      onClick={handleSaveReply}
                      disabled={saving}
                      className="flex-1 px-4 py-2 bg-primary-700 text-white rounded-md hover:bg-primary-600 disabled:bg-gray-400 font-medium text-sm"
                    >
                      {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button
                      onClick={() => {
                        setEditedReply(rfq.draft_reply || '')
                        setShowReplyEditor(false)
                      }}
                      className="flex-1 px-4 py-2 border-2 border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-medium text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column - RFQ Info */}
          <div className="col-span-1">
            {/* RFQ Info Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 sticky top-6">
              <h3 className="text-h4 font-bold text-gray-900 mb-4">Buyer Company</h3>

              {/* RFQ Details */}
              <div className="space-y-3 mb-4 pb-4 border-b border-gray-200">
                <div>
                  <p className="text-xs text-gray-600 uppercase font-semibold">Product</p>
                  <p className="text-sm text-gray-900 mt-1">{rfq.title}</p>
                </div>
                {rfq.quantity && (
                  <div>
                    <p className="text-xs text-gray-600 uppercase font-semibold">Quantity</p>
                    <p className="text-sm text-gray-900 mt-1">{rfq.quantity} {rfq.unit || 'pcs'}</p>
                  </div>
                )}
                {rfq.required_delivery_date && (
                  <div>
                    <p className="text-xs text-gray-600 uppercase font-semibold">Delivery</p>
                    <p className="text-sm text-gray-900 mt-1">{rfq.required_delivery_date}</p>
                  </div>
                )}
              </div>

              {/* Parsed specifications from AI */}
              {Object.keys(parsedData).length > 0 && (
                <div className="space-y-3 mb-4 pb-4 border-b border-gray-200">
                  {hasParsedMaterials && (
                    <div>
                      <p className="text-xs text-gray-600 uppercase font-semibold">Material</p>
                      <p className="text-sm text-gray-900 mt-1">
                        {Array.isArray(parsedMaterials)
                          ? parsedMaterials.map((material) => String(material)).join(', ')
                          : String(parsedMaterials)}
                      </p>
                    </div>
                  )}
                  {hasParsedCertifications && (
                    <div>
                      <p className="text-xs text-gray-600 uppercase font-semibold mb-1">Certifications</p>
                      <div className="flex flex-wrap gap-2">
                        {(Array.isArray(parsedCertifications)
                          ? parsedCertifications
                          : [parsedCertifications]
                        ).map((cert: unknown, i: number) => (
                          <span
                            key={i}
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                          >
                            {String(cert)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="space-y-2">
                <button className="w-full px-4 py-2 bg-primary-700 text-white rounded-md hover:bg-primary-600 font-medium text-sm">
                  Reply to RFQ
                </button>
                <button className="w-full px-4 py-2 border-2 border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-medium text-sm">
                  Save
                </button>
                <button className="w-full px-4 py-2 border-2 border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-medium text-sm">
                  Archive
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
