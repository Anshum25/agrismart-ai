// Runs the ONNX model off the main thread so the UI stays responsive on phones.
import * as ort from 'onnxruntime-web/wasm'
import wasmUrl from 'onnxruntime-web/ort-wasm-simd-threaded.wasm?url'

ort.env.wasm.wasmPaths = { wasm: new URL(wasmUrl, self.location.href).href }
// Threads need cross-origin isolation (COOP/COEP), which would block map tiles.
ort.env.wasm.numThreads = 1

let session = null

async function fetchWithProgress(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Model download failed (${res.status})`)
  const total = Number(res.headers.get('content-length')) || 0
  if (!res.body || !total) return new Uint8Array(await res.arrayBuffer())

  const reader = res.body.getReader()
  const chunks = []
  let loaded = 0
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    chunks.push(value)
    loaded += value.length
    self.postMessage({ type: 'progress', loaded, total })
  }
  const bytes = new Uint8Array(loaded)
  let offset = 0
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length }
  return bytes
}

self.onmessage = async ({ data }) => {
  try {
    if (data.type === 'load') {
      const bytes = await fetchWithProgress(data.modelUrl)
      session = await ort.InferenceSession.create(bytes, { executionProviders: ['wasm'] })
      self.postMessage({ type: 'ready' })
    } else if (data.type === 'run') {
      if (!session) throw new Error('Model not loaded')
      const input = new ort.Tensor('float32', data.input, [1, 224, 224, 3])
      const out = await session.run({ [data.inputName]: input }, [data.featuresName, data.probsName])
      const features = out[data.featuresName]
      const probs = out[data.probsName]
      self.postMessage(
        { type: 'result', id: data.id, probs: probs.data, features: features.data, featureDims: features.dims },
        [probs.data.buffer, features.data.buffer],
      )
    }
  } catch (err) {
    self.postMessage({ type: 'error', id: data.id, message: err?.message || String(err) })
  }
}
