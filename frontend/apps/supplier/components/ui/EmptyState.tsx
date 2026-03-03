/**
 * EmptyState — contextual empty screens with SVG illustrations.
 */

interface EmptyStateProps {
  type?: 'rfq' | 'orders' | 'analytics' | 'outbound' | 'generic'
  title?: string
  description?: string
  action?: { label: string; href?: string; onClick?: () => void }
}

const ILLUSTRATIONS: Record<string, React.ReactNode> = {
  rfq: (
    <svg viewBox="0 0 120 100" className="w-32 h-28" fill="none">
      <rect x="15" y="10" width="90" height="70" rx="8" fill="#E8F4F8" stroke="#7CBFD4" strokeWidth="2"/>
      <rect x="28" y="26" width="40" height="6" rx="3" fill="#7CBFD4"/>
      <rect x="28" y="38" width="64" height="4" rx="2" fill="#d1e9f0"/>
      <rect x="28" y="48" width="50" height="4" rx="2" fill="#d1e9f0"/>
      <rect x="28" y="58" width="56" height="4" rx="2" fill="#d1e9f0"/>
      <circle cx="92" cy="72" r="18" fill="#2B7FA3"/>
      <path d="M85 72h14M92 65v14" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
    </svg>
  ),
  orders: (
    <svg viewBox="0 0 120 100" className="w-32 h-28" fill="none">
      <rect x="20" y="15" width="80" height="65" rx="8" fill="#E8F4F8" stroke="#7CBFD4" strokeWidth="2"/>
      <path d="M40 35h40M40 48h30M40 61h20" stroke="#7CBFD4" strokeWidth="2.5" strokeLinecap="round"/>
      <circle cx="33" cy="35" r="4" fill="#2B7FA3"/>
      <circle cx="33" cy="48" r="4" fill="#2B7FA3"/>
      <circle cx="33" cy="61" r="4" fill="#2B7FA3"/>
    </svg>
  ),
  analytics: (
    <svg viewBox="0 0 120 100" className="w-32 h-28" fill="none">
      <rect x="10" y="60" width="16" height="28" rx="3" fill="#7CBFD4"/>
      <rect x="32" y="44" width="16" height="44" rx="3" fill="#2B7FA3"/>
      <rect x="54" y="30" width="16" height="58" rx="3" fill="#1B5E7F"/>
      <rect x="76" y="50" width="16" height="38" rx="3" fill="#2B7FA3"/>
      <rect x="98" y="20" width="16" height="68" rx="3" fill="#0D3B66"/>
      <path d="M10 90h110" stroke="#d1d5db" strokeWidth="1.5"/>
    </svg>
  ),
  outbound: (
    <svg viewBox="0 0 120 100" className="w-32 h-28" fill="none">
      <circle cx="60" cy="50" r="38" fill="#E8F4F8" stroke="#7CBFD4" strokeWidth="2"/>
      <path d="M42 50l10 10 26-20" stroke="#2B7FA3" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="60" cy="20" r="5" fill="#2B7FA3"/>
      <circle cx="85" cy="35" r="4" fill="#7CBFD4"/>
      <circle cx="90" cy="62" r="3" fill="#7CBFD4"/>
    </svg>
  ),
  generic: (
    <svg viewBox="0 0 120 100" className="w-32 h-28" fill="none">
      <rect x="25" y="20" width="70" height="55" rx="10" fill="#E8F4F8" stroke="#7CBFD4" strokeWidth="2"/>
      <circle cx="60" cy="45" r="14" fill="#7CBFD4"/>
      <path d="M53 45h14M60 38v14" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
      <rect x="35" y="83" width="50" height="6" rx="3" fill="#d1e9f0"/>
    </svg>
  ),
}

const DEFAULTS: Record<string, { title: string; description: string }> = {
  rfq: {
    title: '尚無詢價單',
    description: '當買家送出詢價，它們會顯示在這裡。',
  },
  orders: {
    title: '尚無訂單',
    description: '訂單確認後會出現在這裡。',
  },
  analytics: {
    title: '尚無數據',
    description: '開始接受詢價和訪客後，圖表就會出現。',
  },
  outbound: {
    title: '尚無外發活動',
    description: '建立第一個外發活動，開始接觸潛在買家。',
  },
  generic: {
    title: '目前沒有資料',
    description: '相關資料出現後會顯示在這裡。',
  },
}

export default function EmptyState({
  type = 'generic',
  title,
  description,
  action,
}: EmptyStateProps) {
  const defaults = DEFAULTS[type]
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      <div className="mb-6">{ILLUSTRATIONS[type]}</div>
      <h3 className="text-lg font-semibold text-gray-800 mb-2">
        {title ?? defaults.title}
      </h3>
      <p className="text-sm text-gray-500 max-w-xs">
        {description ?? defaults.description}
      </p>
      {action && (
        <div className="mt-6">
          {action.href ? (
            <a
              href={action.href}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 text-white text-sm font-semibold rounded-lg hover:bg-primary-700 transition-colors"
            >
              {action.label}
            </a>
          ) : (
            <button
              onClick={action.onClick}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 text-white text-sm font-semibold rounded-lg hover:bg-primary-700 transition-colors"
            >
              {action.label}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
