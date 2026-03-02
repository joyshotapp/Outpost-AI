'use client'

import Link from 'next/link'
import { useEffect, useState, useCallback } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Supplier {
  id?: number
  company_name: string
  company_slug: string
  company_description?: string
  main_products?: string
  certifications?: string
  industry?: string
  country?: string
  city?: string
  is_verified: boolean
  view_count?: number
  lead_time_days?: number
  number_of_employees?: number
}

interface SearchResponse {
  total: number
  page: number
  pages: number
  page_size: number
  results: Supplier[]
  _stub?: boolean
}

const INDUSTRIES = ['Automotive', 'Electronics', 'Aerospace', 'Medical', 'Metals', 'Plastics', 'Tooling', 'Steel', 'Semiconductors']
const COUNTRIES = [
  { code: 'DE', name: 'Germany' },
  { code: 'CN', name: 'China' },
  { code: 'TW', name: 'Taiwan' },
  { code: 'KR', name: 'South Korea' },
  { code: 'JP', name: 'Japan' },
  { code: 'US', name: 'United States' },
  { code: 'IT', name: 'Italy' },
  { code: 'SE', name: 'Sweden' },
  { code: 'ES', name: 'Spain' },
]
const CERTS = ['ISO 9001', 'ISO 14001', 'IATF 16949', 'AS9100', 'ISO 13485']

// ── SupplierCard ──────────────────────────────────────────────────────────────

function SupplierCard({ supplier }: { supplier: Supplier }) {
  const countryFlag = supplier.country ? `https://flagcdn.com/16x12/${supplier.country.toLowerCase()}.png` : null
  return (
    <Link
      href={`/suppliers/${supplier.company_slug}`}
      className="block bg-white border border-gray-200 rounded-xl p-5 hover:border-primary-400 hover:shadow-md transition-all"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900 text-lg">{supplier.company_name}</h3>
            {supplier.is_verified && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-50 text-green-700 rounded-full text-xs font-medium border border-green-200">
                ✓ Verified
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
            {countryFlag && <img src={countryFlag} alt={supplier.country} className="w-4 h-3" />}
            <span>{supplier.city ? `${supplier.city}, ${supplier.country}` : supplier.country}</span>
            {supplier.industry && <span className="text-gray-300">·</span>}
            {supplier.industry && <span className="text-primary-600">{supplier.industry}</span>}
          </div>
        </div>
        <div className="text-xs text-gray-400 text-right">
          {supplier.view_count && <div>{supplier.view_count.toLocaleString()} views</div>}
          {supplier.lead_time_days && <div>{supplier.lead_time_days} days lead</div>}
        </div>
      </div>

      {supplier.company_description && (
        <p className="text-sm text-gray-600 mt-2 line-clamp-2">{supplier.company_description}</p>
      )}

      <div className="flex flex-wrap gap-1.5 mt-3">
        {supplier.main_products?.split(',').slice(0, 3).map(p => (
          <span key={p} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">{p.trim()}</span>
        ))}
        {supplier.certifications?.split(',').slice(0, 2).map(c => (
          <span key={c} className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs border border-blue-100">{c.trim()}</span>
        ))}
      </div>
    </Link>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function SuppliersPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [results, setResults] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Filter state
  const [q, setQ] = useState(searchParams.get('q') || '')
  const [industry, setIndustry] = useState(searchParams.get('industry') || '')
  const [country, setCountry] = useState(searchParams.get('country') || '')
  const [certifications, setCertifications] = useState(searchParams.get('certifications') || '')
  const [isVerified, setIsVerified] = useState<boolean | null>(
    searchParams.get('is_verified') === 'true' ? true
      : searchParams.get('is_verified') === 'false' ? false : null
  )
  const [sortBy, setSortBy] = useState(searchParams.get('sort_by') || '_score')
  const [page, setPage] = useState(Number(searchParams.get('page')) || 1)

  const search = useCallback(async (newPage = 1) => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams()
      if (q) params.set('q', q)
      if (industry) params.set('industry', industry)
      if (country) params.set('country', country)
      if (certifications) params.set('certifications', certifications)
      if (isVerified !== null) params.set('is_verified', String(isVerified))
      params.set('sort_by', sortBy)
      params.set('page', String(newPage))
      params.set('page_size', '20')

      const res = await fetch(`/api/v1/search/suppliers?${params}`)
      if (!res.ok) throw new Error('Search failed')
      const data = await res.json()
      setResults(data)
      setPage(newPage)
    } catch (e: any) {
      setError(e.message || 'Search error')
    } finally {
      setLoading(false)
    }
  }, [q, industry, country, certifications, isVerified, sortBy])

  useEffect(() => { search(1) }, [industry, country, certifications, isVerified, sortBy])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    search(1)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <header className="bg-white border-b sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-4">
          <Link href="/" className="font-bold text-primary-700 text-lg whitespace-nowrap">Factory Insider</Link>
          <form onSubmit={handleSearch} className="flex-1 flex gap-2">
            <input
              value={q}
              onChange={e => setQ(e.target.value)}
              placeholder="Search suppliers by product, material, or company..."
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm outline-none focus:border-primary-500"
            />
            <button type="submit" className="px-5 py-2 bg-primary-700 text-white rounded-lg text-sm font-medium hover:bg-primary-600">
              Search
            </button>
          </form>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 flex gap-6">
        {/* Filter Sidebar */}
        <aside className="w-56 flex-shrink-0 space-y-6">
          {/* Industry */}
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Industry</div>
            <ul className="space-y-1">
              <li>
                <button onClick={() => setIndustry('')} className={`text-sm w-full text-left px-2 py-1 rounded ${!industry ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700 hover:bg-gray-100'}`}>
                  All Industries
                </button>
              </li>
              {INDUSTRIES.map(ind => (
                <li key={ind}>
                  <button onClick={() => setIndustry(ind === industry ? '' : ind)} className={`text-sm w-full text-left px-2 py-1 rounded ${industry === ind ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700 hover:bg-gray-100'}`}>
                    {ind}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Country */}
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Country</div>
            <ul className="space-y-1">
              <li>
                <button onClick={() => setCountry('')} className={`text-sm w-full text-left px-2 py-1 rounded ${!country ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700 hover:bg-gray-100'}`}>
                  All Countries
                </button>
              </li>
              {COUNTRIES.map(c => (
                <li key={c.code}>
                  <button onClick={() => setCountry(c.code === country ? '' : c.code)} className={`text-sm w-full text-left px-2 py-1 rounded ${country === c.code ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700 hover:bg-gray-100'}`}>
                    {c.name}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Certifications */}
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Certification</div>
            <ul className="space-y-1">
              {CERTS.map(cert => (
                <li key={cert}>
                  <label className="flex items-center gap-2 cursor-pointer px-2 py-1 rounded hover:bg-gray-100">
                    <input
                      type="checkbox"
                      className="accent-primary-700"
                      checked={certifications.split(',').map(c => c.trim()).includes(cert)}
                      onChange={e => {
                        const current = certifications ? certifications.split(',').map(c => c.trim()).filter(Boolean) : []
                        const next = e.target.checked ? [...current, cert] : current.filter(c => c !== cert)
                        setCertifications(next.join(','))
                      }}
                    />
                    <span className="text-sm text-gray-700">{cert}</span>
                  </label>
                </li>
              ))}
            </ul>
          </div>

          {/* Verified */}
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Verification</div>
            <label className="flex items-center gap-2 cursor-pointer px-2 py-1 rounded hover:bg-gray-100">
              <input type="checkbox" className="accent-primary-700" checked={isVerified === true} onChange={e => setIsVerified(e.target.checked ? true : null)} />
              <span className="text-sm text-gray-700">Verified only</span>
            </label>
          </div>
        </aside>

        {/* Results */}
        <div className="flex-1 min-w-0">
          {/* Sort bar */}
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm text-gray-500">
              {results ? `${results.total.toLocaleString()} suppliers found` : ''}
              {results?._stub && <span className="ml-2 text-xs text-amber-600">(Demo data)</span>}
            </div>
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value)}
              className="text-sm border border-gray-300 rounded px-3 py-1 outline-none"
            >
              <option value="_score">Best Match</option>
              <option value="view_count">Most Viewed</option>
              <option value="lead_time_days">Fastest Delivery</option>
              <option value="newest">Newest</option>
            </select>
          </div>

          {loading && (
            <div className="flex justify-center py-24">
              <div className="animate-spin w-10 h-10 border-4 border-primary-200 border-t-primary-700 rounded-full" />
            </div>
          )}
          {error && <div className="bg-red-50 text-red-700 p-4 rounded-xl mb-4">{error}</div>}
          {!loading && results && (
            <>
              <div className="space-y-3">
                {results.results.length === 0 && (
                  <div className="text-center py-20 text-gray-500">
                    <div className="text-5xl mb-4">🔍</div>
                    <div className="text-lg font-medium">No suppliers found</div>
                    <div className="text-sm mt-1">Try adjusting your filters</div>
                  </div>
                )}
                {results.results.map(s => <SupplierCard key={s.company_slug} supplier={s} />)}
              </div>

              {/* Pagination */}
              {results.pages > 1 && (
                <div className="flex justify-center gap-2 mt-8">
                  <button onClick={() => search(page - 1)} disabled={page <= 1} className="px-3 py-1.5 rounded border text-sm disabled:opacity-40 hover:bg-gray-50">← Prev</button>
                  {Array.from({ length: Math.min(results.pages, 7) }, (_, i) => i + 1).map(p => (
                    <button key={p} onClick={() => search(p)} className={`px-3 py-1.5 rounded border text-sm ${p === page ? 'bg-primary-700 text-white border-primary-700' : 'hover:bg-gray-50'}`}>{p}</button>
                  ))}
                  <button onClick={() => search(page + 1)} disabled={page >= results.pages} className="px-3 py-1.5 rounded border text-sm disabled:opacity-40 hover:bg-gray-50">Next →</button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
