import { Link } from 'react-router-dom'
import { LucideActivity, LucideBrain, LucideLeaf, LucideSun } from 'lucide-react'

export default function Home() {
  return (
    <>
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <div className="hero-badge">🌿 AI-Powered Crop Diagnostics</div>
          <h1>
            Protect your yield with <span>AgriSmart AI</span>
          </h1>
          <p className="hero-sub">
            Real-time plant disease detection powered by ResNet50. Upload a leaf photo and get instant Grad-CAM visual explanations and Gemini-powered care advice.
          </p>
          <div className="hero-actions">
            <Link to="/diagnose" className="btn btn-primary btn-lg">
              🚀 Start Diagnosis
            </Link>
            <Link to="/about" className="btn btn-outline btn-lg">
              View Model Metrics
            </Link>
          </div>

          <div className="hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value">98.9%</span>
              <span className="hero-stat-label">Test Accuracy</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">38</span>
              <span className="hero-stat-label">Crop Categories</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">&lt; 1s</span>
              <span className="hero-stat-label">Inference Time</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="section container">
        <div className="text-center mb-3">
          <span className="section-label">Features</span>
          <h2 className="section-title">Smart Farming Tools</h2>
          <p className="section-sub mx-auto" style={{ margin: '0 auto 3rem' }}>
            A complete suite of diagnostic and preventive tools designed for modern sustainable agriculture.
          </p>
        </div>

        <div className="grid-3">
          <div className="card card-feature">
            <div className="card-feature-icon" style={{ color: 'var(--leaf)' }}>
              <LucideBrain size={28} />
            </div>
            <h3>Explainable AI</h3>
            <p>
              We don't just give you a label. Our Grad-CAM heatmaps show you exactly which visual patterns (like lesions or spots) the neural network used to make its decision.
            </p>
          </div>
          <div className="card card-feature">
            <div className="card-feature-icon" style={{ color: 'var(--amber)' }}>
              <LucideActivity size={28} />
            </div>
            <h3>Actionable Care Plans</h3>
            <p>
              Powered by Google Gemini, get plain-language treatment advice, biological control methods, and preventive measures tailored to the specific disease detected.
            </p>
          </div>
          <div className="card card-feature">
            <div className="card-feature-icon" style={{ color: 'var(--sky)' }}>
              <LucideSun size={28} />
            </div>
            <h3>Smart Irrigation Advisory</h3>
            <p>
              Prevent fungal spore germination with optimized watering schedules and microclimate risk forecasts based on the specific pathogen profile.
            </p>
          </div>
        </div>
      </section>
    </>
  )
}
