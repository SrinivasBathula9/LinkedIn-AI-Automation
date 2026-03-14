import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'

const REGION_COLORS = {
  SG: '#0A66C2', IN: '#22c55e', UK: '#f59e0b',
  EU: '#8b5cf6', US: '#ec4899', UAE: '#14b8a6',
}

export default function RegionChart({ data = [] }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
      <h2 className="font-semibold text-sm mb-4">Sent by Region</h2>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11, fill: '#6b7280' }} />
          <YAxis dataKey="region" type="category" tick={{ fontSize: 11, fill: '#6b7280' }} width={35} />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', fontSize: 12 }}
          />
          <Bar dataKey="sent" fill="#0A66C2" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
