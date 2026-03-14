import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { createActivitySocket } from '../api/client'
import { Activity } from 'lucide-react'

// These WebSocket events signal DB data changed — bust React Query caches immediately
const INVALIDATE_ON = new Set(['connection_sent', 'campaign_done', 'campaign_start'])

const EVENT_COLORS = {
  connection_sent: 'text-green-400',
  campaign_start:  'text-blue-400',
  campaign_done:   'text-linkedin',
  restriction:     'text-red-400',
  throttle:        'text-yellow-400',
  heartbeat:       'text-gray-600',
}

function formatEvent(ev) {
  switch (ev.type) {
    case 'connection_sent':
      return `Sent to ${ev.name} (${ev.title}) · ${ev.region}`
    case 'campaign_start':
      return `Campaign started · ${ev.region}`
    case 'campaign_done':
      return `Campaign done · ${ev.region} · ${ev.sent} sent`
    case 'restriction':
      return `Restriction detected · ${ev.region} — paused`
    case 'heartbeat':
      return 'Heartbeat'
    default:
      return JSON.stringify(ev)
  }
}

export default function ActivityFeed() {
  const [events, setEvents] = useState([])
  const bottomRef = useRef(null)
  const queryClient = useQueryClient()

  useEffect(() => {
    let ws = null
    let retryTimeout = null
    let retryDelay = 2000

    const connect = () => {
      ws = createActivitySocket((ev) => {
        setEvents(prev => [{ ...ev, _id: Date.now() }, ...prev].slice(0, 100))
        if (INVALIDATE_ON.has(ev.type)) {
          queryClient.invalidateQueries({ queryKey: ['overview'] })
          queryClient.invalidateQueries({ queryKey: ['daily'] })
          queryClient.invalidateQueries({ queryKey: ['logs'] })
        }
      })
      ws.onopen = () => { retryDelay = 2000 }
      ws.onclose = () => {
        retryTimeout = setTimeout(() => { retryDelay = Math.min(retryDelay * 2, 30000); connect() }, retryDelay)
      }
    }

    connect()
    return () => {
      if (retryTimeout) clearTimeout(retryTimeout)
      if (ws) ws.onclose = null, ws.close()
    }
  }, [queryClient])

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
      <div className="flex items-center gap-2 mb-4">
        <Activity size={16} className="text-linkedin" />
        <h2 className="font-semibold text-sm">Live Activity</h2>
        <span className="ml-auto w-2 h-2 rounded-full bg-green-400 animate-pulse" />
      </div>
      <div className="space-y-1 max-h-64 overflow-y-auto text-xs font-mono">
        {events.length === 0 && (
          <p className="text-gray-600">Waiting for events…</p>
        )}
        {events.map((ev) => (
          <div key={ev._id} className={`flex gap-2 ${EVENT_COLORS[ev.type] || 'text-gray-400'}`}>
            <span className="text-gray-600 shrink-0">
              {new Date(ev.timestamp).toLocaleTimeString()}
            </span>
            <span>{formatEvent(ev)}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
