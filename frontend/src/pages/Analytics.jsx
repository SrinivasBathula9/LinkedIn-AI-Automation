import { useQuery } from '@tanstack/react-query'
import { fetchDailyStats } from '../api/client'
import DailyChart from '../components/Charts/DailyChart'
import RegionChart from '../components/Charts/RegionChart'

export default function Analytics() {
  const { data: daily30 = [] } = useQuery({ queryKey: ['daily', 30], queryFn: () => fetchDailyStats(30) })
  const { data: daily7 = [] }  = useQuery({ queryKey: ['daily', 7],  queryFn: () => fetchDailyStats(7) })

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-xl font-bold">Analytics</h1>
      <DailyChart data={daily30} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DailyChart data={daily7} />
        <RegionChart data={[]} />
      </div>
    </div>
  )
}
