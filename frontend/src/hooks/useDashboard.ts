import { useQuery } from '@tanstack/react-query'
import { fetchKPIs, fetchStatusBreakdown, fetchErrorDistribution, fetchTopFailingArtifacts, fetchFailureOverTime } from '../api/dashboard'
import { fetchIncidents } from '../api/incidents'
import { fetchFailedMessages } from '../api/failedMessages'

export function useKPIs() {
  return useQuery({ queryKey: ['kpis'], queryFn: fetchKPIs })
}

export function useStatusBreakdown() {
  return useQuery({ queryKey: ['status-breakdown'], queryFn: fetchStatusBreakdown })
}

export function useErrorDistribution() {
  return useQuery({ queryKey: ['error-distribution'], queryFn: fetchErrorDistribution })
}

export function useTopFailingArtifacts(limit = 10) {
  return useQuery({ queryKey: ['top-failing', limit], queryFn: () => fetchTopFailingArtifacts(limit) })
}

export function useFailureOverTime(hours = 24) {
  return useQuery({ queryKey: ['failure-over-time', hours], queryFn: () => fetchFailureOverTime(hours) })
}

export function useIncidents(page: number, pageSize: number, search: string) {
  return useQuery({ queryKey: ['incidents', page, pageSize, search], queryFn: () => fetchIncidents(page, pageSize, search) })
}

export function useFailedMessages(page: number, pageSize: number, search: string) {
  return useQuery({ queryKey: ['failed-messages', page, pageSize, search], queryFn: () => fetchFailedMessages(page, pageSize, search) })
}
