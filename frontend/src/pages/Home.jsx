import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { API_DOCS_URL } from '../lib/api'
import {
  Leaf, Zap, Eye, MessageCircle, ShieldCheck, BarChart2,
  Upload, Brain, ArrowRight, GitBranch, ChevronRight,
  Camera, ImageIcon, Cpu, Database, Layers, FlaskConical,
  Droplets, CloudRain, Recycle, Users, Sprout, TrendingUp,
  CheckCircle2, Clock, Wifi, RefreshCw, Bot, Globe,
  Microscope, Target, Star, Award, Sun
} from 'lucide-react'

/* ---- Animation wrapper --------------------------------- */
const FadeUp = ({ children, delay = 0, className = '', style = {} }) => (
  <motion.div
    className={className}
    style={style}
    initial={{ opacity: 0, y: 28 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: '-60px' }}
    transition={{ duration: .55, delay, ease: [.4, 0, .2, 1] }}
  >
    {children}
  </motion.div>
)

/* ---- Data ---------------------------------------------- */
const TARGET_USERS = [
  { icon: <Leaf size={22} />, label: 'Smallholder Farmers', desc: 'Rapid field diagnosis without expert access' },
  { icon: <Users size={22} />, label: 'Agricultural Advisors', desc: 'Scalable advisory tool for extension agents' },
  { icon: <FlaskConical size={22} />, label: 'Researchers', desc: 'Explainable AI for crop pathology studies' },
  { icon: <Globe size={22} />, label: 'Govt & NGOs', desc: 'Outbreak monitoring and early warning programs' },
]

const IMPACT_ITEMS = [
  { icon: <Sprout size={22} />, color: 'feat-icon-green', val: '40%', title: 'Disease Losses Reducible', desc: 'Early detection enables treatment before disease spreads to the full crop.' },
  { icon: <TrendingUp size={22} />, color: 'feat-icon-amber', val: '~30%', title: 'Yield Improvement', desc: 'Studies show timely fungicide application can recover up to 30% of lost yield.' },
  { icon: <Droplets size={22} />, color: 'feat-icon-blue', val: 'Smarter', title: 'Water Use', desc: 'Irrigation advice tailored to detected disease status avoids wasteful blanket watering.' },
]

const TECH_STACK = [
  { name: 'TensorFlow / Keras', color: '#FF6F00', icon: '🔶' },
  { name: 'ResNet50', color: '#064e3b', icon: '🧠' },
  { name: 'ONNX Runtime (web + server)', color: '#5C3EE8', icon: '⚙️' },
  { name: 'Grad-CAM', color: '#7c3aed', icon: '🔥' },
  { name: 'FastAPI', color: '#009688', icon: '⚡' },
  { name: 'React PWA', color: '#61DAFB', icon: '⚛️' },
  { name: 'Groq Llama 3.3', color: '#F55036', icon: '🤖' },
  { name: 'Whisper speech-to-text', color: '#10a37f', icon: '🎙️' },
  { name: 'Open-Meteo', color: '#2563eb', icon: '🌦️' },
  { name: 'Leaflet + OpenStreetMap', color: '#199900', icon: '🗺️' },
]

const ROADMAP_ITEMS = [
  { icon: <Bot size={20} />, title: 'Agentic AI Advisor', desc: 'Autonomous decision loop that continuously monitors field data and initiates interventions without manual triggers.' },
  { icon: <Wifi size={20} />, title: 'Real IoT Sensor Integration', desc: 'Physical soil moisture, temperature, humidity, and pH sensors feeding real-time data to the model.' },
  { icon: <RefreshCw size={20} />, title: 'Continuous Learning Pipeline', desc: 'Periodic retraining on newly collected field images to adapt to regional disease variants over time.' },
  { icon: <Star size={20} />, title: 'Farmer Feedback Loop', desc: 'In-app feedback ratings that build a personalized recommendation history per farm and region.' },
  { icon: <Globe size={20} />, title: 'Expanded Crop Coverage', desc: 'Scale from 14 to 50+ crop species, add regional disease variants underrepresented in PlantVillage.' },
]

/* ---- Component ----------------------------------------- */
export default function Home() {
  return (
    <>
      {/* =============================================
          HERO (PART A — sets up the real capabilities)
          ============================================= */}
      <section className="hero">
        <div className="hero-bg">
          <div className="hero-grid" />
          <div className="hero-blob hero-blob-1" />
          <div className="hero-blob hero-blob-2" />
        </div>

        <div className="container hero-content">
          <div className="hero-layout">
            <div>
              <motion.div
                className="hero-eyebrow"
                initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .5 }}
              >
                <Leaf size={13} /> SIH 2026 · Smart Agriculture AI
              </motion.div>

              <motion.h1
                className="hero-title"
                initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .55, delay: .1 }}
              >
                Diagnose Crop<br />
                Disease with<br />
                <em>AI You Can Trust</em>
              </motion.h1>

              <motion.p
                className="hero-desc"
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .55, delay: .2 }}
              >
                Photograph a leaf and get a disease diagnosis with a Grad-CAM visual explanation — on your phone,
                even offline. Then get treatment advice and a voice assistant in 9 Indian languages, a 7-day
                disease-risk forecast, and alerts when outbreaks are reported nearby.
              </motion.p>

              <motion.div
                style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}
                initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .5, delay: .3 }}
              >
                <Link to="/diagnose" className="btn btn-primary btn-lg">
                  Try the Diagnosis Tool <ArrowRight size={18} />
                </Link>
                <a href="https://github.com/Anshum25/agrismart-ai" target="_blank" rel="noreferrer" className="btn btn-outline btn-lg">
                  <GitBranch size={18} /> View on GitHub
                </a>
              </motion.div>

              <motion.div
                className="hero-stats"
                initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .5, delay: .45 }}
              >
                {[
                  { val: '98.96%', label: 'Test Accuracy*' },
                  { val: '38', label: 'Disease Classes' },
                  { val: '9', label: 'Languages' },
                  { val: 'Offline', label: 'On-device AI' },
                ].map(s => (
                  <div key={s.label} className="hero-stat">
                    <span className="hero-stat-value">{s.val}</span>
                    <span className="hero-stat-label">{s.label}</span>
                  </div>
                ))}
              </motion.div>
            </div>

            {/* Hero card mock */}
            <motion.div
              initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: .7, delay: .2 }}
              style={{ display: 'flex', justifyContent: 'center' }}
            >
              <div style={{ background: 'var(--white)', borderRadius: 24, padding: 24, boxShadow: 'var(--shadow-xl)', border: '1px solid rgba(0,0,0,.07)', width: '100%', maxWidth: 360 }}>
                <div style={{ background: 'var(--forest)', borderRadius: 16, padding: '20px 24px', marginBottom: 16, color: 'white' }}>
                  <div style={{ fontSize: 11, opacity: .65, fontWeight: 600, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 4 }}>DETECTED ON: TOMATO</div>
                  <div style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 700, fontSize: '1.4rem', marginBottom: 12 }}>Early Blight</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, opacity: .75 }}>
                    <span>Confidence</span><span style={{ fontWeight: 700, color: '#6ee7b7' }}>94.2%</span>
                  </div>
                  <div style={{ height: 6, background: 'rgba(255,255,255,.2)', borderRadius: 99, marginTop: 8, overflow: 'hidden' }}>
                    <div style={{ width: '94.2%', height: '100%', background: 'linear-gradient(90deg, #6ee7b7, #10b981)', borderRadius: 99 }} />
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
                  <div style={{ background: 'var(--sand)', borderRadius: 12, height: 88, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 4, color: 'var(--text-muted)', fontSize: 11, fontWeight: 600 }}>
                    <Upload size={16} color="var(--forest-light)" />Original
                  </div>
                  <div style={{ background: 'linear-gradient(135deg, #1e3a5f, #7c3aed)', borderRadius: 12, height: 88, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 4, color: 'white', fontSize: 11, fontWeight: 600, opacity: .9 }}>
                    <Eye size={16} />Grad-CAM
                  </div>
                </div>
                <div style={{ background: 'var(--sand)', borderRadius: 12, padding: '14px 16px' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--forest)', letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 6 }}>🌿 AI Agronomist Advice</div>
                  <div style={{ fontSize: 12.5, color: 'var(--ink-700)', lineHeight: 1.7 }}>Remove infected tissue immediately. Apply copper-based fungicide and improve airflow spacing…</div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* =============================================
          PART A — HOW IT WORKS (4 Real Layers)
          ============================================= */}
      <section className="section" style={{ background: 'var(--cream-dark)' }}>
        <div className="container">
          <FadeUp className="text-center" style={{ marginBottom: 56 }}>
            <div className="section-label" style={{ display: 'inline-flex', marginBottom: 12 }}><Zap size={11} /> How It Works</div>
            <h2 className="section-title">Four Layers from Photo to Prescription</h2>
            <p className="section-sub mx-auto text-center">Every step below is real and working — no placeholders.</p>
          </FadeUp>

          {/* Layer 1: Data Input */}
          <FadeUp style={{ marginBottom: 32 }}>
            <div className="card layer-card" style={{ borderLeft: '4px solid var(--forest-light)' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ width: 64, height: 64, background: 'rgba(5,150,105,.1)', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px', color: 'var(--forest-light)' }}>
                  <Database size={28} />
                </div>
                <div style={{ fontFamily: 'Outfit,sans-serif', fontWeight: 700, fontSize: '1.1rem', color: 'var(--forest)', marginBottom: 4 }}>Layer 1</div>
                <div style={{ fontSize: '.8rem', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '.06em', textTransform: 'uppercase' }}>Data Input</div>
              </div>
              <div>
                <h3 style={{ marginBottom: 8 }}>Three Ways to Submit a Leaf</h3>
                <p style={{ marginBottom: 16, fontSize: '.95rem' }}>All three input methods are live and functional in the Diagnose dashboard.</p>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  {[
                    { icon: <Upload size={16} />, label: 'Upload Photo', desc: 'Drag & drop JPG/PNG' },
                    { icon: <Camera size={16} />, label: 'Live Camera', desc: 'Webcam capture in-browser' },
                    { icon: <ImageIcon size={16} />, label: 'Sample Gallery', desc: '6 real held-out test images' },
                  ].map(m => (
                    <div key={m.label} style={{ flex: 1, minWidth: 140, background: 'var(--sand)', borderRadius: 12, padding: '14px 16px', border: '1px solid rgba(0,0,0,.07)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--forest)', marginBottom: 4, fontWeight: 700, fontSize: '.9rem' }}>
                        {m.icon}{m.label}
                      </div>
                      <div style={{ fontSize: '.8rem', color: 'var(--text-muted)' }}>{m.desc}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </FadeUp>

          {/* Layer 2: Preprocessing */}
          <FadeUp style={{ marginBottom: 32 }} delay={.06}>
            <div className="card layer-card" style={{ borderLeft: '4px solid var(--amber)' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ width: 64, height: 64, background: 'rgba(217,119,6,.1)', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px', color: 'var(--amber)' }}>
                  <Cpu size={28} />
                </div>
                <div style={{ fontFamily: 'Outfit,sans-serif', fontWeight: 700, fontSize: '1.1rem', color: 'var(--amber)', marginBottom: 4 }}>Layer 2</div>
                <div style={{ fontSize: '.8rem', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '.06em', textTransform: 'uppercase' }}>Processing</div>
              </div>
              <div>
                <h3 style={{ marginBottom: 8 }}>Checked, Then Standardized</h3>
                <p style={{ marginBottom: 16, fontSize: '.95rem' }}>Photos that are not a leaf, too dark or blurry are rejected with retake tips instead of a made-up diagnosis.</p>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                  {['Decode + EXIF rotate', '→', 'Leaf / blur / light check', '→', 'Resize to 224×224', '→', 'ResNet50 BGR mean'].map((step, i) => (
                    <span key={i} style={{
                      background: step === '→' ? 'transparent' : 'var(--sand)',
                      border: step === '→' ? 'none' : '1px solid rgba(0,0,0,.08)',
                      color: step === '→' ? 'var(--text-muted)' : 'var(--ink-700)',
                      borderRadius: 8, padding: step === '→' ? '0 2px' : '6px 12px',
                      fontSize: '.82rem', fontWeight: step === '→' ? 400 : 600,
                      fontFamily: step !== '→' ? 'monospace' : 'inherit'
                    }}>{step}</span>
                  ))}
                </div>
              </div>
            </div>
          </FadeUp>

          {/* Layer 3: AI Model */}
          <FadeUp style={{ marginBottom: 32 }} delay={.1}>
            <div className="card" style={{ borderLeft: '4px solid #7c3aed' }}>
              <div className="layer-card" style={{ alignItems: 'start' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ width: 64, height: 64, background: 'rgba(124,58,237,.1)', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px', color: '#7c3aed' }}>
                    <Brain size={28} />
                  </div>
                  <div style={{ fontFamily: 'Outfit,sans-serif', fontWeight: 700, fontSize: '1.1rem', color: '#7c3aed', marginBottom: 4 }}>Layer 3</div>
                  <div style={{ fontSize: '.8rem', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '.06em', textTransform: 'uppercase' }}>AI Model</div>
                </div>
                <div>
                  <h3 style={{ marginBottom: 8 }}>ResNet50 Architecture — Exactly What's Running</h3>
                  <p style={{ marginBottom: 20, fontSize: '.95rem' }}>Transfer learning on ImageNet weights, fine-tuned with two-phase progressive unfreezing, then exported to a quantized ONNX model that runs in the browser and on the server.</p>
                  {/* Architecture flow */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', overflowX: 'auto', paddingBottom: 4 }}>
                    {[
                      { label: 'Input', sub: '224×224×3', bg: '#f0fdf4', color: '#047857', border: '#6ee7b7' },
                      { label: '→', sub: '', bg: 'transparent', color: 'var(--text-muted)', border: 'transparent' },
                      { label: 'ResNet50', sub: 'Backbone', bg: '#ede9fe', color: '#6d28d9', border: '#c4b5fd' },
                      { label: '→', sub: '', bg: 'transparent', color: 'var(--text-muted)', border: 'transparent' },
                      { label: 'GAP', sub: '(2048,)', bg: '#fef3c7', color: '#92400e', border: '#fde68a' },
                      { label: '→', sub: '', bg: 'transparent', color: 'var(--text-muted)', border: 'transparent' },
                      { label: 'Dense', sub: '256 + ReLU', bg: '#fff7ed', color: '#c2410c', border: '#fed7aa' },
                      { label: '→', sub: '', bg: 'transparent', color: 'var(--text-muted)', border: 'transparent' },
                      { label: 'Dropout', sub: '0.4', bg: '#fce7f3', color: '#9d174d', border: '#fbcfe8' },
                      { label: '→', sub: '', bg: 'transparent', color: 'var(--text-muted)', border: 'transparent' },
                      { label: 'Dense', sub: '38 classes', bg: '#ecfdf5', color: '#047857', border: '#6ee7b7' },
                    ].map((n, i) => n.label === '→' ? (
                      <span key={i} style={{ color: 'var(--text-muted)', fontSize: 18, fontWeight: 300 }}>→</span>
                    ) : (
                      <div key={i} style={{ textAlign: 'center', background: n.bg, border: `1.5px solid ${n.border}`, borderRadius: 10, padding: '8px 14px', flexShrink: 0 }}>
                        <div style={{ fontFamily: 'Outfit,sans-serif', fontWeight: 700, color: n.color, fontSize: '.9rem' }}>{n.label}</div>
                        {n.sub && <div style={{ fontSize: '.72rem', color: n.color, opacity: .75, marginTop: 2 }}>{n.sub}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </FadeUp>

          {/* Layer 4: Prediction & Explainability */}
          <FadeUp delay={.14}>
            <div className="card layer-card" style={{ borderLeft: '4px solid #2563eb' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ width: 64, height: 64, background: 'rgba(37,99,235,.1)', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px', color: '#2563eb' }}>
                  <Eye size={28} />
                </div>
                <div style={{ fontFamily: 'Outfit,sans-serif', fontWeight: 700, fontSize: '1.1rem', color: '#2563eb', marginBottom: 4 }}>Layer 4</div>
                <div style={{ fontSize: '.8rem', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '.06em', textTransform: 'uppercase' }}>Prediction & XAI</div>
              </div>
              <div>
                <h3 style={{ marginBottom: 8 }}>Real Outputs — Every Time</h3>
                <div className="outputs-grid">
                  {[
                    { icon: <Target size={16} />, title: 'Disease + Top-3', desc: '38-class prediction; low-confidence results are flagged "not sure" with the top-3 matches' },
                    { icon: <BarChart2 size={16} />, title: 'Severity Estimate', desc: 'Estimated % of leaf area affected — not just model confidence' },
                    { icon: <Eye size={16} />, title: 'Grad-CAM Heatmap', desc: 'Exact Grad-CAM computed from the model head, on-device' },
                  ].map(o => (
                    <div key={o.title} style={{ background: 'var(--sand)', borderRadius: 12, padding: '14px 16px', border: '1px solid rgba(0,0,0,.07)' }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6, color: '#2563eb', fontWeight: 700, fontSize: '.9rem' }}>{o.icon}{o.title}</div>
                      <div style={{ fontSize: '.8rem', color: 'var(--text-muted)' }}>{o.desc}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </FadeUp>
        </div>
      </section>

      {/* =============================================
          PART A — BONUS MODULES (Real, Working)
          ============================================= */}
      <section className="section" style={{ background: 'var(--white)' }}>
        <div className="container">
          <FadeUp className="text-center" style={{ marginBottom: 48 }}>
            <div className="section-label" style={{ display: 'inline-flex', marginBottom: 12 }}>
              <CheckCircle2 size={11} /> Built & Working
            </div>
            <h2 className="section-title">Beyond Detection — Built for Indian Farmers</h2>
            <p className="section-sub mx-auto text-center">
              Every module below is implemented and returns real output in the app.
            </p>
          </FadeUp>

          <div className="modules-grid">
            {[
              {
                icon: <Wifi size={22} />, color: 'feat-icon-green',
                badge: '✅ Live · ONNX Runtime Web',
                title: 'Offline Crop Doctor (PWA)',
                desc: 'Install the app once; diagnosis, Grad-CAM, treatment guides and scan history keep working with no internet in the field.',
              },
              {
                icon: <MessageCircle size={22} />, color: 'feat-icon-amber',
                badge: '✅ Live · Groq Llama 3.3 + Whisper',
                title: 'Vernacular Advice & Voice Assistant',
                desc: 'Structured treatment plans (organic and chemical, with doses) in 9 Indian languages, read aloud. Farmers can ask follow-up questions by voice.',
              },
              {
                icon: <CloudRain size={22} />, color: 'feat-icon-blue',
                badge: '✅ Live · Open-Meteo forecast',
                title: '7-Day Disease Risk Forecast',
                desc: 'Disease-specific rules (temperature, leaf-wetness hours, rain) score each day and suggest the best dry, calm day to spray.',
              },
              {
                icon: <Globe size={22} />, color: 'feat-icon-red',
                badge: '✅ Live · Community reports',
                title: 'Outbreak Map & Nearby Alerts',
                desc: 'Farmers can anonymously share a diagnosis (location rounded to ~5 km). The map shows hotspots and warns others within 25 km.',
              },
              {
                icon: <Droplets size={22} />, color: 'feat-icon-blue',
                badge: '✅ Live · Rules + live temperature',
                title: 'Irrigation Advisory',
                desc: 'Crop- and disease-aware watering guidance using live temperature. No IoT sensor involved; soil moisture is clearly marked as assumed.',
              },
              {
                icon: <Recycle size={22} />, color: 'feat-icon-green',
                badge: '✅ Live · Rule-based scoring',
                title: 'Sustainability Score',
                desc: 'Grades the treatment path and highlights organic, biological and low-chemical alternatives.',
              },
            ].map((m, i) => (
              <FadeUp key={m.title} delay={i * .07}>
                <div className="card card-hover" style={{ height: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
                    <div className={`feat-icon ${m.color}`} style={{ margin: 0 }}>{m.icon}</div>
                    <span style={{ fontSize: '.72rem', fontWeight: 700, color: 'var(--forest)', background: 'rgba(5,150,105,.1)', padding: '3px 10px', borderRadius: 99, border: '1px solid rgba(5,150,105,.2)', whiteSpace: 'nowrap' }}>
                      {m.badge}
                    </span>
                  </div>
                  <h3 style={{ marginBottom: 8 }}>{m.title}</h3>
                  <p style={{ fontSize: '.9rem' }}>{m.desc}</p>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* =============================================
          PART A — MODEL TRANSPARENCY
          ============================================= */}
      <section className="section transparency-section">
        <div className="container">
          <FadeUp style={{ marginBottom: 48 }}>
            <div className="section-label"><Award size={11} /> Model Transparency</div>
            <h2 className="section-title">Real Numbers. No Placeholders.</h2>
            <p style={{ color: 'rgba(255,255,255,.7)', maxWidth: 580, marginBottom: 48, fontSize: '1.05rem' }}>
              Metrics from our trained model on a fully held-out PlantVillage test split. *PlantVillage photos are taken in
              controlled lab conditions; accuracy on real field photos is lower, which is why the app rejects poor photos and flags uncertain results.
            </p>
          </FadeUp>

          <div className="transparency-grid">
            {[
              { val: '98.96%', label: 'Test Accuracy', desc: 'Held-out 15% stratified split — unseen during training.' },
              { val: '98.85%', label: 'Validation Accuracy', desc: 'Measured every epoch during training on a 15% val split.' },
              { val: '0.0324', label: 'Test Loss', desc: 'Categorical cross-entropy on the test set.' },
              { val: '38', label: 'Classes Detected', desc: '14 crop species, including Tomato, Potato, Apple, Grape, Corn.' },
              { val: '54,306', label: 'Training Images', desc: 'PlantVillage color dataset — stratified 70/15/15 split.' },
              { val: '2-phase', label: 'Fine-Tuning Strategy', desc: 'Frozen backbone → unfreeze last 30 layers at lr=1e-5.' },
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

      {/* =============================================
          PART A — TARGET USERS & REAL-WORLD IMPACT
          (Aspirational framing — clearly vision/mission, not technical claims)
          ============================================= */}
      <section className="section" style={{ background: 'var(--cream-dark)' }}>
        <div className="container">
          <FadeUp className="text-center" style={{ marginBottom: 48 }}>
            <div className="section-label" style={{ display: 'inline-flex', marginBottom: 12 }}><Users size={11} /> Who This Is For</div>
            <h2 className="section-title">Built for the People Who Feed the World</h2>
          </FadeUp>
          <div className="grid-4" style={{ marginBottom: 72 }}>
            {TARGET_USERS.map((u, i) => (
              <FadeUp key={u.label} delay={i * .07}>
                <div className="card card-hover text-center" style={{ height: '100%' }}>
                  <div className="feat-icon feat-icon-green" style={{ margin: '0 auto 16px' }}>{u.icon}</div>
                  <h3 style={{ fontSize: '1rem', marginBottom: 8 }}>{u.label}</h3>
                  <p style={{ fontSize: '.875rem' }}>{u.desc}</p>
                </div>
              </FadeUp>
            ))}
          </div>

          <FadeUp className="text-center" style={{ marginBottom: 40 }}>
            <div className="section-label" style={{ display: 'inline-flex', marginBottom: 12 }}><TrendingUp size={11} /> Potential Impact</div>
            <h2 className="section-title">Why Early Detection Matters</h2>
            <p className="section-sub mx-auto text-center">
              Research-backed estimates of what timely, accurate disease detection enables for farmers.
            </p>
          </FadeUp>
          <div className="grid-3">
            {IMPACT_ITEMS.map((item, i) => (
              <FadeUp key={item.title} delay={i * .08}>
                <div className="card card-hover" style={{ height: '100%' }}>
                  <div className={`feat-icon ${item.color}`}>{item.icon}</div>
                  <div style={{ fontFamily: 'Outfit,sans-serif', fontWeight: 700, fontSize: '2rem', color: 'var(--forest)', marginBottom: 4 }}>{item.val}</div>
                  <h3 style={{ marginBottom: 8 }}>{item.title}</h3>
                  <p style={{ fontSize: '.9rem' }}>{item.desc}</p>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* =============================================
          PART B — ROADMAP (clearly labeled, distinct style)
          ============================================= */}
      <section className="section" style={{ background: 'var(--cream)' }}>
        <div className="container">
          <FadeUp className="text-center" style={{ marginBottom: 48 }}>
            {/* Distinct badge to signal "not yet built" */}
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(217,119,6,.08)', border: '1.5px dashed var(--amber)', color: 'var(--amber)', fontWeight: 700, fontSize: '.75rem', letterSpacing: '.1em', textTransform: 'uppercase', padding: '4px 16px', borderRadius: 999, marginBottom: 16 }}>
              <Clock size={12} /> Future Roadmap · Not Yet Built
            </div>
            <h2 className="section-title">Where We're Headed — Vision 2027</h2>
            <p className="section-sub mx-auto text-center">
              These features are <strong>planned — not built yet</strong>. We present them transparently as our development roadmap, distinct from the working features above.
            </p>
          </FadeUp>

          <div className="roadmap-grid">
            {ROADMAP_ITEMS.map((item, i) => (
              <FadeUp key={item.title} delay={i * .07}>
                {/* Visually distinct: dashed border, muted palette */}
                <div style={{
                  background: 'var(--white)',
                  border: '2px dashed var(--ink-300)',
                  borderRadius: 'var(--r-lg)',
                  padding: 'var(--sp-6)',
                  height: '100%',
                  opacity: .85,
                  transition: 'all var(--dur-base)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                    <div style={{ width: 42, height: 42, background: 'var(--ink-100)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ink-500)' }}>
                      {item.icon}
                    </div>
                    <span style={{ fontSize: '.7rem', fontWeight: 700, color: 'var(--ink-400)', background: 'var(--ink-100)', padding: '2px 10px', borderRadius: 99 }}>PLANNED</span>
                  </div>
                  <h3 style={{ fontSize: '1rem', color: 'var(--ink-700)', marginBottom: 8 }}>{item.title}</h3>
                  <p style={{ fontSize: '.875rem', color: 'var(--ink-500)' }}>{item.desc}</p>
                </div>
              </FadeUp>
            ))}

            {/* Final card — spanning full last row slot — team commitment note */}
            <FadeUp delay={.35} style={{ gridColumn: ROADMAP_ITEMS.length % 3 !== 0 ? `span ${3 - (ROADMAP_ITEMS.length % 3)}` : 'span 1' }}>
              <div style={{ background: 'var(--amber)', borderRadius: 'var(--r-lg)', padding: 'var(--sp-6)', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 8 }}>
                <div style={{ fontFamily: 'Outfit,sans-serif', fontWeight: 700, fontSize: '1.1rem', color: 'white', marginBottom: 4 }}>Our Commitment</div>
                <p style={{ color: 'rgba(255,255,255,.85)', fontSize: '.9rem', margin: 0 }}>
                  The working features in this demo are entirely built and functional. The roadmap above represents our honest vision for what comes next — not overclaimed features.
                </p>
              </div>
            </FadeUp>
          </div>
        </div>
      </section>

      {/* =============================================
          PART A — TECH STACK BAND
          ============================================= */}
      <section style={{ background: 'var(--ink-900)', padding: '40px 0' }}>
        <div className="container">
          <FadeUp className="text-center" style={{ marginBottom: 28 }}>
            <p style={{ fontSize: '.8rem', fontWeight: 600, letterSpacing: '.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,.4)', marginBottom: 0 }}>
              Key Technologies Powering AgriSmart AI
            </p>
          </FadeUp>
          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 12 }}>
            {TECH_STACK.map((t, i) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0, scale: .9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * .04 }}
                style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,.07)', border: '1px solid rgba(255,255,255,.1)', borderRadius: 99, padding: '8px 16px', cursor: 'default' }}
              >
                <span style={{ fontSize: 16 }}>{t.icon}</span>
                <span style={{ fontSize: '.85rem', fontWeight: 600, color: 'rgba(255,255,255,.8)' }}>{t.name}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* =============================================
          CTA + FOOTER
          ============================================= */}
      <section className="cta-section">
        <div className="container">
          <FadeUp>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,.12)', border: '1px solid rgba(255,255,255,.2)', color: 'rgba(255,255,255,.9)', fontSize: '.78rem', fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', padding: '4px 14px', borderRadius: 999, marginBottom: 20 }}>
              <Leaf size={11} /> Live Demo Ready
            </div>
            <h2 style={{ color: 'white', marginBottom: 16 }}>See It in Action</h2>
            <p style={{ color: 'rgba(255,255,255,.75)', marginBottom: 32, maxWidth: 520, marginLeft: 'auto', marginRight: 'auto' }}>
              Upload a real leaf photo or use a sample image — diagnosis and Grad-CAM run right in your browser.
            </p>
            <Link to="/diagnose" className="btn btn-amber btn-lg">
              Open Diagnosis Dashboard <ChevronRight size={18} />
            </Link>
          </FadeUp>
        </div>
      </section>

      <footer className="footer">
        <div className="container">
          <div className="footer-top">
            <div>
              <div className="footer-brand">🌿 AgriSmart AI</div>
              <p className="footer-desc">
                AI-powered plant disease diagnostic platform built for the Smart India Hackathon 2026.
                ResNet50 · Grad-CAM · ONNX · Groq Llama 3.3 · FastAPI · React PWA.
              </p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 20 }}>
                {['SIH 2026', 'Open Source', 'Explainable AI', 'Agriculture'].map(b => (
                  <span key={b} className="footer-badge">{b}</span>
                ))}
              </div>
            </div>
            <div className="footer-col">
              <h5>Pages</h5>
              <ul>
                <li><Link to="/">Home</Link></li>
                <li><Link to="/diagnose">Diagnose</Link></li>
                <li><Link to="/about">About</Link></li>
              </ul>
            </div>
            <div className="footer-col">
              <h5>Resources</h5>
              <ul>
                <li><a href="https://github.com/Anshum25/agrismart-ai" target="_blank" rel="noreferrer">GitHub Repo</a></li>
                <li><Link to="/outbreaks">Outbreak Map</Link></li>
                {API_DOCS_URL && <li><a href={API_DOCS_URL} target="_blank" rel="noreferrer">API Docs</a></li>}
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <span style={{ fontSize: '.8rem' }}>© 2026 AgriSmart AI · Smart India Hackathon 2026</span>
            <span style={{ fontSize: '.8rem' }}>Made with ❤️ for Indian farmers</span>
          </div>
        </div>
      </footer>
    </>
  )
}
