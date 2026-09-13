import { NavLink, Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Leaf, GitBranch, Menu, X, Download, Languages } from 'lucide-react'
import { useI18n, LANGUAGES } from '../i18n'
import { useInstallPrompt, useOnline } from '../lib/hooks'

const GITHUB_URL = 'https://github.com/Anshum25/agrismart-ai'

function LanguageSelect({ className = '' }) {
  const { lang, setLang, t } = useI18n()
  return (
    <label className={`lang-select ${className}`}>
      <Languages size={15} aria-hidden="true" />
      <span className="sr-only">{t('nav.language')}</span>
      <select value={lang} onChange={e => setLang(e.target.value)} aria-label={t('nav.language')}>
        {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.native}</option>)}
      </select>
    </label>
  )
}

export default function Navbar() {
  const { t } = useI18n()
  const online = useOnline()
  const { available: canInstall, install } = useInstallPrompt()
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => { setOpen(false) }, [location.pathname])

  const links = [
    { to: '/', label: t('nav.home'), end: true },
    { to: '/diagnose', label: t('nav.diagnose') },
    { to: '/outbreaks', label: t('nav.outbreaks') },
    { to: '/about', label: t('nav.about') },
  ]

  return (
    <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <div className="navbar-logo-icon"><Leaf size={18} color="white" /></div>
          <span className="navbar-brand-name">Agri<span>Smart</span> AI</span>
        </Link>

        <ul className="navbar-links">
          {links.map(l => (
            <li key={l.to}><NavLink to={l.to} end={l.end}>{l.label}</NavLink></li>
          ))}
          <li>
            <a href={GITHUB_URL} target="_blank" rel="noreferrer" className="flex items-center gap-1">
              <GitBranch size={14} /> GitHub
            </a>
          </li>
        </ul>

        <div className="navbar-actions">
          <span className={`net-status ${online ? 'on' : 'off'}`} title={online ? t('status.online') : t('status.offline')}>
            <span className="net-dot" /> <span className="net-label">{online ? t('status.online') : t('status.offline')}</span>
          </span>
          <LanguageSelect className="hide-mobile" />
          {canInstall && (
            <button className="btn btn-outline btn-sm hide-mobile" onClick={install}>
              <Download size={14} /> {t('nav.install')}
            </button>
          )}
          <button
            className="btn btn-ghost btn-sm nav-toggle"
            onClick={() => setOpen(o => !o)}
            aria-label={t('nav.menu')}
            aria-expanded={open}
            aria-controls="mobile-drawer"
          >
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {open && (
        <div id="mobile-drawer" className="mobile-drawer">
          {links.map(l => (
            <NavLink key={l.to} to={l.to} end={l.end} className="mobile-link">{l.label}</NavLink>
          ))}
          <a href={GITHUB_URL} target="_blank" rel="noreferrer" className="mobile-link">GitHub</a>
          <div className="mobile-drawer-row">
            <LanguageSelect />
            {canInstall && (
              <button className="btn btn-primary btn-sm" onClick={install}>
                <Download size={14} /> {t('nav.install')}
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}
