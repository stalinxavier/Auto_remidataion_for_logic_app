export const STATUS_COLORS: Record<string, string> = {
  'In Progress': 'bg-orange-100 text-orange-700 border border-orange-200',
  'Auto Fixed': 'bg-blue-100 text-blue-700 border border-blue-200',
  'Fix Failed': 'bg-red-100 text-red-700 border border-red-200',
  'Ticket Created': 'bg-purple-100 text-purple-700 border border-purple-200',
  'RCA Complete': 'bg-green-100 text-green-700 border border-green-200',
  'Fix Applied Pending': 'bg-teal-100 text-teal-700 border border-teal-200',
  'Pending Approval': 'bg-yellow-100 text-yellow-700 border border-yellow-200',
  'Failed': 'bg-red-100 text-red-700 border border-red-200',
  'Retry': 'bg-orange-100 text-orange-700 border border-orange-200',
  'Processing': 'bg-blue-100 text-blue-700 border border-blue-200',
  'default': 'bg-gray-100 text-gray-700 border border-gray-200',
}

export const CHART_COLORS = [
  '#0070F2', '#107E3E', '#E9730C', '#BB0000', '#6A2B81', '#0FAAAA',
  '#E8A000', '#5A6872', '#354A5E', '#8967DA',
]

export const ERROR_COLORS: Record<string, string> = {
  'Connectivity Error': '#BB0000',
  'Unknown Error': '#6A6D70',
  'SMTP Error': '#E9730C',
  'Credential Error': '#6A2B81',
  'Timeout Error': '#E8A000',
  'Artifact Missing': '#354A5E',
}
