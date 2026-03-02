/**
 * Simple i18n helper for Factory Insider buyer app.
 * Loads messages from the /messages/{locale}.json files at runtime.
 *
 * Usage (client component):
 *   import { useT } from '@/lib/i18n'
 *   const t = useT()
 *   <h1>{t('home.heroTitle')}</h1>
 *
 * Supported locales: en (default), zh, de, ja, es
 *
 * Note: Full next-intl App Router integration (with [locale] routing) requires
 * restructuring the app directory. This helper provides a simpler client-side
 * approach for the Sprint 10 MVP while the full locale routing is planned for
 * Sprint 11.
 */

'use client'

import { useCallback, useEffect, useState } from 'react'

export const SUPPORTED_LOCALES = ['en', 'zh', 'de', 'ja', 'es'] as const
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number]

const DEFAULT_LOCALE: SupportedLocale = 'en'

// In-memory cache so JSON is fetched once per locale per session
const _cache: Partial<Record<SupportedLocale, Record<string, unknown>>> = {}

function detectLocale(): SupportedLocale {
  if (typeof window === 'undefined') return DEFAULT_LOCALE
  const lang = navigator.language?.split('-')[0] as SupportedLocale
  return SUPPORTED_LOCALES.includes(lang) ? lang : DEFAULT_LOCALE
}

async function loadMessages(locale: SupportedLocale): Promise<Record<string, unknown>> {
  if (_cache[locale]) return _cache[locale]!
  try {
    const res = await fetch(`/messages/${locale}.json`)
    if (!res.ok) throw new Error()
    const data = await res.json()
    _cache[locale] = data
    return data
  } catch {
    // Fallback to English
    if (locale !== DEFAULT_LOCALE) return loadMessages(DEFAULT_LOCALE)
    return {}
  }
}

/** Deeply resolve a dot-notation key like "home.heroTitle" */
function resolve(msgs: Record<string, unknown>, key: string): string {
  const parts = key.split('.')
  let cur: unknown = msgs
  for (const part of parts) {
    if (cur == null || typeof cur !== 'object') return key
    cur = (cur as Record<string, unknown>)[part]
  }
  return typeof cur === 'string' ? cur : key
}

export function useT(overrideLocale?: SupportedLocale) {
  const [msgs, setMsgs] = useState<Record<string, unknown>>(_cache[DEFAULT_LOCALE] || {})

  useEffect(() => {
    const locale = overrideLocale || detectLocale()
    loadMessages(locale).then(setMsgs)
  }, [overrideLocale])

  return useCallback(
    (key: string, vars?: Record<string, string | number>): string => {
      let result = resolve(msgs, key)
      if (vars) {
        Object.entries(vars).forEach(([k, v]) => {
          result = result.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v))
        })
      }
      return result
    },
    [msgs]
  )
}

export function useLocale(): SupportedLocale {
  const [locale, setLocale] = useState<SupportedLocale>(DEFAULT_LOCALE)
  useEffect(() => { setLocale(detectLocale()) }, [])
  return locale
}
