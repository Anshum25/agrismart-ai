import { useEffect, useState } from 'react'

/**
 * Animated confidence progress bar.
 * Props:
 *   value: number  0..1
 *   note?: string
 */
export default function ConfidenceBar({ value, note }) {
  const [width, setWidth] = useState(0)
  const pct = Math.round(value * 100)

  // Animate on mount
  useEffect(() => {
    const t = requestAnimationFrame(() => setWidth(pct))
    return () => cancelAnimationFrame(t)
  }, [pct])

  const color =
    pct >= 85 ? 'var(--leaf)' :
    pct >= 60 ? 'var(--amber)' :
    'var(--red)'

  return (
    <div id="confidence-bar-wrap" style={{ marginTop: '1rem' }}>
      <div className="conf-label">
        <span>Model Confidence</span>
        <span style={{ color }}>{pct}%</span>
      </div>
      <div className="conf-track">
        <div
          className="conf-fill"
          style={{ width: `${width}%`, background: `linear-gradient(90deg, ${color}, var(--leaf-light))` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      {note && <p className="conf-note">{note}</p>}
    </div>
  )
}
