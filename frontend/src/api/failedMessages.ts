import apiClient from './apiClient'
import type { APIResponse, PaginatedResponse, FailedMessage } from '../types'

export const fetchFailedMessages = async (page = 1, pageSize = 10, search = ''): Promise<PaginatedResponse<FailedMessage>> => {
  const { data } = await apiClient.get<APIResponse<PaginatedResponse<FailedMessage>>>(
    `/failed-messages?page=${page}&pageSize=${pageSize}&search=${encodeURIComponent(search)}`
  )
  return data.data
}
