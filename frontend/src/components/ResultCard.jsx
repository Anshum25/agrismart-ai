import { AlertTriangle, Info, Smartphone, Server, Camera } from 'lucide-react'
import { useI18n } from '../i18n'
import AdvicePanel, { useAdvice } from './AdvicePanel'
import HealthMeter from './HealthMeter'
import VoiceAssistant from './VoiceAssistant'
import InsightsPanel from './InsightsPanel'
import SharePanel from './SharePanel'

const SEVERITY_CLASS = {
  healthy: 'severity-healthy',
  mild: 'severity-low',
  moderate: 'severity-moderate',
  severe: 'severity-high',
}

export function RejectCard({ reason, onRetake }) {
  const { t } = useI18n()
  return (
    <div className="card reject-card">
      <div className="reject-icon"><Camera size={28} /></div>
      <h3>{t('reject.title')}</h3>
      <p className="reject-reason">{t(`reject.${reason}`)}</p>
      <ul className="tips">
        <li>{t('reject.tip1')}</li>
        <li>{t('reject.tip2')}</li>
        <li>{t('reject.tip3')}</li>
      </ul>
      <button className="btn btn-primary" onClick={onRetake}><Camera size={16} /> {t('diag.change')}</button>
    </div>
  )
}

export default function ResultCard({ result, previewUrl, location, onRequestLocation }) {
  const { t, lang } = useI18n()
  const { advice, loading } = useAdvice(result.label, lang)
  const pct = Math.round(result.confidence * 1000) / 10
  const uncertain = result.status === 'uncertain'

  return (
    <div className="result-stack">
      <div className="result-wrapper">
        <div className="result-header">
          <div className="result-header-row">
            <div>
              <div className="result-crop-name">{t('result.detectedOn', { crop: result.crop })}</div>
              <div className="result-disease-name">{result.pretty_label}</div>
              <div className="flex items-center gap-2" style={{ flexWrap: 'wrap' }}>
                <span className={`severity-badge ${SEVERITY_CLASS[result.severity]}`}>{t(`severity.${result.severity}`)}</span>
                <span className="severity-badge badge-muted">
                  {result.inference === 'device' ? <><Smartphone size={12} /> {t('result.onDevice')}</> : <><Server size={12} /> {t('result.server')}</>}
                </span>
              </div>
              {!result.is_healthy && (
                <div className="result-affected">{t('result.affected', { pct: result.affected_area_pct })}</div>
              )}
            </div>
            <div className="result-confidence">
              <div className={`result-confidence-value ${uncertain ? 'uncertain' : ''}`}>{pct}%</div>
              <div className="result-confidence-label">{t('result.confidence')}</div>
            </div>
          </div>
          <div className="confidence-bar-track" style={{ background: 'rgba(255,255,255,.15)', marginTop: 16 }}>
            <div
              className="confidence-bar-fill"
              style={{ width: `${pct}%`, background: uncertain ? 'linear-gradient(90deg,#fbbf24,#f59e0b)' : 'linear-gradient(90deg,#6ee7b7,#10b981)' }}
            />
          </div>
        </div>

        <div className="result-body">
          {uncertain && (
            <div className="alert alert-warn"><AlertTriangle size={16} /> <span>{t('result.uncertain')}</span></div>
          )}
          {result.warnings?.includes('slightly_blurry') && (
            <div className="alert alert-info"><Info size={16} /> <span>{t('result.slightlyBlurry')}</span></div>
          )}

          <HealthMeter health={result.health} isHealthy={result.is_healthy} />

          <div className="image-pair">
            {previewUrl && (
              <div className="image-pair-item">
                <img src={previewUrl} alt={t('result.original')} />
                <div className="image-pair-caption">{t('result.original')}</div>
              </div>
            )}
            {result.gradcam_image && (
              <div className="image-pair-item">
                <img src={result.gradcam_image} alt={t('result.heatmap')} />
                <div className="image-pair-caption">{t('result.heatmap')}</div>
              </div>
            )}
          </div>

          <div className="top3">
            <h4 className="subhead">{t('result.top3')}</h4>
            {result.top3.map(m => (
              <div key={m.label} className="top3-row">
                <span className="top3-label">{m.pretty_label}</span>
                <span className="top3-bar"><span style={{ width: `${m.confidence * 100}%` }} /></span>
                <span className="top3-pct">{(m.confidence * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <AdvicePanel advice={advice} loading={loading} />
      <VoiceAssistant result={result} />
      <InsightsPanel label={result.label} location={location} />
      <SharePanel result={result} location={location} onRequestLocation={onRequestLocation} />

      <div className="disclaimer">
        <Info size={14} style={{ flexShrink: 0, marginTop: 1 }} />
        <span>{t('result.disclaimer')}</span>
      </div>
    </div>
  )
}
