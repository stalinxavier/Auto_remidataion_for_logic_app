import { STATUS_COLORS } from '../constants'
import { cn } from '../utils'

interface Props {
  status: string
  className?: string
}

export default function StatusBadge({ status, className }: Props) {
  const colorClass = STATUS_COLORS[status] || STATUS_COLORS['default']
  return (
    <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', colorClass, className)}>
      {status}
    </span>
  )
}
