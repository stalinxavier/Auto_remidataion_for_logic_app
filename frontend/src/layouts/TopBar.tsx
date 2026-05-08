import { Bell, RefreshCw, Search } from 'lucide-react'
import { useLocation } from 'react-router-dom'

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard Overview',
  '/incidents': 'Active Incidents',
  '/failed-messages': 'Failed Messages',
}

export default function TopBar() {
  const location = useLocation()
  const title = PAGE_TITLES[location.pathname] || 'SAP CPI Monitor'

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 flex-shrink-0">
      <div>
        <h1 className="text-base font-semibold text-gray-900">{title}</h1>
        <p className="text-xs text-gray-400">Auto-refreshes every 30 seconds</p>
      </div>
      <div className="flex items-center gap-3">
        <button className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors" title="Search">
          <Search className="w-4 h-4" />
        </button>
        <button className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors" title="Refresh">
          <RefreshCw className="w-4 h-4" />
        </button>
        <button className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 relative transition-colors" title="Notifications">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-500 rounded-full" />
        </button>
        <div className="w-8 h-8 bg-sap-blue rounded-full flex items-center justify-center text-white text-xs font-bold ml-1">
          SE
        </div>
      </div>
    </header>
  )
}
