import { useState } from 'react'
import { ChevronDown, AlertTriangle, CheckCircle, Info, Leaf, Droplets, Cloud, Recycle } from 'lucide-react'

/* ---------- helpers ------------------------------------ */
function getSeverity(label, confidence) {
  if (!label) return { level: 'unknown', label: 'Unknown', cls: '' }
  const lc = label.toLowerCase()
  if (lc.includes('healthy')) return { level: 'healthy', label: '✅ Healthy', cls: 'severity-healthy' }
  if (confidence >= .92) return { level: 'high', label: '🔴 High Severity', cls: 'severity-high' }
  if (confidence >= .75) return { level: 'moderate', label: '🟠 Moderate Severity', cls: 'severity-moderate' }
  return { level: 'low', label: '🟡 Low Severity', cls: 'severity-low' }
}

function parseAdvice(raw = '') {
  // Try to split into sections
  const sections = {
    immediate: '',
    prevention: '',
    care: '',
    raw: raw,
  }
  const lower = raw.toLowerCase()
  // Look for numbered sections or keywords
  const immIdx = lower.search(/immediate|treat|step 1|1\)/)
  const prevIdx = lower.search(/prevent|avoid|step 2|2\)/)
  const careIdx = lower.search(/care|recovery|long.term|step 3|3\)/)

  if (immIdx >= 0 && prevIdx > immIdx) {
    sections.immediate = raw.slice(immIdx, prevIdx > immIdx ? prevIdx : undefined).trim()
    if (prevIdx >= 0 && careIdx > prevIdx) {
      sections.prevention = raw.slice(prevIdx, careIdx > prevIdx ? careIdx : undefined).trim()
      sections.care = raw.slice(careIdx).trim()
    } else if (prevIdx >= 0) {
      sections.prevention = raw.slice(prevIdx).trim()
    }
  }
  return sections
}

/* ---------- Accordion ---------------------------------- */
function Accordion({ title, icon, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="accordion-item">
      <button className="accordion-trigger" onClick={() => setOpen(!open)}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {icon} {title}
        </span>
        <ChevronDown size={16} style={{ transform: open ? 'rotate(180deg)' : '', transition: 'transform .2s' }} />
      </button>
      {open && <div className="accordion-content">{children}</div>}
    </div>
  )
}

/* ---------- Main Component ----------------------------- */
export default function ResultCard({ result, originalPreview }) {
  const {
    pretty_label, crop, label, confidence, confidence_pct,
    gradcam_overlay, care_advice, model_loaded
  } = result

  const sev = getSeverity(label, confidence)
  const advSections = parseAdvice(care_advice)
  const isHealthy = sev.level === 'healthy'

  const originalSrc = originalPreview || null
  const heatmapSrc = gradcam_overlay ? `data:image/png;base64,${gradcam_overlay}` : null

  return (
    <div className="result-wrapper">
      {/* ---- Header ---- */}
      <div className="result-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="result-crop-name">Detected on: {crop}</div>
            <div className="result-disease-name">{pretty_label}</div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <span className={`severity-badge ${sev.cls}`}>{sev.label}</span>
              {!model_loaded && (
                <span className="severity-badge" style={{ background: 'rgba(255,255,255,.1)', color: 'rgba(255,255,255,.7)' }}>
                  Demo Mode
                </span>
              )}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 700, fontSize: '2.5rem', color: isHealthy ? '#6ee7b7' : '#fbbf24', lineHeight: 1 }}>
              {confidence_pct}
            </div>
            <div style={{ fontSize: '.75rem', color: 'rgba(255,255,255,.6)', fontWeight: 500, marginTop: 2 }}>Confidence</div>
          </div>
        </div>

        {/* Confidence bar */}
        <div style={{ marginTop: 16 }}>
          <div className="confidence-bar-track" style={{ background: 'rgba(255,255,255,.15)' }}>
            <div
              className="confidence-bar-fill"
              style={{
                width: `${confidence * 100}%`,
                background: isHealthy
                  ? 'linear-gradient(90deg, #6ee7b7, #10b981)'
                  : 'linear-gradient(90deg, #fbbf24, #f59e0b)'
              }}
            />
          </div>
        </div>
      </div>

      {/* ---- Body ---- */}
      <div className="result-body">
        {/* Image pair */}
        {(originalSrc || heatmapSrc) && (
          <div className="image-pair" style={{ marginBottom: 24 }}>
            {originalSrc && (
              <div className="image-pair-item">
                <img src={originalSrc} alt="Original leaf" />
                <div className="image-pair-caption">📷 Original Upload</div>
              </div>
            )}
            {heatmapSrc && (
              <div className="image-pair-item">
                <img src={heatmapSrc} alt="Grad-CAM heatmap" />
                <div className="image-pair-caption">🔥 AI Focus (Grad-CAM)</div>
              </div>
            )}
          </div>
        )}

        {/* Advice */}
        {care_advice && (
          <div className="advice-card" style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <Leaf size={16} color="var(--forest-light)" />
              <span style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 700, color: 'var(--forest)', fontSize: '1rem' }}>
                AI Agronomist Advice
              </span>
            </div>

            {(advSections.immediate || advSections.prevention || advSections.care) ? (
              <>
                {advSections.immediate && (
                  <div className="advice-section">
                    <h4>⚡ Immediate Action</h4>
                    <p>{advSections.immediate}</p>
                  </div>
                )}
                {advSections.prevention && (
                  <div className="advice-section">
                    <h4>🛡️ Prevention</h4>
                    <p>{advSections.prevention}</p>
                  </div>
                )}
                {advSections.care && (
                  <div className="advice-section">
                    <h4>🌱 Long-term Care</h4>
                    <p>{advSections.care}</p>
                  </div>
                )}
              </>
            ) : (
              <p style={{ fontSize: '.9rem', color: 'var(--ink-700)', lineHeight: 1.75 }}>{care_advice}</p>
            )}
          </div>
        )}

        {/* Bonus modules accordion */}
        <div style={{ marginBottom: 16 }}>
          <p style={{ fontSize: '.78rem', fontWeight: 700, letterSpacing: '.06em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 10 }}>
            Additional Insights
          </p>
          <div className="accordion">
            <Accordion title="Irrigation Advice" icon={<Droplets size={14} color="var(--forest-light)" />}>
              {isHealthy
                ? 'Continue regular watering schedule — deep watering once or twice per week for most crops. Avoid overhead irrigation to reduce humidity-related risks.'
                : `For ${crop} affected by ${pretty_label}: reduce overhead irrigation immediately. Use drip irrigation to deliver water directly to roots. Allow topsoil to dry slightly between waterings.`
              }
            </Accordion>
            <Accordion title="Weather Risk Assessment" icon={<Cloud size={14} color="#2563eb" />}>
              Humid conditions above 80% RH and temperatures between 20–28°C significantly increase fungal disease risk.
              Monitor forecasts closely and apply preventive fungicide sprays before forecast rain events lasting more than 6 hours.
            </Accordion>
            <Accordion title="Sustainability & Organic Options" icon={<Recycle size={14} color="var(--amber)" />}>
              Organic alternatives: neem oil spray (5ml/L), copper-based formulations, or Trichoderma biofungicides.
              These are effective for early-stage infections and approved for certified organic operations.
              Rotate with synthetic fungicides (different MOA groups) to prevent resistance development.
            </Accordion>
          </div>
        </div>

        {/* Disclaimer */}
        <div style={{ display: 'flex', gap: 8, background: 'var(--ink-100)', borderRadius: 8, padding: '10px 14px', fontSize: '.78rem', color: 'var(--text-muted)' }}>
          <Info size={14} style={{ flexShrink: 0, marginTop: 1 }} />
          <span>This analysis is AI-generated and intended as a decision support tool only. Always consult a certified agronomist for critical crop management decisions.</span>
        </div>
      </div>
    </div>
  )
}
