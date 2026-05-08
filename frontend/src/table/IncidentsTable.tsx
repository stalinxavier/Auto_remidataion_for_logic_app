import { useState } from 'react'
import { AlertCircle } from 'lucide-react'
import StatusBadge from '../components/StatusBadge'
import SearchInput from '../components/SearchInput'
import Pagination from '../components/Pagination'
import { TableSkeleton } from '../components/LoadingSkeleton'
import { useIncidents } from '../hooks/useDashboard'
import { formatDate, timeAgo } from '../utils'

interface Props {
  compact?: boolean
}

export default function IncidentsTable({ compact }: Props) {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const pageSize = compact ? 5 : 10

  const { data, isLoading } = useIncidents(page, pageSize, search)

  const handleSearch = (v: string) => {
    setSearch(v)
    setPage(1)
  }

  if (isLoading) return <TableSkeleton rows={pageSize} />

  return (
    <div className="sap-card overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-sap-blue" />
          <h3 className="text-sm font-semibold text-gray-700">Active Incidents</h3>
          <span className="text-xs bg-sap-blue-light text-sap-blue font-medium px-2 py-0.5 rounded-full">{data?.total ?? 0}</span>
        </div>
        <SearchInput value={search} onChange={handleSearch} placeholder="Search incidents..." className="w-56" />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/50">
              {['Incident ID', 'Subscription', 'Integration Scenario', 'Error Type', 'Status', 'Created'].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {data?.items.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-400">No incidents found</td></tr>
            ) : (
              data?.items.map((inc) => (
                <tr key={inc.id} className="hover:bg-gray-50/80 transition-colors cursor-pointer">
                  <td className="px-4 py-3 font-mono text-xs text-sap-blue font-medium">{inc.id}</td>
                  <td className="px-4 py-3 text-xs text-gray-500 max-w-[120px] truncate">{inc.subscriptionId}</td>
                  <td className="px-4 py-3 text-xs text-gray-700 max-w-[180px] truncate" title={inc.integrationScenario}>{inc.integrationScenario}</td>
                  <td className="px-4 py-3 text-xs text-gray-600">{inc.errorType}</td>
                  <td className="px-4 py-3"><StatusBadge status={inc.status} /></td>
                  <td className="px-4 py-3 text-xs text-gray-400" title={formatDate(inc.createdAt)}>{timeAgo(inc.createdAt)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {data && data.totalPages > 1 && (
        <Pagination page={page} totalPages={data.totalPages} total={data.total} pageSize={pageSize} onPageChange={setPage} />
      )}
    </div>
  )
}
