// Single place that knows how to reach the FastAPI backend.

export const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/+$/, '')
export const API_DOCS_URL = import.meta.env.VITE_API_URL ? `${API_BASE}/docs` : null

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, { method = 'GET', json, form, timeout = 20000, signal } = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  signal?.addEventListener('abort', () => controller.abort())
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: json ? { 'Content-Type': 'application/json' } : undefined,
      body: json ? JSON.stringify(json) : form,
      signal: controller.signal,
    })
    const isJson = res.headers.get('content-type')?.includes('application/json')
    const data = isJson ? await res.json() : null
    if (!res.ok) {
      const detail = typeof data?.detail === 'string' ? data.detail : data?.error || res.statusText
      throw new ApiError(detail || 'Request failed', res.status)
    }
    return data
  } catch (err) {
    if (err instanceof ApiError) throw err
    if (err.name === 'AbortError') throw new ApiError('The server took too long to respond.', 0)
    throw new ApiError('Cannot reach the server. Check your internet connection.', 0)
  } finally {
    clearTimeout(timer)
  }
}

const qs = params =>
  new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')).toString()

export const api = {
  health: () => request('/health', { timeout: 60000 }),
  // Render's free tier sleeps; the first request can take ~50s.
  predict: file => {
    const form = new FormData()
    form.append('file', file)
    return request('/predict?gradcam=true', { method: 'POST', form, timeout: 90000 })
  },
  advice: (label, lang) => request('/advice', { method: 'POST', json: { label, lang }, timeout: 45000 }),
  insights: (label, loc) => request(`/insights?${qs({ label, lat: loc?.lat, lon: loc?.lon })}`, { timeout: 45000 }),
  forecast: (label, loc) => request(`/forecast?${qs({ label, lat: loc.lat, lon: loc.lon })}`, { timeout: 45000 }),
  voiceAsk: form => request('/voice/ask', { method: 'POST', form, timeout: 60000 }),
  createReport: report => request('/reports', { method: 'POST', json: report, timeout: 30000 }),
  aggregate: params => request(`/reports/aggregate?${qs(params)}`, { timeout: 60000 }),
  alerts: params => request(`/alerts?${qs(params)}`, { timeout: 60000 }),
}
