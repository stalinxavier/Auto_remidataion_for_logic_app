import IncidentsTable from '../table/IncidentsTable'

export default function IncidentsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold text-gray-900">Active Incidents</h2>
        <p className="text-sm text-gray-500 mt-0.5">All incidents tracked by the auto-remediation pipeline</p>
      </div>
      <IncidentsTable />
    </div>
  )
}
