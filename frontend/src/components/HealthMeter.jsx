import { CheckCircle, AlertTriangle } from 'lucide-react'
import { useI18n } from '../i18n'

/** Good vs bad share of the leaf. Healthy leaves are shown as 100% good. */
export default function HealthMeter({ health, isHealthy, compact = false, dark = false }) {
  const { t } = useI18n()
  if (!health) return null
  const { good_pct: good, bad_pct: bad } = health

  return (
    <div className={`health-meter ${compact ? 'compact' : ''} ${dark ? 'dark' : ''}`}>
      <div className="health-meter-head">
        {isHealthy ? (
          <span className="health-verdict good"><CheckCircle size={16} /> {t('health.allGood')}</span>
        ) : (
          <span className="health-verdict bad"><AlertTriangle size={16} /> {t('health.needsCare')}</span>
        )}
      </div>
      <div className="health-bar" role="img" aria-label={`${t('health.good')} ${good}%, ${t('health.bad')} ${bad}%`}>
        <span className="health-good" style={{ width: `${good}%` }} />
        <span className="health-bad" style={{ width: `${bad}%` }} />
      </div>
      <div className="health-legend">
        <span><i className="dot good" /> {t('health.good')} <strong>{good}%</strong></span>
        <span><i className="dot bad" /> {t('health.bad')} <strong>{bad}%</strong></span>
      </div>
    </div>
  )
}
