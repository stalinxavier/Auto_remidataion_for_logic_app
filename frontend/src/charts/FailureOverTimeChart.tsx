import { useState } from 'react'
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { ChartSkeleton } from '../components/LoadingSkeleton'
import { cn } from '../utils'
import type { FailureTimeItem } from '../types'

interface Props {
  data: FailureTimeItem[]
  loading?: boolean
  onHoursChange?: (hours: number) => void
}

const RANGES = [
  { label: '1h', value: 1 },
  { label: '24h', value: 24 },
  { label: '7d', value: 168 },
]

export default function FailureOverTimeChart({ data, loading, onHoursChange }: Props) {
  const [selected, setSelected] = useState(24)

  const handleChange = (v: number) => {
    setSelected(v)
    onHoursChange?.(v)
  }

  const chartData = data.map((d) => ({
    time: d.timestamp.substring(11, 16) || d.timestamp.substring(5, 10),
    count: d.count,
  }))

  if (loading) return <ChartSkeleton height={240} />

  return (
    <div className="sap-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700">Failure Over Time</h3>
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          {RANGES.map((r) => (
            <button
              key={r.value}
              onClick={() => handleChange(r.value)}
              className={cn('px-2.5 py-1 text-xs rounded-md transition-all font-medium', selected === r.value ? 'bg-white text-sap-blue shadow-sm' : 'text-gray-500 hover:text-gray-700')}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={chartData} margin={{ top: 4, right: 10, bottom: 0, left: -10 }}>
          <defs>
            <linearGradient id="failureGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0070F2" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#0070F2" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
          <XAxis dataKey="time" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip />
          <Area type="monotone" dataKey="count" name="Failures" stroke="#0070F2" strokeWidth={2} fill="url(#failureGrad)" dot={false} activeDot={{ r: 4 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
