export interface KPIData {
  inProgress: number
  totalIncidents: number
  pendingApproval: number
  fixFailed: number
  autoFixed: number
  failedMessages: number
  autoFixRate: number
  avgResolutionTime: number
  rcaCoverage: number
}

export interface StatusBreakdownItem {
  status: string
  count: number
}

export interface ErrorDistributionItem {
  errorType: string
  count: number
}

export interface TopArtifactItem {
  artifact: string
  failureCount: number
}

export interface FailureTimeItem {
  timestamp: string
  count: number
}

export interface Incident {
  id: string
  subscriptionId: string
  integrationScenario: string
  errorType: string
  status: string
  message?: string
  rootCause?: string
  autoFixApplied: boolean
  resolutionTime?: number
  createdAt: string
  updatedAt: string
}

export interface FailedMessage {
  id: string
  subscriptionId: string
  iflowName: string
  status: string
  errorType: string
  createdAt: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface APIResponse<T> {
  success: boolean
  data: T
  message: string
}
