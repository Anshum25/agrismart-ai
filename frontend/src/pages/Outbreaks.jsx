import { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { AlertTriangle, MapPin, Loader2, Bell } from 'lucide-react'
import { api } from '../lib/api'
import { CROP_COLORS, formatLabel } from '../lib/labels'
import { useLocation as useGeoLocation, useOnline } from '../lib/hooks'
import { useI18n } from '../i18n'

const INDIA_CENTER = [22.5, 79]
const DAY_OPTIONS = [7, 14, 30]

export default function Outbreaks() {
  const { t, lang } = useI18n()
  const online = useOnline()
  const geo = useGeoLocation()
  const [days, setDays] = useState(14)
  const [crop, setCrop] = useState('')
  const [includeDemo, setIncludeDemo] = useState(true)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [alerts, setAlerts] = useState(null)
  const [alertsLoading, setAlertsLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    setError(null)
    api.aggregate({ days, crop, include_demo: includeDemo })
      .then(d => !cancelled && setData(d))
      .catch(err => !cancelled && setError(err.message))
    return () => { cancelled = true }
  }, [days, crop, includeDemo, online])

  const crops = useMemo(() => Object.keys(CROP_COLORS).sort(), [])
  const cells = data?.cells || []
  const fmtDate = iso => new Date(iso).toLocaleDateString(lang, { day: 'numeric', month: 'short' })

  const checkAlerts = async () => {
    const loc = geo.location || await geo.request()
    if (!loc) return
    setAlertsLoading(true)
    try {
      const res = await api.alerts({ lat: loc.lat, lon: loc.lon, radius_km: 25, days: 7, include_demo: includeDemo })
      setAlerts(res.alerts)
    } catch (err) {
      setError(err.message)
    } finally {
      setAlertsLoading(false)
    }
  }

  return (
    <div className="outbreaks-page">
      <div className="page-hero">
        <div className="container">
          <div className="hero-chip">📡 {t('map.badge')}</div>
          <h1>{t('map.title')}</h1>
          <p>{t('map.subtitle')}</p>
        </div>
      </div>

      <div className="container" style={{ marginTop: -20 }}>
        <div className="outbreak-layout">
          <div className="card map-card">
            <div className="map-filters">
              <div className="segmented" role="group">
                {DAY_OPTIONS.map(d => (
                  <button key={d} className={days === d ? 'active' : ''} onClick={() => setDays(d)}>{t('map.days', { days: d })}</button>
                ))}
              </div>
              <label className="select-field">
                <span>{t('map.crop')}</span>
                <select value={crop} onChange={e => setCrop(e.target.value)}>
                  <option value="">{t('map.allCrops')}</option>
                  {crops.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </label>
              <label className="check-field">
                <input type="checkbox" checked={includeDemo} onChange={e => setIncludeDemo(e.target.checked)} />
                <span>{t('map.includeSimulated')}</span>
              </label>
            </div>

            {data?.has_simulated && includeDemo && (
              <div className="alert alert-warn"><AlertTriangle size={15} /> <span>{t('map.simulatedNote')}</span></div>
            )}
            {error && <div className="alert alert-warn"><AlertTriangle size={15} /> <span>{t('map.error')} {error}</span></div>}

            <div className="map-frame">
              {!data && !error && <div className="map-loading"><Loader2 className="spin" /> {t('map.loading')}</div>}
              <MapContainer center={INDIA_CENTER} zoom={5} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {cells.map(cell => {
                  const color = cell.is_healthy ? '#059669' : (CROP_COLORS[cell.crop] || '#b91c1c')
                  return (
                    <CircleMarker
                      key={`${cell.lat},${cell.lon},${cell.label}`}
                      center={[cell.lat, cell.lon]}
                      radius={Math.min(6 + Math.sqrt(cell.count) * 4, 26)}
                      pathOptions={{ color, fillColor: color, fillOpacity: cell.is_healthy ? 0.25 : 0.45, weight: 1.5, dashArray: cell.simulated ? '4 3' : null }}
                    >
                      <Popup>
                        <strong>{formatLabel(cell.label)}</strong><br />
                        {t('map.reports', { count: cell.count })} · {t('map.lastSeen', { date: fmtDate(cell.last_seen) })}
                        {cell.simulated && <><br /><em>{t('map.simulated')}</em></>}
                      </Popup>
                    </CircleMarker>
                  )
                })}
              </MapContainer>
            </div>

            <div className="map-legend">
              {crops.map(c => (
                <span key={c} className="legend-item"><span className="legend-dot" style={{ background: CROP_COLORS[c] }} />{c}</span>
              ))}
              <span className="legend-item"><span className="legend-dot" style={{ background: '#059669', opacity: 0.5 }} />{t('map.healthy')}</span>
              <span className="legend-item"><span className="legend-dot dashed" />{t('map.simulated')}</span>
            </div>
          </div>

          <aside className="card alerts-card">
            <h3 className="panel-title"><Bell size={17} color="var(--amber)" /> {t('map.alertsTitle')}</h3>
            <p className="muted-line">{t('map.alertsHint')}</p>
            <button className="btn btn-primary btn-sm" onClick={checkAlerts} disabled={alertsLoading || geo.pending}>
              {alertsLoading || geo.pending ? <Loader2 size={14} className="spin" /> : <MapPin size={14} />} {t('map.findAlerts')}
            </button>
            {geo.error === 'denied' && <p className="note">{t('diag.locationDenied')}</p>}
            {alerts && alerts.length === 0 && <p className="success-line">{t('map.noAlerts')}</p>}
            {alerts?.map(a => (
              <div key={a.label} className="alert-row">
                <span className="legend-dot" style={{ background: CROP_COLORS[a.crop] || '#b91c1c' }} />
                <div>
                  <div className="history-label">{formatLabel(a.label)}</div>
                  <div className="history-meta">
                    {t('map.reports', { count: a.count })} · {t('map.nearest', { km: a.nearest_km })}
                    {a.simulated && ` · ${t('map.simulated')}`}
                  </div>
                </div>
              </div>
            ))}
          </aside>
        </div>
      </div>
    </div>
  )
}
