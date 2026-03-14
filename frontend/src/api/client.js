import axios from 'axios'

export const api = axios.create({ baseURL: '/api' })

// WebSocket activity feed
export function createActivitySocket(onMessage) {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${protocol}://${window.location.host}/ws/activity`)
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)) } catch {}
  }
  ws.onerror = (e) => console.warn('WebSocket error', e)
  return ws
}

// ── Stats ─────────────────────────────────────────────────────────────────────
export const fetchOverview = () => api.get('/stats/overview').then(r => r.data)
export const fetchDailyStats = (days = 30) => api.get(`/stats/daily?days=${days}`).then(r => r.data)

// ── Campaigns ─────────────────────────────────────────────────────────────────
export const fetchCampaigns = () => api.get('/campaigns/').then(r => r.data)
export const createCampaign = (data) => api.post('/campaigns/', data).then(r => r.data)
export const updateCampaign = (id, data) => api.put(`/campaigns/${id}`, data).then(r => r.data)
export const toggleCampaign = (id) => api.put(`/campaigns/${id}/toggle`).then(r => r.data)
export const deleteCampaign = (id) => api.delete(`/campaigns/${id}`)

// ── Profiles ──────────────────────────────────────────────────────────────────
export const fetchQueue = (limit = 50) => api.get(`/profiles/queue?limit=${limit}`).then(r => r.data)
export const skipProfile = (id) => api.post(`/profiles/skip/${id}`).then(r => r.data)

// ── Logs ──────────────────────────────────────────────────────────────────────
export const fetchLogs = (limit = 50) => api.get(`/logs/?limit=${limit}`).then(r => r.data)
