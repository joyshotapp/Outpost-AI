'use client'

import Link from 'next/link'
import { useEffect, useRef, useState } from 'react'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Conversation {
  id: number
  supplier_name: string
  last_message_preview: string
  last_message_at: string
  unread_count: number
  status: string
}

interface Message {
  id: number
  sender_type: 'buyer' | 'supplier' | 'system'
  body: string
  created_at: string
  is_read: boolean
}

// ── Demo data ──────────────────────────────────────────────────────────────────

const DEMO_CONVERSATIONS: Conversation[] = [
  { id: 1, supplier_name: 'Precision Parts Co', last_message_preview: 'Sure, we can provide ISO 9001 certs along with the custom quote.', last_message_at: '2 min ago', unread_count: 2, status: 'active' },
  { id: 2, supplier_name: 'TechForge GmbH', last_message_preview: 'We have availability for Q2 2025. Lead time is 18 days.', last_message_at: '1 hr ago', unread_count: 0, status: 'active' },
  { id: 3, supplier_name: 'AsiaMetals Ltd', last_message_preview: 'Thank you for reaching out. Our min order quantity is 500 pcs.', last_message_at: 'Yesterday', unread_count: 0, status: 'active' },
  { id: 4, supplier_name: 'Nordic Precision', last_message_preview: 'Please confirm the alloy grade — Ti-6Al-4V or Ti-3Al-2.5V?', last_message_at: '3 days ago', unread_count: 1, status: 'active' },
]

function generateDemoMessages(supplierName: string): Message[] {
  const now = new Date()
  return [
    { id: 1, sender_type: 'buyer', body: `Hi, we're interested in sourcing from ${supplierName}. Could you share your product catalogue for CNC machined parts?`, created_at: formatTime(new Date(now.getTime() - 3 * 3600000)), is_read: true },
    { id: 2, sender_type: 'supplier', body: 'Thank you for reaching out! Happy to share details. We specialise in CNC milling and turning with tolerances down to ±0.01mm. What material and quantity are you looking at?', created_at: formatTime(new Date(now.getTime() - 2.5 * 3600000)), is_read: true },
    { id: 3, sender_type: 'buyer', body: 'We need aluminium 6061-T6 housing parts, approximately 500 units per month. Do you hold ISO 9001 certification?', created_at: formatTime(new Date(now.getTime() - 2 * 3600000)), is_read: true },
    { id: 4, sender_type: 'supplier', body: 'Yes, we are ISO 9001:2015 certified. For 500 units/month, we can offer a unit price of €4.20 with a 14-day lead time. Shall I prepare a formal quotation?', created_at: formatTime(new Date(now.getTime() - 30 * 60000)), is_read: true },
    { id: 5, sender_type: 'buyer', body: 'That sounds good. Please send a formal quote including packing and shipping to Germany.', created_at: formatTime(new Date(now.getTime() - 10 * 60000)), is_read: true },
  ]
}

function formatTime(d: Date): string {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

// ── Message Bubble ─────────────────────────────────────────────────────────────

function MessageBubble({ msg }: { msg: Message }) {
  const isBuyer = msg.sender_type === 'buyer'
  return (
    <div className={`flex ${isBuyer ? 'justify-end' : 'justify-start'} mb-3`}>
      <div className={`max-w-xs md:max-w-md lg:max-w-lg rounded-2xl px-4 py-3 text-sm leading-relaxed ${
        isBuyer
          ? 'bg-primary-700 text-white rounded-br-sm'
          : msg.sender_type === 'system'
          ? 'bg-gray-100 text-gray-500 rounded text-xs text-center mx-auto'
          : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm'
      }`}>
        {msg.body}
        <div className={`text-xs mt-1 ${isBuyer ? 'text-primary-200' : 'text-gray-400'} text-right`}>{msg.created_at}</div>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function MessagesPage() {
  const [conversations] = useState<Conversation[]>(DEMO_CONVERSATIONS)
  const [activeConvId, setActiveConvId] = useState<number>(1)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  const activeConv = conversations.find(c => c.id === activeConvId)

  useEffect(() => {
    if (activeConv) setMessages(generateDemoMessages(activeConv.supplier_name))
  }, [activeConvId])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sending) return
    setSending(true)
    const newMsg: Message = {
      id: Date.now(),
      sender_type: 'buyer',
      body: input.trim(),
      created_at: formatTime(new Date()),
      is_read: false,
    }
    setMessages(prev => [...prev, newMsg])
    setInput('')
    setSending(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Nav */}
      <header className="bg-white border-b z-20">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-5 text-sm">
          <Link href="/" className="font-bold text-primary-700 text-base">Factory Insider</Link>
          <Link href="/dashboard" className="text-gray-600 hover:text-primary-700">← Dashboard</Link>
          <span className="font-medium text-gray-900">Messages</span>
        </div>
      </header>

      <div className="flex flex-1 max-w-7xl mx-auto w-full px-4 py-4 gap-4" style={{ height: 'calc(100vh - 56px)' }}>
        {/* Conversation List */}
        <aside className="w-72 flex-shrink-0 bg-white border border-gray-200 rounded-xl overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b">
            <h2 className="font-semibold text-gray-900 text-sm">Conversations</h2>
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-gray-50">
            {conversations.map(conv => (
              <button
                key={conv.id}
                onClick={() => setActiveConvId(conv.id)}
                className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${activeConvId === conv.id ? 'bg-primary-50 border-l-2 border-primary-700' : ''}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-sm font-semibold truncate ${activeConvId === conv.id ? 'text-primary-700' : 'text-gray-800'}`}>
                    {conv.supplier_name}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {conv.unread_count > 0 && (
                      <span className="w-4 h-4 text-xs font-bold bg-red-500 text-white rounded-full flex items-center justify-center flex-shrink-0">{conv.unread_count}</span>
                    )}
                    <span className="text-xs text-gray-400 whitespace-nowrap">{conv.last_message_at}</span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 truncate">{conv.last_message_preview}</p>
              </button>
            ))}
          </div>
        </aside>

        {/* Chat Panel */}
        <div className="flex-1 min-w-0 bg-white border border-gray-200 rounded-xl flex flex-col overflow-hidden">
          {/* Chat header */}
          <div className="px-5 py-3 border-b flex items-center justify-between">
            <div>
              <div className="font-semibold text-gray-900">{activeConv?.supplier_name}</div>
              <div className="text-xs text-green-600">● Active</div>
            </div>
            <div className="flex gap-2">
              <Link
                href={activeConv ? `/suppliers/${activeConv.supplier_name.toLowerCase().replace(/\s+/g, '-')}` : '/suppliers'}
                className="px-3 py-1.5 text-xs border border-gray-300 rounded-lg text-gray-600 hover:border-primary-400 hover:text-primary-700"
              >
                View Profile
              </Link>
              <Link
                href="/rfq/new"
                className="px-3 py-1.5 text-xs bg-primary-700 text-white rounded-lg hover:bg-primary-600"
              >
                Send RFQ
              </Link>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-5 py-4 bg-gray-50">
            {messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)}
            <div ref={endRef} />
          </div>

          {/* Input */}
          <form onSubmit={sendMessage} className="px-4 py-3 border-t bg-white flex gap-2 items-end">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(e as any) } }}
              placeholder="Type a message... (Enter to send)"
              rows={1}
              className="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-primary-400 resize-none"
              style={{ maxHeight: '120px', overflowY: 'auto' }}
            />
            <button
              type="submit"
              disabled={!input.trim() || sending}
              className="px-4 py-2.5 bg-primary-700 text-white rounded-xl text-sm font-medium hover:bg-primary-600 disabled:opacity-40"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
