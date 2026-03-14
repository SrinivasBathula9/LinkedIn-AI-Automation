import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { SkipForward, ExternalLink } from 'lucide-react'
import { fetchQueue, skipProfile } from '../api/client'

function ConfidenceBadge({ score }) {
  const pct = Math.round((score ?? 0) * 100)
  const color = pct >= 80 ? 'bg-green-900/40 text-green-400'
              : pct >= 50 ? 'bg-yellow-900/40 text-yellow-400'
              : 'bg-gray-800 text-gray-500'
  return <span className={`text-xs px-2 py-0.5 rounded-full ${color}`}>{pct}%</span>
}

export default function ProfileQueue() {
  const qc = useQueryClient()
  const { data: profiles = [], isLoading } = useQuery({
    queryKey: ['queue'],
    queryFn: () => fetchQueue(50),
    refetchInterval: 30_000,
  })
  const skipMut = useMutation({
    mutationFn: skipProfile,
    onSuccess: () => qc.invalidateQueries(['queue']),
  })

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Profile Queue</h1>
        <span className="text-sm text-gray-500">{profiles.length} profiles pending</span>
      </div>

      <div className="rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-900 text-gray-500 text-xs">
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">Title</th>
              <th className="px-4 py-3 text-left">Company</th>
              <th className="px-4 py-3 text-left">Region</th>
              <th className="px-4 py-3 text-left">Score</th>
              <th className="px-4 py-3 text-left">Confidence</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-600">Loading…</td></tr>
            )}
            {profiles.map(p => (
              <tr key={p.id} className="bg-gray-950 hover:bg-gray-900 transition-colors">
                <td className="px-4 py-3 font-medium">{p.full_name || '—'}</td>
                <td className="px-4 py-3 text-gray-400">{p.title || '—'}</td>
                <td className="px-4 py-3 text-gray-400">{p.company || '—'}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded text-xs bg-gray-800 text-gray-300">{p.region || '—'}</span>
                </td>
                <td className="px-4 py-3 text-gray-300">{p.relevance_score?.toFixed(1) ?? '—'}</td>
                <td className="px-4 py-3"><ConfidenceBadge score={p.classifier_confidence} /></td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    <a
                      href={p.linkedin_url} target="_blank" rel="noreferrer"
                      className="p-1.5 rounded hover:bg-gray-800 text-gray-500 hover:text-white"
                    ><ExternalLink size={13} /></a>
                    <button
                      onClick={() => skipMut.mutate(p.id)}
                      className="p-1.5 rounded hover:bg-gray-800 text-gray-500 hover:text-yellow-400"
                      title="Skip"
                    ><SkipForward size={13} /></button>
                  </div>
                </td>
              </tr>
            ))}
            {!isLoading && profiles.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-600">Queue is empty.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
