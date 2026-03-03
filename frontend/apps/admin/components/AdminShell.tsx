'use client'

import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'

const NAV_ITEMS = [
  { label: 'Dashboard',       href: '/',          icon: '📊' },
  { label: 'Suppliers',       href: '/suppliers',  icon: '🏭' },
  { label: 'Buyers',          href: '/buyers',     icon: '👤' },
  { label: 'Content Review',  href: '/content',    icon: '✍️' },
  { label: 'Outbound Health', href: '/outbound',   icon: '📡' },
  { label: 'API Usage',       href: '/api-usage',  icon: '⚡' },
  { label: 'Settings',        href: '/settings',   icon: '⚙️' },
]

function getToken() {
  if (typeof window === 'undefined') return null
  return (
    localStorage.getItem('token') ||
    localStorage.getItem('auth_token') ||
    localStorage.getItem('access_token') ||
    null
  )
}

export default function AdminShell({ children }: { children: React.ReactNode }) {
  const router   = useRouter()
  const pathname = usePathname() ?? ''

  useEffect(() => {
    if (pathname === '/login') return
    if (!getToken()) router.replace('/login')
  }, [pathname, router])

  // Don't wrap login page in the shell
  if (pathname === '/login') return <>{children}</>

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* ── Sidebar ── */}
      <aside className="w-56 bg-white border-r border-gray-200 min-h-screen flex flex-col py-6 shrink-0">
        <div className="px-6 mb-8">
          <h1 className="text-lg font-bold text-gray-900">Factory Insider</h1>
          <p className="text-xs text-purple-600 font-medium mt-0.5">Admin Console</p>
        </div>

        <nav className="flex-1 px-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === '/'
                ? pathname === '/'
                : pathname.startsWith(item.href)
            return (
              <a
                key={item.label}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? 'bg-purple-50 text-purple-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <span>{item.icon}</span>
                {item.label}
              </a>
            )
          })}
        </nav>

        <div className="px-6 pt-4 border-t border-gray-100 space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white text-xs font-bold">
              A
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Admin</p>
              <p className="text-xs text-gray-400">Super Admin</p>
            </div>
          </div>
          <button
            onClick={() => {
              localStorage.removeItem('token')
              localStorage.removeItem('auth_token')
              localStorage.removeItem('access_token')
              localStorage.removeItem('user')
              router.replace('/login')
            }}
            className="w-full text-left px-3 py-2 text-xs text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Page content ── */}
      <main className="flex-1 p-8 min-w-0">
        {children}
      </main>
    </div>
  )
}
