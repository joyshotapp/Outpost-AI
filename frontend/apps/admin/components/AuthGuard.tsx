'use client'

import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'

export function getAdminToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('token') || localStorage.getItem('auth_token') || null
}

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (pathname === '/login') return
    const token = getAdminToken()
    if (!token) {
      router.replace('/login')
    }
  }, [pathname, router])

  return <>{children}</>
}
