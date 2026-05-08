import apiClient from './apiClient'
import type { APIResponse, PaginatedResponse, Incident } from '../types'

export const fetchIncidents = async (page = 1, pageSize = 10, search = ''): Promise<PaginatedResponse<Incident>> => {
  const { data } = await apiClient.get<APIResponse<PaginatedResponse<Incident>>>(
    `/incidents?page=${page}&pageSize=${pageSize}&search=${encodeURIComponent(search)}`
  )
  return data.data
}
