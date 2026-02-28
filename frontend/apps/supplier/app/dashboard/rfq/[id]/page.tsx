'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import Link from 'next/link'

// Mock RFQ detail data
const mockRFQDetail = {
  id: 1,
  product_name: 'CNC Machined Aluminum Parts',
  description: 'We are looking for precision CNC machined aluminum components. Parts need to be made from 6061-T6 aluminum with tight tolerances of ±0.05mm. We require ISO 9001 certification. Delivery needed within 60 days.',
  buyer_company: 'TechCorp Manufacturing',
  buyer_contact: {
    name: 'John Smith',
    email: 'john@techcorp.com',
    phone: '+1-555-0123',
  },
  company_profile: {
    industry: 'Electronics Manufacturing',
    employees: 500,
    founded: 2010,
    location: 'San Francisco, USA',
    certifications: ['ISO 9001', 'ISO 14001'],
    description: 'Leading manufacturer of electronic components and devices',
  },
  specifications: {
    quantity: '1000 pieces',
    material: '6061-T6 Aluminum',
    dimensions: '100mm x 50mm x 20mm',
    tolerances: '±0.05mm',
    certifications: 'ISO 9001',
    special_requirements: 'Anodized finish, RoHS compliant',
  },
  lead_grade: 'A' as const,
  lead_score: 85,
  created_at: '2024-02-28T10:30:00Z',
  status: 'new' as const,

  // AI-generated content
  ai_summary: 'High-quality manufacturing opportunity. Customer is seeking precision CNC-machined aluminum parts with tight tolerances (±0.05mm). ISO 9001 certification required. 1000-unit order with 60-day delivery window. Established buyer with strong manufacturing credentials.',
  ai_draft_reply: 'Dear TechCorp Manufacturing,\n\nThank you for your RFQ for CNC machined aluminum components. We are very interested in this opportunity.\n\nBased on your specifications, we can provide 6061-T6 aluminum parts with the required ±0.05mm tolerance. Our facility is ISO 9001 certified and equipped with modern CNC machinery capable of delivering precision components to your exact specifications.\n\nWe can meet your 60-day delivery requirement for 1000 pieces. Our pricing is highly competitive and we offer volume discounts for orders of this size.\n\nWe would welcome the opportunity to discuss this project further and provide you with a detailed quotation. Please feel free to contact us at your earliest convenience.\n\nBest regards,\nYour Manufacturing Team',
}

export default function RFQDetailPage({ params }: { params: { id: string } }) {
  const t = useTranslations('rfq')
  const [showReplyEditor, setShowReplyEditor] = useState(false)
  const [editedReply, setEditedReply] = useState(mockRFQDetail.ai_draft_reply)
  const [saving, setSaving] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleCopyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleSaveReply = async () => {
    setSaving(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    setSaving(false)
    setShowReplyEditor(false)
  }

  const GRADE_COLORS = {
    A: { bg: 'bg-green-100', text: 'text-green-800' },
    B: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
    C: { bg: 'bg-red-100', text: 'text-red-800' },
  }

  const colors = GRADE_COLORS[mockRFQDetail.lead_grade]

  return (
    <main className="flex-1">
      {/* Page Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <Link href="/dashboard/rfq" className="text-primary-600 hover:text-primary-700 mb-2 inline-block">
              ← Back to Inbox
            </Link>
            <h1 className="text-h2 font-bold text-gray-900">{mockRFQDetail.product_name}</h1>
            <p className="text-sm text-gray-600 mt-1">RFQ #{mockRFQDetail.id}</p>
          </div>
          <div className={`px-4 py-2 rounded-lg font-semibold ${colors.bg} ${colors.text}`}>
            Grade {mockRFQDetail.lead_grade} ({mockRFQDetail.lead_score}/100)
          </div>
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
                    {mockRFQDetail.description}
                  </p>
                </div>

                {/* Specifications */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-gray-600 uppercase">Quantity</label>
                    <p className="text-gray-900 font-medium">{mockRFQDetail.specifications.quantity}</p>
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-gray-600 uppercase">Material</label>
                    <p className="text-gray-900 font-medium">{mockRFQDetail.specifications.material}</p>
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-gray-600 uppercase">Dimensions</label>
                    <p className="text-gray-900 font-medium">{mockRFQDetail.specifications.dimensions}</p>
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-gray-600 uppercase">Tolerances</label>
                    <p className="text-gray-900 font-medium">{mockRFQDetail.specifications.tolerances}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Summary Section */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-start gap-3">
                <div className="text-2xl">🤖</div>
                <div className="flex-1">
                  <h3 className="font-bold text-gray-900 mb-2">AI Summary</h3>
                  <p className="text-gray-700 text-sm leading-relaxed">
                    {mockRFQDetail.ai_summary}
                  </p>
                </div>
              </div>
            </div>

            {/* Draft Reply Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <h3 className="text-h3 font-bold text-gray-900">AI Draft Reply</h3>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    Draft
                  </span>
                </div>
                <button
                  onClick={() => handleCopyToClipboard(editedReply)}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  {copied ? '✓ Copied' : 'Copy'}
                </button>
              </div>

              {!showReplyEditor ? (
                <div>
                  <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap font-mono leading-relaxed">
                      {mockRFQDetail.ai_draft_reply}
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
                        setEditedReply(mockRFQDetail.ai_draft_reply)
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

          {/* Right Column - Buyer Profile */}
          <div className="col-span-1">
            {/* Buyer Company Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 sticky top-6">
              <h3 className="text-h4 font-bold text-gray-900 mb-4">Buyer Company</h3>

              {/* Company Name */}
              <div className="mb-4 pb-4 border-b border-gray-200">
                <p className="text-sm text-gray-600 uppercase font-semibold">Company</p>
                <p className="text-gray-900 font-medium mt-1">{mockRFQDetail.buyer_company}</p>
              </div>

              {/* Contact Person */}
              <div className="mb-4 pb-4 border-b border-gray-200">
                <p className="text-sm text-gray-600 uppercase font-semibold">Contact Person</p>
                <p className="text-gray-900 font-medium mt-1">{mockRFQDetail.buyer_contact.name}</p>
                <p className="text-sm text-gray-600 mt-1">{mockRFQDetail.buyer_contact.email}</p>
                <p className="text-sm text-gray-600">{mockRFQDetail.buyer_contact.phone}</p>
              </div>

              {/* Company Details */}
              <div className="space-y-3 mb-4 pb-4 border-b border-gray-200">
                <div>
                  <p className="text-xs text-gray-600 uppercase font-semibold">Industry</p>
                  <p className="text-sm text-gray-900 mt-1">{mockRFQDetail.company_profile.industry}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 uppercase font-semibold">Employees</p>
                  <p className="text-sm text-gray-900 mt-1">{mockRFQDetail.company_profile.employees}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 uppercase font-semibold">Location</p>
                  <p className="text-sm text-gray-900 mt-1">{mockRFQDetail.company_profile.location}</p>
                </div>
              </div>

              {/* Certifications */}
              <div className="mb-4 pb-4 border-b border-gray-200">
                <p className="text-xs text-gray-600 uppercase font-semibold mb-2">Certifications</p>
                <div className="flex flex-wrap gap-2">
                  {mockRFQDetail.company_profile.certifications.map(cert => (
                    <span
                      key={cert}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                    >
                      {cert}
                    </span>
                  ))}
                </div>
              </div>

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
