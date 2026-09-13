import { useState } from 'react'
import { Users, CheckCircle, Loader2 } from 'lucide-react'
import { api } from '../lib/api'
import { queueReport } from '../lib/offlineStore'
import { useI18n } from '../i18n'

export default function SharePanel({ result, location, onRequestLocation }) {
  const { t } = useI18n()
  const [state, setState] = useState('idle') // idle | sending | done | queued | error
  const [error, setError] = useState(null)

  if (result.status !== 'ok') {
    return <div className="panel"><p className="note">{t('share.lowConfidence')}</p></div>
  }

  const share = async () => {
    let loc = location
    if (!loc) loc = await onRequestLocation()
    if (!loc) { setError(t('share.needLocation')); return }
    const report = { label: result.label, confidence: result.confidence, lat: loc.lat, lon: loc.lon }
    setState('sending')
    setError(null)
    if (!navigator.onLine) {
      await queueReport(report)
      setState('queued')
      return
    }
    try {
      await api.createReport(report)
      setState('done')
    } catch (err) {
      if (err.status === 0) { await queueReport(report); setState('queued') }
      else { setError(err.message); setState('error') }
    }
  }

  return (
    <div className="panel share-panel">
      <div className="panel-head">
        <span className="panel-title"><Users size={16} color="var(--forest-light)" /> {t('share.title')}</span>
      </div>
      <p className="muted-line">{t('share.hint')}</p>
      {state === 'done' || state === 'queued' ? (
        <p className="success-line"><CheckCircle size={15} /> {t(state === 'done' ? 'share.done' : 'share.queued')}</p>
      ) : (
        <button className="btn btn-outline btn-sm" onClick={share} disabled={state === 'sending'}>
          {state === 'sending' ? <Loader2 size={14} className="spin" /> : <Users size={14} />} {t('share.button')}
        </button>
      )}
      {error && <p className="note">{error}</p>}
    </div>
  )
}
