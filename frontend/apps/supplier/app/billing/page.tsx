'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

const PLAN_COLORS: Record<string, string> = {
  free: 'bg-gray-100 text-gray-700 border-gray-300',
  starter: 'bg-blue-50 text-blue-700 border-blue-300',
  professional: 'bg-purple-50 text-purple-700 border-purple-400',
  enterprise: 'bg-amber-50 text-amber-800 border-amber-400',
}

const PLAN_CTA: Record<string, string> = {
  free: 'bg-blue-600 hover:bg-blue-700 text-white',
  starter: 'bg-purple-600 hover:bg-purple-700 text-white',
  professional: 'bg-amber-600 hover:bg-amber-700 text-white',
  enterprise: 'bg-gray-800 hover:bg-gray-900 text-white',
}

interface Plan {
  tier: string
  name: string
  price_usd: number
  features: string[]
  limits: Record<string, number>
}

interface Subscription {
  plan_tier: string
  status: string
  trial_end: string | null
  current_period_end: string | null
  canceled_at: string | null
  _stub?: boolean
}

interface Invoice {
  id: string
  date: string
  amount_usd: number
  status: string
  pdf_url: string | null
}

export default function BillingPage() {
  const router = useRouter()
  const [plans, setPlans] = useState<Plan[]>([])
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [features, setFeatures] = useState<{ tier: string; features: string[]; limits: Record<string, number> } | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'plans' | 'invoices' | 'features'>('plans')

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

  useEffect(() => {
    fetchAll()
  }, [])

  async function fetchAll() {
    setLoading(true)
    try {
      const [plansRes, subRes, invRes, featRes] = await Promise.all([
        fetch(`${API}/billing/plans`),
        token ? fetch(`${API}/billing/subscription`, { headers: { Authorization: `Bearer ${token}` } }) : Promise.resolve(null),
        token ? fetch(`${API}/billing/invoices`, { headers: { Authorization: `Bearer ${token}` } }) : Promise.resolve(null),
        token ? fetch(`${API}/billing/features`, { headers: { Authorization: `Bearer ${token}` } }) : Promise.resolve(null),
      ])
      const plansData = await plansRes.json()
      setPlans(plansData.plans || [])
      if (subRes?.ok) setSubscription(await subRes.json())
      if (invRes?.ok) { const d = await invRes.json(); setInvoices(d.invoices || []) }
      if (featRes?.ok) setFeatures(await featRes.json())
    } catch {
      setError('Failed to load billing information')
    } finally {
      setLoading(false)
    }
  }

  async function handleSelectPlan(tier: string) {
    if (!token) { router.push('/login'); return }
    if (tier === subscription?.plan_tier) return
    setActionLoading(true)
    try {
      const res = await fetch(`${API}/billing/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          plan_tier: tier,
          success_url: `${window.location.origin}/billing?success=1`,
          cancel_url: `${window.location.origin}/billing?canceled=1`,
        }),
      })
      const data = await res.json()
      if (data.checkout_url) window.location.href = data.checkout_url
    } catch {
      setError('Failed to initiate checkout')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleManageBilling() {
    if (!token) return
    setActionLoading(true)
    try {
      const res = await fetch(`${API}/billing/portal`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      if (data.portal_url) window.location.href = data.portal_url
    } catch {
      setError('Failed to open billing portal')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleCancel() {
    if (!token || !confirm('Cancel your subscription? Your access continues until the end of the billing period.')) return
    setActionLoading(true)
    try {
      await fetch(`${API}/billing/subscription`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      await fetchAll()
    } finally {
      setActionLoading(false)
    }
  }

  const currentTier = subscription?.plan_tier || 'free'

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600" />
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Subscription & Billing</h1>
            <p className="text-sm text-gray-500">Manage your Factory Insider plan</p>
          </div>
          <button
            onClick={() => router.push('/dashboard')}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            ← Back to Dashboard
          </button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Current plan banner */}
        {subscription && (
          <div className={`mb-8 rounded-xl border-2 p-6 ${PLAN_COLORS[currentTier]}`}>
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider opacity-70">Current Plan</span>
                <h2 className="text-2xl font-bold mt-1 capitalize">{currentTier}</h2>
                <p className="text-sm mt-1 opacity-80">
                  Status: <span className="font-medium capitalize">{subscription.status}</span>
                  {subscription.trial_end && ` · Trial ends ${new Date(subscription.trial_end).toLocaleDateString()}`}
                  {subscription.current_period_end && ` · Renews ${new Date(subscription.current_period_end).toLocaleDateString()}`}
                  {subscription._stub && ' · (sandbox mode)'}
                </p>
              </div>
              <div className="flex gap-2">
                {currentTier !== 'free' && (
                  <button
                    onClick={handleManageBilling}
                    disabled={actionLoading}
                    className="text-sm bg-white bg-opacity-70 hover:bg-opacity-100 border border-current px-4 py-2 rounded-lg font-medium transition"
                  >
                    Manage Billing
                  </button>
                )}
                {currentTier !== 'free' && subscription.status !== 'canceled' && (
                  <button
                    onClick={handleCancel}
                    disabled={actionLoading}
                    className="text-sm text-red-600 hover:text-red-800 px-4 py-2 rounded-lg font-medium transition"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
          {(['plans', 'invoices', 'features'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition capitalize ${
                activeTab === tab ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'invoices' ? 'Billing History' : tab}
            </button>
          ))}
        </div>

        {/* Plans Tab */}
        {activeTab === 'plans' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan) => {
              const isCurrent = plan.tier === currentTier
              return (
                <div
                  key={plan.tier}
                  className={`bg-white rounded-xl border-2 p-6 flex flex-col transition ${
                    isCurrent ? 'border-purple-500 shadow-md' : 'border-gray-200 hover:border-gray-300'
                  } ${plan.tier === 'professional' ? 'relative' : ''}`}
                >
                  {plan.tier === 'professional' && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                      Most Popular
                    </div>
                  )}
                  <div className="mb-4">
                    <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
                    <div className="mt-2">
                      {plan.price_usd === 0 ? (
                        <span className="text-3xl font-bold text-gray-900">Free</span>
                      ) : (
                        <>
                          <span className="text-3xl font-bold text-gray-900">${plan.price_usd}</span>
                          <span className="text-gray-500 text-sm">/month</span>
                        </>
                      )}
                    </div>
                  </div>
                  <ul className="space-y-2 flex-1 mb-6">
                    {plan.features.map((f, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                        <span className="text-green-500 mt-0.5">✓</span>
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                  <button
                    onClick={() => handleSelectPlan(plan.tier)}
                    disabled={actionLoading || isCurrent}
                    className={`w-full py-2.5 rounded-lg text-sm font-semibold transition ${
                      isCurrent
                        ? 'bg-gray-100 text-gray-500 cursor-default'
                        : PLAN_CTA[plan.tier] || PLAN_CTA.professional
                    }`}
                  >
                    {isCurrent ? 'Current Plan' : plan.price_usd === 0 ? 'Downgrade to Free' : `Upgrade to ${plan.name}`}
                  </button>
                </div>
              )
            })}
          </div>
        )}

        {/* Invoices Tab */}
        {activeTab === 'invoices' && (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            {invoices.length === 0 ? (
              <div className="p-12 text-center text-gray-500">No invoices yet</div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    {['Date', 'Amount', 'Status', 'Invoice'].map((h) => (
                      <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {invoices.map((inv) => (
                    <tr key={inv.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{inv.date}</td>
                      <td className="px-6 py-4 text-sm font-medium">${inv.amount_usd.toFixed(2)}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          inv.status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {inv.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {inv.pdf_url ? (
                          <a href={inv.pdf_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline text-sm">
                            Download PDF
                          </a>
                        ) : (
                          <span className="text-gray-400 text-sm">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Features Tab */}
        {activeTab === 'features' && features && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Features available on your <span className="capitalize font-bold">{features.tier}</span> plan</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
              {features.features.map((f) => (
                <div key={f} className="flex items-center gap-2 bg-green-50 rounded-lg px-3 py-2">
                  <span className="text-green-500 text-sm">✓</span>
                  <span className="text-sm text-gray-700 capitalize">{f.replace(/_/g, ' ')}</span>
                </div>
              ))}
            </div>
            <h4 className="font-medium text-gray-700 mb-3">Plan Limits</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(features.limits).map(([k, v]) => (
                <div key={k} className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-gray-900">{v === -1 ? '∞' : v}</div>
                  <div className="text-xs text-gray-500 mt-1 capitalize">{k.replace(/_/g, ' ')}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
