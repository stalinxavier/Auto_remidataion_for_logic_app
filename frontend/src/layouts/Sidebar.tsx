import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { LayoutDashboard, AlertCircle, MessageSquareX, ChevronLeft, ChevronRight, Activity, GitBranch, Zap } from 'lucide-react'
import { cn } from '../utils'

const NAV_ITEMS = [
  {
    section: 'Dashboard',
    items: [
      { label: 'Overview', path: '/dashboard', icon: LayoutDashboard },
    ],
  },
  {
    section: 'Observability',
    items: [
      { label: 'Active Incidents', path: '/incidents', icon: AlertCircle },
      { label: 'Failed Messages', path: '/failed-messages', icon: MessageSquareX },
    ],
  },
  {
    section: 'Pipeline',
    items: [
      { label: 'Activity', path: '/pipeline/activity', icon: Activity },
      { label: 'Flows', path: '/pipeline/flows', icon: GitBranch },
    ],
  },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  return (
    <aside className={cn('relative flex flex-col bg-white border-r border-gray-200 h-full transition-all duration-300', collapsed ? 'w-16' : 'w-60')}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-4 border-b border-gray-100 h-16">
        <div className="w-8 h-8 bg-sap-blue rounded-lg flex items-center justify-center flex-shrink-0">
          <Zap className="w-4 h-4 text-white" />
        </div>
        {!collapsed && (
          <div>
            <p className="text-sm font-bold text-gray-900 leading-tight">SAP CPI</p>
            <p className="text-xs text-gray-400">Monitoring</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 overflow-y-auto">
        {NAV_ITEMS.map((section) => (
          <div key={section.section} className="mb-4">
            {!collapsed && (
              <p className="px-4 mb-1 text-[10px] font-semibold text-gray-400 uppercase tracking-widest">{section.section}</p>
            )}
            {section.items.map((item) => {
              const active = location.pathname === item.path
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  title={collapsed ? item.label : undefined}
                  className={cn(
                    'flex items-center gap-3 px-4 py-2.5 mx-2 rounded-lg text-sm transition-all',
                    active ? 'bg-sap-blue-light text-sap-blue font-medium' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  )}
                >
                  <item.icon className={cn('w-4 h-4 flex-shrink-0', active ? 'text-sap-blue' : 'text-gray-400')} />
                  {!collapsed && <span>{item.label}</span>}
                </NavLink>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 w-6 h-6 bg-white border border-gray-200 rounded-full flex items-center justify-center shadow-sm hover:shadow-md transition-shadow z-10"
      >
        {collapsed ? <ChevronRight className="w-3 h-3 text-gray-500" /> : <ChevronLeft className="w-3 h-3 text-gray-500" />}
      </button>
    </aside>
  )
}
