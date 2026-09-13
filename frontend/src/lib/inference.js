/**
 * On-device crop diagnosis (works offline once the model is cached).
 *
 * Browser port of model/runtime.py: same preprocessing, quality gate,
 * affected-area estimate and closed-form Grad-CAM. Keep QUALITY and SEVERITY
 * identical to the Python file (backend/tests/test_runtime.py checks this).
 */
import { formatLabel, extractCrop, isHealthy } from './labels'

export const QUALITY = {
  "minPlantRatio": 0.2,
  "minGreenRatio": 0.03,
  "minBrightness": 35,
  "maxBrightness": 235,
  "blurReject": 10,
  "blurWarn": 40,
  "minConfidence": 0.6,
  "minMargin": 0.2
}

export const SEVERITY = {
  "moderate": 10,
  "severe": 25
}

const IMG = 224
const ANALYSIS = 128
const MEAN_BGR = [103.939, 116.779, 123.68]

/* ---------------- model loading ---------------- */

let worker = null
let meta = null
let head = null
let loadPromise = null
let nextId = 1
const pending = new Map()
const listeners = new Set()
let status = { state: 'idle', progress: 0, error: null }

function setStatus(patch) {
  status = { ...status, ...patch }
  listeners.forEach(fn => fn(status))
}

export function subscribeModelStatus(fn) {
  listeners.add(fn)
  fn(status)
  return () => listeners.delete(fn)
}

async function loadHead(metaJson) {
  const res = await fetch(`/model/${metaJson.head.file}?v=${metaJson.sha256?.slice(0, 12) || metaJson.version}`)
  if (!res.ok) throw new Error('Head weights missing')
  const raw = new Float32Array(await res.arrayBuffer())
  const out = {}
  let offset = 0
  for (const [name, shape] of metaJson.head.layout) {
    const size = shape.reduce((a, b) => a * b, 1)
    out[name] = { data: raw.subarray(offset, offset + size), shape }
    offset += size
  }
  if (offset !== raw.length) throw new Error('Head weights do not match metadata')
  return out
}

export function loadModel() {
  if (loadPromise) return loadPromise
  setStatus({ state: 'loading', progress: 0, error: null })
  loadPromise = (async () => {
    const res = await fetch('/model/head_meta.json', { cache: 'no-cache' })
    // SPA hosts answer missing files with index.html, so also check the content type.
    if (!res.ok || !res.headers.get('content-type')?.includes('json')) throw new Error('model_not_deployed')
    const metaJson = await res.json()
    const headWeights = await loadHead(metaJson)

    worker = new Worker(new URL('./inference.worker.js', import.meta.url), { type: 'module' })
    await new Promise((resolve, reject) => {
      worker.onmessage = ({ data }) => {
        if (data.type === 'progress') setStatus({ progress: data.total ? data.loaded / data.total : 0 })
        else if (data.type === 'ready') resolve()
        else if (data.type === 'error' && data.id === undefined) reject(new Error(data.message))
        else if (data.type === 'result' || data.type === 'error') {
          const p = pending.get(data.id)
          if (!p) return
          pending.delete(data.id)
          data.type === 'result' ? p.resolve(data) : p.reject(new Error(data.message))
        }
      }
      worker.onerror = e => reject(new Error(e.message || 'Worker failed'))
      const version = metaJson.sha256?.slice(0, 12) || metaJson.version
      worker.postMessage({ type: 'load', modelUrl: `/model/${metaJson.model_file}?v=${version}` })
    })
    meta = metaJson
    head = headWeights
    setStatus({ state: 'ready', progress: 1 })
    return meta
  })().catch(err => {
    loadPromise = null
    worker?.terminate()
    worker = null
    setStatus({ state: 'error', error: err.message })
    throw err
  })
  return loadPromise
}

function runModel(input) {
  const id = nextId++
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject })
    worker.postMessage(
      { type: 'run', id, input, inputName: meta.input_name, featuresName: meta.features_output, probsName: meta.probs_output },
      [input.buffer],
    )
  })
}

/* ---------------- image helpers ---------------- */

export async function toImageBitmap(source) {
  if (source instanceof Blob) return createImageBitmap(source, { imageOrientation: 'from-image' })
  return createImageBitmap(source)
}

function drawToCanvas(source, width, height) {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d', { willReadFrequently: true })
  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  ctx.drawImage(source, 0, 0, width, height)
  return { canvas, ctx }
}

function rgbToHsvCv(r, g, b) {
  const v = Math.max(r, g, b)
  const mn = Math.min(r, g, b)
  const delta = v - mn
  const s = v > 0 ? (delta / v) * 255 : 0
  let h = 0
  if (delta > 0) {
    if (v === r) h = (60 * (g - b)) / delta
    else if (v === g) h = 120 + (60 * (b - r)) / delta
    else h = 240 + (60 * (r - g)) / delta
    if (h < 0) h += 360
  }
  return [h / 2, s, v]
}

function fillHoles(mask, w, h) {
  const outside = new Uint8Array(w * h)
  const queue = new Int32Array(w * h)
  let head_ = 0
  let tail = 0
  const push = i => { if (!mask[i] && !outside[i]) { outside[i] = 1; queue[tail++] = i } }
  for (let x = 0; x < w; x++) { push(x); push((h - 1) * w + x) }
  for (let y = 0; y < h; y++) { push(y * w); push(y * w + w - 1) }
  while (head_ < tail) {
    const i = queue[head_++]
    const x = i % w
    const y = (i - x) / w
    if (y > 0) push(i - w)
    if (y < h - 1) push(i + w)
    if (x > 0) push(i - 1)
    if (x < w - 1) push(i + 1)
  }
  return outside
}

export function analyseImage(rgba224, rgbaSmall) {
  // Plant / green masks + affected area on the 128px analysis image.
  const n = ANALYSIS * ANALYSIS
  const plant = new Uint8Array(n)
  const green = new Uint8Array(n)
  let plantCount = 0
  let greenCount = 0
  for (let i = 0; i < n; i++) {
    const [h, s, v] = rgbToHsvCv(rgbaSmall[i * 4], rgbaSmall[i * 4 + 1], rgbaSmall[i * 4 + 2])
    const colourful = s >= 40 && v >= 40
    if (colourful && h >= 8 && h <= 95) { plant[i] = 1; plantCount++ }
    if (colourful && h >= 30 && h <= 95) { green[i] = 1; greenCount++ }
  }
  const outside = fillHoles(plant, ANALYSIS, ANALYSIS)
  let leafPx = 0
  let affected = 0
  for (let i = 0; i < n; i++) {
    if (!outside[i]) { leafPx++; if (!green[i]) affected++ }
  }

  // Brightness + Laplacian variance on the 224px model input.
  const gray = new Float32Array(IMG * IMG)
  let sum = 0
  for (let i = 0; i < IMG * IMG; i++) {
    gray[i] = 0.299 * rgba224[i * 4] + 0.587 * rgba224[i * 4 + 1] + 0.114 * rgba224[i * 4 + 2]
    sum += gray[i]
  }
  let lapSum = 0
  let lapSq = 0
  let count = 0
  for (let y = 1; y < IMG - 1; y++) {
    for (let x = 1; x < IMG - 1; x++) {
      const i = y * IMG + x
      const lap = -4 * gray[i] + gray[i - IMG] + gray[i + IMG] + gray[i - 1] + gray[i + 1]
      lapSum += lap
      lapSq += lap * lap
      count++
    }
  }
  const lapMean = lapSum / count
  const round = (x, d) => Math.round(x * 10 ** d) / 10 ** d
  return {
    plant_ratio: round(plantCount / n, 4),
    green_ratio: round(greenCount / n, 4),
    brightness: round(sum / (IMG * IMG), 1),
    sharpness: round(lapSq / count - lapMean * lapMean, 1),
    affected_area_pct: leafPx ? round((100 * affected) / leafPx, 1) : 0,
  }
}

export function qualityGate(m) {
  const warnings = []
  if (m.plant_ratio < QUALITY.minPlantRatio || m.green_ratio < QUALITY.minGreenRatio) return { reason: 'not_leaf', warnings }
  if (m.brightness < QUALITY.minBrightness) return { reason: 'too_dark', warnings }
  if (m.brightness > QUALITY.maxBrightness) return { reason: 'overexposed', warnings }
  if (m.sharpness < QUALITY.blurReject) return { reason: 'blurry', warnings }
  if (m.sharpness < QUALITY.blurWarn) warnings.push('slightly_blurry')
  return { reason: null, warnings }
}

export function severityFromArea(label, pct) {
  if (isHealthy(label)) return 'healthy'
  if (pct >= SEVERITY.severe) return 'severe'
  if (pct >= SEVERITY.moderate) return 'moderate'
  return 'mild'
}

/* ---------------- Grad-CAM ---------------- */

export function gradcamFromFeatures(features, dims, weights, classIndex) {
  const [, fh, fw, c] = dims
  const { W1, b1, W2, b2 } = weights
  const hidden = b1.data.length
  const k = b2.data.length
  const pixels = fh * fw

  const g = new Float64Array(c)
  for (let p = 0; p < pixels; p++) for (let j = 0; j < c; j++) g[j] += features[p * c + j]
  for (let j = 0; j < c; j++) g[j] /= pixels

  const pre = new Float64Array(hidden)
  for (let h = 0; h < hidden; h++) {
    let acc = b1.data[h]
    for (let j = 0; j < c; j++) acc += g[j] * W1.data[j * hidden + h]
    pre[h] = acc
  }
  const z = new Float64Array(k)
  let zMax = -Infinity
  for (let q = 0; q < k; q++) {
    let acc = b2.data[q]
    for (let h = 0; h < hidden; h++) acc += Math.max(pre[h], 0) * W2.data[h * k + q]
    z[q] = acc
    zMax = Math.max(zMax, acc)
  }
  let zSum = 0
  const p = new Float64Array(k)
  for (let q = 0; q < k; q++) { p[q] = Math.exp(z[q] - zMax); zSum += p[q] }
  for (let q = 0; q < k; q++) p[q] /= zSum

  const dz = new Float64Array(k)
  for (let q = 0; q < k; q++) dz[q] = p[classIndex] * ((q === classIndex ? 1 : 0) - p[q])
  const dpre = new Float64Array(hidden)
  for (let h = 0; h < hidden; h++) {
    if (pre[h] <= 0) continue
    let acc = 0
    for (let q = 0; q < k; q++) acc += W2.data[h * k + q] * dz[q]
    dpre[h] = acc
  }
  const alpha = new Float64Array(c)
  for (let j = 0; j < c; j++) {
    let acc = 0
    for (let h = 0; h < hidden; h++) acc += W1.data[j * hidden + h] * dpre[h]
    alpha[j] = acc / pixels
  }

  const cam = new Float32Array(pixels)
  let peak = 0
  for (let pIdx = 0; pIdx < pixels; pIdx++) {
    let acc = 0
    for (let j = 0; j < c; j++) acc += features[pIdx * c + j] * alpha[j]
    cam[pIdx] = Math.max(acc, 0)
    peak = Math.max(peak, cam[pIdx])
  }
  for (let i = 0; i < pixels; i++) cam[i] /= peak + 1e-8
  return { cam, width: fw, height: fh }
}

function jet(v) {
  const clamp = x => Math.min(1, Math.max(0, x))
  return [clamp(1.5 - Math.abs(4 * v - 3)) * 255, clamp(1.5 - Math.abs(4 * v - 2)) * 255, clamp(1.5 - Math.abs(4 * v - 1)) * 255]
}

function overlayHeatmap(bitmap, { cam, width, height }, alpha = 0.45, maxSide = 512) {
  const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height))
  const w = Math.max(1, Math.round(bitmap.width * scale))
  const h = Math.max(1, Math.round(bitmap.height * scale))
  const { canvas, ctx } = drawToCanvas(bitmap, w, h)
  const img = ctx.getImageData(0, 0, w, h)
  for (let y = 0; y < h; y++) {
    // bilinear sample of the low-res CAM (pixel-centre aligned)
    const fy = Math.min(Math.max(((y + 0.5) * height) / h - 0.5, 0), height - 1)
    const y0 = Math.floor(fy)
    const y1 = Math.min(y0 + 1, height - 1)
    const ty = fy - y0
    for (let x = 0; x < w; x++) {
      const fx = Math.min(Math.max(((x + 0.5) * width) / w - 0.5, 0), width - 1)
      const x0 = Math.floor(fx)
      const x1 = Math.min(x0 + 1, width - 1)
      const tx = fx - x0
      const v = (cam[y0 * width + x0] * (1 - tx) + cam[y0 * width + x1] * tx) * (1 - ty)
        + (cam[y1 * width + x0] * (1 - tx) + cam[y1 * width + x1] * tx) * ty
      const [r, g, b] = jet(v)
      const i = (y * w + x) * 4
      img.data[i] = alpha * r + (1 - alpha) * img.data[i]
      img.data[i + 1] = alpha * g + (1 - alpha) * img.data[i + 1]
      img.data[i + 2] = alpha * b + (1 - alpha) * img.data[i + 2]
    }
  }
  ctx.putImageData(img, 0, 0)
  return canvas.toDataURL('image/jpeg', 0.85)
}

/* ---------------- full pipeline ---------------- */

export async function diagnoseOnDevice(fileOrBlob) {
  await loadModel()
  const bitmap = await toImageBitmap(fileOrBlob)
  const { canvas: c224, ctx: ctx224 } = drawToCanvas(bitmap, IMG, IMG)
  const rgba224 = ctx224.getImageData(0, 0, IMG, IMG).data
  const { ctx: ctxSmall } = drawToCanvas(c224, ANALYSIS, ANALYSIS)
  const rgbaSmall = ctxSmall.getImageData(0, 0, ANALYSIS, ANALYSIS).data

  const metrics = analyseImage(rgba224, rgbaSmall)
  const { reason, warnings } = qualityGate(metrics)
  if (reason) return { status: 'rejected', reason, warnings, metrics, inference: 'device' }

  const input = new Float32Array(IMG * IMG * 3)
  for (let i = 0; i < IMG * IMG; i++) {
    input[i * 3] = rgba224[i * 4 + 2] - MEAN_BGR[0]
    input[i * 3 + 1] = rgba224[i * 4 + 1] - MEAN_BGR[1]
    input[i * 3 + 2] = rgba224[i * 4] - MEAN_BGR[2]
  }
  const { probs, features, featureDims } = await runModel(input)

  const order = Array.from(probs.keys()).sort((a, b) => probs[b] - probs[a])
  const idx = order[0]
  const label = meta.labels[idx]
  const confidence = probs[idx]
  const margin = confidence - probs[order[1]]
  const uncertain = confidence < QUALITY.minConfidence || margin < QUALITY.minMargin
  const r4 = x => Math.round(x * 1e4) / 1e4

  return {
    status: uncertain ? 'uncertain' : 'ok',
    reason: uncertain ? 'low_confidence' : null,
    warnings,
    label,
    pretty_label: formatLabel(label),
    crop: extractCrop(label),
    confidence: r4(confidence),
    top3: order.slice(0, 3).map(i => ({ label: meta.labels[i], pretty_label: formatLabel(meta.labels[i]), confidence: r4(probs[i]) })),
    is_healthy: isHealthy(label),
    affected_area_pct: isHealthy(label) ? 0 : metrics.affected_area_pct,
    severity: severityFromArea(label, metrics.affected_area_pct),
    metrics,
    inference: 'device',
    model: { quantization: meta.quantization, version: meta.version },
    gradcam_image: overlayHeatmap(bitmap, gradcamFromFeatures(features, featureDims, head, idx)),
  }
}
