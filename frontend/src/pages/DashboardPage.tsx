import { useState } from 'react'
import {
  Activity, AlertCircle, CheckCircle2, XCircle, Clock, MessageSquareX,
  Percent, Timer, FileSearch
} from 'lucide-react'
import KPICard from '../components/KPICard'
import StatusBreakdownChart from '../charts/StatusBreakdownChart'
import ErrorDistributionChart from '../charts/ErrorDistributionChart'
import TopFailingArtifacts from '../charts/TopFailingArtifacts'
import FailureOverTimeChart from '../charts/FailureOverTimeChart'
import IncidentsTable from '../table/IncidentsTable'
import FailedMessagesTable from '../table/FailedMessagesTable'
import {
  useKPIs, useStatusBreakdown, useErrorDistribution,
  useTopFailingArtifacts, useFailureOverTime,
} from '../hooks/useDashboard'
import { useQueryClient } from '@tanstack/react-query'

export default function DashboardPage() {
  const [timeHours, setTimeHours] = useState(24)
  const queryClient = useQueryClient()
  const { data: kpis, isLoading: kpiLoading } = useKPIs()
  const { data: statusData, isLoading: statusLoading } = useStatusBreakdown()
  const { data: errorData, isLoading: errorLoading } = useErrorDistribution()
  const { data: artifactData, isLoading: artifactLoading } = useTopFailingArtifacts()
  const { data: timeData, isLoading: timeLoading } = useFailureOverTime(timeHours)

  const handleHoursChange = (hours: number) => {
    setTimeHours(hours)
    queryClient.invalidateQueries({ queryKey: ['failure-over-time', hours] })
  }

  const kpiCards = [
    { title: 'In Progress', value: kpis?.inProgress ?? '-', icon: Activity, iconColor: 'text-orange-600', iconBg: 'bg-orange-50', subtitle: 'Currently being remediated' },
    { title: 'Total Incidents', value: kpis?.totalIncidents ?? '-', icon: AlertCircle, iconColor: 'text-sap-blue', iconBg: 'bg-sap-blue-light', subtitle: 'All time incidents' },
    { title: 'Pending Approval', value: kpis?.pendingApproval ?? '-', icon: Clock, iconColor: 'text-yellow-600', iconBg: 'bg-yellow-50', subtitle: 'Awaiting human review' },
    { title: 'Fix Failed', value: kpis?.fixFailed ?? '-', icon: XCircle, iconColor: 'text-red-600', iconBg: 'bg-red-50', subtitle: 'Auto-fix unsuccessful' },
    { title: 'Auto Fixed', value: kpis?.autoFixed ?? '-', icon: CheckCircle2, iconColor: 'text-green-600', iconBg: 'bg-green-50', subtitle: 'Successfully auto-remediated' },
    { title: 'Failed Messages', value: kpis?.failedMessages ?? '-', icon: MessageSquareX, iconColor: 'text-purple-600', iconBg: 'bg-purple-50', subtitle: 'Messages in error state' },
    { title: 'Auto Fix Rate', value: kpis ? `${kpis.autoFixRate}%` : '-', icon: Percent, iconColor: 'text-teal-600', iconBg: 'bg-teal-50', subtitle: 'Of all incidents' },
    { title: 'Avg Resolution', value: kpis ? `${kpis.avgResolutionTime}s` : '-', icon: Timer, iconColor: 'text-indigo-600', iconBg: 'bg-indigo-50', subtitle: 'Average time to resolve' },
    { title: 'RCA Coverage', value: kpis ? `${kpis.rcaCoverage}%` : '-', icon: FileSearch, iconColor: 'text-gray-600', iconBg: 'bg-gray-100', subtitle: 'Incidents with root cause' },
  ]

  return (
    <div className="space-y-6">
      {/* KPI Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {kpiCards.map((card) => (
          <KPICard key={card.title} {...card} loading={kpiLoading} />
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <StatusBreakdownChart data={statusData ?? []} loading={statusLoading} />
        <ErrorDistributionChart data={errorData ?? []} loading={errorLoading} />
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TopFailingArtifacts data={artifactData ?? []} loading={artifactLoading} />
        <FailureOverTimeChart data={timeData ?? []} loading={timeLoading} onHoursChange={handleHoursChange} />
      </div>

      {/* Tables */}
      <IncidentsTable compact />
      <FailedMessagesTable compact />
    </div>
  )
}
