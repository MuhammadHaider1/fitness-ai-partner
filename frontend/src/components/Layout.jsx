import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { user, logout } = useAuth()

  const links = [
    { to: '/', label: 'Dashboard', end: true },
    { to: '/log', label: 'AI Logging' },
    { to: '/routine', label: 'Routine' },
    { to: '/history', label: 'History' },
    { to: '/coach', label: 'AI Coach' },
    { to: '/settings', label: 'Settings' },
  ]

  return (
    <div className="app-shell">
      <nav className="navbar">
        <div className="navbar__inner">
          <Link to="/" className="navbar__brand">
            <img src="/favicon.svg" alt="Fitness AI Partner" />
            <span>Fitness AI Partner</span>
          </Link>
          <div className="navbar__links">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.end}
                className={({ isActive }) => `navbar__link${isActive ? ' navbar__link--active' : ''}`}
              >
                {l.label}
              </NavLink>
            ))}
            {user && (
              <button className="btn btn--ghost btn--sm" onClick={logout} style={{ marginLeft: 8 }}>
                Logout
              </button>
            )}
          </div>
        </div>
      </nav>
      <main className="container">
        <Outlet />
      </main>
    </div>
  )
}