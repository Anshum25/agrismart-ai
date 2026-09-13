import { useState, useRef, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import Webcam from 'react-webcam'
import toast from 'react-hot-toast'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, Camera, ImageIcon, X, Loader2, CheckCircle, MapPin, Smartphone, Server, AlertTriangle, ScanLine } from 'lucide-react'
import ResultCard, { RejectCard } from '../components/ResultCard'
import LiveScan from '../components/LiveScan'
import { useI18n } from '../i18n'
import { api } from '../lib/api'
import { diagnoseOnDevice, loadModel, subscribeModelStatus } from '../lib/inference'
import { getHistory, saveToHistory, clearHistory } from '../lib/offlineStore'
import { useLocation as useGeoLocation, useOnline } from '../lib/hooks'

// Real held-out PlantVillage test images exported by model/export_onnx.py
const SAMPLES = [
  { file: 'tomato_early_blight.jpg', label: 'Tomato — Early blight' },
  { file: 'apple_scab.jpg', label: 'Apple — Apple scab' },
  { file: 'potato_late_blight.jpg', label: 'Potato — Late blight' },
  { file: 'corn_gray_leaf_spot.jpg', label: 'Corn — Gray leaf spot' },
  { file: 'grape_black_rot.jpg', label: 'Grape — Black rot' },
  { file: 'tomato_healthy.jpg', label: 'Tomato — Healthy' },
]

const MAX_BYTES = 5 * 1024 * 1024

function useModelStatus() {
  const [status, setStatus] = useState({ state: 'idle', progress: 0 })
  useEffect(() => subscribeModelStatus(setStatus), [])
  return status
}

function ModelStatus({ status }) {
  const { t } = useI18n()
  if (status.state === 'ready') return <p className="model-status ok"><Smartphone size={14} /> {t('diag.modelReady')}</p>
  if (status.state === 'loading') {
    return <p className="model-status"><Loader2 size={14} className="spin" /> {t('diag.loadingModel', { percent: Math.round(status.progress * 100) })}</p>
  }
  if (status.state === 'error') {
    return <p className="model-status warn"><Server size={14} /> {status.error === 'model_not_deployed' ? t('diag.modelMissing') : t('diag.modelServer')}</p>
  }
  return null
}

function UploadZone({ onFile }) {
  const { t } = useI18n()
  const onDrop = useCallback((accepted, rejected) => {
    if (accepted[0]) onFile(accepted[0])
    else if (rejected[0]) toast.error(rejected[0].errors[0]?.message || 'Unsupported file')
  }, [onFile])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxFiles: 1,
    maxSize: MAX_BYTES,
  })
  return (
    <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
      <input {...getInputProps()} />
      <Upload size={36} className="dropzone-icon" color="var(--ink-300)" />
      <h3>{t('diag.drop')}</h3>
      <p style={{ marginBottom: 16 }}>{t('diag.dropHint')}</p>
      <button className="btn btn-outline btn-sm" type="button">{t('diag.browse')}</button>
    </div>
  )
}

export default function Diagnose() {
  const { t } = useI18n()
  const online = useOnline()
  const modelStatus = useModelStatus()
  const geo = useGeoLocation()
  const [tab, setTab] = useState('upload')
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [selectedSample, setSelectedSample] = useState(null)
  const [missingSamples, setMissingSamples] = useState(new Set())
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const webcamRef = useRef(null)

  useEffect(() => {
    loadModel().catch(() => {})
    getHistory().then(setHistory)
  }, [])

  useEffect(() => () => previewUrl?.startsWith('blob:') && URL.revokeObjectURL(previewUrl), [previewUrl])

  const selectFile = (f, sample = null) => {
    setFile(f)
    setPreviewUrl(URL.createObjectURL(f))
    setResult(null)
    setSelectedSample(sample)
  }

  const handleCapture = async () => {
    const shot = webcamRef.current?.getScreenshot()
    if (!shot) return toast.error('Camera not ready')
    const blob = await (await fetch(shot)).blob()
    selectFile(new File([blob], 'camera.jpg', { type: 'image/jpeg' }))
    setTab('upload')
  }

  const handleSample = async sample => {
    try {
      const res = await fetch(`/samples/${sample.file}`)
      const blob = await res.blob()
      if (!res.ok || !blob.type.startsWith('image/')) throw new Error()
      selectFile(new File([blob], sample.file, { type: blob.type || 'image/jpeg' }), sample.file)
    } catch {
      toast.error(t('diag.samplesMissing'))
    }
  }

  const handleClear = () => {
    setFile(null); setPreviewUrl(null); setResult(null); setSelectedSample(null)
  }

  const runDiagnosis = async f => {
    // Prefer on-device (private, offline, no server cold start); fall back to the API.
    if (modelStatus.state === 'ready' || !online) {
      try { return await diagnoseOnDevice(f) } catch (err) { if (!online) throw err }
    }
    try {
      return await api.predict(f)
    } catch (err) {
      if (err.status === 503) throw new Error(t('diag.notDeployed'))
      if (modelStatus.state !== 'error') return diagnoseOnDevice(f)
      throw err
    }
  }

  // "Get full report" from live mode: run the normal photo pipeline on the captured frame.
  const handleLiveReport = liveFile => {
    selectFile(liveFile)
    setTab('upload')
    handleAnalyze(liveFile)
  }

  const handleAnalyze = async (target = file) => {
    if (!(target instanceof Blob)) target = file
    if (!target) return
    setLoading(true)
    setResult(null)
    try {
      const data = await runDiagnosis(target)
      setResult(data)
      if (data.status !== 'rejected') {
        await saveToHistory(data, target === file && previewUrl ? previewUrl : URL.createObjectURL(target))
        setHistory(await getHistory())
      }
      setTimeout(() => document.getElementById('result-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
    } catch (err) {
      toast.error(`${t('diag.failed')}: ${err.message === 'model_not_deployed' ? t('diag.notDeployed') : err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="diagnose-page">
      <div className="page-hero">
        <div className="container">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
            <div className="hero-chip">🔬 {t('diag.badge')}</div>
            <h1>{t('diag.title')}</h1>
            <p>{t('diag.subtitle')}</p>
          </motion.div>
        </div>
      </div>

      <div className="container" style={{ marginTop: -20 }}>
        <div className="diagnose-layout">
          {/* ---- Input ---- */}
          <div>
            <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: 'var(--sp-4)' }}>
              <div style={{ padding: '16px 20px 0' }}>
                <div className="tabs" role="tablist">
                  {[['upload', Upload], ['camera', Camera], ['live', ScanLine], ['samples', ImageIcon]].map(([key, Icon]) => (
                    <button key={key} role="tab" aria-selected={tab === key} className={`tab-btn ${tab === key ? 'active' : ''}`} onClick={() => setTab(key)}>
                      <Icon size={14} /> {t(`diag.tab.${key}`)}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ padding: 20 }}>
                {tab === 'live' && <LiveScan onFullReport={handleLiveReport} modelState={modelStatus.state} />}

                {tab === 'upload' && (previewUrl ? (
                  <div className="image-preview">
                    <img src={previewUrl} alt={t('result.original')} />
                    <div className="image-preview-label">{file?.name}</div>
                  </div>
                ) : <UploadZone onFile={f => selectFile(f)} />)}

                {tab === 'camera' && (
                  <div>
                    <div className="webcam-wrapper">
                      <Webcam
                        ref={webcamRef}
                        screenshotFormat="image/jpeg"
                        screenshotQuality={0.92}
                        forceScreenshotSourceSize
                        videoConstraints={{ facingMode: 'environment' }}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                      <div className="webcam-overlay">
                        <button className="btn btn-primary btn-sm" onClick={handleCapture}><Camera size={14} /> {t('diag.capture')}</button>
                      </div>
                    </div>
                    <p className="muted-line text-center" style={{ marginTop: 10 }}>{t('diag.cameraHint')}</p>
                  </div>
                )}

                {tab === 'samples' && (
                  <div>
                    <p className="muted-line" style={{ marginBottom: 12 }}>{t('diag.samplesHint')}</p>
                    <div className="sample-grid">
                      {SAMPLES.filter(s => !missingSamples.has(s.file)).map(s => (
                        <button key={s.file} className={`sample-card ${selectedSample === s.file ? 'selected' : ''}`} onClick={() => handleSample(s)}>
                          <img
                            src={`/samples/${s.file}`}
                            alt={s.label}
                            loading="lazy"
                            onError={() => setMissingSamples(prev => new Set(prev).add(s.file))}
                          />
                          <div className="sample-card-label">{s.label}</div>
                        </button>
                      ))}
                    </div>
                    {missingSamples.size === SAMPLES.length && <p className="note">{t('diag.samplesMissing')}</p>}
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-2">
              <button className="btn btn-primary" style={{ flex: 1, justifyContent: 'center' }} onClick={handleAnalyze} disabled={!file || loading}>
                {loading ? <><Loader2 size={16} className="spin" /> {t('diag.analysing')}</> : <><CheckCircle size={16} /> {t('diag.analyse')}</>}
              </button>
              {(file || result) && !loading && (
                <button className="btn btn-ghost" onClick={handleClear} aria-label={t('diag.change')}><X size={16} /></button>
              )}
            </div>

            <ModelStatus status={modelStatus} />

            <button className={`location-toggle ${geo.location ? 'on' : ''}`} onClick={geo.location ? geo.clear : geo.request} disabled={geo.pending}>
              <MapPin size={15} />
              <span>{geo.location ? `${t('diag.locationOn')} (${geo.location.lat.toFixed(2)}, ${geo.location.lon.toFixed(2)})` : t('diag.location')}</span>
              {geo.pending && <Loader2 size={14} className="spin" />}
            </button>
            {geo.error === 'denied' && <p className="note">{t('diag.locationDenied')}</p>}

            {history.length > 0 && (
              <div className="history">
                <div className="flex items-center justify-between">
                  <h4 className="subhead">{t('diag.recent')}</h4>
                  <button className="btn btn-ghost btn-sm" onClick={async () => { await clearHistory(); setHistory([]) }}>{t('diag.clearHistory')}</button>
                </div>
                {history.slice(0, 5).map(h => (
                  <div key={h.id} className="history-row">
                    {h.thumbnail ? <img src={h.thumbnail} alt="" /> : <span className="history-thumb" />}
                    <div>
                      <div className="history-label">{h.pretty_label}</div>
                      <div className="history-meta">{new Date(h.at).toLocaleDateString()} · {t(`severity.${h.severity}`)} · {(h.confidence * 100).toFixed(0)}%</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ---- Result ---- */}
          <div id="result-panel">
            <AnimatePresence mode="wait">
              {loading && (
                <motion.div key="loading" className="card analyze-loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <Loader2 size={40} className="spin" color="var(--forest-light)" />
                  <p style={{ fontWeight: 700 }}>{t('diag.analysing')}</p>
                  <div className="loading-dots"><span /><span /><span /></div>
                </motion.div>
              )}

              {!loading && !result && (
                <motion.div key="empty" className="card empty-state" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <div style={{ fontSize: 56 }}>🌿</div>
                  <h3>{t('diag.awaiting')}</h3>
                  <p>{t('diag.awaitingHint')}</p>
                  {!online && <p className="note"><AlertTriangle size={14} /> {t('status.offline')}</p>}
                </motion.div>
              )}

              {!loading && result?.status === 'rejected' && (
                <motion.div key="rejected" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
                  <RejectCard reason={result.reason} onRetake={() => { handleClear(); setTab('camera') }} />
                </motion.div>
              )}

              {!loading && result && result.status !== 'rejected' && (
                <motion.div key="result" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
                  <ResultCard result={result} previewUrl={previewUrl} location={geo.location} onRequestLocation={geo.request} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}
