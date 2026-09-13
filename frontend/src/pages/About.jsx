import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, API_DOCS_URL } from '../lib/api'
import {
  Brain, Layers, Code2, Zap, Leaf, Target, Users, BookOpen,
  CheckCircle, ExternalLink
} from 'lucide-react'

const FadeUp = ({ children, delay = 0, className = '' }) => (
  <motion.div
    className={className}
    initial={{ opacity: 0, y: 28 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: '-60px' }}
    transition={{ duration: .55, delay, ease: [.4, 0, .2, 1] }}
  >
    {children}
  </motion.div>
)

const TECH_STACK = [
  { name: 'TensorFlow / Keras', role: 'Model training & inference', icon: <Brain size={18} />, color: 'feat-icon-amber' },
  { name: 'ResNet50', role: 'CNN backbone (ImageNet pretrained)', icon: <Layers size={18} />, color: 'feat-icon-green' },
  { name: 'FastAPI + Uvicorn', role: 'High-performance Python API server', icon: <Zap size={18} />, color: 'feat-icon-green' },
  { name: 'React + Vite', role: 'Modern frontend framework', icon: <Code2 size={18} />, color: 'feat-icon-blue' },
  { name: 'Groq GPT-OSS 120B + Whisper', role: 'Vernacular advice and voice assistant', icon: <Brain size={18} />, color: 'feat-icon-amber' },
  { name: 'ONNX Runtime + Grad-CAM', role: 'On-device inference and explainability', icon: <Target size={18} />, color: 'feat-icon-red' },
]

const ARCH_POINTS = [
  'Transfer learning from ImageNet — leverages visual feature representations learned from millions of images.',
  'The deployed checkpoint is Phase 1: the ResNet50 backbone is frozen and only the classification head is trained (88.6% accuracy verified on 1,500 PlantVillage images). Phase 2, unfreezing the last 30 layers, is supported by the training script and is the next accuracy improvement.',
  'Stratified 70/15/15 train/val/test split ensures representative class distribution across all splits.',
  'Augmentation pipeline: horizontal/vertical flips, random rotation (±25°), shifts, shear, zoom (15%) and brightness (0.8–1.2).',
  'Callbacks: EarlyStopping (patience=5), ReduceLROnPlateau (factor=0.5, patience=2), ModelCheckpoint for best weights.',
  'Export: the Keras model is converted to an ONNX model with two outputs (features + probabilities), verified against Keras for accuracy and Grad-CAM parity, and runs both in the browser and on the API.',
]

export default function About() {
  const [health, setHealth] = useState(null)

  const [healthError, setHealthError] = useState(false)

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealthError(true))
  }, [])

  return (
    <>
      {/* Hero */}
      <div className="about-hero">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: .55 }}
          >
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'rgba(255,255,255,.12)', border: '1px solid rgba(255,255,255,.2)', color: 'rgba(255,255,255,.9)', fontSize: '.75rem', fontWeight: 700, letterSpacing: '.1em', textTransform: 'uppercase', padding: '3px 12px', borderRadius: 999, marginBottom: 14 }}>
              <BookOpen size={11} /> SIH 2026 · Problem Statement
            </div>
            <h1>About AgriSmart AI</h1>
            <p>
              An end-to-end plant disease diagnostic platform combining deep learning,
              explainability, and generative AI — built for the Smart India Hackathon 2026.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Live Backend Status */}
      <div style={{ background: health?.model_loaded ? 'rgba(5,150,105,.06)' : 'rgba(217,119,6,.06)', borderBottom: '1px solid rgba(0,0,0,.07)', padding: '14px 0' }}>
        <div className="container">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            {health?.model_loaded
              ? <><CheckCircle size={16} color="var(--forest-light)" /> <span style={{ fontWeight: 600, fontSize: '.9rem', color: 'var(--forest)' }}>API online — ResNet50 ONNX model loaded ({health.quantization})</span></>
              : <><Zap size={16} color="var(--amber)" /> <span style={{ fontWeight: 600, fontSize: '.9rem', color: 'var(--amber)' }}>
                  {health ? 'API online — server model not loaded (diagnosis runs on-device when available)'
                    : healthError ? 'API unreachable — offline features still work' : 'Connecting to API… (free servers can take up to a minute to wake)'}
                </span></>
            }
            {health && (
              <span style={{ marginLeft: 'auto', fontSize: '.8rem', color: 'var(--text-muted)' }}>
                {health.classes ? `Model classes: ${health.classes} · ` : ''}AI advice: {health.ai_advice_enabled ? 'on' : 'offline guide'}
                {API_DOCS_URL && <> · <a href={API_DOCS_URL} target="_blank" rel="noreferrer" style={{ color: 'var(--forest-light)', textDecoration: 'none' }}>API Docs <ExternalLink size={11} /></a></>}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Problem */}
      <section className="section about-section">
        <div className="container">
          <div className="about-grid">
            <FadeUp>
              <div className="section-label"><Target size={11} /> The Problem</div>
              <h2 className="section-title">Crop Disease Costs Billions Annually</h2>
              <p style={{ marginBottom: 16 }}>
                Plant diseases and pests destroy up to <strong>40% of global food production</strong> every year, costing
                the agricultural sector an estimated $220 billion. For smallholder farmers in India, an undetected
                fungal infection can wipe out an entire season's income.
              </p>
              <p style={{ marginBottom: 16 }}>
                The challenge isn't just detection accuracy on clean benchmark images — it's building a system
                that <em>explains its reasoning</em> in a way that earns a farmer's trust, and provides
                <em>actionable guidance</em> rather than just a label.
              </p>
              <p>
                AgriSmart AI addresses all three dimensions: <strong>accurate detection</strong>,
                <strong> visual explanation (Grad-CAM)</strong>, and <strong>language-model-generated care advice</strong>.
              </p>
            </FadeUp>

            <FadeUp delay={.1}>
              <div className="stat-grid-2">
                {[
                  { num: '40%', desc: 'of global food production lost to disease & pests annually' },
                  { num: '$220B', desc: 'annual economic cost of crop disease worldwide' },
                  { num: '38', desc: 'disease classes detected by AgriSmart AI' },
                  { num: '88.6%', desc: 'verified accuracy of the deployed model (PlantVillage)' },
                ].map(s => (
                  <div key={s.num} className="metric-card">
                    <div className="metric-value">{s.num}</div>
                    <div className="metric-label">{s.desc}</div>
                  </div>
                ))}
              </div>
            </FadeUp>
          </div>
        </div>
      </section>

      {/* Approach */}
      <section className="section" style={{ background: 'var(--cream-dark)' }}>
        <div className="container">
          <FadeUp className="text-center" style={{ marginBottom: 48 }}>
            <div className="section-label"><Brain size={11} /> Technical Approach</div>
            <h2 className="section-title">How the Model Was Built</h2>
          </FadeUp>

          <div className="approach-grid">
            <FadeUp>
              <h3 style={{ marginBottom: 20 }}>Training Pipeline</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {ARCH_POINTS.map((p, i) => (
                  <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                    <div style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--forest)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, flexShrink: 0, marginTop: 2 }}>
                      {i + 1}
                    </div>
                    <p style={{ fontSize: '.9rem', margin: 0 }}>{p}</p>
                  </div>
                ))}
              </div>
            </FadeUp>

            <FadeUp delay={.1}>
              <h3 style={{ marginBottom: 20 }}>Model Architecture</h3>
              <div className="card" style={{ padding: 0, overflow: 'hidden', fontFamily: 'monospace', fontSize: '.82rem' }}>
                <div style={{ background: '#1e293b', color: '#e2e8f0', padding: '14px 20px', fontSize: '.75rem', fontWeight: 600, letterSpacing: '.06em', textTransform: 'uppercase' }}>Model Summary</div>
                {[
                  { layer: 'Input', shape: '(224, 224, 3)', color: '#6ee7b7' },
                  { layer: 'ResNet50 backbone', shape: 'ImageNet weights', color: '#93c5fd' },
                  { layer: 'GlobalAveragePooling2D', shape: '(2048,)', color: '#c4b5fd' },
                  { layer: 'Dense(256, relu)', shape: '(256,)', color: '#fde68a' },
                  { layer: 'Dropout(0.4)', shape: '(256,)', color: '#fca5a5' },
                  { layer: 'Dense(38, softmax)', shape: '(38,)', color: '#6ee7b7' },
                ].map((l) => (
                  <div key={l.layer} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 20px', borderBottom: '1px solid rgba(255,255,255,.06)', background: '#1e293b', color: '#e2e8f0' }}>
                    <span style={{ color: l.color }}>{l.layer}</span>
                    <span style={{ opacity: .55 }}>{l.shape}</span>
                  </div>
                ))}
              </div>

              <div className="card card-sand" style={{ marginTop: 20 }}>
                <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                  <Leaf size={16} color="var(--forest-light)" />
                  <strong style={{ fontSize: '.9rem' }}>Dataset</strong>
                </div>
                <p style={{ fontSize: '.875rem', margin: 0 }}>
                  PlantVillage (color) — 54,306 images across 38 plant-disease classes from 14 crop species.
                  Sourced via Kaggle API. Stratified 70/15/15 split ensures class balance across all subsets.
                </p>
              </div>
            </FadeUp>
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="section" style={{ background: 'var(--white)' }}>
        <div className="container">
          <FadeUp className="text-center" style={{ marginBottom: 48 }}>
            <div className="section-label"><Code2 size={11} /> Tech Stack</div>
            <h2 className="section-title">Built with Industry-Grade Tools</h2>
          </FadeUp>

          <div className="grid-3">
            {TECH_STACK.map((t, i) => (
              <FadeUp key={t.name} delay={i * .06}>
                <div className="tech-item">
                  <div className={`feat-icon ${t.color}`} style={{ width: 40, height: 40, margin: 0, flexShrink: 0 }}>
                    <div className="tech-item-icon">{t.icon}</div>
                  </div>
                  <div>
                    <div className="tech-item-name">{t.name}</div>
                    <div className="tech-item-role">{t.role}</div>
                  </div>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="section" style={{ background: 'var(--forest)' }}>
        <div className="container text-center">
          <FadeUp>
            <div className="section-label" style={{ background: 'rgba(255,255,255,.12)', borderColor: 'rgba(255,255,255,.2)', color: 'rgba(255,255,255,.9)' }}>
              <Users size={11} /> The Team
            </div>
            <h2 className="section-title" style={{ color: 'white' }}>Built for SIH 2026</h2>
            <p style={{ color: 'rgba(255,255,255,.7)', maxWidth: 580, margin: '0 auto 40px', fontSize: '1.05rem' }}>
              AgriSmart AI is an original implementation developed for the Smart India Hackathon 2026.
              Every line of code — from the training pipeline to the React frontend — was authored for this event.
            </p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
              <a href="https://github.com/Anshum25/agrismart-ai" target="_blank" rel="noreferrer" className="btn btn-amber">
                View on GitHub <ExternalLink size={15} />
              </a>
              <Link to="/diagnose" className="btn btn-outline" style={{ borderColor: 'rgba(255,255,255,.3)', color: 'white' }}>
                Try the Demo
              </Link>
            </div>
          </FadeUp>
        </div>
      </section>
    </>
  )
}
