import { LucideAlertTriangle, LucideCheckCircle2, LucideInfo } from 'lucide-react'
import ConfidenceBar from './ConfidenceBar.jsx'

/**
 * Result display card showing disease info, severity, and GradCAM.
 * Props:
 *   result: { label, pretty_label, crop, confidence, is_healthy, severity, advice, original_image_b64, gradcam_image_b64 }
 */
export default function ResultCard({ result }) {
  if (!result) return null

  const isHealthy = result.is_healthy
  const Icon = isHealthy ? LucideCheckCircle2 : (result.severity === 'Severe' ? LucideAlertTriangle : LucideInfo)
  const iconColor = isHealthy ? 'var(--leaf)' : (result.severity === 'Severe' ? 'var(--red)' : 'var(--amber)')

  return (
    <div className="result-card" id="diagnosis-result">
      {/* Header */}
      <div className="result-header">
        <Icon className="result-icon" color={iconColor} size={42} />
        <div>
          <h2 className="result-title">{result.pretty_label.split('—').pop().trim()}</h2>
          <p className="result-crop">Detected on: {result.crop}</p>
        </div>
      </div>

      {/* Badges */}
      <div className="flex gap-1 mb-2">
        <span className={`badge badge-${result.severity.toLowerCase()}`}>
          {isHealthy ? 'Healthy Plant' : `${result.severity} Severity`}
        </span>
        {!isHealthy && (
          <span className="badge" style={{ background: 'var(--sand)', color: 'var(--forest)' }}>
            Disease Detected
          </span>
        )}
      </div>

      {/* Confidence */}
      <ConfidenceBar value={result.confidence} note="ResNet50 AI Prediction Score" />

      {/* GradCAM Images */}
      {result.original_image_b64 && result.gradcam_image_b64 && (
        <div className="gradcam-grid">
          <div>
            <div className="gradcam-img-wrap">
              <img src={`data:image/png;base64,${result.original_image_b64}`} alt="Original Leaf" />
            </div>
            <p className="gradcam-caption">Original Upload</p>
          </div>
          <div>
            <div className="gradcam-img-wrap">
              <img src={`data:image/png;base64,${result.gradcam_image_b64}`} alt="Grad-CAM Overlay" />
            </div>
            <p className="gradcam-caption">AI Focus (Grad-CAM Heatmap)</p>
          </div>
        </div>
      )}

      {/* Advice Panel */}
      {!isHealthy && result.advice && (
        <div className="advice-panel">
          <h4><span style={{fontSize: '1.2rem'}}>🌱</span> AI Agronomist Advice</h4>
          <div dangerouslySetInnerHTML={{ __html: result.advice.replace(/\n/g, '<br/>') }} />
        </div>
      )}
    </div>
  )
}
