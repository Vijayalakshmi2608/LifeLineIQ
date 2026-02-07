import { useMemo, useState } from 'react'
import { Check, Search } from 'lucide-react'
import { motion } from 'framer-motion'
import '../styles/language-selector.css'
import { setLanguage } from '../i18n'

const LANGUAGES = [
  { code: 'en', native: 'English', english: 'English', accent: '#10B981' },
  { code: 'hi', native: 'हिन्दी', english: 'Hindi', accent: '#F59E0B' },
  { code: 'ta', native: 'தமிழ்', english: 'Tamil', accent: '#3B82F6' },
  { code: 'te', native: 'తెలుగు', english: 'Telugu', accent: '#06B6D4' },
  { code: 'kn', native: 'ಕನ್ನಡ', english: 'Kannada', accent: '#14B8A6' },
  { code: 'ml', native: 'മലയാളം', english: 'Malayalam', accent: '#0EA5E9' },
  { code: 'mr', native: 'मराठी', english: 'Marathi', accent: '#22C55E' },
  { code: 'bn', native: 'বাংলা', english: 'Bengali', accent: '#EF4444' },
  { code: 'gu', native: 'ગુજરાતી', english: 'Gujarati', accent: '#F97316' },
  { code: 'pa', native: 'ਪੰਜਾਬੀ', english: 'Punjabi', accent: '#E11D48' },
  { code: 'or', native: 'ଓଡ଼ିଆ', english: 'Odia', accent: '#8B5CF6' },
]

const STORAGE_KEY = 'preferred_language'

const LanguageSelector = ({ onContinue }) => {
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState(
    () => localStorage.getItem(STORAGE_KEY) || 'en',
  )

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase()
    if (!term) return LANGUAGES
    return LANGUAGES.filter(
      (lang) =>
        lang.native.toLowerCase().includes(term) ||
        lang.english.toLowerCase().includes(term),
    )
  }, [query])

  const handleSelect = (code) => {
    setSelected(code)
    localStorage.setItem(STORAGE_KEY, code)
    setLanguage(code)
  }

  const handleContinue = () => {
    if (!selected) return
    if (onContinue) onContinue(selected)
  }

  return (
    <div className="language-selector">
      <label className="language-search">
        <Search size={18} />
        <input
          type="search"
          placeholder="Search language"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label="Search language"
        />
      </label>

      <div className="language-grid">
        {filtered.map((lang) => {
          const isActive = selected === lang.code
          return (
            <motion.button
              key={lang.code}
              type="button"
              className={`language-card ${isActive ? 'active' : ''}`}
              onClick={() => handleSelect(lang.code)}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
              style={{ borderColor: isActive ? lang.accent : 'transparent' }}
            >
              <span
                className="language-accent"
                style={{ background: lang.accent }}
                aria-hidden="true"
              />
              <div>
                <p className="language-native">{lang.native}</p>
                <p className="language-english">{lang.english}</p>
              </div>
              {isActive && (
                <span className="language-check">
                  <Check size={16} />
                </span>
              )}
            </motion.button>
          )
        })}
      </div>

      <button className="btn btn-primary language-continue" onClick={handleContinue}>
        Continue
      </button>
    </div>
  )
}

export default LanguageSelector
