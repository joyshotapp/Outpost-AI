'use client'

import React, { useEffect, useMemo, useRef, useState } from 'react'
import Link from 'next/link'
import { io, Socket } from 'socket.io-client'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'

interface HeaderProps {
  sidebarOpen: boolean
  onToggleSidebar: () => void
}

export default function Header({ sidebarOpen, onToggleSidebar }: HeaderProps) {
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [notificationCount, setNotificationCount] = useState(0)
  const socketRef = useRef<Socket | null>(null)

  const token = useMemo(() => {
    if (typeof window === 'undefined') {
      return null
    }
    return localStorage.getItem('access_token')
  }, [])

  useEffect(() => {
    if (!token) {
      return
    }

    const fetchUnreadCount = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/notifications?unread_only=true&limit=100`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        if (!response.ok) {
          return
        }
        const notifications = await response.json()
        if (Array.isArray(notifications)) {
          setNotificationCount(notifications.length)
        }
      } catch {
        // Ignore notification fetch failures in header.
      }
    }

    const setupSocket = async () => {
      try {
        const summaryResponse = await fetch(`${API_BASE_URL}/visitor-intent/summary`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        if (!summaryResponse.ok) {
          return
        }
        const summary = await summaryResponse.json()
        const supplierId = summary?.supplier_id
        if (!supplierId) {
          return
        }

        const socket = io(API_BASE_URL, {
          path: '/ws/socket.io',
          transports: ['websocket'],
          auth: {
            token: `Bearer ${token}`,
          },
        })

        socket.on('connect', () => {
          socket.emit('notification:subscribe', { supplier_id: supplierId })
        })

        socket.on('notification:new', () => {
          setNotificationCount((prev) => prev + 1)
        })

        socketRef.current = socket
      } catch {
        // Ignore socket setup failures in header.
      }
    }

    fetchUnreadCount()
    setupSocket()

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect()
        socketRef.current = null
      }
    }
  }, [token])

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 flex-shrink-0">
      {/* Left side - Menu toggle */}
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          <svg
            className="w-5 h-5 text-gray-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </button>

        {/* Page title placeholder */}
        <div className="text-gray-600 text-sm">
          {/* Page-specific title would be passed from child components */}
        </div>
      </div>

      {/* Right side - Search, notifications, user menu */}
      <div className="flex items-center gap-6">
        {/* Search */}
        <div className="hidden md:flex items-center bg-gray-100 rounded-lg px-3 py-2">
          <svg
            className="w-4 h-4 text-gray-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
              clipRule="evenodd"
            />
          </svg>
          <input
            type="text"
            placeholder="Search..."
            className="bg-gray-100 ml-2 outline-none text-sm text-gray-700 placeholder-gray-500"
          />
        </div>

        {/* Notifications */}
        <button className="relative p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
          <svg
            className="w-5 h-5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M10.5 1.5H9.5A1.5 1.5 0 008 3v1a1 1 0 01-1 1H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-1a1 1 0 01-1-1V3a1.5 1.5 0 00-1.5-1.5zM4 8a.5.5 0 100 1h12a.5.5 0 100-1H4zm0 3a.5.5 0 100 1h12a.5.5 0 100-1H4zm0 3a.5.5 0 100 1h12a.5.5 0 100-1H4z" />
          </svg>
          {notificationCount > 0 && (
            <>
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
              <span className="absolute -top-1 -right-1 min-w-4 h-4 px-1 rounded-full bg-red-600 text-white text-[10px] leading-4 text-center">
                {notificationCount > 99 ? '99+' : notificationCount}
              </span>
            </>
          )}
        </button>

        {/* User Menu */}
        <div className="relative">
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
              A
            </div>
            <div className="hidden md:flex flex-col items-start">
              <span className="text-sm font-medium text-gray-900">ABC Company</span>
              <span className="text-xs text-gray-500">Admin</span>
            </div>
            <svg
              className={`w-4 h-4 text-gray-600 transition-transform ${
                userMenuOpen ? 'transform rotate-180' : ''
              }`}
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>

          {/* User Menu Dropdown */}
          {userMenuOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg z-10 border border-gray-200">
              <Link
                href="/dashboard/profile"
                className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 border-b border-gray-200"
              >
                My Profile
              </Link>
              <Link
                href="/dashboard/settings"
                className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 border-b border-gray-200"
              >
                Settings
              </Link>
              <button className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100">
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
