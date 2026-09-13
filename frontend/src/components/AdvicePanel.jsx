import { useEffect, useState } from 'react'
import { Leaf, Zap, ShieldCheck, Sprout, FlaskConical, Droplets, CloudRain, Volume2, Square, Loader2 } from 'lucide-react'
import { api } from '../lib/api'
import { speak, stopSpeaking, speechSupported } from '../lib/speech'
import { useI18n } from '../i18n'

async function loadOfflineAdvice(label, lang) {
  for (const code of [lang, 'en']) {
    try {
      const res = await fetch(`/offline/advice_${code}.json`)
      if (!res.ok) continue
      const pack = await res.json()
      const entry = pack.advice?.[label]
      if (entry) return { ...entry, source: code === 'en' && lang !== 'en' ? 'knowledge_base' : 'offline', lang: code }
    } catch { /* keep trying */ }
  }
  return null
}

export function useAdvice(label, lang) {
  const [state, setState] = useState({ advice: null, loading: true })
  useEffect(() => {
    if (!label) return
    let cancelled = false
    setState({ advice: null, loading: true })
    ;(async () => {
      let advice = null
      if (navigator.onLine) {
        try { advice = await api.advice(label, lang) } catch { /* fall back */ }
      }
      if (!advice) advice = await loadOfflineAdvice(label, lang)
      if (!cancelled) setState({ advice, loading: false })
    })()
    return () => { cancelled = true }
  }, [label, lang])
  return state
}

function Section({ icon, title, items, text }) {
  if (!(items?.length) && !text) return null
  return (
    <div className="advice-section">
      <h4>{icon} {title}</h4>
      {items?.length ? <ul>{items.map((item, i) => <li key={i}>{item}</li>)}</ul> : <p>{text}</p>}
    </div>
  )
}

export function adviceToSpeech(advice, t) {
  if (!advice) return ''
  return [
    advice.summary,
    `${t('advice.immediate')}: ${(advice.immediate_steps || []).join('. ')}`,
    `${t('advice.organic')}: ${(advice.organic_options || []).join('. ')}`,
  ].join('. ')
}

export default function AdvicePanel({ advice, loading }) {
  const { t, bcp47 } = useI18n()
  const [speaking, setSpeaking] = useState(false)
  const [noVoice, setNoVoice] = useState(false)

  useEffect(() => () => stopSpeaking(), [])
  useEffect(() => { stopSpeaking(); setSpeaking(false); setNoVoice(false) }, [advice])

  const toggleSpeech = async () => {
    if (speaking) { stopSpeaking(); setSpeaking(false); return }
    const voiceLang = advice.lang === 'en' ? 'en-IN' : bcp47
    const ok = await speak(adviceToSpeech(advice, t), voiceLang, { onEnd: () => setSpeaking(false) })
    setSpeaking(ok)
    setNoVoice(!ok)
  }

  return (
    <div className="advice-card">
      <div className="panel-head">
        <span className="panel-title"><Leaf size={16} color="var(--forest-light)" /> {t('advice.title')}</span>
        {advice && (
          <span className="flex items-center gap-2">
            <span className="tag tag-green">{t(`advice.source.${advice.source}`)}</span>
            {speechSupported() && (
              <button className="btn btn-outline btn-sm" onClick={toggleSpeech}>
                {speaking ? <><Square size={13} /> {t('advice.stop')}</> : <><Volume2 size={14} /> {t('advice.listen')}</>}
              </button>
            )}
          </span>
        )}
      </div>

      {loading && <p className="muted-line"><Loader2 size={14} className="spin" /> {t('advice.loading')}</p>}
      {noVoice && <p className="note">{t('advice.noVoice')}</p>}

      {advice && (
        <>
          {advice.summary && <p className="advice-summary">{advice.summary}</p>}
          {advice.pathogen && <p className="advice-pathogen">{advice.pathogen}</p>}
          <Section icon={<Zap size={14} />} title={t('advice.immediate')} items={advice.immediate_steps} />
          <Section icon={<ShieldCheck size={14} />} title={t('advice.prevention')} items={advice.prevention} />
          <div className="advice-two-col">
            <Section icon={<Sprout size={14} />} title={t('advice.organic')} items={advice.organic_options} />
            <Section icon={<FlaskConical size={14} />} title={t('advice.chemical')} items={advice.chemical_options} />
          </div>
          <Section icon={<Droplets size={14} />} title={t('advice.irrigation')} text={advice.irrigation_tip} />
          <Section icon={<CloudRain size={14} />} title={t('advice.weather')} text={advice.weather_watch} />
        </>
      )}
    </div>
  )
}
