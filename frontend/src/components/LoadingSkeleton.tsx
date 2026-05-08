import { cn } from '../utils'

interface Props {
  className?: string
  rows?: number
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('animate-pulse bg-gray-200 rounded', className)} />
}

export function KPISkeleton() {
  return (
    <div className="sap-card p-5 space-y-3">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-8 w-16" />
      <Skeleton className="h-3 w-24" />
    </div>
  )
}

export function ChartSkeleton({ height = 280 }: { height?: number }) {
  return (
    <div className="sap-card p-5">
      <Skeleton className="h-5 w-40 mb-4" />
      <Skeleton style={{ height }} className="w-full rounded-lg" />
    </div>
  )
}

export function TableSkeleton({ rows = 5 }: Props) {
  return (
    <div className="sap-card overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <Skeleton className="h-5 w-40" />
      </div>
      <div className="divide-y divide-gray-50">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="p-4 flex gap-4">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-4 w-20" />
          </div>
        ))}
      </div>
    </div>
  )
}
