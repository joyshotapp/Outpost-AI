'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'

// ── Types ─────────────────────────────────────────────────────────────────────

interface SupplierProfile {
  id?: number
  company_name: string
  company_slug: string
  company_description?: string
  main_products?: string
  certifications?: string
  industry?: string
  country?: string
  city?: string
  website?: string
  phone?: string
  email?: string
  is_verified: boolean
  is_active?: boolean
  view_count?: number
  lead_time_days?: number
  number_of_employees?: number
  established_year?: number
  manufacturing_capacity?: string
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function CertBadge({ cert }: { cert: string }) {
  const colors: Record<string, string> = {
    'ISO 9001': 'bg-blue-50 text-blue-700 border-blue-200',
    'ISO 14001': 'bg-green-50 text-green-700 border-green-200',
    'IATF 16949': 'bg-purple-50 text-purple-700 border-purple-200',
    'AS9100': 'bg-sky-50 text-sky-700 border-sky-200',
    'ISO 13485': 'bg-rose-50 text-rose-700 border-rose-200',
  }
  const cls = colors[cert.trim()] || 'bg-gray-50 text-gray-700 border-gray-200'
  return <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${cls}`}>{cert.trim()}</span>
}

function InfoItem({ label, value }: { label: string; value?: string | number | null }) {
  if (!value) return null
  return (
    <div>
      <div className="text-xs text-gray-500 mb-0.5">{label}</div>
      <div className="text-sm font-medium text-gray-800">{value}</div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function SupplierProfilePage() {
  const params = useParams()
  const slug = params?.slug as string

  const [supplier, setSupplier] = useState<SupplierProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!slug) return
    fetch(`/api/v1/suppliers/${slug}`)
      .then(r => r.ok ? r.json() : Promise.reject('Not found'))
      .then(data => setSupplier(data))
      .catch(() => setError('Supplier not found or unavailable.'))
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-12 h-12 border-4 border-primary-200 border-t-primary-700 rounded-full" />
      </div>
    )
  }

  if (error || !supplier) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center text-gray-500">
        <div className="text-6xl mb-4">🏭</div>
        <h1 className="text-xl font-semibold mb-2">Supplier not found</h1>
        <p className="text-sm mb-6">{error || 'This supplier profile does not exist.'}</p>
        <Link href="/suppliers" className="px-5 py-2 bg-primary-700 text-white rounded-lg text-sm">← Back to Suppliers</Link>
      </div>
    )
  }

  const certs = supplier.certifications?.split(',').filter(Boolean) || []
  const products = supplier.main_products?.split(',').filter(Boolean) || []
  const countryName = supplier.country

  return (
    <>
      {/* JSON-LD for SEO */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'Organization',
            name: supplier.company_name,
            description: supplier.company_description,
            url: supplier.website,
            address: {
              '@type': 'PostalAddress',
              addressLocality: supplier.city,
              addressCountry: supplier.country,
            },
          }),
        }}
      />

      <div className="min-h-screen bg-gray-50">
        {/* Nav */}
        <header className="bg-white border-b sticky top-0 z-20">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-4 text-sm">
            <Link href="/" className="font-bold text-primary-700 text-base">Factory Insider</Link>
            <span className="text-gray-400">/</span>
            <Link href="/suppliers" className="text-gray-600 hover:text-primary-700">Suppliers</Link>
            <span className="text-gray-400">/</span>
            <span className="text-gray-800 font-medium truncate">{supplier.company_name}</span>
          </div>
        </header>

        <div className="max-w-5xl mx-auto px-4 py-8">
          {/* Hero Card */}
          <div className="bg-white rounded-2xl border border-gray-200 p-8 mb-6 shadow-sm">
            <div className="flex items-start justify-between gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2 flex-wrap">
                  <h1 className="text-2xl font-bold text-gray-900">{supplier.company_name}</h1>
                  {supplier.is_verified && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-green-50 text-green-700 rounded-full text-xs font-semibold border border-green-200">
                      ✓ Verified Supplier
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500 mb-4">
                  {supplier.industry && <span>🏭 {supplier.industry}</span>}
                  {countryName && <span>📍 {supplier.city ? `${supplier.city}, ${countryName}` : countryName}</span>}
                  {supplier.established_year && <span>📅 Est. {supplier.established_year}</span>}
                  {supplier.number_of_employees && <span>👥 {supplier.number_of_employees.toLocaleString()} employees</span>}
                </div>
                {supplier.company_description && (
                  <p className="text-gray-600 leading-relaxed text-sm">{supplier.company_description}</p>
                )}
              </div>

              {/* Action buttons */}
              <div className="flex flex-col gap-2 flex-shrink-0">
                <Link
                  href={`/rfq/new?supplier=${supplier.company_slug}`}
                  className="px-6 py-2.5 bg-primary-700 text-white rounded-xl text-sm font-semibold hover:bg-primary-600 text-center"
                >
                  Send RFQ
                </Link>
                <button
                  onClick={() => setSaved(!saved)}
                  className={`px-6 py-2.5 rounded-xl text-sm font-semibold border transition-colors ${saved ? 'bg-amber-50 text-amber-700 border-amber-300' : 'border-gray-300 text-gray-700 hover:border-primary-400 hover:text-primary-700'}`}
                >
                  {saved ? '★ Saved' : '☆ Save Supplier'}
                </button>
                <button
                  onClick={() => {/* open message modal */}}
                  className="px-6 py-2.5 rounded-xl text-sm font-semibold border border-gray-300 text-gray-700 hover:border-primary-400 hover:text-primary-700"
                >
                  💬 Message
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Details */}
            <div className="lg:col-span-2 space-y-6">
              {/* Products */}
              {products.length > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <h2 className="font-semibold text-gray-900 mb-4">Main Products & Services</h2>
                  <div className="flex flex-wrap gap-2">
                    {products.map(p => (
                      <span key={p} className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm">{p.trim()}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Certifications */}
              {certs.length > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <h2 className="font-semibold text-gray-900 mb-4">Certifications & Standards</h2>
                  <div className="flex flex-wrap gap-2">
                    {certs.map(c => <CertBadge key={c} cert={c} />)}
                  </div>
                </div>
              )}

              {/* Manufacturing */}
              {supplier.manufacturing_capacity && (
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <h2 className="font-semibold text-gray-900 mb-3">Manufacturing Capacity</h2>
                  <p className="text-sm text-gray-600">{supplier.manufacturing_capacity}</p>
                </div>
              )}
            </div>

            {/* Right: Quick Facts */}
            <div className="space-y-4">
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-4">Quick Facts</h3>
                <div className="space-y-3">
                  <InfoItem label="Lead Time" value={supplier.lead_time_days ? `${supplier.lead_time_days} days` : null} />
                  <InfoItem label="Employees" value={supplier.number_of_employees?.toLocaleString()} />
                  <InfoItem label="Founded" value={supplier.established_year} />
                  <InfoItem label="Industry" value={supplier.industry} />
                  {supplier.website && (
                    <div>
                      <div className="text-xs text-gray-500 mb-0.5">Website</div>
                      <a href={supplier.website} target="_blank" rel="noopener noreferrer" className="text-sm text-primary-600 hover:underline break-all">
                        {supplier.website.replace(/^https?:\/\//, '')}
                      </a>
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-primary-50 border border-primary-100 rounded-xl p-5 text-center">
                <div className="text-sm text-primary-700 font-medium mb-1">Ready to source?</div>
                <p className="text-xs text-primary-600 mb-4">Send an RFQ and get a quote within 24 hours</p>
                <Link
                  href={`/rfq/new?supplier=${supplier.company_slug}`}
                  className="block w-full px-4 py-2 bg-primary-700 text-white rounded-lg text-sm font-semibold hover:bg-primary-600"
                >
                  Create RFQ
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
