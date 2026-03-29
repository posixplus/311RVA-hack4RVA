import { useState, useEffect, useRef, useCallback } from 'react'

const NONPROFIT_ORGS = [
  { key: 'irc', name: 'IRC Richmond', nameEs: 'IRC Richmond' },
  { key: 'reestablish', name: 'ReEstablish Richmond', nameEs: 'ReEstablish Richmond' },
  { key: 'sacred_heart', name: 'Sacred Heart Center', nameEs: 'Centro Sacred Heart' },
  { key: 'afghan', name: 'Afghan Association of VA', nameEs: 'Asociación Afgana de VA' },
  { key: 'legal_aid', name: 'Central VA Legal Aid', nameEs: 'Ayuda Legal de VA Central' },
  { key: 'bha', name: 'Richmond BHA', nameEs: 'Richmond BHA' },
  { key: 'crossover', name: 'CrossOver Healthcare', nameEs: 'CrossOver Healthcare' },
]

export default function ChatInterface({ messages, status, onSend, onHandoff, lang, category }) {
  const [input, setInput] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [speechSupported, setSpeechSupported] = useState(false)
  const [showHandoff, setShowHandoff] = useState(false)
  const chatEndRef = useRef(null)
  const recognitionRef = useRef(null)
  const inputRef = useRef(null)
  const isSendingRef = useRef(false)
  const onSendRef = useRef(onSend)

  useEffect(() => {
    onSendRef.current = onSend
  }, [onSend])

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return
    setSpeechSupported(true)

    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort()
      } catch (_) {}
    }

    const rec = new SR()
    rec.continuous = false
    rec.interimResults = true
    rec.lang = lang === 'es' ? 'es-US' : 'en-US'

    rec.onresult = (e) => {
      const transcript = Array.from(e.results).map(r => r[0].transcript).join('')
      setInput(transcript)
    }

    rec.onend = () => {
      setIsListening(false)
      setInput(prev => {
        const text = prev.trim()
        if (text && !isSendingRef.current) {
          isSendingRef.current = true
          setTimeout(() => {
            onSendRef.current(text)
            isSendingRef.current = false
          }, 50)
        }
        return ''
      })
    }

    rec.onerror = (e) => {
      if (e.error === 'no-speech') return
      console.error('Speech error:', e.error)
      setIsListening(false)
    }

    recognitionRef.current = rec
  }, [lang])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status])

  const handleSend = useCallback(() => {
    const text = input.trim()
    if (!text || status === 'thinking' || isSendingRef.current) return
    isSendingRef.current = true
    onSend(text)
    setInput('')
    inputRef.current?.focus()
    setTimeout(() => {
      isSendingRef.current = false
    }, 300)
  }, [input, status, onSend])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const startListening = () => {
    if (!recognitionRef.current || isListening || status === 'thinking') return
    setInput('')
    setIsListening(true)
    try {
      recognitionRef.current.start()
    } catch (_) {
      setIsListening(false)
    }
  }

  const stopListening = () => {
    if (!isListening) return
    try {
      recognitionRef.current?.stop()
    } catch (_) {}
  }

  const statusLabels = {
    en: { ready: '● Ready', listening: '🎙 Listening...', thinking: '⏳ Thinking...', speaking: '🔊 Speaking...' },
    es: { ready: '● Listo', listening: '🎙 Escuchando...', thinking: '⏳ Procesando...', speaking: '🔊 Hablando...' }
  }

  const labels = statusLabels[lang] || statusLabels.en

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="message assistant">
            <div className="message-bubble">
              {lang === 'es'
                ? `¿Cómo puedo ayudarle${category ? ` con ${category.nameEs}` : ''}?`
                : `How can I help you${category ? ` with ${category.name}` : ''}?`
              }
            </div>
          </div>
        )}
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="message-bubble">{msg.text}</div>
            {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
              <div className="message-sources">
                <div className="sources-label">{lang === 'es' ? 'Fuentes:' : 'Sources:'}</div>
                {msg.sources.map((src, i) => (
                  <div key={i} className="source-item">
                    <span className="source-number">{i + 1}</span>
                    <span className="source-text">{src.title || src.excerpt || 'Knowledge Base'}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {status === 'thinking' && (
          <div className="message assistant">
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {messages.length >= 2 && (
        <div className="handoff-section">
          <button
            className="handoff-toggle-btn"
            onClick={() => setShowHandoff(!showHandoff)}
          >
            🤝 {lang === 'es' ? 'Transferir a una organización' : 'Hand off to an organization'}
            <span style={{ marginLeft: '6px' }}>{showHandoff ? '▲' : '▼'}</span>
          </button>
          {showHandoff && (
            <div className="handoff-panel">
              <p className="handoff-description">
                {lang === 'es'
                  ? 'Seleccione una organización para transferir su caso:'
                  : 'Select an organization to hand off your case to:'}
              </p>
              <div className="handoff-grid">
                {NONPROFIT_ORGS.map(org => (
                  <button
                    key={org.key}
                    className="handoff-org-btn"
                    onClick={() => { onHandoff(org.key); setShowHandoff(false); }}
                  >
                    {lang === 'es' ? org.nameEs : org.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <input
            ref={inputRef}
            type="text"
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={lang === 'es' ? 'Escriba su pregunta...' : 'Type your question...'}
            disabled={status === 'thinking'}
          />
          {speechSupported && (
            <button
              className={`voice-button ${isListening ? 'listening' : ''}`}
              onMouseDown={startListening}
              onMouseUp={stopListening}
              onTouchStart={startListening}
              onTouchEnd={stopListening}
              disabled={status === 'thinking'}
              title={lang === 'es' ? 'Mantener para hablar' : 'Hold to speak'}
            >
              {isListening ? '🔴' : '🎤'}
            </button>
          )}
        </div>
        <button
          className="send-button"
          onClick={handleSend}
          disabled={!input.trim() || status === 'thinking'}
        >
          {lang === 'es' ? 'Enviar' : 'Send'}
        </button>
      </div>
    </div>
  )
}
