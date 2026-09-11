import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Leaf, Zap, Eye, MessageCircle, ShieldCheck, BarChart2,
  Upload, Brain, ArrowRight, GitBranch, ChevronRight,
  Microscope, CloudRain, Sprout, Sun
} from 'lucide-react'

/* ---- Fade-up wrapper ---------------------------------- */
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

/* ---- Data --------------------------------------------- */
const FEATURES = [
  {
    icon: <Microscope size={24} />,
    color: 'feat-icon-green',
    title: 'ResNet50 Disease Detection',
    desc: '98.96% accuracy on the PlantVillage benchmark — identifying 38 disease classes across 14 crops in under one second.',
    wide: true,
  },
  {
    icon: <Eye size={24} />,
    color: 'feat-icon-amber',
    title: 'Grad-CAM Explainability',
    desc: 'A heatmap overlay shows exactly which leaf regions triggered the prediction — no black boxes.',
  },
  {
    icon: <MessageCircle size={24} />,
    color: 'feat-icon-green',
    title: 'AI Agronomist Advice',
    desc: 'Groq Llama 3 generates structured treatment plans: immediate action, prevention, and long-term care.',
  },
  {
    icon: <CloudRain size={24} />,
    color: 'feat-icon-blue',
    title: 'Weather Risk Layer',
    desc: 'Correlates disease likelihood with local weather conditions to flag high-risk periods before symptoms appear.',
  },
  {
    icon: <Sprout size={24} />,
    color: 'feat-icon-green',
    title: 'Irrigation Advisor',
    desc: 'Gives crop-specific watering recommendations based on the detected disease and growth stage.',
  },
  {
    icon: <Sun size={24} />,
    color: 'feat-icon-amber',
    title: 'Sustainability Module',
    desc: 'Highlights organic, eco-friendly treatment alternatives and tracks chemical reduction over time.',
  },
]

const STEPS = [
  { num: '01', icon: <Upload size={22} />, title: 'Upload or Capture', desc: 'Drag-and-drop a photo, use your webcam, or pick from sample images.' },
  { num: '02', icon: <Brain size={22} />, title: 'AI Analysis', desc: 'ResNet50 classifies the leaf and pinpoints the disease with 98.9% accuracy.' },
  { num: '03', icon: <Eye size={22} />, title: 'Grad-CAM Explanation', desc: 'A heatmap highlights the exact lesion regions the model focused on.' },
  { num: '04', icon: <MessageCircle size={22} />, title: 'Actionable Advice', desc: 'An AI agronomist provides a treatment plan tailored to the specific disease.' },
]

const TECH_BADGES = ['ResNet50', 'TensorFlow', 'FastAPI', 'Groq Llama 3', 'OpenCV', 'Grad-CAM', 'React', 'Vite']

/* ---- Component ---------------------------------------- */
export default function Home() {
  return (
    <>
      {/* HERO */}
      <section className="hero">
        <div className="hero-bg">
          <div className="hero-grid" />
          <div className="hero-blob hero-blob-1" />
          <div className="hero-blob hero-blob-2" />
        </div>

        <div className="container hero-content">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 440px', gap: 64, alignItems: 'center' }}>
            <div>
              <motion.div
                className="hero-eyebrow"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: .5 }}
              >
                <Leaf size={13} /> SIH 2026 · Smart Agriculture AI
              </motion.div>

              <motion.h1
                className="hero-title"
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: .55, delay: .1 }}
              >
                Protect Crops<br />
                with <em>AI-Powered</em><br />
                Diagnostics
              </motion.h1>

              <motion.p
                className="hero-desc"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: .55, delay: .2 }}
              >
                Upload a photo of any crop leaf and get an instant disease classification,
                Grad-CAM visual explanation, and expert treatment advice — in under one second.
              </motion.p>

              <motion.div
                style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: .5, delay: .3 }}
              >
                <Link to="/diagnose" className="btn btn-primary btn-lg">
                  Diagnose a Leaf <ArrowRight size={18} />
                </Link>
                <a
                  href="https://github.com/Anshum25/agrismart-ai"
                  target="_blank" rel="noreferrer"
                  className="btn btn-outline btn-lg"
                >
                  <GitBranch size={18} /> View on GitHub
                </a>
              </motion.div>

              <motion.div
                className="hero-stats"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: .5, delay: .45 }}
              >
                <div className="hero-stat">
                  <span className="hero-stat-value">98.96%</span>
                  <span className="hero-stat-label">Test Accuracy</span>
                </div>
                <div className="hero-stat">
                  <span className="hero-stat-value">38</span>
                  <span className="hero-stat-label">Disease Classes</span>
                </div>
                <div className="hero-stat">
                  <span className="hero-stat-value">&lt;1s</span>
                  <span className="hero-stat-label">Inference Time</span>
                </div>
                <div className="hero-stat">
                  <span className="hero-stat-value">54k+</span>
                  <span className="hero-stat-label">Training Images</span>
                </div>
              </motion.div>
            </div>

            {/* Right: Decorative card mock */}
            <motion.div
              className="hero-image-wrap"
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: .7, delay: .2 }}
              style={{ display: 'flex', justifyContent: 'center' }}
            >
              <div style={{
                background: 'var(--white)',
                borderRadius: 24,
                padding: 24,
                boxShadow: 'var(--shadow-xl)',
                border: '1px solid rgba(0,0,0,.07)',
                width: '100%',
                maxWidth: 360
              }}>
                {/* Mini result card simulation */}
                <div style={{ background: 'var(--forest)', borderRadius: 16, padding: '20px 24px', marginBottom: 16, color: 'white' }}>
                  <div style={{ fontSize: 11, opacity: .65, fontWeight: 600, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 4 }}>DETECTED ON: TOMATO</div>
                  <div style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 700, fontSize: '1.4rem', marginBottom: 12 }}>Early Blight</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, opacity: .75 }}>
                    <span>Model Confidence</span>
                    <span style={{ fontWeight: 700, color: '#6ee7b7' }}>94.2%</span>
                  </div>
                  <div style={{ height: 6, background: 'rgba(255,255,255,.2)', borderRadius: 99, marginTop: 8, overflow: 'hidden' }}>
                    <div style={{ width: '94.2%', height: '100%', background: 'linear-gradient(90deg, #6ee7b7, #10b981)', borderRadius: 99 }} />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
                  <div style={{ background: 'var(--sand)', borderRadius: 12, height: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 12, fontWeight: 600, flexDirection: 'column', gap: 4 }}>
                    <Upload size={18} color="var(--forest-light)" />
                    Original
                  </div>
                  <div style={{ background: 'linear-gradient(135deg, #1e3a5f, #7c3aed)', borderRadius: 12, height: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: 12, fontWeight: 600, flexDirection: 'column', gap: 4, opacity: .9 }}>
                    <Eye size={18} />
                    Grad-CAM
                  </div>
                </div>

                <div style={{ background: 'var(--sand)', borderRadius: 12, padding: '14px 16px' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--forest)', letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 6 }}>🌿 AI Agronomist Advice</div>
                  <div style={{ fontSize: 12.5, color: 'var(--ink-700)', lineHeight: 1.7 }}>
                    Remove infected tissue immediately. Apply copper-based fungicide and improve airflow spacing...
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="section how-section">
        <div className="container">
          <FadeUp className="text-center" style={{ marginBottom: 'var(--sp-12)' }}>
            <div className="section-label" style={{ display: 'inline-flex', marginBottom: 'var(--sp-3)' }}>
              <Zap size={11} /> How it works
            </div>
            <h2 className="section-title">Diagnosis in 4 Simple Steps</h2>
            <p className="section-sub mx-auto text-center">
              From photo to prescription in under a second. No agronomy degree required.
            </p>
          </FadeUp>

          <div className="how-steps">
            {STEPS.map((s, i) => (
              <FadeUp key={s.num} delay={i * .08}>
                <div className="how-step">
                  <div className="how-step-num">{s.num}</div>
                  <div className="how-step-icon">{s.icon}</div>
                  <h3>{s.title}</h3>
                  <p>{s.desc}</p>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="section features-section">
        <div className="container">
          <FadeUp className="text-center" style={{ marginBottom: 'var(--sp-10)' }}>
            <div className="section-label" style={{ display: 'inline-flex', marginBottom: 'var(--sp-3)' }}>
              <ShieldCheck size={11} /> Capabilities
            </div>
            <h2 className="section-title">Everything a Field Agronomist Needs</h2>
            <p className="section-sub mx-auto text-center">
              AgriSmart combines deep learning, XAI, and generative AI into a single unified diagnostic platform.
            </p>
          </FadeUp>

          <div className="features-bento">
            {FEATURES.map((f, i) => (
              <FadeUp key={f.title} delay={i * .06} className={f.wide ? 'feat-card wide card-hover' : 'feat-card card-hover'}>
                <div className={`feat-icon ${f.color}`}>{f.icon}</div>
                <h3 style={{ marginBottom: 8 }}>{f.title}</h3>
                <p style={{ fontSize: '.9rem' }}>{f.desc}</p>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* MODEL TRANSPARENCY */}
      <section className="section transparency-section">
        <div className="container">
          <FadeUp style={{ marginBottom: 'var(--sp-10)' }}>
            <div className="section-label">
              <BarChart2 size={11} /> Model Transparency
            </div>
            <h2 className="section-title">Built to be Audited</h2>
            <p style={{ color: 'rgba(255,255,255,.7)', maxWidth: 560, marginBottom: 'var(--sp-10)', fontSize: '1.05rem' }}>
              We believe trustworthy AI requires full transparency about training data, architecture decisions, and real-world limitations.
            </p>
          </FadeUp>

          <div className="transparency-grid">
            {[
              { val: '98.96%', label: 'Test Accuracy', desc: 'Evaluated on a fully held-out 15% stratified split from PlantVillage.' },
              { val: '38', label: 'Disease Classes', desc: '14 crop species including Tomato, Potato, Apple, Corn, Grape, and more.' },
              { val: '54k+', label: 'Training Images', desc: 'PlantVillage dataset (color variant). Stratified 70/15/15 train/val/test split.' },
              { val: 'ResNet50', label: 'Backbone', desc: 'Two-phase fine-tuning: frozen base, then unfreezing last 30 layers at lr=1e-5.' },
              { val: 'Grad-CAM', label: 'Explainability', desc: 'Gradient-weighted Class Activation Mapping — every prediction is explained visually.' },
              { val: '< 1s', label: 'Inference Time', desc: 'Full prediction + Grad-CAM + LLM advice pipeline on commodity hardware.' },
            ].map((item, i) => (
              <FadeUp key={item.label} delay={i * .06}>
                <div className="transparency-card">
                  <div className="transparency-metric">{item.val}</div>
                  <h4>{item.label}</h4>
                  <p>{item.desc}</p>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <div className="container">
          <FadeUp>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,.12)', border: '1px solid rgba(255,255,255,.2)', color: 'rgba(255,255,255,.9)', fontSize: '.78rem', fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', padding: '4px 14px', borderRadius: 999, marginBottom: 20 }}>
              <Leaf size={11} /> Live Demo Ready
            </div>
            <h2 style={{ color: 'white', marginBottom: 16 }}>Ready to Try It?</h2>
            <p style={{ color: 'rgba(255,255,255,.75)', marginBottom: 32, maxWidth: 520, marginLeft: 'auto', marginRight: 'auto' }}>
              Upload a crop leaf photo or use your webcam — get a full diagnostic report with Grad-CAM explanation in seconds.
            </p>
            <Link to="/diagnose" className="btn btn-amber btn-lg">
              Start Diagnosis <ChevronRight size={18} />
            </Link>
          </FadeUp>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="footer">
        <div className="container">
          <div className="footer-top">
            <div>
              <div className="footer-brand">🌿 AgriSmart AI</div>
              <p className="footer-desc">
                AI-powered plant disease diagnostic platform built for the Smart India Hackathon 2026.
                Combining ResNet50 transfer learning, Grad-CAM explainability, and Groq LLM advisory.
              </p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 20 }}>
                {TECH_BADGES.map(b => (
                  <span key={b} className="footer-badge">{b}</span>
                ))}
              </div>
            </div>
            <div className="footer-col">
              <h5>Pages</h5>
              <ul>
                <li><Link to="/" className="footer-link">Home</Link></li>
                <li><Link to="/diagnose" className="footer-link">Diagnose</Link></li>
                <li><Link to="/about" className="footer-link">About</Link></li>
              </ul>
            </div>
            <div className="footer-col">
              <h5>Resources</h5>
              <ul>
                <li><a href="https://github.com/Anshum25/agrismart-ai" target="_blank" rel="noreferrer">GitHub Repo</a></li>
                <li><a href="#" target="_blank" rel="noreferrer">Demo Video</a></li>
                <li><a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API Docs (Swagger)</a></li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <span style={{ fontSize: '.8rem' }}>© 2026 AgriSmart AI · Built for SIH 2026</span>
            <span style={{ fontSize: '.8rem' }}>Made with ❤️ for Indian farmers</span>
          </div>
        </div>
      </footer>
    </>
  )
}
