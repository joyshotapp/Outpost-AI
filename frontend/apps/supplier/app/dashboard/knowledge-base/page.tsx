'use client'

import { FormEvent, useCallback, useEffect, useState } from 'react'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Defined outside the component — no state dependencies.
function getHeaders() {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }
}

interface KnowledgeDocument {
  id: number
  title: string
  source_type: string
  language: string
  status: string
  chunk_count: number
  created_at: string
  error_message?: string | null
}

export default function KnowledgeBasePage() {
  const [supplierId, setSupplierId] = useState<number | null>(null)
  const [namespace, setNamespace] = useState('')
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const [title, setTitle] = useState('')
  const [sourceType, setSourceType] = useState('catalog')
  const [language, setLanguage] = useState('en')
  const [textContent, setTextContent] = useState('')
  const [sourceS3Key, setSourceS3Key] = useState('')

  const loadContextAndDocuments = useCallback(async () => {
    setLoading(true)
    setMessage('')
    try {
      const contextRes = await fetch(`${API_BASE_URL}/api/v1/knowledge-base/me`, {
        headers: getHeaders(),
      })
      if (!contextRes.ok) {
        throw new Error('Failed to load supplier knowledge context')
      }
      const contextData = await contextRes.json()
      setSupplierId(contextData.supplier_id)
      setNamespace(contextData.namespace)

      const docsRes = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-base/documents?supplier_id=${contextData.supplier_id}`,
        { headers: getHeaders() }
      )
      if (!docsRes.ok) {
        throw new Error('Failed to load knowledge documents')
      }
      const docs = await docsRes.json()
      setDocuments(docs)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Failed to load knowledge base')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadContextAndDocuments()
  }, [loadContextAndDocuments])

  const handleInitNamespace = async () => {
    if (!supplierId) {
      return
    }
    setMessage('')
    const res = await fetch(
      `${API_BASE_URL}/api/v1/knowledge-base/suppliers/${supplierId}/namespace/init`,
      { method: 'POST', headers: getHeaders() }
    )
    if (!res.ok) {
      setMessage('Failed to initialize namespace')
      return
    }
    setMessage('Namespace initialized successfully')
    await loadContextAndDocuments()
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!supplierId) {
      return
    }

    setMessage('')

    const payload = {
      supplier_id: supplierId,
      title,
      source_type: sourceType,
      language,
      text_content: textContent || null,
      source_s3_key: sourceS3Key || null,
    }

    const res = await fetch(`${API_BASE_URL}/api/v1/knowledge-base/documents`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => null)
      setMessage(err?.detail || 'Failed to create knowledge document')
      return
    }

    setTitle('')
    setTextContent('')
    setSourceS3Key('')
    setMessage('Knowledge document queued for indexing')
    await loadContextAndDocuments()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-h1 font-bold text-gray-900">Knowledge Base</h1>
          <p className="text-body-lg text-gray-600 mt-2">
            Manage AI avatar knowledge sources and indexing status
          </p>
        </div>
        <button
          onClick={handleInitNamespace}
          className="px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700"
          disabled={!supplierId}
        >
          Initialize Namespace
        </button>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <p className="text-sm text-gray-700">
          Supplier ID: <span className="font-semibold">{supplierId ?? '-'}</span>
        </p>
        <p className="text-sm text-gray-700 mt-1">
          Namespace: <span className="font-semibold">{namespace || '-'}</span>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
        <h2 className="text-h2 font-semibold text-gray-900">Add Knowledge Document</h2>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
            required
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Source Type</label>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="catalog">catalog</option>
              <option value="manual">manual</option>
              <option value="faq">faq</option>
              <option value="transcript">transcript</option>
              <option value="other">other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="en">en</option>
              <option value="de">de</option>
              <option value="ja">ja</option>
              <option value="es">es</option>
              <option value="zh">zh</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Text Content</label>
          <textarea
            value={textContent}
            onChange={(e) => setTextContent(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 min-h-32"
            placeholder="Paste transcript/catalog text here"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Source S3 Key (optional)</label>
          <input
            value={sourceS3Key}
            onChange={(e) => setSourceS3Key(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
            placeholder="documents/123/catalog.pdf"
          />
        </div>

        <button className="px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700">
          Submit for Indexing
        </button>
      </form>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-h2 font-semibold text-gray-900">Indexed Documents</h2>
          <button
            onClick={loadContextAndDocuments}
            className="px-3 py-1.5 rounded border border-gray-300 text-sm text-gray-700 hover:bg-gray-50"
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <p className="text-sm text-gray-600">Loading...</p>
        ) : documents.length === 0 ? (
          <p className="text-sm text-gray-600">No knowledge documents yet.</p>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <div key={doc.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-gray-900">{doc.title}</h3>
                  <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700">{doc.status}</span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {doc.source_type} · {doc.language} · chunks: {doc.chunk_count}
                </p>
                {doc.error_message && (
                  <p className="text-sm text-red-600 mt-2">Error: {doc.error_message}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {message && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          {message}
        </div>
      )}
    </div>
  )
}
