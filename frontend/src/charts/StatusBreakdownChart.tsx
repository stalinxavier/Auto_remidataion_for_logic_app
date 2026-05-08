import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { CHART_COLORS } from '../constants'
import { ChartSkeleton } from '../components/LoadingSkeleton'
import type { StatusBreakdownItem } from '../types'

interface Props {
  data: StatusBreakdownItem[]
  loading?: boolean
}

export default function StatusBreakdownChart({ data, loading }: Props) {
  if (loading) return <ChartSkeleton height={260} />
  return (
    <div className="sap-card p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">Status Breakdown</h3>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie data={data} dataKey="count" nameKey="status" cx="50%" cy="50%" outerRadius={90} innerRadius={40} paddingAngle={2}>
            {data.map((_, i) => (
              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(v: number) => [v, 'Count']} />
          <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '11px' }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
