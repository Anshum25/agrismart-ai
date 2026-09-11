import { useState, useRef, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import Webcam from 'react-webcam'
import toast from 'react-hot-toast'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload, Camera, ImageIcon, X, Loader2,
  CheckCircle, AlertTriangle, ChevronDown, ChevronRight
} from 'lucide-react'
import ResultCard from '../components/ResultCard'

/* ---------- Sample images -------------------------------- */
const SAMPLES = [
  { label: 'Tomato Early Blight',  hint: 'Tomato___Early_blight',   bg: '#4a1c03', emoji: '🍅' },
  { label: 'Apple Scab',           hint: 'Apple___Apple_scab',       bg: '#2d4a1c', emoji: '🍎' },
  { label: 'Potato Late Blight',   hint: 'Potato___Late_blight',     bg: '#1c2d4a', emoji: '🥔' },
  { label: 'Corn Gray Leaf Spot',  hint: 'Corn_(maize)___Gray_leaf_spot', bg: '#3a3a1c', emoji: '🌽' },
  { label: 'Grape Black Rot',      hint: 'Grape___Black_rot',         bg: '#2d1c4a', emoji: '🍇' },
  { label: 'Healthy Leaf',         hint: 'Tomato___healthy',          bg: '#1c4a2d', emoji: '🌿' },
]

/* ---------- Loading Animation --------------------------- */
function LoadingState() {
  return (
    <motion.div
      className="analyze-loading"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div style={{ position: 'relative', width: 80, height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{
          position: 'absolute', inset: 0,
          borderRadius: '50%',
          border: '3px solid rgba(5,150,105,.15)',
          borderTopColor: 'var(--forest-light)',
          animation: 'spin 1s linear infinite'
        }} />
        <div style={{ fontSize: 28 }}>🌿</div>
      </div>
      <div>
        <p style={{ fontWeight: 700, color: 'var(--ink-900)', textAlign: 'center', marginBottom: 8, fontFamily: 'Outfit, sans-serif', fontSize: '1.1rem' }}>
          Analysing your leaf…
        </p>
        <p style={{ fontSize: '.875rem', color: 'var(--text-muted)', textAlign: 'center' }}>
          Running ResNet50 inference and computing Grad-CAM heatmap
        </p>
      </div>
      <div className="loading-dots">
        <span /><span /><span />
      </div>
    </motion.div>
  )
}

/* ---------- Drop Zone component ------------------------- */
function DropZoneInline({ onFileSelected }) {
  const onDrop = useCallback(accepted => {
    if (accepted[0]) onFileSelected(accepted[0])
  }, [onFileSelected])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxFiles: 1,
  })

  return (
    <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
      <input {...getInputProps()} />
      <Upload size={36} className="dropzone-icon" color="var(--ink-300)" style={{ margin: '0 auto 16px' }} />
      <h3>Drag & drop a leaf photo</h3>
      <p style={{ marginBottom: 16 }}>JPG, PNG, WEBP up to 10 MB</p>
      <button className="btn btn-outline btn-sm" type="button">Browse Files</button>
    </div>
  )
}

/* ---------- Main Component ------------------------------ */
export default function Diagnose() {
  const [tab, setTab] = useState('upload') // 'upload' | 'webcam' | 'sample'
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [selectedSample, setSelectedSample] = useState(null)
  const webcamRef = useRef(null)

  const handleFile = (f) => {
    setFile(f)
    setPreviewUrl(URL.createObjectURL(f))
    setResult(null)
    setSelectedSample(null)
  }

  const handleCapture = () => {
    const img = webcamRef.current?.getScreenshot()
    if (!img) return toast.error('Camera not ready')
    // Convert base64 to File
    const byteStr = atob(img.split(',')[1])
    const arr = new Uint8Array(byteStr.length)
    for (let i = 0; i < byteStr.length; i++) arr[i] = byteStr.charCodeAt(i)
    const capturedFile = new File([arr], 'webcam-capture.jpg', { type: 'image/jpeg' })
    handleFile(capturedFile)
    setTab('upload') // show preview
  }

  const handleSampleSelect = (sample) => {
    setSelectedSample(sample)
    setFile(null)
    setPreviewUrl(null)
    setResult(null)
    toast(`Selected: ${sample.label}`, { icon: sample.emoji })
  }

  const handleClear = () => {
    setFile(null); setPreviewUrl(null); setResult(null); setSelectedSample(null)
  }

  const handleAnalyze = async () => {
    if (!file && !selectedSample) return
    setLoading(true)
    setResult(null)

    try {
      let body, res

      if (file) {
        const formData = new FormData()
        formData.append('file', file)
        res = await fetch('/api/predict/gradcam', { method: 'POST', body: formData })
      } else {
        // Sample: use placeholder endpoint or simulate with label hint
        // We create a minimal placeholder image and send it
        const canvas = document.createElement('canvas')
        canvas.width = 224; canvas.height = 224
        const ctx = canvas.getContext('2d')
        ctx.fillStyle = selectedSample.bg
        ctx.fillRect(0, 0, 224, 224)
        ctx.fillStyle = 'rgba(255,255,255,.3)'
        ctx.fillRect(40, 40, 144, 144)
        const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg'))
        const sampleFile = new File([blob], 'sample.jpg', { type: 'image/jpeg' })
        const formData = new FormData()
        formData.append('file', sampleFile)
        res = await fetch('/api/predict/gradcam', { method: 'POST', body: formData })
      }

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Analysis failed')
      }
      const data = await res.json()
      setResult(data)
      toast.success('Diagnosis complete!')
      setTimeout(() => {
        document.getElementById('result-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  const canAnalyze = (file || selectedSample) && !loading

  return (
    <div style={{ minHeight: '100vh', background: 'var(--cream)', paddingBottom: 80 }}>
      {/* Header */}
      <div style={{ background: 'var(--forest)', padding: '48px 0 32px' }}>
        <div className="container">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .45 }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'rgba(255,255,255,.12)', border: '1px solid rgba(255,255,255,.18)', color: 'rgba(255,255,255,.9)', fontSize: '.75rem', fontWeight: 700, letterSpacing: '.1em', textTransform: 'uppercase', padding: '3px 12px', borderRadius: 999, marginBottom: 12 }}>
              🔬 Diagnostic Dashboard
            </div>
            <h1 style={{ color: 'white', fontFamily: 'Outfit, sans-serif', fontSize: 'clamp(1.6rem, 4vw, 2.8rem)', marginBottom: 10 }}>
              Plant Health Analysis
            </h1>
            <p style={{ color: 'rgba(255,255,255,.7)', fontSize: '1.05rem', maxWidth: 560 }}>
              Upload a leaf image, use your webcam, or pick a sample — and get a diagnosis in under a second.
            </p>
          </motion.div>
        </div>
      </div>

      <div className="container" style={{ marginTop: -20 }}>
        <div className="diagnose-layout">
          {/* ---- LEFT PANEL: Input ---- */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: .45, delay: .1 }}
          >
            <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: 'var(--sp-4)' }}>
              {/* Tab bar */}
              <div style={{ padding: '16px 20px 0', background: 'var(--white)' }}>
                <div className="tabs">
                  <button className={`tab-btn ${tab === 'upload' ? 'active' : ''}`} onClick={() => setTab('upload')}>
                    <Upload size={14} /> Upload
                  </button>
                  <button className={`tab-btn ${tab === 'webcam' ? 'active' : ''}`} onClick={() => setTab('webcam')}>
                    <Camera size={14} /> Camera
                  </button>
                  <button className={`tab-btn ${tab === 'sample' ? 'active' : ''}`} onClick={() => setTab('sample')}>
                    <ImageIcon size={14} /> Samples
                  </button>
                </div>
              </div>

              {/* Tab content */}
              <div style={{ padding: 20, background: 'var(--white)' }}>
                <AnimatePresence mode="wait">
                  {tab === 'upload' && (
                    <motion.div key="upload" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: .2 }}>
                      {previewUrl ? (
                        <div className="image-preview">
                          <img src={previewUrl} alt="Leaf preview" />
                          <div className="image-preview-label">{file?.name}</div>
                        </div>
                      ) : (
                        <DropZoneInline onFileSelected={handleFile} />
                      )}
                    </motion.div>
                  )}

                  {tab === 'webcam' && (
                    <motion.div key="webcam" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: .2 }}>
                      <div className="webcam-wrapper">
                        <Webcam
                          ref={webcamRef}
                          screenshotFormat="image/jpeg"
                          videoConstraints={{ facingMode: 'environment' }}
                          style={{ width: '100%', height: 240, objectFit: 'cover' }}
                        />
                        <div className="webcam-overlay">
                          <button className="btn btn-primary btn-sm" onClick={handleCapture}>
                            <Camera size={14} /> Capture Photo
                          </button>
                        </div>
                      </div>
                      <p style={{ fontSize: '.8rem', color: 'var(--text-muted)', marginTop: 10, textAlign: 'center' }}>
                        Point your camera at a leaf, then click Capture.
                      </p>
                    </motion.div>
                  )}

                  {tab === 'sample' && (
                    <motion.div key="sample" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: .2 }}>
                      <p style={{ fontSize: '.85rem', color: 'var(--text-muted)', marginBottom: 12, fontWeight: 500 }}>
                        Pick a sample to test the model:
                      </p>
                      <div className="sample-grid">
                        {SAMPLES.map(s => (
                          <div
                            key={s.hint}
                            className={`sample-card ${selectedSample?.hint === s.hint ? 'selected' : ''}`}
                            onClick={() => handleSampleSelect(s)}
                          >
                            <div style={{ height: 72, background: s.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 32 }}>
                              {s.emoji}
                            </div>
                            <div className="sample-card-label">{s.label}</div>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Action buttons */}
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                className="btn btn-primary w-full justify-center"
                style={{ flex: 1, justifyContent: 'center' }}
                onClick={handleAnalyze}
                disabled={!canAnalyze}
              >
                {loading
                  ? <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Analysing…</>
                  : <><CheckCircle size={16} /> Analyse Plant Health</>
                }
              </button>
              {(file || selectedSample || result) && !loading && (
                <button className="btn btn-ghost" onClick={handleClear}>
                  <X size={16} />
                </button>
              )}
            </div>
          </motion.div>

          {/* ---- RIGHT PANEL: Results ---- */}
          <motion.div
            id="result-panel"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: .45, delay: .15 }}
          >
            <AnimatePresence mode="wait">
              {loading && (
                <motion.div key="loading" className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <LoadingState />
                </motion.div>
              )}

              {!loading && !result && (
                <motion.div
                  key="empty"
                  className="card"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  style={{
                    minHeight: 420,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'var(--sand)',
                    border: 'none',
                    gap: 12
                  }}
                >
                  <div style={{ fontSize: 56 }}>🔬</div>
                  <h3 style={{ color: 'var(--ink-700)' }}>Awaiting Sample</h3>
                  <p style={{ textAlign: 'center', maxWidth: 300, color: 'var(--text-muted)', fontSize: '.9rem' }}>
                    Select an image using any of the input methods on the left, then click <strong>Analyse Plant Health</strong>.
                  </p>
                </motion.div>
              )}

              {!loading && result && (
                <motion.div key="result" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .4 }}>
                  <ResultCard result={result} originalPreview={previewUrl} />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
