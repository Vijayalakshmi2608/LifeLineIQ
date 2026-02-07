import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import en from './locales/en.json'
import hi from './locales/hi.json'
import ta from './locales/ta.json'
import te from './locales/te.json'
import kn from './locales/kn.json'
import ml from './locales/ml.json'
import mr from './locales/mr.json'
import bn from './locales/bn.json'
import gu from './locales/gu.json'
import pa from './locales/pa.json'
import or from './locales/or.json'

const STORAGE_KEY = 'preferred_language'
const supported = ['en', 'hi', 'ta', 'te', 'kn', 'ml', 'mr', 'bn', 'gu', 'pa', 'or']

const detectLanguage = () => {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored && supported.includes(stored)) return stored
  const nav = navigator.language?.slice(0, 2) || 'en'
  return supported.includes(nav) ? nav : 'en'
}

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    hi: { translation: hi },
    ta: { translation: ta },
    te: { translation: te },
    kn: { translation: kn },
    ml: { translation: ml },
    mr: { translation: mr },
    bn: { translation: bn },
    gu: { translation: gu },
    pa: { translation: pa },
    or: { translation: or },
  },
  lng: detectLanguage(),
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

export const setLanguage = (lang) => {
  if (!supported.includes(lang)) return
  i18n.changeLanguage(lang)
  localStorage.setItem(STORAGE_KEY, lang)
}

export default i18n
