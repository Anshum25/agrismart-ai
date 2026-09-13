import { useEffect, useRef, useState } from 'react'
import { Mic, Square, Send, Loader2, Volume2, MessageCircle } from 'lucide-react'
import { api } from '../lib/api'
import { speak, stopSpeaking } from '../lib/speech'
import { useI18n } from '../i18n'
import { useOnline } from '../lib/hooks'

function pickMimeType() {
  if (typeof MediaRecorder === 'undefined') return null
  for (const type of ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg']) {
    if (MediaRecorder.isTypeSupported(type)) return type
  }
  return ''
}

export default function VoiceAssistant({ result }) {
  const { t, lang, bcp47 } = useI18n()
  const online = useOnline()
  const [recording, setRecording] = useState(false)
  const [busy, setBusy] = useState(false)
  const [text, setText] = useState('')
  const [messages, setMessages] = useState([])
  const [error, setError] = useState(null)
  const recorderRef = useRef(null)
  const chunksRef = useRef([])

  useEffect(() => () => {
    recorderRef.current?.stream?.getTracks().forEach(tr => tr.stop())
    stopSpeaking()
  }, [])

  const ask = async ({ audio, question }) => {
    setBusy(true)
    setError(null)
    const form = new FormData()
    if (audio) form.append('audio', audio.blob, audio.name)
    if (question) form.append('question', question)
    form.append('lang', lang)
    if (result?.label) {
      form.append('label', result.label)
      form.append('confidence', result.confidence)
      form.append('affected_area_pct', result.affected_area_pct ?? 0)
    }
    try {
      const res = await api.voiceAsk(form)
      setMessages(m => [...m, { role: 'user', text: res.transcript }, { role: 'assistant', text: res.answer }])
      const spoke = await speak(res.answer, bcp47)
      if (!spoke) setError(t('advice.noVoice'))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const startRecording = async () => {
    setError(null)
    const mimeType = pickMimeType()
    if (mimeType === null || !navigator.mediaDevices?.getUserMedia) {
      setError('Voice recording is not supported in this browser.')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      chunksRef.current = []
      recorder.ondataavailable = e => e.data.size && chunksRef.current.push(e.data)
      recorder.onstop = () => {
        stream.getTracks().forEach(tr => tr.stop())
        const type = recorder.mimeType || 'audio/webm'
        const ext = type.includes('mp4') ? 'm4a' : type.includes('ogg') ? 'ogg' : 'webm'
        const blob = new Blob(chunksRef.current, { type })
        if (blob.size > 0) ask({ audio: { blob, name: `question.${ext}` } })
      }
      recorderRef.current = recorder
      recorder.start()
      setRecording(true)
      // Safety stop after 30 seconds
      setTimeout(() => recorder.state === 'recording' && recorder.stop(), 30000)
    } catch {
      setError(t('voice.micDenied'))
    }
  }

  const stopRecording = () => {
    recorderRef.current?.state === 'recording' && recorderRef.current.stop()
    setRecording(false)
  }

  const submitText = e => {
    e.preventDefault()
    const q = text.trim()
    if (!q) return
    setText('')
    ask({ question: q })
  }

  return (
    <div className="panel">
      <div className="panel-head">
        <span className="panel-title"><MessageCircle size={16} color="var(--forest-light)" /> {t('voice.title')}</span>
      </div>
      {!online ? (
        <p className="note">{t('voice.offline')}</p>
      ) : (
        <>
          <p className="muted-line">{t('voice.hint')}</p>
          {messages.length > 0 && (
            <div className="chat">
              {messages.map((m, i) => (
                <div key={i} className={`chat-msg ${m.role}`}>
                  <span className="chat-who">{m.role === 'user' ? t('voice.you') : t('voice.assistant')}</span>
                  <p>{m.text}</p>
                  {m.role === 'assistant' && (
                    <button className="btn btn-ghost btn-sm" onClick={() => speak(m.text, bcp47)} aria-label={t('advice.listen')}>
                      <Volume2 size={14} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
          <div className="voice-controls">
            <button
              className={`mic-btn ${recording ? 'recording' : ''}`}
              onClick={recording ? stopRecording : startRecording}
              disabled={busy}
              aria-label={recording ? t('voice.stop') : t('voice.record')}
            >
              {busy ? <Loader2 size={22} className="spin" /> : recording ? <Square size={20} /> : <Mic size={22} />}
            </button>
            <form className="voice-form" onSubmit={submitText}>
              <input
                value={text}
                onChange={e => setText(e.target.value)}
                placeholder={t('voice.placeholder')}
                maxLength={500}
                disabled={busy || recording}
              />
              <button className="btn btn-primary btn-sm" disabled={busy || recording || !text.trim()} aria-label={t('voice.ask')}>
                <Send size={14} />
              </button>
            </form>
          </div>
          {busy && <p className="muted-line">{t('voice.thinking')}</p>}
          {error && <p className="note">{error}</p>}
        </>
      )}
    </div>
  )
}
