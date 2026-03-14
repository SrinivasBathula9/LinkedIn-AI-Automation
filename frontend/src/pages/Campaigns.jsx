import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Play, Pause, Trash2, Target, Pencil, Check, X } from 'lucide-react'
import { fetchCampaigns, createCampaign, updateCampaign, toggleCampaign, deleteCampaign } from '../api/client'

const REGIONS = ['SG', 'IN', 'UK', 'EU', 'US', 'UAE']
const ROLES = [
  'CEO', 'CTO', 'COO', 'CIO', 'HR Recruiter', 'HR Manager',
  'AI Architect', 'Platform Engineer', 'Cloud Solution Engineer',
  'AI/ML Engineer', 'Job Consulting Agency',
]

function CampaignForm({ initial, onSubmit, onCancel }) {
  const [form, setForm] = useState(initial || { name: '', target_roles: [], target_regions: [], daily_limit: 20 })

  const toggle = (field, val) =>
    setForm(f => ({
      ...f,
      [field]: f[field].includes(val) ? f[field].filter(x => x !== val) : [...f[field], val],
    }))

  return (
    <div className="rounded-xl border border-gray-700 bg-gray-900 p-5 space-y-4">
      <h3 className="font-semibold text-sm">{initial ? 'Edit Campaign' : 'New Campaign'}</h3>
      <input
        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-linkedin"
        placeholder="Campaign name"
        value={form.name}
        onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
      />
      <div>
        <label className="text-xs text-gray-400 mb-2 block">Target Regions</label>
        <div className="flex flex-wrap gap-2">
          {REGIONS.map(r => (
            <button
              key={r}
              onClick={() => toggle('target_regions', r)}
              className={`px-3 py-1 rounded-full text-xs border transition-colors ${
                form.target_regions.includes(r)
                  ? 'bg-linkedin border-linkedin text-white'
                  : 'border-gray-700 text-gray-400 hover:border-gray-500'
              }`}
            >{r}</button>
          ))}
        </div>
      </div>
      <div>
        <label className="text-xs text-gray-400 mb-2 block">Target Roles</label>
        <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto">
          {ROLES.map(r => (
            <button
              key={r}
              onClick={() => toggle('target_roles', r)}
              className={`px-2 py-1 rounded text-xs border transition-colors ${
                form.target_roles.includes(r)
                  ? 'bg-linkedin/20 border-linkedin text-linkedin'
                  : 'border-gray-700 text-gray-500 hover:border-gray-500'
              }`}
            >{r}</button>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <label className="text-xs text-gray-400">Daily limit</label>
        <input
          type="number" min={1} max={25}
          className="w-20 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm"
          value={form.daily_limit}
          onChange={e => setForm(f => ({ ...f, daily_limit: parseInt(e.target.value) }))}
        />
      </div>
      <div className="flex gap-3">
        <button
          onClick={() => onSubmit(form)}
          className="flex items-center gap-2 px-4 py-2 bg-linkedin hover:bg-linkedin-dark rounded-lg text-sm font-medium"
        ><Check size={14} /> {initial ? 'Save' : 'Create'}</button>
        <button
          onClick={onCancel}
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm"
        ><X size={14} /> Cancel</button>
      </div>
    </div>
  )
}

export default function Campaigns() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)

  const { data: campaigns = [] } = useQuery({ queryKey: ['campaigns'], queryFn: fetchCampaigns })
  const createMut = useMutation({
    mutationFn: createCampaign,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['campaigns'] }); setShowForm(false) },
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }) => updateCampaign(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['campaigns'] }); setEditingId(null) },
  })
  const toggleMut = useMutation({
    mutationFn: toggleCampaign,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['campaigns'] }),
  })
  const deleteMut = useMutation({
    mutationFn: deleteCampaign,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['campaigns'] }),
  })

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Campaigns</h1>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-linkedin hover:bg-linkedin-dark rounded-lg text-sm font-medium"
        ><Plus size={14} /> New Campaign</button>
      </div>

      {showForm && (
        <CampaignForm
          onSubmit={data => createMut.mutate(data)}
          onCancel={() => setShowForm(false)}
        />
      )}

      <div className="space-y-3">
        {campaigns.map(c => (
          <div key={c.id}>
            {editingId === c.id ? (
              <CampaignForm
                initial={{ name: c.name, target_roles: c.target_roles ?? [], target_regions: c.target_regions ?? [], daily_limit: c.daily_limit }}
                onSubmit={data => updateMut.mutate({ id: c.id, data })}
                onCancel={() => setEditingId(null)}
              />
            ) : (
              <div className="rounded-xl border border-gray-800 bg-gray-900 p-4 flex items-center gap-4">
                <Target size={18} className="text-linkedin shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{c.name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      c.is_active ? 'bg-green-900/40 text-green-400' : 'bg-gray-800 text-gray-500'
                    }`}>{c.is_active ? 'Active' : 'Paused'}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    Regions: {c.target_regions?.join(', ') || '—'} · Limit: {c.daily_limit}/day
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setEditingId(c.id)}
                    className="p-2 rounded-lg hover:bg-gray-800 text-gray-400"
                    title="Edit"
                  ><Pencil size={14} /></button>
                  <button
                    onClick={() => toggleMut.mutate(c.id)}
                    className="p-2 rounded-lg hover:bg-gray-800 text-gray-400"
                    title={c.is_active ? 'Pause' : 'Resume'}
                  >
                    {c.is_active ? <Pause size={14} /> : <Play size={14} />}
                  </button>
                  <button
                    onClick={() => deleteMut.mutate(c.id)}
                    className="p-2 rounded-lg hover:bg-gray-800 text-red-400"
                    title="Delete"
                  ><Trash2 size={14} /></button>
                </div>
              </div>
            )}
          </div>
        ))}
        {campaigns.length === 0 && (
          <p className="text-gray-600 text-sm text-center py-8">No campaigns yet. Create one above.</p>
        )}
      </div>
    </div>
  )
}
