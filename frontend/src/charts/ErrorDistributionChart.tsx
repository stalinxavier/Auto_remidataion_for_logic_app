import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { ERROR_COLORS, CHART_COLORS } from '../constants'
import { ChartSkeleton } from '../components/LoadingSkeleton'
import type { ErrorDistributionItem } from '../types'

interface Props {
  data: ErrorDistributionItem[]
  loading?: boolean
}

export default function ErrorDistributionChart({ data, loading }: Props) {
  if (loading) return <ChartSkeleton height={260} />
  return (
    <div className="sap-card p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">Error Distribution</h3>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie data={data} dataKey="count" nameKey="errorType" cx="50%" cy="50%" outerRadius={90} innerRadius={50} paddingAngle={2}>
            {data.map((entry, i) => (
              <Cell key={i} fill={ERROR_COLORS[entry.errorType] || CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(v: number) => [v, 'Count']} />
          <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '11px' }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
