import { NavLink, useLocation } from 'react-router-dom'
import Header from './Header'
import '../styles/layout.css'

const navItems = [
  { label: 'Home', path: '/', icon: '\u{1F3E0}' },
  { label: 'Symptom Check', path: '/symptom', icon: '\u{1FA7A}' },
  { label: 'Visual Check', path: '/visual-check', icon: '\u{1F4F7}' },
  { label: 'History', path: '/timeline', icon: '\u{1F552}' },
  { label: 'Insights', path: '/insights', icon: '\u{1F4CD}' },
  { label: 'Settings', path: '/settings', icon: '\u2699\uFE0F' },
]

const Layout = ({ children }) => {
  const location = useLocation()

  return (
    <div className="app-shell">
      <Header />
      <main className="app-main" key={location.pathname}>
        {children}
      </main>

      <nav className="bottom-nav" aria-label="Primary">
        {navItems.map((item) => (
          <NavLink key={item.path} to={item.path} className="nav-item">
            <span className="nav-icon" aria-hidden="true">
              {item.icon}
            </span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <aside className="side-nav">
        <div className="side-nav-inner">
          {navItems.map((item) => (
            <NavLink key={item.path} to={item.path} className="side-item">
              <span className="nav-icon" aria-hidden="true">
                {item.icon}
              </span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>
      </aside>
    </div>
  )
}

export default Layout
