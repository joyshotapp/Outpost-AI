'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

const INDUSTRIES = [
  { name: 'Automotive', icon: '🚗', slug: 'Automotive' },
  { name: 'Electronics', icon: '💡', slug: 'Electronics' },
  { name: 'Aerospace', icon: '✈️', slug: 'Aerospace' },
  { name: 'Medical Devices', icon: '🏥', slug: 'Medical' },
  { name: 'Steel & Metals', icon: '🔩', slug: 'Metals' },
  { name: 'Plastics', icon: '⚙️', slug: 'Plastics' },
]

const STATS = [
  { label: 'Verified Suppliers', value: '12,000+' },
  { label: 'Countries', value: '60+' },
  { label: 'RFQs Processed', value: '50,000+' },
  { label: 'Avg. Quote Time', value: '< 24h' },
]

export default function Home() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      router.push(`/suppliers?q=${encodeURIComponent(query.trim())}`)
    }
  }

  const handleSuggest = async (val: string) => {
    setQuery(val)
    if (val.length < 2) { setSuggestions([]); setShowSuggestions(false); return }
    try {
      const res = await fetch(`/api/v1/search/suppliers/suggest?q=${encodeURIComponent(val)}&size=5`)
      if (res.ok) {
        const data = await res.json()
        setSuggestions(data.suggestions || [])
        setShowSuggestions((data.suggestions || []).length > 0)
      }
    } catch {
      setSuggestions([])
    }
  }

  return (
    <main className="flex-1 w-full">
      {/* Navigation */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-30">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold text-primary-700">Factory Insider</Link>
          <div className="flex items-center gap-3">
            <Link href="/suppliers" className="text-sm text-gray-600 hover:text-primary-700 font-medium">Browse Suppliers</Link>
            <Link href="/rfq/new" className="text-sm text-gray-600 hover:text-primary-700 font-medium">Post RFQ</Link>
            <Link href="/dashboard" className="text-sm text-gray-600 hover:text-primary-700 font-medium">Dashboard</Link>
            <button className="px-4 py-1.5 text-primary-700 border border-primary-700 rounded hover:bg-primary-50 text-sm font-medium">Login</button>
            <button className="px-4 py-1.5 bg-primary-700 text-white rounded hover:bg-primary-600 text-sm font-medium">Sign Up</button>
          </div>
        </nav>
      </header>

      {/* Hero + Search */}
      <section className="bg-gradient-to-br from-primary-700 to-primary-900 py-24 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <h1 className="text-4xl md:text-5xl font-extrabold mb-4 leading-tight">
            Find Verified Manufacturers Worldwide
          </h1>
          <p className="text-primary-100 text-lg mb-10 max-w-2xl mx-auto">
            Search 12,000+ pre-screened suppliers across 60 countries. Get quotes in under 24 hours.
          </p>

          {/* Search bar */}
          <form onSubmit={handleSearch} className="relative max-w-2xl mx-auto">
            <div className="flex gap-2 bg-white rounded-xl p-2 shadow-xl">
              <input
                type="text"
                value={query}
                onChange={e => handleSuggest(e.target.value)}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                placeholder="Search by product, material, industry, or company..."
                className="flex-1 px-4 py-2 text-gray-900 bg-transparent outline-none text-base placeholder-gray-400"
              />
              <button
                type="submit"
                className="px-6 py-2 bg-primary-700 text-white rounded-lg font-semibold hover:bg-primary-600 transition-colors"
              >
                Search
              </button>
            </div>
            {/* Suggestions dropdown */}
            {showSuggestions && suggestions.length > 0 && (
              <ul className="absolute w-full bg-white border border-gray-200 rounded-xl mt-1 shadow-lg z-20 text-left overflow-hidden">
                {suggestions.map(s => (
                  <li
                    key={s}
                    className="px-5 py-3 text-gray-800 hover:bg-primary-50 cursor-pointer text-sm"
                    onMouseDown={() => { setQuery(s); setShowSuggestions(false) }}
                  >
                    🔍 {s}
                  </li>
                ))}
              </ul>
            )}
          </form>

          {/* Quick filters */}
          <div className="flex flex-wrap justify-center gap-2 mt-6">
            {['ISO 9001', 'AS9100', 'IATF 16949', 'ISO 13485'].map(cert => (
              <button
                key={cert}
                onClick={() => router.push(`/suppliers?certifications=${cert}`)}
                className="px-3 py-1 rounded-full bg-white/20 hover:bg-white/30 text-sm font-medium transition-colors"
              >
                {cert}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Platform stats */}
      <section className="bg-gray-50 border-y border-gray-100 py-10">
        <div className="max-w-5xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-6">
          {STATS.map(stat => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl font-extrabold text-primary-700">{stat.value}</div>
              <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Industry grid */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2 text-center">Browse by Industry</h2>
          <p className="text-gray-500 text-center mb-10">Specialists across every manufacturing sector</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {INDUSTRIES.map(ind => (
              <Link
                key={ind.slug}
                href={`/suppliers?industry=${ind.slug}`}
                className="group flex flex-col items-center p-5 bg-white border border-gray-200 rounded-xl hover:border-primary-400 hover:shadow-md transition-all text-center"
              >
                <span className="text-4xl mb-3">{ind.icon}</span>
                <span className="text-sm font-semibold text-gray-700 group-hover:text-primary-700">{ind.name}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Card */}
      <section className="py-14 bg-primary-50">
        <div className="max-w-3xl mx-auto text-center px-4">
          <h2 className="text-2xl font-bold text-primary-900 mb-3">Ready to Source Smarter?</h2>
          <p className="text-gray-600 mb-8">Post your RFQ and receive competitive bids from verified suppliers within 24 hours.</p>
          <div className="flex justify-center gap-4">
            <Link href="/rfq/new" className="px-8 py-3 bg-primary-700 text-white rounded-lg font-semibold hover:bg-primary-600">
              Post an RFQ
            </Link>
            <Link href="/suppliers" className="px-8 py-3 border border-primary-700 text-primary-700 rounded-lg font-semibold hover:bg-primary-50">
              Explore Suppliers
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm">
          © {new Date().getFullYear()} Factory Insider · Connecting Global Buyers with Manufacturers
        </div>
      </footer>
    </main>
  )
}
