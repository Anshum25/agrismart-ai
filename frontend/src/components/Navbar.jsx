import { NavLink, Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Leaf, GitBranch, Menu, X } from 'lucide-react'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <div className="navbar-logo-icon">
            <Leaf size={18} color="white" />
          </div>
          <span className="navbar-brand-name">
            Agri<span>Smart</span> AI
          </span>
        </Link>

        <ul className="navbar-links">
          <li><NavLink to="/" className={({isActive}) => isActive ? 'active' : ''} end>Home</NavLink></li>
          <li><NavLink to="/diagnose" className={({isActive}) => isActive ? 'active' : ''}>Diagnose</NavLink></li>
          <li><NavLink to="/about" className={({isActive}) => isActive ? 'active' : ''}>About</NavLink></li>
          <li>
            <a
              href="https://github.com/Anshum25/agrismart-ai"
              target="_blank" rel="noreferrer"
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <GitBranch size={14} /> GitHub
            </a>
          </li>
          <li>
            <NavLink to="/diagnose" className="navbar-cta">
              Try Demo →
            </NavLink>
          </li>
        </ul>

        <button
          className="btn btn-ghost btn-sm"
          style={{ display: 'none' }}
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Menu"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>
    </nav>
  )
}
