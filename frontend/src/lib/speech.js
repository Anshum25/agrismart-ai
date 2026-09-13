// Browser text-to-speech with per-language voice matching.

export const speechSupported = () => typeof window !== 'undefined' && 'speechSynthesis' in window

function loadVoices() {
  return new Promise(resolve => {
    const voices = window.speechSynthesis.getVoices()
    if (voices.length) return resolve(voices)
    const done = () => resolve(window.speechSynthesis.getVoices())
    window.speechSynthesis.addEventListener('voiceschanged', done, { once: true })
    setTimeout(done, 1500)
  })
}

export async function findVoice(bcp47) {
  if (!speechSupported()) return null
  const voices = await loadVoices()
  const prefix = bcp47.split('-')[0].toLowerCase()
  return voices.find(v => v.lang.toLowerCase() === bcp47.toLowerCase())
    || voices.find(v => v.lang.toLowerCase().startsWith(prefix))
    || null
}

/** Speak text; resolves false if no voice exists for the language. */
export async function speak(text, bcp47, { onEnd } = {}) {
  const voice = await findVoice(bcp47)
  if (!voice) return false
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.voice = voice
  utterance.lang = voice.lang
  utterance.rate = 0.95
  utterance.onend = () => onEnd?.()
  utterance.onerror = () => onEnd?.()
  window.speechSynthesis.speak(utterance)
  return true
}

export function stopSpeaking() {
  if (speechSupported()) window.speechSynthesis.cancel()
}
