'use client'

import React, { useCallback, useEffect, useState } from 'react'

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface Exhibition {
  id: number
  name: string
  location: string | null
  booth_number: string | null
  start_date: string | null
  end_date: string | null
  status: 'planning' | 'active' | 'post_show' | 'completed'
  contacts_count: number
  notes: string | null
  created_at: string
}

interface ExhibitionForm {
  name: string
  location: string
  booth_number: string
  start_date: string
  end_date: string
  notes: string
}

const EMPTY_FORM: ExhibitionForm = {
  name: '',
  location: '',
  booth_number: '',
  start_date: '',
  end_date: '',
  notes: '',
}

const STATUS_LABELS: Record<string, string> = {
  planning:   '🗓 規劃中',
  active:     '🟢 展出中',
  post_show:  '📦 展後跟進',
  completed:  '✅ 已完成',
}

const STATUS_COLORS: Record<string, string> = {
  planning:   'bg-blue-50 text-blue-700 border-blue-200',
  active:     'bg-green-50 text-green-700 border-green-200',
  post_show:  'bg-orange-50 text-orange-700 border-orange-200',
  completed:  'bg-gray-50 text-gray-600 border-gray-200',
}

const NEXT_STATUS: Record<string, { label: string; value: string } | null> = {
  planning:  { label: '▶ 開始展覽', value: 'active' },
  active:    { label: '📦 進入展後', value: 'post_show' },
  post_show: { label: '✅ 標記完成', value: 'completed' },
  completed: null,
}

// ─────────────────────────────────────────────────────────────────────────────
// API helpers
// ─────────────────────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

function authHeaders(): Record<string, string> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  return headers
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const mergedHeaders: Record<string, string> = {
    ...authHeaders(),
    ...((options?.headers as Record<string, string> | undefined) ?? {}),
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers: mergedHeaders })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  if (res.status === 204) return null as T
  return res.json()
}

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

export default function ExhibitionsPage() {
  const [exhibitions, setExhibitions] = useState<Exhibition[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<ExhibitionForm>(EMPTY_FORM)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>('')

  const loadExhibitions = useCallback(async () => {
    setLoading(true)
    try {
      const url = statusFilter ? `/exhibitions?status=${statusFilter}` : '/exhibitions'
      const data = await apiFetch<Exhibition[]>(url)
      setExhibitions(data)
    } catch (err) {
      console.error(err)
      // Demo data
      setExhibitions([
        {
          id: 1, name: 'Hannover Messe 2026', location: 'Hannover, Germany', booth_number: 'Hall 4, C22',
          start_date: '2026-04-22', end_date: '2026-04-26', status: 'planning',
          contacts_count: 0, notes: '首次參展，目標拿到 50 張名片', created_at: new Date().toISOString(),
        },
        {
          id: 2, name: 'TWTC Taiwan Machine Tool Show', location: 'Taipei, Taiwan', booth_number: '1F-B05',
          start_date: '2026-03-15', end_date: '2026-03-19', status: 'post_show',
          contacts_count: 38, notes: null, created_at: new Date(Date.now() - 86400000 * 10).toISOString(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => { loadExhibitions() }, [loadExhibitions])

  const openCreate = () => {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setShowForm(true)
  }

  const openEdit = (ex: Exhibition) => {
    setEditingId(ex.id)
    setForm({
      name: ex.name,
      location: ex.location ?? '',
      booth_number: ex.booth_number ?? '',
      start_date: ex.start_date ?? '',
      end_date: ex.end_date ?? '',
      notes: ex.notes ?? '',
    })
    setShowForm(true)
  }

  const handleSave = async () => {
    if (!form.name.trim()) return
    setSaving(true)
    setError(null)
    try {
      const payload = {
        name: form.name,
        location: form.location || null,
        booth_number: form.booth_number || null,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        notes: form.notes || null,
      }
      if (editingId) {
        const updated = await apiFetch<Exhibition>(`/exhibitions/${editingId}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        })
        setExhibitions(prev => prev.map(e => e.id === editingId ? updated : e))
      } else {
        const created = await apiFetch<Exhibition>('/exhibitions', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
        setExhibitions(prev => [created, ...prev])
      }
      setShowForm(false)
      setForm(EMPTY_FORM)
    } catch (err) {
      setError(String(err))
    } finally {
      setSaving(false)
    }
  }

  const handleAdvanceStatus = async (ex: Exhibition) => {
    const next = NEXT_STATUS[ex.status]
    if (!next) return
    try {
      const updated = await apiFetch<Exhibition>(`/exhibitions/${ex.id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: next.value }),
      })
      setExhibitions(prev => prev.map(e => e.id === ex.id ? updated : e))
    } catch (err) {
      setError(String(err))
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('確定要刪除這筆展覽？')) return
    try {
      await apiFetch(`/exhibitions/${id}`, { method: 'DELETE' })
      setExhibitions(prev => prev.filter(e => e.id !== id))
    } catch (err) {
      setError(String(err))
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🏛 展覽活動管理</h1>
          <p className="text-sm text-gray-500 mt-1">展前 ICP 名單 + 展中名片 + 展後跟進序列</p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors shadow-sm"
        >
          <span className="text-base">+</span> 新增展覽
        </button>
      </div>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">
          ⚠ {error}
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        {['', 'planning', 'active', 'post_show', 'completed'].map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`text-xs px-3 py-1 rounded-full border font-medium transition-colors ${
              statusFilter === s
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
            }`}
          >
            {s === '' ? '全部' : STATUS_LABELS[s] ?? s}
          </button>
        ))}
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center h-40 text-gray-400">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3" />
          載入中…
        </div>
      ) : exhibitions.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">🗓</p>
          <p className="text-lg font-medium">尚無展覽資料</p>
          <p className="text-sm mt-1">點擊「新增展覽」開始加入展前規劃</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">展覽名稱</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 hidden md:table-cell">地點 / 攤位</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 hidden lg:table-cell">日期</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">狀態</th>
                <th className="text-center px-4 py-3 font-semibold text-gray-600 hidden sm:table-cell">名片數</th>
                <th className="text-right px-5 py-3 font-semibold text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {exhibitions.map(ex => (
                <tr key={ex.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-5 py-4">
                    <div className="font-medium text-gray-900">{ex.name}</div>
                    {ex.notes && <div className="text-xs text-gray-400 mt-0.5 truncate max-w-[200px]">{ex.notes}</div>}
                  </td>
                  <td className="px-4 py-4 hidden md:table-cell text-gray-600">
                    <div>{ex.location ?? '—'}</div>
                    {ex.booth_number && <div className="text-xs text-gray-400">{ex.booth_number}</div>}
                  </td>
                  <td className="px-4 py-4 hidden lg:table-cell text-gray-600">
                    {ex.start_date && ex.end_date
                      ? `${ex.start_date} ～ ${ex.end_date}`
                      : ex.start_date ?? '—'}
                  </td>
                  <td className="px-4 py-4">
                    <span className={`inline-block text-xs font-semibold px-2.5 py-1 rounded-full border ${STATUS_COLORS[ex.status]}`}>
                      {STATUS_LABELS[ex.status] ?? ex.status}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-center hidden sm:table-cell">
                    <span className="font-semibold text-gray-700">{ex.contacts_count}</span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {NEXT_STATUS[ex.status] && (
                        <button
                          onClick={() => handleAdvanceStatus(ex)}
                          className="text-xs bg-green-50 text-green-700 border border-green-200 px-2.5 py-1 rounded-lg hover:bg-green-100 transition-colors hidden sm:block"
                        >
                          {NEXT_STATUS[ex.status]!.label}
                        </button>
                      )}
                      <button
                        onClick={() => openEdit(ex)}
                        className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1"
                      >
                        編輯
                      </button>
                      {ex.status === 'planning' && (
                        <button
                          onClick={() => handleDelete(ex.id)}
                          className="text-xs text-red-500 hover:text-red-700 px-2 py-1"
                        >
                          刪除
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create / Edit modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-5 border-b border-gray-100">
              <h2 className="text-lg font-bold text-gray-900">
                {editingId ? '編輯展覽資料' : '新增展覽活動'}
              </h2>
            </div>
            <div className="px-6 py-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">展覽名稱 *</label>
                <input
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. Hannover Messe 2026"
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">地點</label>
                  <input
                    value={form.location}
                    onChange={e => setForm(f => ({ ...f, location: e.target.value }))}
                    placeholder="Hannover, Germany"
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">攤位號碼</label>
                  <input
                    value={form.booth_number}
                    onChange={e => setForm(f => ({ ...f, booth_number: e.target.value }))}
                    placeholder="Hall 4, C22"
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">開始日期</label>
                  <input
                    type="date"
                    value={form.start_date}
                    onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">結束日期</label>
                  <input
                    type="date"
                    value={form.end_date}
                    onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">備註</label>
                <textarea
                  value={form.notes}
                  onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
                  rows={3}
                  placeholder="展前目標、ICP 策略…"
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                />
              </div>
              {error && <p className="text-xs text-red-600">{error}</p>}
            </div>
            <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
              <button
                onClick={() => { setShowForm(false); setError(null) }}
                className="text-sm text-gray-600 hover:text-gray-800 px-4 py-2"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !form.name.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
              >
                {saving ? '儲存中…' : '儲存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
