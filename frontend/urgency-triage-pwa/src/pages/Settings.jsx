import { useTranslation } from 'react-i18next'
import '../styles/settings.css'
import { setLanguage } from '../i18n'

const Settings = () => {
  const { i18n } = useTranslation()
  const current = i18n.language || 'en'
  return (
    <div className="settings-page">
      <header>
        <h1>Settings</h1>
        <p className="muted">Manage language, notifications, and your data.</p>
      </header>

      <section className="settings-card">
        <h2>Language Preference</h2>
        <p className="muted">Currently: {current.toUpperCase()}</p>
        <div className="language-list">
          {[
            { code: 'en', label: 'English' },
            { code: 'hi', label: 'हिन्दी' },
            { code: 'ta', label: 'தமிழ்' },
            { code: 'te', label: 'తెలుగు' },
            { code: 'kn', label: 'ಕನ್ನಡ' },
            { code: 'ml', label: 'മലയാളം' },
            { code: 'mr', label: 'मराठी' },
            { code: 'bn', label: 'বাংলা' },
            { code: 'gu', label: 'ગુજરાતી' },
            { code: 'pa', label: 'ਪੰਜਾਬੀ' },
            { code: 'or', label: 'ଓଡ଼ିଆ' },
          ].map((lang) => (
            <button
              key={lang.code}
              className={`language-pill ${current === lang.code ? 'active' : ''}`}
              type="button"
              onClick={() => setLanguage(lang.code)}
            >
              {lang.label}
            </button>
          ))}
        </div>
      </section>

      <section className="settings-card">
        <h2>Notifications</h2>
        <label className="toggle-row">
          <input type="checkbox" defaultChecked />
          <span>Appointment reminders</span>
        </label>
        <label className="toggle-row">
          <input type="checkbox" />
          <span>Community alerts</span>
        </label>
      </section>

      <section className="settings-card">
        <h2>Data Management</h2>
        <p className="muted">Clear stored history and cached data.</p>
        <button className="btn btn-outline" type="button">
          Clear History
        </button>
      </section>

      <section className="settings-card">
        <h2>About</h2>
        <p className="muted">LifeLineIQ version 0.1.0</p>
        <button className="btn btn-outline" type="button">
          View privacy policy
        </button>
      </section>
    </div>
  )
}

export default Settings
