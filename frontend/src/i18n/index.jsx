import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import en from './en.json'
import hi from './hi.json'
import mr from './mr.json'
import ta from './ta.json'
import te from './te.json'
import kn from './kn.json'
import bn from './bn.json'
import gu from './gu.json'
import pa from './pa.json'

// Keep in sync with bonus/languages.py
export const LANGUAGES = [
  { code: 'en', native: 'English', bcp47: 'en-IN' },
  { code: 'hi', native: 'हिन्दी', bcp47: 'hi-IN' },
  { code: 'mr', native: 'मराठी', bcp47: 'mr-IN' },
  { code: 'ta', native: 'தமிழ்', bcp47: 'ta-IN' },
  { code: 'te', native: 'తెలుగు', bcp47: 'te-IN' },
  { code: 'kn', native: 'ಕನ್ನಡ', bcp47: 'kn-IN' },
  { code: 'bn', native: 'বাংলা', bcp47: 'bn-IN' },
  { code: 'gu', native: 'ગુજરાતી', bcp47: 'gu-IN' },
  { code: 'pa', native: 'ਪੰਜਾਬੀ', bcp47: 'pa-IN' },
]

const MESSAGES = { en, hi, mr, ta, te, kn, bn, gu, pa }
const STORAGE_KEY = 'agrismart.lang'

function initialLang() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved && MESSAGES[saved]) return saved
  } catch { /* storage blocked */ }
  const browser = (navigator.language || 'en').split('-')[0]
  return MESSAGES[browser] ? browser : 'en'
}

const I18nContext = createContext(null)

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(initialLang)

  const setLang = useCallback(code => {
    if (!MESSAGES[code]) return
    setLangState(code)
    try { localStorage.setItem(STORAGE_KEY, code) } catch { /* ignore */ }
  }, [])

  useEffect(() => { document.documentElement.lang = lang }, [lang])

  const t = useCallback((key, vars) => {
    let text = MESSAGES[lang]?.[key] ?? en[key] ?? key
    if (vars) for (const [k, v] of Object.entries(vars)) text = text.replaceAll(`{${k}}`, v)
    return text
  }, [lang])

  const value = useMemo(() => ({
    lang,
    setLang,
    t,
    bcp47: LANGUAGES.find(l => l.code === lang)?.bcp47 || 'en-IN',
  }), [lang, setLang, t])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error('useI18n must be used inside I18nProvider')
  return ctx
}
