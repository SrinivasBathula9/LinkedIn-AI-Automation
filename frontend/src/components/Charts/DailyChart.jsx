import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend,
  CartesianGrid, ResponsiveContainer,
} from 'recharts'

export default function DailyChart({ data = [] }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
      <h2 className="font-semibold text-sm mb-4">Daily Requests — Sent vs Accepted</h2>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} />
          <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', fontSize: 12 }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="sent"     stroke="#0A66C2" strokeWidth={2} dot={false} name="Sent" />
          <Line type="monotone" dataKey="accepted" stroke="#22c55e" strokeWidth={2} dot={false} name="Accepted" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
