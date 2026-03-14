export default function StatCard({ label, value, sub, icon: Icon, accent = 'blue' }) {
  const colors = {
    blue:   'bg-blue-900/30 border-blue-800/40 text-blue-400',
    green:  'bg-green-900/30 border-green-800/40 text-green-400',
    yellow: 'bg-yellow-900/30 border-yellow-800/40 text-yellow-400',
    red:    'bg-red-900/30 border-red-800/40 text-red-400',
  }
  return (
    <div className={`rounded-xl border p-5 ${colors[accent]}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium uppercase tracking-wider opacity-70">{label}</span>
        {Icon && <Icon size={18} className="opacity-60" />}
      </div>
      <div className="text-3xl font-bold text-white">{value ?? '—'}</div>
      {sub && <div className="mt-1 text-xs opacity-60">{sub}</div>}
    </div>
  )
}
