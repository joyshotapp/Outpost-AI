'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface SidebarProps {
  open: boolean
}

interface NavItem {
  label: string
  href: string
  icon: React.ReactNode
  children?: NavItem[]
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: (
      <svg
        className="w-5 h-5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
      </svg>
    ),
  },
  {
    label: 'Company Profile',
    href: '/dashboard/profile',
    icon: (
      <svg
        className="w-5 h-5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    label: 'Videos',
    href: '/dashboard/videos',
    icon: (
      <svg
        className="w-5 h-5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path d="M2 6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm4 2v4h8V8H6z" />
      </svg>
    ),
  },
  {
    label: 'Knowledge Base',
    href: '/dashboard/knowledge-base',
    icon: (
      <svg
        className="w-5 h-5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm-1 3a1 1 0 112 0v4a1 1 0 11-2 0V5zm1 10a1.25 1.25 0 110-2.5A1.25 1.25 0 0110 15z" />
      </svg>
    ),
  },
  {
    label: 'Visitor Intent',
    href: '/dashboard/visitor-intent',
    icon: (
      <svg
        className="w-5 h-5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path d="M10 3a7 7 0 100 14 7 7 0 000-14zm0 2a1 1 0 011 1v3.382l2.447 1.224a1 1 0 11-.894 1.788l-3-1.5A1 1 0 019 10V6a1 1 0 011-1z" />
      </svg>
    ),
  },
  {
    label: 'Inquiries',
    href: '/dashboard/inquiries',
    icon: (
      <svg
        className="w-5 h-5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path d="M2.5 3A1.5 1.5 0 001 4.5v.793c.026.009.051.02.076.032a.75.75 0 00.658.482 60.456 60.456 0 014.064-.053.75.75 0 00.658-.482c.025-.012.05-.023.076-.032V4.5A1.5 1.5 0 002.5 3zM1 7.75V19.5A1.5 1.5 0 002.5 21h15A1.5 1.5 0 0019 19.5V7.75c-.345.104-.681.227-1 .367V19.5H2.5V7.75c-.319-.14-.655-.263-1-.367z" />
      </svg>
    ),
  },
  {
    label: 'Orders',
    href: '/dashboard/orders',
    icon: (
      <svg
        className="w-5 h-5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.5.5 0 00.487.358h12.382a.5.5 0 00.494-.574l-2-10A.5.5 0 0015.35 3H4.196a.5.5 0 00-.487.358L2.293 2H1a1 1 0 000 2h1l3.355 16.954a.5.5 0 00.487.358h10.516a.5.5 0 00.487-.358L17.707 5H16a1 1 0 100-2h1.293l-.305-1.222A.5.5 0 0015.382 1H3z" />
      </svg>
    ),
  },
  {
    label: 'Analytics',
    href: '/dashboard/analytics',
    icon: (
      <svg
        className="w-5 h-5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
      </svg>
    ),
  },
  {
    label: 'Settings',
    href: '/dashboard/settings',
    icon: (
      <svg
        className="w-5 h-5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path
          fillRule="evenodd"
          d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
]

export default function Sidebar({ open }: SidebarProps) {
  const pathname = usePathname()

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard'
    }
    return pathname.startsWith(href)
  }

  return (
    <aside
      className={`${
        open ? 'w-64' : 'w-20'
      } bg-gray-900 text-gray-100 transition-all duration-300 flex flex-col overflow-hidden`}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-center border-b border-gray-800 flex-shrink-0">
        <Link href="/" className="flex items-center gap-2">
          {open && (
            <>
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center font-bold text-sm">
                FI
              </div>
              <span className="font-semibold text-sm">Factory</span>
            </>
          )}
          {!open && (
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center font-bold text-sm">
              F
            </div>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-6 space-y-2 overflow-y-auto">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive(item.href)
                ? 'bg-primary-600 text-white'
                : 'text-gray-300 hover:bg-gray-800'
            }`}
            title={!open ? item.label : undefined}
          >
            {item.icon}
            {open && <span>{item.label}</span>}
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-gray-800">
        <button
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-800 transition-colors"
          title="Logout"
        >
          <svg
            className="w-5 h-5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z"
              clipRule="evenodd"
            />
          </svg>
          {open && <span>Logout</span>}
        </button>
      </div>
    </aside>
  )
}
