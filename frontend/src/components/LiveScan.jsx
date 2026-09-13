import { useCallback, useEffect, useRef, useState } from 'react'
import { Pause, Play, FileText, Eye, EyeOff, Loader2, ScanLine, AlertTriangle } from 'lucide-react'
import { analyseFrame, gradcamForClass, drawHeatmap, summarizeProbs, loadModel } from '../lib/inference'
import { useI18n } from '../i18n'
import HealthMeter from './HealthMeter'

const MIN_INTERVAL_MS = 350     // pause between scans so phones stay cool
const SMOOTHING = 0.55          // weight of the newest frame in the running average
const HEALTHY_COLOR = '#10b981'
const DISEASE_COLOR = '#f59e0b'
const IDLE_COLOR = 'rgba(255,255,255,.7)'

/**
 * Live crop scan: continuously analyses camera frames on-device (no photo needed).
 * Same OpenCV-style leaf segmentation + quality gate + ResNet50 + Grad-CAM as photo mode,
 * with probabilities averaged over recent frames to avoid flicker.
 */
export default function LiveScan({ onFullReport, modelState }) {
  const { t } = useI18n()
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const smoothRef = useRef(null)
  const runningRef = useRef(false)
  const [running, setRunning] = useState(true)
  const [showFocus, setShowFocus] = useState(true)
  const [cameraError, setCameraError] = useState(null)
  const [live, setLive] = useState(null)
  const [latency, setLatency] = useState(null)
  const showFocusRef = useRef(showFocus)
  showFocusRef.current = showFocus

  // Camera lifecycle
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: false,
        })
        if (cancelled) { stream.getTracks().forEach(tr => tr.stop()); return }
        streamRef.current = stream
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      } catch (err) {
        setCameraError(err?.name === 'NotAllowedError' ? t('live.cameraDenied') : t('live.cameraError'))
      }
    })()
    return () => {
      cancelled = true
      runningRef.current = false
      streamRef.current?.getTracks().forEach(tr => tr.stop())
    }
  }, [t])

  const draw = useCallback((frame, summary) => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas || !video.videoWidth) return
    const rect = canvas.getBoundingClientRect()
    const dpr = window.devicePixelRatio || 1
    canvas.width = Math.round(rect.width * dpr)
    canvas.height = Math.round(rect.height * dpr)
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // The model sees only the detected leaf crop; map crop-relative coordinates back to the frame.
    const crop = frame.cropRect || { x: 0, y: 0, w: 1, h: 1 }
    const cropPx = { x: crop.x * canvas.width, y: crop.y * canvas.height, w: crop.w * canvas.width, h: crop.h * canvas.height }
    if (summary && showFocusRef.current && frame.features) {
      drawHeatmap(ctx, gradcamForClass(frame.features, frame.featureDims, summary.index), cropPx)
    }
    const inner = frame.metrics?.leaf_box
    const box = inner && { x: crop.x + inner.x * crop.w, y: crop.y + inner.y * crop.h, w: inner.w * crop.w, h: inner.h * crop.h }
    const color = !summary ? IDLE_COLOR : summary.is_healthy ? HEALTHY_COLOR : DISEASE_COLOR
    if (box) {
      const x = box.x * canvas.width, y = box.y * canvas.height
      const w = box.w * canvas.width, h = box.h * canvas.height
      ctx.lineWidth = 3 * dpr
      ctx.strokeStyle = color
      ctx.setLineDash(summary ? [] : [10 * dpr, 8 * dpr])
      ctx.strokeRect(x, y, w, h)
      if (summary) {
        const text = summary.is_healthy
          ? `${summary.crop} · ${t('health.allGoodShort')}`
          : `${summary.pretty_label} · ${Math.round(summary.confidence * 100)}%`
        ctx.font = `600 ${14 * dpr}px Inter, sans-serif`
        const pad = 6 * dpr
        const tw = ctx.measureText(text).width + pad * 2
        const ty = Math.max(0, y - 26 * dpr)
        ctx.fillStyle = color
        ctx.fillRect(x, ty, Math.min(tw, canvas.width - x), 24 * dpr)
        ctx.fillStyle = '#062b21'
        ctx.fillText(text, x + pad, ty + 17 * dpr)
      }
    }
  }, [t])

  // Scan loop
  useEffect(() => {
    if (!running || cameraError) return
    runningRef.current = true
    let timer = null

    const tick = async () => {
      if (!runningRef.current) return
      const video = videoRef.current
      if (!video || video.readyState < 2 || document.hidden) {
        timer = setTimeout(tick, 300)
        return
      }
      const started = performance.now()
      try {
        const frame = await analyseFrame(video)
        if (!runningRef.current) return
        if (frame.status === 'rejected') {
          smoothRef.current = null
          setLive({ status: 'rejected', reason: frame.reason })
          draw(frame, null)
        } else {
          const prev = smoothRef.current
          const probs = prev
            ? frame.probs.map((p, i) => SMOOTHING * p + (1 - SMOOTHING) * prev[i])
            : Float32Array.from(frame.probs)
          smoothRef.current = probs
          const summary = summarizeProbs(probs, frame.metrics, frame.warnings)
          setLive(summary)
          draw(frame, summary)
        }
        setLatency(Math.round(performance.now() - started))
      } catch (err) {
        setLive({ status: 'error', message: err.message })
      }
      const elapsed = performance.now() - started
      timer = setTimeout(tick, Math.max(0, MIN_INTERVAL_MS - elapsed))
    }

    loadModel().then(tick).catch(err => setLive({ status: 'error', message: err.message }))
    return () => {
      runningRef.current = false
      clearTimeout(timer)
    }
  }, [running, cameraError, draw])

  const fullReport = async () => {
    const video = videoRef.current
    if (!video?.videoWidth) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0)
    const blob = await new Promise(res => canvas.toBlob(res, 'image/jpeg', 0.92))
    setRunning(false)
    onFullReport(new File([blob], 'live-scan.jpg', { type: 'image/jpeg' }))
  }

  if (modelState === 'error') {
    return <p className="note"><AlertTriangle size={14} /> {t('live.modelNeeded')}</p>
  }

  const scored = live && (live.status === 'ok' || live.status === 'uncertain')

  return (
    <div className="live-scan">
      <div className="live-stage">
        <video
          ref={videoRef}
          playsInline
          muted
          className="live-video"
          onLoadedMetadata={e => {
            const v = e.currentTarget
            if (v.videoWidth) v.parentElement.style.aspectRatio = `${v.videoWidth} / ${v.videoHeight}`
          }}
        />
        <canvas ref={canvasRef} className="live-overlay" />
        {cameraError && <div className="live-message">{cameraError}</div>}
        {!cameraError && !live && <div className="live-message"><Loader2 className="spin" size={18} /> {t('live.starting')}</div>}
        <div className="live-hud">
          <span className={`live-dot ${running ? 'on' : ''}`} /> {running ? t('live.scanning') : t('live.paused')}
          {latency && running && <span className="live-latency">{t('live.speed', { ms: latency })}</span>}
        </div>
      </div>

      <div className="live-controls">
        <button className="btn btn-outline btn-sm" onClick={() => setRunning(r => !r)} disabled={Boolean(cameraError)}>
          {running ? <><Pause size={14} /> {t('live.pause')}</> : <><Play size={14} /> {t('live.resume')}</>}
        </button>
        <button className="btn btn-ghost btn-sm" onClick={() => setShowFocus(s => !s)}>
          {showFocus ? <EyeOff size={14} /> : <Eye size={14} />} {t('live.showFocus')}
        </button>
        <button className="btn btn-primary btn-sm" onClick={fullReport} disabled={!scored || Boolean(cameraError)}>
          <FileText size={14} /> {t('live.fullReport')}
        </button>
      </div>

      <div className="live-result">
        {live?.status === 'rejected' && (
          <p className="live-hint"><ScanLine size={16} /> {t(`live.reject.${live.reason}`)}</p>
        )}
        {live?.status === 'error' && <p className="note">{live.message}</p>}
        {scored && (
          <>
            <div className="live-label-row">
              <div>
                <div className="live-label">{live.is_healthy ? `${live.crop} — ${t('severity.healthy')}` : live.pretty_label}</div>
                <div className="live-sub">
                  {t('result.confidence')} {Math.round(live.confidence * 100)}%
                  {live.status === 'uncertain' && <> · <span className="text-amber">{t('live.notSure')}</span></>}
                </div>
              </div>
            </div>
            <HealthMeter health={live.health} isHealthy={live.is_healthy} compact />
          </>
        )}
        <p className="live-footnote">{t('live.hint')}</p>
      </div>
    </div>
  )
}
