import { useEffect, useState } from 'react'
import { LucideCheckCircle, LucideXCircle } from 'lucide-react'

export default function About() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.error(err))
  }, [])

  return (
    <div className="section container">
      <div className="text-center mb-4">
        <h1 className="section-title">Architecture & Metrics</h1>
        <p className="section-sub mx-auto">Transparent engineering documentation for hackathon judges.</p>
      </div>

      <div className="card mb-4">
        <h3 className="mb-2">Backend Status</h3>
        <div className="flex items-center gap-1 mb-2">
          {health?.model_loaded ? (
            <><LucideCheckCircle color="var(--leaf)" size={20} /> <strong>Model Loaded:</strong> ResNet50 Weights Active</>
          ) : (
            <><LucideXCircle color="var(--red)" size={20} /> <strong>Model Status:</strong> Demo Mode (Weights not found)</>
          )}
        </div>
        {!health?.model_loaded && health?.model_error && (
          <div className="text-muted" style={{ fontSize: '0.85rem', background: 'var(--sand)', padding: '1rem', borderRadius: '8px' }}>
            {health.model_error}
          </div>
        )}
      </div>

      <div className="grid-3 mb-4">
        <div className="metric-card">
          <div className="metric-value">{health ? `${(health.test_accuracy * 100).toFixed(2)}%` : '--'}</div>
          <div className="metric-label">Test Accuracy</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{health ? `${(health.val_accuracy * 100).toFixed(2)}%` : '--'}</div>
          <div className="metric-label">Validation Accuracy</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{health?.classes || '--'}</div>
          <div className="metric-label">Crop/Disease Classes</div>
        </div>
      </div>

      <div className="card">
        <h3 className="mb-2">Technical Stack</h3>
        <ul style={{ paddingLeft: '1.2rem', lineHeight: '1.8' }}>
          <li><strong>Frontend:</strong> React, Vite, React Router, custom CSS design system.</li>
          <li><strong>Backend:</strong> FastAPI, Python, Uvicorn.</li>
          <li><strong>Deep Learning:</strong> TensorFlow/Keras, Transfer Learning (ResNet50).</li>
          <li><strong>Explainable AI:</strong> Custom Grad-CAM implementation.</li>
          <li><strong>GenAI:</strong> Google Gemini 2.0 Flash for agronomist care advice.</li>
        </ul>
      </div>
    </div>
  )
}
