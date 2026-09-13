// IndexedDB persistence: diagnosis history + outbreak reports waiting for a connection.
import { get, set, createStore } from 'idb-keyval'
import { api } from './api'

const store = createStore('agrismart', 'kv')
const HISTORY_KEY = 'history'
const QUEUE_KEY = 'pending-reports'
const MAX_HISTORY = 20

async function makeThumbnail(src, size = 96) {
  const img = new Image()
  img.src = src
  await img.decode()
  const scale = size / Math.max(img.width, img.height)
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(img.width * scale)
  canvas.height = Math.round(img.height * scale)
  canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height)
  return canvas.toDataURL('image/jpeg', 0.7)
}

export async function saveToHistory(result, previewUrl) {
  if (!result?.label) return
  let thumbnail = null
  try { thumbnail = previewUrl ? await makeThumbnail(previewUrl) : null } catch { /* ignore */ }
  const entry = {
    id: crypto.randomUUID?.() || String(Date.now()),
    at: new Date().toISOString(),
    label: result.label,
    pretty_label: result.pretty_label,
    confidence: result.confidence,
    severity: result.severity,
    affected_area_pct: result.affected_area_pct,
    thumbnail,
  }
  const history = (await get(HISTORY_KEY, store)) || []
  await set(HISTORY_KEY, [entry, ...history].slice(0, MAX_HISTORY), store)
  return entry
}

export const getHistory = async () => (await get(HISTORY_KEY, store)) || []
export const clearHistory = () => set(HISTORY_KEY, [], store)

export async function queueReport(report) {
  const queue = (await get(QUEUE_KEY, store)) || []
  await set(QUEUE_KEY, [...queue, report], store)
}

export const pendingReportCount = async () => ((await get(QUEUE_KEY, store)) || []).length

export async function syncPendingReports() {
  const queue = (await get(QUEUE_KEY, store)) || []
  if (!queue.length || !navigator.onLine) return 0
  const remaining = []
  let sent = 0
  for (const report of queue) {
    try {
      await api.createReport(report)
      sent++
    } catch (err) {
      // 4xx = invalid report, drop it; network/server errors = retry later
      if (!(err.status >= 400 && err.status < 500)) remaining.push(report)
    }
  }
  await set(QUEUE_KEY, remaining, store)
  return sent
}
