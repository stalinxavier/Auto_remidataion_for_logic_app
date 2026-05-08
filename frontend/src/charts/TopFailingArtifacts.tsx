import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { CHART_COLORS } from '../constants'
import { ChartSkeleton } from '../components/LoadingSkeleton'
import type { TopArtifactItem } from '../types'

interface Props {
  data: TopArtifactItem[]
  loading?: boolean
}

export default function TopFailingArtifacts({ data, loading }: Props) {
  if (loading) return <ChartSkeleton height={280} />
  const chartData = data.map((d) => ({ name: d.artifact.replace('_', ' ').substring(0, 20), value: d.failureCount }))
  return (
    <div className="sap-card p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">Top Failing Integration Artifacts</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
          <XAxis type="number" tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="value" name="Failures" radius={[0, 4, 4, 0]}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
