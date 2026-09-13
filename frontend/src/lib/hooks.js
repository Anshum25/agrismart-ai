import { useEffect, useState, useCallback } from 'react'

export function useOnline() {
  const [online, setOnline] = useState(typeof navigator === 'undefined' ? true : navigator.onLine)
  useEffect(() => {
    const on = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    return () => {
      window.removeEventListener('online', on)
      window.removeEventListener('offline', off)
    }
  }, [])
  return online
}

let deferredPrompt = null
const promptListeners = new Set()
if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', e => {
    e.preventDefault()
    deferredPrompt = e
    promptListeners.forEach(fn => fn(true))
  })
  window.addEventListener('appinstalled', () => {
    deferredPrompt = null
    promptListeners.forEach(fn => fn(false))
  })
}

export function useInstallPrompt() {
  const [available, setAvailable] = useState(Boolean(deferredPrompt))
  useEffect(() => {
    promptListeners.add(setAvailable)
    return () => promptListeners.delete(setAvailable)
  }, [])
  const install = useCallback(async () => {
    if (!deferredPrompt) return
    deferredPrompt.prompt()
    await deferredPrompt.userChoice
    deferredPrompt = null
    setAvailable(false)
  }, [])
  return { available, install }
}

const LOCATION_KEY = 'agrismart.location'

function readSavedLocation() {
  try { return JSON.parse(localStorage.getItem(LOCATION_KEY)) } catch { return null }
}

/** Opt-in browser geolocation, remembered on this device. */
export function useLocation() {
  const [location, setLocation] = useState(readSavedLocation)
  const [error, setError] = useState(null)
  const [pending, setPending] = useState(false)

  const request = useCallback(() => new Promise(resolve => {
    if (!navigator.geolocation) {
      setError('unsupported')
      return resolve(null)
    }
    setPending(true)
    navigator.geolocation.getCurrentPosition(
      pos => {
        const loc = { lat: +pos.coords.latitude.toFixed(4), lon: +pos.coords.longitude.toFixed(4) }
        try { localStorage.setItem(LOCATION_KEY, JSON.stringify(loc)) } catch { /* ignore */ }
        setLocation(loc)
        setError(null)
        setPending(false)
        resolve(loc)
      },
      err => {
        setError(err.code === 1 ? 'denied' : 'unavailable')
        setPending(false)
        resolve(null)
      },
      { enableHighAccuracy: false, timeout: 15000, maximumAge: 10 * 60 * 1000 },
    )
  }), [])

  const clear = useCallback(() => {
    try { localStorage.removeItem(LOCATION_KEY) } catch { /* ignore */ }
    setLocation(null)
  }, [])

  return { location, error, pending, request, clear }
}
