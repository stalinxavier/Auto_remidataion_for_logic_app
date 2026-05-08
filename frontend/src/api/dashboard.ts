import apiClient from './apiClient'
import type { APIResponse, KPIData, StatusBreakdownItem, ErrorDistributionItem, TopArtifactItem, FailureTimeItem } from '../types'

export const fetchKPIs = async (): Promise<KPIData> => {
  const { data } = await apiClient.get<APIResponse<KPIData>>('/dashboard/kpis')
  return data.data
}

export const fetchStatusBreakdown = async (): Promise<StatusBreakdownItem[]> => {
  const { data } = await apiClient.get<APIResponse<StatusBreakdownItem[]>>('/dashboard/status-breakdown')
  return data.data
}

export const fetchErrorDistribution = async (): Promise<ErrorDistributionItem[]> => {
  const { data } = await apiClient.get<APIResponse<ErrorDistributionItem[]>>('/dashboard/error-distribution')
  return data.data
}

export const fetchTopFailingArtifacts = async (limit = 10): Promise<TopArtifactItem[]> => {
  const { data } = await apiClient.get<APIResponse<TopArtifactItem[]>>(`/dashboard/top-failing-artifacts?limit=${limit}`)
  return data.data
}

export const fetchFailureOverTime = async (hours = 24): Promise<FailureTimeItem[]> => {
  const { data } = await apiClient.get<APIResponse<FailureTimeItem[]>>(`/dashboard/failure-over-time?hours=${hours}`)
  return data.data
}
