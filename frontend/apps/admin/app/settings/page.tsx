'use client'

import { useState, useEffect, useCallback } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface Setting {
  key: string
  value: string | null
  description: string | null
  updated_at: string
}

const PRESET_KEYS = [
  { key: 'platform.maintenance_mode', description: 'Set to "true" to enable maintenance mode for all users' },
  { key: 'platform.global_notification', description: 'Banner message shown to all users (leave empty to hide)' },
  { key: 'platform.max_suppliers', description: 'Maximum number of supplier accounts allowed (0 = unlimited)' },
  { key: 'email.from_name', description: 'Display name for outbound platform emails' },
  { key: 'email.reply_to', description: 'Reply-to address for platform emails' },
  { key: 'stripe.test_mode', description: 'Set to "true" to force Stripe test mode regardless of environment' },
]

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<Setting[]>([])
  const [loading, setLoading] = useState(true)
  const [editKey, setEditKey] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [saveLoading, setSaveLoading] = useState(false)
  const [newKey, setNewKey] = useState('')
  const [newValue, setNewValue] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

  const fetchSettings = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/admin/settings`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const data = await res.json()
        setSettings(data.settings || [])
      }
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => { fetchSettings() }, [fetchSettings])

  async function saveEdit(key: string) {
    setSaveLoading(true)
    try {
      await fetch(`${API}/admin/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ key, value: editValue, description: editDesc || null }),
      })
      setEditKey(null)
      setSuccessMsg(`Setting "${key}" saved`)
      setTimeout(() => setSuccessMsg(null), 3000)
      await fetchSettings()
    } finally {
      setSaveLoading(false)
    }
  }

  async function deleteSetting(key: string) {
    if (!confirm(`Delete setting "${key}"?`)) return
    await fetch(`${API}/admin/settings/${encodeURIComponent(key)}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    await fetchSettings()
  }

  async function addSetting() {
    if (!newKey.trim()) return
    setSaveLoading(true)
    try {
      await fetch(`${API}/admin/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ key: newKey.trim(), value: newValue, description: newDesc || null }),
      })
      setNewKey(''); setNewValue(''); setNewDesc(''); setShowAddForm(false)
      setSuccessMsg(`Setting "${newKey.trim()}" created`)
      setTimeout(() => setSuccessMsg(null), 3000)
      await fetchSettings()
    } finally {
      setSaveLoading(false)
    }
  }

  const startEdit = (s: Setting) => {
    setEditKey(s.key)
    setEditValue(s.value || '')
    setEditDesc(s.description || '')
  }

  const settingKeys = new Set(settings.map((s) => s.key))
  const missingPresets = PRESET_KEYS.filter((p) => !settingKeys.has(p.key))

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">System Settings</h1>
            <p className="text-gray-500 mt-1">Platform-wide configuration and feature flags</p>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg"
          >
            + Add Setting
          </button>
        </div>

        {/* Success msg */}
        {successMsg && (
          <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
            {successMsg}
          </div>
        )}

        {/* Add form */}
        {showAddForm && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
            <h3 className="font-semibold text-gray-900 mb-4">Add New Setting</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Key *</label>
                <input
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  placeholder="e.g. platform.feature_flag"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Value</label>
                <input
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  placeholder="Setting value"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
                <input
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Optional description"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>
            {/* Preset quick-add */}
            {missingPresets.length > 0 && (
              <div className="mb-3">
                <p className="text-xs text-gray-500 mb-2">Quick add preset:</p>
                <div className="flex flex-wrap gap-2">
                  {missingPresets.map((p) => (
                    <button
                      key={p.key}
                      onClick={() => { setNewKey(p.key); setNewDesc(p.description) }}
                      className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded"
                    >
                      {p.key}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <div className="flex gap-2">
              <button onClick={addSetting} disabled={saveLoading || !newKey.trim()}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg">
                Save
              </button>
              <button onClick={() => setShowAddForm(false)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-lg">
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Settings table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
            </div>
          ) : settings.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              No settings configured yet. Click "+ Add Setting" to create the first one.
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {['Key', 'Value', 'Description', 'Updated', 'Actions'].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {settings.map((s) => (
                  <tr key={s.key} className="hover:bg-gray-50">
                    <td className="px-5 py-4">
                      <code className="text-sm font-mono text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded">{s.key}</code>
                    </td>
                    <td className="px-5 py-4">
                      {editKey === s.key ? (
                        <input
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="border border-gray-300 rounded-lg px-2 py-1 text-sm w-full focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      ) : (
                        <span className="text-sm text-gray-900 font-mono">{s.value ?? <span className="text-gray-400 italic">empty</span>}</span>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      {editKey === s.key ? (
                        <input
                          value={editDesc}
                          onChange={(e) => setEditDesc(e.target.value)}
                          className="border border-gray-300 rounded-lg px-2 py-1 text-sm w-full focus:outline-none"
                        />
                      ) : (
                        <span className="text-sm text-gray-500">{s.description || '—'}</span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-sm text-gray-400 whitespace-nowrap">
                      {new Date(s.updated_at).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-4">
                      {editKey === s.key ? (
                        <div className="flex gap-2">
                          <button onClick={() => saveEdit(s.key)} disabled={saveLoading}
                            className="text-xs px-3 py-1.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg font-medium">
                            Save
                          </button>
                          <button onClick={() => setEditKey(null)}
                            className="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium">
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex gap-2">
                          <button onClick={() => startEdit(s)}
                            className="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium">
                            Edit
                          </button>
                          <button onClick={() => deleteSetting(s.key)}
                            className="text-xs px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-700 rounded-lg font-medium">
                            Delete
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
