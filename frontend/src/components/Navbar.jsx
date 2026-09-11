import { NavLink, useLocation } from 'react-router-dom'

const links = [
  { to: '/',         label: 'Home',    emoji: '🏠' },
  { to: '/diagnose', label: 'Diagnose', emoji: '🔬' },
  { to: '/about',    label: 'About',   emoji: '📋' },
]

export default function Navbar() {
  const { pathname } = useLocation()

  return (
    <nav className="navbar" aria-label="Main navigation">
      <div className="navbar-inner">
        {/* Brand */}
        <NavLink to="/" className="navbar-brand" id="nav-brand">
          <span className="emoji">🌿</span>
          AgriSmart AI
        </NavLink>

        {/* Links */}
        <ul className="navbar-links" role="list">
          {links.map(({ to, label, emoji }) => (
            <li key={to}>
              <NavLink
                to={to}
                id={`nav-${label.toLowerCase()}`}
                className={({ isActive }) => isActive ? 'active' : ''}
                end={to === '/'}
              >
                <span>{emoji}</span>
                {label}
              </NavLink>
            </li>
          ))}
          <li>
            <NavLink
              to="/diagnose"
              id="nav-cta"
              className="navbar-cta"
            >
              🚀 Diagnose Now
            </NavLink>
          </li>
        </ul>
      </div>
    </nav>
  )
}
