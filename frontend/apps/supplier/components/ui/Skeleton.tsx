/**
 * Reusable skeleton loader components.
 * Usage:
 *   <Skeleton className="h-6 w-32" />
 *   <SkeletonCard />
 *   <SkeletonTable rows={5} />
 */

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-gray-200 rounded-md ${className}`}
      aria-hidden="true"
    />
  )
}

export function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 space-y-3">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="h-8 w-20" />
      <Skeleton className="h-3 w-32" />
    </div>
  )
}

export function SkeletonChart({ height = 240 }: { height?: number }) {
  const barHeights = [32, 46, 58, 41, 67, 52, 36, 63, 49, 72, 44, 55, 39, 61, 47, 69, 53, 42, 64, 48]

  return (
    <div
      className="bg-white rounded-xl border border-gray-100 shadow-sm p-5"
      style={{ minHeight: height + 40 }}
    >
      <Skeleton className="h-4 w-40 mb-4" />
      <div className="animate-pulse flex items-end gap-1" style={{ height }}>
        {barHeights.map((heightPct, i) => (
          <div
            key={i}
            className="flex-1 bg-gray-200 rounded-t"
            style={{ height: `${heightPct}%` }}
          />
        ))}
      </div>
    </div>
  )
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100">
        <Skeleton className="h-4 w-40" />
      </div>
      <div className="divide-y divide-gray-50">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="px-5 py-3 flex gap-4">
            <Skeleton className="h-3 flex-1" />
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  )
}
