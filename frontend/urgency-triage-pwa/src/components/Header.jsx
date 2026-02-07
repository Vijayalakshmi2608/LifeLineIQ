import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Globe, HelpCircle, DownloadCloud, Moon, Sun } from 'lucide-react'
import { usePwaInstall } from '../hooks/usePwaInstall'
import '../styles/layout.css'

const Header = () => {
  const { canInstall, promptInstall } = usePwaInstall()
  const [showLang, setShowLang] = useState(false)
  const [theme, setTheme] = useState(
    () => localStorage.getItem('lifelineiq_theme') || 'light',
  )

  useEffect(() => {
    document.body.classList.toggle('theme-dark', theme === 'dark')
    localStorage.setItem('lifelineiq_theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'))
  }

  return (
    <header className="app-header">
      <NavLink className="brand" to="/">
        <span className="brand-mark">♥</span>
        <div>
          <p className="brand-name">LifeLineIQ</p>
          <span className="brand-subtitle">AI Health Triage</span>
        </div>
      </NavLink>

      <div className="header-actions">
        <button
          className="icon-btn"
          type="button"
          aria-label="Select language"
          onClick={() => setShowLang((prev) => !prev)}
        >
          <Globe size={18} />
        </button>
        <button
          className="icon-btn theme-toggle"
          type="button"
          aria-label="Toggle theme"
          onClick={toggleTheme}
        >
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>
        <button className="icon-btn" type="button" aria-label="Help">
          <HelpCircle size={18} />
        </button>
        {canInstall && (
          <button className="icon-btn" type="button" onClick={promptInstall}>
            <DownloadCloud size={18} />
          </button>
        )}
      </div>

      {showLang && (
        <div className="lang-popover">
          <p>Language settings are coming soon.</p>
          <button className="btn btn-outline" onClick={() => setShowLang(false)}>
            Close
          </button>
        </div>
      )}
    </header>
  )
}

export default Header
