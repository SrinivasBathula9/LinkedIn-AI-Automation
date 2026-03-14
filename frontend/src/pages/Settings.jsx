import { useState } from 'react'
import { Settings, Shield, Clock, Brain, AlertTriangle } from 'lucide-react'

function Section({ icon: Icon, title, children }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-4">
      <div className="flex items-center gap-2 border-b border-gray-800 pb-3">
        <Icon size={16} className="text-linkedin" />
        <h2 className="font-semibold text-sm">{title}</h2>
      </div>
      {children}
    </div>
  )
}

function Field({ label, value, type = 'text', description }) {
  const [val, setVal] = useState(value)
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-gray-300">{label}</label>
      {description && <p className="text-xs text-gray-600">{description}</p>}
      <input
        type={type}
        value={val}
        onChange={e => setVal(e.target.value)}
        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-linkedin"
      />
    </div>
  )
}

export default function SettingsPage() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-xl font-bold">Settings</h1>

      {/* Emergency Stop */}
      <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertTriangle size={20} className="text-red-400" />
          <div>
            <div className="font-semibold text-sm text-red-300">Emergency Stop</div>
            <div className="text-xs text-gray-500">Immediately halt all automation across all regions</div>
          </div>
        </div>
        <button className="px-4 py-2 bg-red-700 hover:bg-red-600 text-white rounded-lg text-sm font-medium">
          STOP ALL
        </button>
      </div>

      <Section icon={Shield} title="Automation Limits (Anti-ban)">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Daily limit per region" value="20" type="number"
            description="Max connections per region per day (recommended: 20)" />
          <Field label="Session limit" value="10" type="number"
            description="Max connections per browser session" />
          <Field label="Min delay (seconds)" value="8" type="number" />
          <Field label="Max delay (seconds)" value="20" type="number" />
        </div>
      </Section>

      <Section icon={Clock} title="Scheduling Windows">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Morning window start" value="09:00" type="time" />
          <Field label="Evening window start" value="19:00" type="time" />
        </div>
        <p className="text-xs text-gray-600">
          Windows are applied in each target region's local timezone.
        </p>
      </Section>

      <Section icon={Brain} title="AI / LLM Configuration">
        <Field label="Ollama URL" value="http://localhost:11434"
          description="URL of your local Ollama instance" />
        <Field label="Ollama model" value="mistral:7b"
          description="Model to use for connection note generation" />
        <Field label="Embedding model" value="sentence-transformers/all-MiniLM-L6-v2" />
      </Section>

      <Section icon={Settings} title="LinkedIn Session">
        <Field label="LinkedIn email" value="" type="email" />
        <Field label="li_at session cookie" value=""
          description="Preferred over password. Extract from browser DevTools → Application → Cookies." />
        <div className="text-xs text-yellow-500/80 bg-yellow-900/10 border border-yellow-900/30 rounded-lg p-3">
          Credentials are stored locally and never transmitted externally.
          Use session cookies instead of passwords in production.
        </div>
      </Section>

      <button className="px-6 py-2 bg-linkedin hover:bg-linkedin-dark rounded-lg text-sm font-medium">
        Save Settings
      </button>
    </div>
  )
}
