'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { io, Socket } from 'socket.io-client'

interface AIAvatarWidgetProps {
  supplierId: number
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function AIAvatarWidget({ supplierId }: AIAvatarWidgetProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [language, setLanguage] = useState('en')
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'Hi, I am your AI procurement assistant. Ask me about products, lead time, and capabilities.' },
  ])
  const [isTyping, setIsTyping] = useState(false)

  const socketRef = useRef<Socket | null>(null)
  const scrollRef = useRef<HTMLDivElement | null>(null)

  const visitorSessionId = useMemo(() => {
    if (typeof window === 'undefined') {
      return ''
    }
    const key = 'fi_visitor_session_id'
    const existing = window.localStorage.getItem(key)
    if (existing) {
      return existing
    }
    const generated = `visitor-${crypto.randomUUID()}`
    window.localStorage.setItem(key, generated)
    return generated
  }, [])

  // Connect to Socket.IO only when the widget is opened for the first time,
  // and disconnect when it is closed. This avoids creating persistent WebSocket
  // connections on pages where the widget is never interacted with.
  useEffect(() => {
    if (!isOpen) {
      return
    }

    if (socketRef.current) {
      // Already connected from a previous open – nothing to do.
      return
    }

    const socket = io(API_BASE_URL, {
      path: '/ws/socket.io',
      transports: ['websocket'],
    })

    socket.on('chat:response', (payload: { answer: string }) => {
      setMessages((prev) => [...prev, { role: 'assistant', content: payload.answer }])
      setIsTyping(false)
    })

    socket.on('chat:error', (payload: { error: string }) => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `System error: ${payload.error}` },
      ])
      setIsTyping(false)
    })

    socketRef.current = socket

    return () => {
      socket.disconnect()
      socketRef.current = null
    }
  }, [isOpen])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isTyping])

  const handleSend = () => {
    const question = input.trim()
    if (!question || !socketRef.current) {
      return
    }

    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setInput('')
    setIsTyping(true)

    socketRef.current.emit('chat:message', {
      supplier_id: supplierId,
      question,
      language,
      visitor_session_id: visitorSessionId,
    })
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {!isOpen ? (
        <button
          onClick={() => setIsOpen(true)}
          className="rounded-full bg-primary-600 text-white px-5 py-3 shadow-lg hover:bg-primary-700 transition-colors"
        >
          AI Assistant
        </button>
      ) : (
        <div className="w-[360px] bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden">
          <div className="px-4 py-3 bg-primary-600 text-white flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold">AI Procurement Assistant</p>
              <p className="text-xs opacity-90">24/7 supplier Q&A</p>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-sm font-semibold">×</button>
          </div>

          <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
            <label className="text-xs text-gray-600 mr-2">Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="en">English</option>
              <option value="de">Deutsch</option>
              <option value="ja">日本語</option>
              <option value="es">Español</option>
              <option value="auto">Auto Detect</option>
            </select>
          </div>

          <div ref={scrollRef} className="h-80 overflow-y-auto px-4 py-3 space-y-3 bg-white">
            {messages.map((msg, index) => (
              <div
                key={`${msg.role}-${index}`}
                className={`max-w-[85%] px-3 py-2 rounded-lg text-sm whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'ml-auto bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                {msg.content}
              </div>
            ))}
            {isTyping && (
              <div className="bg-gray-100 text-gray-900 rounded-lg px-3 py-2 text-sm w-fit">
                <span className="inline-flex gap-1">
                  <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" />
                  <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce [animation-delay:120ms]" />
                  <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce [animation-delay:240ms]" />
                </span>
              </div>
            )}
          </div>

          <div className="p-3 border-t border-gray-200 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  handleSend()
                }
              }}
              placeholder="Ask about MOQ, lead time, materials..."
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300"
            />
            <button
              onClick={handleSend}
              className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
