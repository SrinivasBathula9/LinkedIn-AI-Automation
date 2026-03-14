import { Routes, Route, NavLink } from 'react-router-dom'
import { LayoutDashboard, Target, Users, BarChart2, Settings, Linkedin } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Campaigns from './pages/Campaigns'
import ProfileQueue from './pages/ProfileQueue'
import Analytics from './pages/Analytics'
import SettingsPage from './pages/Settings'

const NAV = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/campaigns', icon: Target,          label: 'Campaigns' },
  { to: '/queue',     icon: Users,           label: 'Queue' },
  { to: '/analytics', icon: BarChart2,       label: 'Analytics' },
  { to: '/settings',  icon: Settings,        label: 'Settings' },
]

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="px-5 py-4 flex items-center gap-2 border-b border-gray-800">
          <Linkedin className="text-linkedin" size={22} />
          <span className="font-bold text-sm tracking-wide">LI Automation</span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-linkedin text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-3 text-xs text-gray-600 border-t border-gray-800">
          v1.0.0 · Personal use only
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto bg-gray-950">
        <Routes>
          <Route path="/"          element={<Dashboard />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/queue"     element={<ProfileQueue />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings"  element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  )
}
