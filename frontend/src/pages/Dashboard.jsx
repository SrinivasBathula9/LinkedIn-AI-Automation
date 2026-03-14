import { useQuery } from '@tanstack/react-query'
import { Send, CheckCircle, Clock, XCircle, Users } from 'lucide-react'
import StatCard from '../components/StatCard'
import ActivityFeed from '../components/ActivityFeed'
import DailyChart from '../components/Charts/DailyChart'
import { fetchOverview, fetchDailyStats } from '../api/client'

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['overview'],
    queryFn: fetchOverview,
    refetchInterval: 10_000,
  })
  const { data: daily = [] } = useQuery({
    queryKey: ['daily', 30],
    queryFn: () => fetchDailyStats(30),
    refetchInterval: 30_000,
  })

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-xl font-bold">Dashboard</h1>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard label="Sent Today"    value={stats?.total_sent_today}  icon={Send}         accent="blue"   />
        <StatCard label="Sent This Week" value={stats?.total_sent_week}  icon={Send}         accent="blue"   />
        <StatCard label="Accepted"      value={stats?.total_accepted}    sub={`${stats?.acceptance_rate ?? 0}% rate`} icon={CheckCircle} accent="green"  />
        <StatCard label="Pending"       value={stats?.total_pending}     icon={Clock}        accent="yellow" />
        <StatCard label="Failed/Skipped" value={stats?.total_failed}    icon={XCircle}      accent="red"    />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DailyChart data={daily} />
        <ActivityFeed />
      </div>

      <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
        <div className="flex items-center gap-2 mb-3">
          <Users size={16} className="text-linkedin" />
          <h2 className="font-semibold text-sm">Profile Stats</h2>
        </div>
        <p className="text-gray-400 text-sm">
          Total profiles in database: <span className="text-white font-bold">{stats?.total_profiles ?? 0}</span>
        </p>
      </div>
    </div>
  )
}
