import { useState, useRef, useCallback, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import ChatInterface from './components/ChatInterface'
import CategoryGrid from './components/CategoryGrid'
import Dashboard from './components/Dashboard'
import AdminDashboard from './components/AdminDashboard'
import FAQs from './components/FAQs'
import { API_ENDPOINT, MODE, SPEAK_RESPONSES, DEMO_RESPONSES, DEMO_RESPONSES_ES, TRANSLATIONS, CONNECT_PHONE, PRIVACY_NOTICE_EN, PRIVACY_NOTICE_ES } from './config'

const SWITCH_TO_ES = /español|spanish|en español|cambiar.*español|switch.*spanish/i
const SWITCH_TO_EN = /english|inglés|ingles|cambiar.*ingles|switch.*english|en inglés/i

function generateSessionId() {
  return 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

function getDemoResponse(message, lang) {
  const responses = lang === 'es' ? DEMO_RESPONSES_ES : DEMO_RESPONSES
  const lower = message.toLowerCase()
  for (const [pattern, response] of Object.entries(responses)) {
    if (pattern === 'default') continue
    if (pattern.split('|').some(kw => lower.includes(kw))) return response
  }
  return responses.default
}

export default function App() {
  const [lang, setLang] = useState(() => {
    try {
      return localStorage.getItem('rva311_lang') || 'en'
    } catch {
      return 'en'
    }
  })
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sessionId, setSessionId] = useState(() => generateSessionId())
  const [messages, setMessages] = useState([])
  const [status, setStatus] = useState('ready')
  const [speakEnabled, setSpeakEnabled] = useState(SPEAK_RESPONSES)
  const [selectedCategory, setSelectedCategory] = useState(null)
  const synthRef = useRef(window.speechSynthesis)

  const t = TRANSLATIONS[lang]
  const privacyNotice = lang === 'es' ? PRIVACY_NOTICE_ES : PRIVACY_NOTICE_EN

  useEffect(() => {
    try {
      localStorage.setItem('rva311_lang', lang)
    } catch {
      // Ignore localStorage errors
    }
  }, [lang])

  const addMessage = useCallback((role, text, sources = []) => {
    setMessages(prev => [...prev, { id: Date.now(), role, text, sources, timestamp: new Date() }])
  }, [])

  const speak = useCallback((text, forceLang) => {
    if (!speakEnabled || !synthRef.current) return
    synthRef.current.cancel()
    const utt = new SpeechSynthesisUtterance(text)
    const targetLang = forceLang || lang
    const voices = synthRef.current.getVoices()
    const preferred = targetLang === 'es'
      ? (voices.find(v => v.lang.startsWith('es')) || voices[0])
      : (voices.find(v => v.lang === 'en-US') || voices[0])
    if (preferred) utt.voice = preferred
    utt.lang = targetLang === 'es' ? 'es-US' : 'en-US'
    utt.rate = 0.95
    utt.onstart = () => setStatus('speaking')
    utt.onend = () => setStatus('ready')
    synthRef.current.speak(utt)
  }, [speakEnabled, lang])

  const switchLang = useCallback((newLang) => {
    setLang(newLang)
  }, [])

  const sendMessage = useCallback(async (text) => {
    if (!text.trim()) return
    synthRef.current?.cancel()
    addMessage('user', text)
    setStatus('thinking')

    if (SWITCH_TO_ES.test(text) && lang !== 'es') {
      setStatus('ready')
      switchLang('es')
      return
    }
    if (SWITCH_TO_EN.test(text) && lang !== 'en') {
      setStatus('ready')
      switchLang('en')
      return
    }

    try {
      let responseText
      let responseSources = []

      if (MODE === 'demo') {
        await new Promise(r => setTimeout(r, 900))
        responseText = getDemoResponse(text, lang)
      } else if (MODE === 'local') {
        const history = messages.slice(-8).map(m => ({ role: m.role, content: m.text }))
        const res = await fetch(`${API_ENDPOINT}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, lang, history, sessionId })
        })
        if (!res.ok) throw new Error(`Server error: ${res.status}`)
        const data = await res.json()
        responseText = data.response
      } else {
        const history = messages.slice(-8).map(m => ({ role: m.role, content: m.text }))
        const res = await fetch(`${API_ENDPOINT}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, sessionId, lang, history })
        })
        if (!res.ok) throw new Error(`API error: ${res.status}`)
        const data = await res.json()
        responseText = data.response
        responseSources = data.sources || []
      }

      addMessage('assistant', responseText, responseSources)
      speak(responseText)
    } catch (err) {
      console.error('Send error:', err)
      const errorMsg = lang === 'es'
        ? 'Lo siento, tengo problemas para conectarme. Por favor intente de nuevo.'
        : "I'm having trouble connecting right now. Please try again."
      addMessage('assistant', errorMsg)
      speak(errorMsg)
    } finally {
      setStatus('ready')
    }
  }, [sessionId, lang, messages, addMessage, speak, switchLang])

  const handleCategorySelect = (category) => {
    setSelectedCategory(category)
    setMessages([])
    const greeting = lang === 'es'
      ? `¿Cómo puedo ayudarle con ${category.nameEs}?`
      : `How can I help you with ${category.name}?`
    addMessage('assistant', greeting)
  }

  const handleHandoff = useCallback(async (orgKey) => {
    try {
      const res = await fetch(`${API_ENDPOINT}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'handoff', sessionId, action: 'handoff', targetOrg: orgKey })
      })
      const data = await res.json()
      const confirmMsg = lang === 'es'
        ? `Su caso ha sido transferido a ${data.handoffTarget || orgKey}. Un representante se comunicará con usted pronto.`
        : `Your case has been handed off to ${data.handoffTarget || orgKey}. A representative will reach out to you soon.`
      addMessage('assistant', confirmMsg)
    } catch (err) {
      console.error('Handoff error:', err)
      const errorMsg = lang === 'es'
        ? 'No se pudo completar la transferencia. Por favor intente de nuevo.'
        : 'Could not complete the handoff. Please try again.'
      addMessage('assistant', errorMsg)
    }
  }, [sessionId, lang, addMessage])

  const handleGoHome = () => {
    setSelectedCategory(null)
    setMessages([])
    setSessionId(generateSessionId())
    synthRef.current?.cancel()
    setStatus('ready')
  }

  return (
    <div className="app-container">
      <Sidebar lang={lang} onLangChange={switchLang} isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} onGoHome={handleGoHome} />
      <div className="main-content">
        <Header lang={lang} onLangChange={switchLang} onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} onGoHome={handleGoHome} />
        <div className="content">
          <Routes>
            <Route path="/" element={
              messages.length === 0 && !selectedCategory ? (
                <CategoryGrid lang={lang} onCategorySelect={handleCategorySelect} />
              ) : (
                <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                  <div className="privacy-notice">{privacyNotice}</div>
                  <ChatInterface
                    messages={messages}
                    status={status}
                    onSend={sendMessage}
                    onHandoff={handleHandoff}
                    lang={lang}
                    category={selectedCategory}
                  />
                </div>
              )
            } />
            <Route path="/faqs" element={<FAQs lang={lang} />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/dashboard/admin" element={<AdminDashboard />} />
          </Routes>
        </div>
      </div>
    </div>
  )
}
