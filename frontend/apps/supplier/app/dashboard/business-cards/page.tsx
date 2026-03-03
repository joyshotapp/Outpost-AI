'use client'

import React, { useCallback, useEffect, useRef, useState } from 'react'

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface BusinessCard {
  id: number
  exhibition_id: number | null
  image_url: string | null
  full_name: string | null
  company_name: string | null
  job_title: string | null
  email: string | null
  phone: string | null
  website: string | null
  address: string | null
  country: string | null
  linkedin_url: string | null
  ocr_status: 'pending' | 'processing' | 'completed' | 'failed'
  ocr_confidence: number | null
  converted_to_contact: boolean
  follow_up_sent: boolean
  notes: string | null
  created_at: string
}

interface Exhibition {
  id: number
  name: string
}

// ─────────────────────────────────────────────────────────────────────────────
// API helpers
// ─────────────────────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

function authHeaders(): Record<string, string> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  const headers: Record<string, string> = {}
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
  if (options?.body && !(options.body instanceof FormData) && !('Content-Type' in mergedHeaders)) {
    mergedHeaders['Content-Type'] = 'application/json'
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: mergedHeaders,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  if (res.status === 204) return null as T
  return res.json()
}

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function ConfidenceBadge({ value }: { value: number | null }) {
  if (value === null) return null
  const pct = Math.round((value ?? 0) * 100)
  const color = pct >= 80 ? 'text-green-600 bg-green-50' : pct >= 50 ? 'text-amber-600 bg-amber-50' : 'text-red-500 bg-red-50'
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${color}`}>
      {pct}% 信心
    </span>
  )
}

function CardRow({ card, onConvert, onDelete }: {
  card: BusinessCard
  onConvert: (id: number) => void
  onDelete: (id: number) => void
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex gap-4 items-start hover:shadow-md transition-shadow">
      {/* Avatar / initials */}
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
        {(card.full_name ?? 'U').charAt(0).toUpperCase()}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-gray-900">{card.full_name ?? '—'}</span>
          <ConfidenceBadge value={card.ocr_confidence} />
          {card.ocr_status === 'failed' && (
            <span className="text-xs text-red-500 bg-red-50 px-2 py-0.5 rounded-full">OCR 失敗</span>
          )}
          {card.converted_to_contact && (
            <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full">✓ 已轉為聯絡人</span>
          )}
        </div>
        <div className="text-sm text-gray-500 mt-0.5">
          {[card.job_title, card.company_name].filter(Boolean).join(' · ') || '—'}
        </div>
        <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-500">
          {card.email && (
            <a href={`mailto:${card.email}`} className="hover:text-blue-600 flex items-center gap-1">
              ✉ {card.email}
            </a>
          )}
          {card.phone && <span>📞 {card.phone}</span>}
          {card.country && <span>🌍 {card.country}</span>}
          {card.linkedin_url && (
            <a href={card.linkedin_url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600">
              LinkedIn ↗
            </a>
          )}
        </div>
      </div>
      <div className="flex flex-col gap-1 items-end flex-shrink-0">
        {!card.converted_to_contact && card.email && (
          <button
            onClick={() => onConvert(card.id)}
            className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-lg hover:bg-blue-100 transition-colors whitespace-nowrap"
          >
            轉為聯絡人
          </button>
        )}
        <button
          onClick={() => onDelete(card.id)}
          className="text-xs text-red-400 hover:text-red-600 px-2 py-1"
        >
          刪除
        </button>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

export default function BusinessCardsPage() {
  const [cards, setCards] = useState<BusinessCard[]>([])
  const [exhibitions, setExhibitions] = useState<Exhibition[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<string | null>(null)
  const [selectedExhibitionId, setSelectedExhibitionId] = useState<number | ''>('')
  const [filterExhibitionId, setFilterExhibitionId] = useState<number | ''>('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  const loadCards = useCallback(async () => {
    setLoading(true)
    try {
      const url = filterExhibitionId
        ? `/business-cards?exhibition_id=${filterExhibitionId}`
        : '/business-cards'
      const data = await apiFetch<BusinessCard[]>(url)
      setCards(data)
    } catch {
      // Demo data
      setCards([
        {
          id: 1, exhibition_id: 1, image_url: null,
          full_name: 'Klaus Müller', company_name: 'Müller Maschinenbau GmbH', job_title: 'Procurement Manager',
          email: 'k.mueller@muellermb.de', phone: '+49 511 123456', website: 'www.muellermb.de',
          address: 'Hannover, Germany', country: 'Germany', linkedin_url: null,
          ocr_status: 'completed', ocr_confidence: 0.92, converted_to_contact: false,
          follow_up_sent: false, notes: null, created_at: new Date().toISOString(),
        },
        {
          id: 2, exhibition_id: 1, image_url: null,
          full_name: 'Yuki Tanaka', company_name: 'Tanaka Industries', job_title: 'Supply Chain Director',
          email: 'y.tanaka@tanaka-ind.co.jp', phone: null, website: null,
          address: 'Tokyo, Japan', country: 'Japan', linkedin_url: null,
          ocr_status: 'completed', ocr_confidence: 0.78, converted_to_contact: true,
          follow_up_sent: true, notes: '對精密零件有興趣', created_at: new Date(Date.now() - 3600000).toISOString(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }, [filterExhibitionId])

  const loadExhibitions = async () => {
    try {
      const data = await apiFetch<Exhibition[]>('/exhibitions')
      setExhibitions(data)
    } catch {
      setExhibitions([
        { id: 1, name: 'Hannover Messe 2026' },
        { id: 2, name: 'TWTC Taiwan Machine Tool Show' },
      ])
    }
  }

  useEffect(() => {
    loadCards()
    loadExhibitions()
  }, [loadCards])

  const handleFileUpload = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('請上傳圖片檔案 (JPEG / PNG / WebP)')
      return
    }
    setUploading(true)
    setUploadProgress('正在處理名片 OCR…')
    setError(null)

    const form = new FormData()
    form.append('image', file)
    if (selectedExhibitionId) form.append('exhibition_id', String(selectedExhibitionId))

    try {
      const card = await fetch(`${API_BASE}/business-cards/scan`, {
        method: 'POST',
        headers: authHeaders(),
        body: form,
      }).then(async res => {
        if (!res.ok) throw new Error(await res.text())
        return res.json() as Promise<BusinessCard>
      })
      setCards(prev => [card, ...prev])
      setUploadProgress(null)
    } catch (err) {
      setError(String(err))
      setUploadProgress(null)
    } finally {
      setUploading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFileUpload(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFileUpload(file)
  }

  const handleConvert = async (cardId: number) => {
    try {
      await apiFetch(`/business-cards/${cardId}/convert-to-lead`, { method: 'POST' })
      setCards(prev => prev.map(c => c.id === cardId ? { ...c, converted_to_contact: true } : c))
    } catch (err) {
      setError(String(err))
    }
  }

  const handleDelete = async (cardId: number) => {
    if (!confirm('確定刪除？')) return
    try {
      await apiFetch(`/business-cards/${cardId}`, { method: 'DELETE' })
      setCards(prev => prev.filter(c => c.id !== cardId))
    } catch (err) {
      setError(String(err))
    }
  }

  const completedCards = cards.filter(c => c.ocr_status === 'completed').length
  const convertedCards = cards.filter(c => c.converted_to_contact).length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📇 名片掃描</h1>
          <p className="text-sm text-gray-500 mt-1">拍照上傳 → Claude Vision OCR → 建立 CRM 聯絡人</p>
        </div>
        {/* Stats */}
        <div className="flex gap-4 text-sm">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-800">{cards.length}</div>
            <div className="text-xs text-gray-500">總名片</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{completedCards}</div>
            <div className="text-xs text-gray-500">OCR 完成</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{convertedCards}</div>
            <div className="text-xs text-gray-500">已轉聯絡人</div>
          </div>
        </div>
      </div>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">
          ⚠ {error}
        </div>
      )}

      {/* Upload zone */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">上傳名片圖片</h2>

        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <select
            value={selectedExhibitionId}
            onChange={e => setSelectedExhibitionId(e.target.value ? Number(e.target.value) : '')}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="">不關聯展覽</option>
            {exhibitions.map(ex => (
              <option key={ex.id} value={ex.id}>{ex.name}</option>
            ))}
          </select>
          <p className="text-xs text-gray-400 self-center">（可選）選擇展覽以歸類名片</p>
        </div>

        {/* Drop zone */}
        <div
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
            dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
          }`}
        >
          {uploading ? (
            <div className="flex flex-col items-center gap-2 text-blue-600">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
              <p className="text-sm font-medium">{uploadProgress ?? '上傳中…'}</p>
            </div>
          ) : (
            <>
              <div className="text-5xl mb-3">📷</div>
              <p className="text-sm font-medium text-gray-600">拖曳圖片到這裡，或點擊選擇檔案</p>
              <p className="text-xs text-gray-400 mt-1">支援 JPEG、PNG、WebP（最大 10 MB）</p>
            </>
          )}
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={handleInputChange}
        />
      </div>

      {/* Filter */}
      {exhibitions.length > 0 && (
        <div className="flex gap-2 flex-wrap items-center">
          <span className="text-xs text-gray-500">篩選展覽：</span>
          <button
            onClick={() => setFilterExhibitionId('')}
            className={`text-xs px-3 py-1 rounded-full border font-medium transition-colors ${
              filterExhibitionId === '' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
            }`}
          >
            全部
          </button>
          {exhibitions.map(ex => (
            <button
              key={ex.id}
              onClick={() => setFilterExhibitionId(ex.id)}
              className={`text-xs px-3 py-1 rounded-full border font-medium transition-colors ${
                filterExhibitionId === ex.id ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
              }`}
            >
              {ex.name}
            </button>
          ))}
        </div>
      )}

      {/* Cards list */}
      {loading ? (
        <div className="flex items-center justify-center h-40 text-gray-400">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3" />
          載入中…
        </div>
      ) : cards.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p className="text-4xl mb-3">📇</p>
          <p className="text-lg font-medium">尚無名片資料</p>
          <p className="text-sm mt-1">上傳名片圖片開始建立聯絡人資料庫</p>
        </div>
      ) : (
        <div className="space-y-3">
          {cards.map(card => (
            <CardRow key={card.id} card={card} onConvert={handleConvert} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  )
}
