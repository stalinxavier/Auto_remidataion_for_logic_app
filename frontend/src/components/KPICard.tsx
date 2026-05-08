import { type LucideIcon } from 'lucide-react'
import { cn } from '../utils'
import { Skeleton } from './LoadingSkeleton'

interface Props {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  iconColor?: string
  iconBg?: string
  trend?: { value: number; label: string }
  loading?: boolean
  className?: string
}

export default function KPICard({ title, value, subtitle, icon: Icon, iconColor = 'text-sap-blue', iconBg = 'bg-sap-blue-light', trend, loading, className }: Props) {
  if (loading) {
    return (
      <div className={cn('sap-card p-5 space-y-3', className)}>
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-3 w-28" />
      </div>
    )
  }

  return (
    <div className={cn('sap-card p-5 hover:shadow-card-hover transition-shadow cursor-default', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
          {trend && (
            <p className={cn('text-xs mt-2 font-medium', trend.value >= 0 ? 'text-green-600' : 'text-red-600')}>
              {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}% {trend.label}
            </p>
          )}
        </div>
        <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', iconBg)}>
          <Icon className={cn('w-5 h-5', iconColor)} />
        </div>
      </div>
    </div>
  )
}
