import { useEffect, useState } from 'react'
import { Cloud, Droplets, Recycle, BarChart2, CalendarCheck } from 'lucide-react'
import { api } from '../lib/api'
import { useI18n } from '../i18n'
import { useOnline } from '../lib/hooks'

const RISK_CLASS = { low: 'risk-low', moderate: 'risk-moderate', high: 'risk-high' }

function ForecastStrip({ forecast, lang }) {
  const { t } = useI18n()
  const fmt = date => new Date(`${date}T12:00:00`).toLocaleDateString(lang, { weekday: 'short', day: 'numeric' })
  return (
    <div>
      <div className="forecast-strip">
        {forecast.days.map(d => (
          <div key={d.date} className={`forecast-day ${RISK_CLASS[d.risk_level]}`} title={`${d.temp_min}–${d.temp_max} °C · ${d.rain_mm} mm`}>
            <span className="forecast-date">{fmt(d.date)}</span>
            <span className="forecast-level">{t(`risk.${d.risk_level}`)}</span>
            <span className="forecast-meta">{Math.round(d.temp_max)}° · {d.rain_mm.toFixed(0)}mm</span>
          </div>
        ))}
      </div>
      <p className="spray-callout">
        <CalendarCheck size={15} />
        {forecast.best_spray_day ? t('forecast.spray', { day: fmt(forecast.best_spray_day.date) }) : t('forecast.noSpray')}
      </p>
    </div>
  )
}

export default function InsightsPanel({ label, location }) {
  const { t, lang } = useI18n()
  const online = useOnline()
  const [insights, setInsights] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [forecastError, setForecastError] = useState(false)

  useEffect(() => {
    if (!online || !label) return
    let cancelled = false
    api.insights(label, location).then(d => !cancelled && setInsights(d)).catch(() => {})
    if (location) {
      setForecastError(false)
      api.forecast(label, location)
        .then(d => !cancelled && setForecast(d))
        .catch(() => !cancelled && setForecastError(true))
    }
    return () => { cancelled = true }
  }, [label, location?.lat, location?.lon, online])

  if (!online && !insights) {
    return <div className="panel"><p className="note">{t('insights.unavailable')}</p></div>
  }

  const risk = insights?.weather_risk
  const irrigation = insights?.irrigation
  const sustainability = insights?.sustainability

  return (
    <div className="panel">
      <div className="panel-head">
        <span className="panel-title"><BarChart2 size={16} color="var(--forest-light)" /> {t('insights.title')}</span>
      </div>

      {insights && (
        <div className="insight-grid">
          <div className="insight">
            <span className="insight-label"><Cloud size={14} /> {t('insights.weatherRisk')}</span>
            <span className={`insight-value ${RISK_CLASS[risk.risk_level]}`}>{t(`risk.${risk.risk_level}`)} · {risk.risk_score}/100</span>
            <span className="insight-sub">{risk.weather.temperature_c}°C · {risk.weather.humidity_pct}% RH · {risk.weather.rainfall_mm} mm</span>
          </div>
          <div className="insight">
            <span className="insight-label"><Droplets size={14} /> {t('insights.irrigation')}</span>
            <span className="insight-value">{t('insights.water', { mm: irrigation.daily_water_mm, hours: irrigation.next_watering_hours })}</span>
            {irrigation.soil_moisture_assumed && <span className="insight-sub">{t('insights.assumed')}</span>}
          </div>
          <div className="insight">
            <span className="insight-label"><Recycle size={14} /> {t('insights.sustainability')}</span>
            <span className="insight-value">{sustainability.grade} · {sustainability.score}/100</span>
            <span className="insight-sub">{sustainability.recommended_treatments.join(', ')}</span>
          </div>
        </div>
      )}
      {insights?.location?.is_default && <p className="note">{t('insights.defaultLocation')}</p>}

      <h4 className="subhead">{t('forecast.title')}</h4>
      {!location ? <p className="note">{t('forecast.needLocation')}</p>
        : forecast ? <ForecastStrip forecast={forecast} lang={lang} />
        : forecastError ? <p className="note">{t('forecast.unavailable')}</p>
        : <div className="skeleton" style={{ height: 64 }} />}
    </div>
  )
}
