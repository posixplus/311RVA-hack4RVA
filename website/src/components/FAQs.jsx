import { useState } from 'react'

const FAQ_SECTIONS = [
  {
    id: 'general',
    title: 'General',
    titleEs: 'General',
    icon: '🏛️',
    color: '#eff6ff',
    borderColor: '#2563eb',
    questions: [
      {
        q: 'What is RVA 311 Bridge?',
        qEs: '¿Qué es RVA 311 Bridge?',
        a: 'RVA 311 Bridge is a City of Richmond resource assistant that helps residents submit service requests, find city resources, and get connected to the right department — all in one place. It extends 311 services to 24/7 availability using an AI-powered assistant backed by verified Richmond city documents. Available in English, Spanish, and Arabic.',
        aEs: 'RVA 311 Bridge es un asistente de recursos de la Ciudad de Richmond que ayuda a los residentes a enviar solicitudes de servicio, encontrar recursos de la ciudad y conectarse con el departamento adecuado. Disponible en inglés, español y árabe.'
      },
      {
        q: 'Who can use this tool?',
        qEs: '¿Quién puede usar esta herramienta?',
        a: 'Any Richmond resident or visitor can use RVA 311 Bridge to report city issues, request services, or get information. No account is required to browse or chat — you only need to create an account to track your requests over time.',
        aEs: 'Cualquier residente o visitante de Richmond puede usar RVA 311 Bridge. No se requiere cuenta para navegar o chatear.'
      },
      {
        q: 'What languages are supported?',
        qEs: '¿Qué idiomas están disponibles?',
        a: 'The platform is available in English (EN), Spanish (ES), and Arabic (AR). You can switch languages at any time using the Language menu in the top navigation bar or sidebar. The AI assistant responds in the selected language.',
        aEs: 'La plataforma está disponible en inglés (EN), español (ES) y árabe (AR). Puede cambiar de idioma en cualquier momento.'
      },
      {
        q: 'Is this an official City of Richmond service?',
        qEs: '¿Es este un servicio oficial de la Ciudad de Richmond?',
        a: 'RVA 311 Bridge is a prototype developed at Hack4RVA 2026 to demonstrate how AI can extend 311 services after hours. It uses publicly available Richmond city documents but is not an official City service. For authoritative information, please call 311 during business hours or visit rva.gov.',
        aEs: 'RVA 311 Bridge es un prototipo desarrollado en Hack4RVA 2026. No es un servicio oficial de la Ciudad. Para información oficial, llame al 311 o visite rva.gov.'
      },
      {
        q: 'How does the AI assistant work?',
        qEs: '¿Cómo funciona el asistente de IA?',
        a: 'The assistant uses Retrieval Augmented Generation (RAG) to search verified Richmond city documents before answering. It does not make up information — every response is grounded in uploaded documents and cites its sources. If information is not available, it will tell you honestly and suggest contacting the appropriate agency.',
        aEs: 'El asistente usa Generación Aumentada por Recuperación (RAG) para buscar en documentos verificados de la ciudad antes de responder. No inventa información — cada respuesta cita sus fuentes.'
      },
    ]
  },
  {
    id: 'requests',
    title: 'Submitting Service Requests',
    titleEs: 'Envío de Solicitudes de Servicio',
    icon: '📝',
    color: '#f0fdf4',
    borderColor: '#166534',
    questions: [
      {
        q: 'What types of service requests can I submit?',
        qEs: '¿Qué tipos de solicitudes puedo enviar?',
        a: 'You can submit requests across these categories: Emergency Preparedness (storm damage, downed trees), Immigration & Refugee Support (legal aid, multilingual resources), Business Support Services (licenses, permits), Roads, Alleys, Sidewalks & Ramps, Lights, Signs & Traffic Signals, Trees & Vegetation, Parks & Public Spaces, Trash Collection & Cleanup, Housing & Rental Assistance, Food & Nutrition Assistance, and Healthcare & Mental Health.',
        aEs: 'Puede enviar solicitudes en: Preparación para Emergencias, Apoyo a Inmigrantes, Servicios Empresariales, Carreteras, Luces y Señales, Árboles, Parques, Recolección, Vivienda, Alimentos y Salud.'
      },
      {
        q: 'How do I submit a service request?',
        qEs: '¿Cómo envío una solicitud de servicio?',
        a: 'Click a category from the home screen, then chat with the AI assistant about your issue. You can also follow the four-step form: What (category) → Where (location) → Why (description) → Who (contact info). You can submit without an account, but creating one lets you track your request.',
        aEs: 'Haga clic en una categoría y chatee con el asistente. Siga los pasos: Qué → Dónde → Por qué → Quién.'
      },
      {
        q: 'What happens after I submit a request?',
        qEs: '¿Qué pasa después de enviar una solicitud?',
        a: 'Your request is logged and assigned a unique Session ID. The status will show as ACTIVE while being reviewed, COMPLETED when resolved, or HANDED OFF if it has been referred to a partner nonprofit or city department.',
        aEs: 'Su solicitud se registra con un ID de sesión único. El estado será ACTIVO, COMPLETADO o TRANSFERIDO.'
      },
      {
        q: 'Can I submit a request in Spanish or Arabic?',
        qEs: '¿Puedo enviar una solicitud en español o árabe?',
        a: 'Yes. Switch to your preferred language using the Language toggle before starting a chat, and the assistant will respond in that language.',
        aEs: 'Sí. Cambie al idioma deseado antes de iniciar un chat y el asistente responderá en ese idioma.'
      },
      {
        q: 'What does "Handed Off" mean?',
        qEs: '¿Qué significa "Transferido"?',
        a: 'Handed Off means your session has been forwarded to a partner agency — such as IRC Richmond, ReEstablish Richmond, Sacred Heart Center, Central Virginia Legal Aid, or another nonprofit — that is better equipped to help with your specific need.',
        aEs: 'Transferido significa que su sesión fue enviada a una agencia asociada como IRC Richmond, ReEstablish Richmond u otra organización mejor equipada para ayudarle.'
      },
    ]
  },
  {
    id: 'emergency',
    title: 'Emergency & Non-Emergency Issues',
    titleEs: 'Emergencias y No Emergencias',
    icon: '🚨',
    color: '#fef2f2',
    borderColor: '#dc2626',
    questions: [
      {
        q: 'What should I do in a life-threatening emergency?',
        qEs: '¿Qué debo hacer en una emergencia que amenaza la vida?',
        a: 'Call 911 immediately. RVA 311 Bridge is for non-emergency service requests and information only.',
        aEs: 'Llame al 911 inmediatamente. RVA 311 Bridge es solo para solicitudes no urgentes.'
      },
      {
        q: 'Who do I call for non-emergency police matters?',
        qEs: '¿A quién llamo para asuntos policiales no urgentes?',
        a: 'For non-emergency police situations — such as reporting downed trees blocking roads or storm damage — call the Richmond non-emergency police line at 804-646-5100.',
        aEs: 'Para situaciones policiales no urgentes, llame a la línea no urgente de Richmond al 804-646-5100.'
      },
      {
        q: 'What if my issue is urgent but not an emergency?',
        qEs: '¿Qué pasa si mi problema es urgente pero no es una emergencia?',
        a: 'Use the Emergency Preparedness category to flag urgent non-emergency issues like storm damage, road hazards, or freezing weather safety questions. City staff monitor these requests and prioritize accordingly.',
        aEs: 'Use la categoría de Preparación para Emergencias para problemas urgentes como daños por tormenta o peligros en carreteras.'
      },
      {
        q: 'What crisis hotlines are available 24/7?',
        qEs: '¿Qué líneas de crisis están disponibles 24/7?',
        a: 'Emergency: 911 · Richmond BHA Crisis Line: 804-819-4100 (24/7) · National Crisis Line: 988 · Immigration Emergency: 1-855-HELP-MY-FAMILY (1-855-435-7693) · Domestic Violence Hotline: 800-799-7233 · Human Trafficking Hotline: 888-373-7888',
        aEs: 'Emergencia: 911 · Línea de Crisis BHA: 804-819-4100 · Línea Nacional: 988 · Emergencia Migratoria: 1-855-435-7693 · Violencia Doméstica: 800-799-7233'
      },
    ]
  },
  {
    id: 'immigrant',
    title: 'Immigrant & Refugee Services',
    titleEs: 'Servicios para Inmigrantes y Refugiados',
    icon: '🌍',
    color: '#f5f3ff',
    borderColor: '#7c3aed',
    questions: [
      {
        q: 'Where can I get temporary housing or shelter assistance?',
        qEs: '¿Dónde puedo obtener ayuda con vivienda temporal?',
        a: 'Contact RRHA (Richmond Redevelopment & Housing Authority) at 804-780-4200, Dept. of Social Services Emergency Assistance at 804-646-7201, IRC Richmond for refugee-specific housing, or ReEstablish Richmond. You can also use the Hand Off button in the chat to connect directly.',
        aEs: 'Contacte a RRHA al 804-780-4200, Servicios Sociales al 804-646-7201, IRC Richmond o ReEstablish Richmond. También puede usar el botón de Transferencia en el chat.'
      },
      {
        q: 'Do I need to share my immigration status to use this tool?',
        qEs: '¿Necesito compartir mi estatus migratorio?',
        a: 'No. RVA 311 Bridge does not collect or store immigration status, and you are never asked for it. The tool is designed with privacy-first principles — no PII is collected or stored. All residents can access services regardless of immigration status.',
        aEs: 'No. RVA 311 Bridge no recopila ni almacena estatus migratorio. La herramienta está diseñada con privacidad primero — no se recopila información personal.'
      },
      {
        q: 'What if I need legal help with an immigration issue?',
        qEs: '¿Qué pasa si necesito ayuda legal con un tema migratorio?',
        a: 'Contact Central Virginia Legal Aid Society at 804-648-1012 for free legal help. For 24/7 immigration emergency support, call 1-855-HELP-MY-FAMILY (1-855-435-7693).',
        aEs: 'Contacte a Central Virginia Legal Aid al 804-648-1012. Para emergencias migratorias 24/7: 1-855-HELP-MY-FAMILY (1-855-435-7693).'
      },
      {
        q: 'What are my rights if I encounter ICE or CBP officers?',
        qEs: '¿Cuáles son mis derechos si encuentro oficiales de ICE o CBP?',
        a: 'Stay calm — do not run, argue, or resist. You have the right to remain silent. Do NOT open your door — officers need a warrant signed by a judge to enter. ICE forms are NOT judge-signed warrants. Ask: "Are you from ICE or CBP?" For 24/7 support: 1-855-HELP-MY-FAMILY. Richmond Legal Aid: 804-648-1012.',
        aEs: 'Mantenga la calma — no corra ni discuta. Tiene derecho a guardar silencio. NO abra su puerta — necesitan una orden firmada por un juez. Pregunte: "¿Es usted de ICE o CBP?" Apoyo 24/7: 1-855-435-7693.'
      },
    ]
  },
  {
    id: 'business',
    title: 'Business Support Services',
    titleEs: 'Servicios de Apoyo Empresarial',
    icon: '💼',
    color: '#fff7ed',
    borderColor: '#c2410c',
    questions: [
      {
        q: 'I want to start a business in Richmond. Where do I begin?',
        qEs: 'Quiero iniciar un negocio en Richmond. ¿Por dónde empiezo?',
        a: 'Use the Business Support Services category on the home screen. It opens the RVA BizNavigator — a self-guided webpage that walks you through business registration, permits, licensing, zoning requirements, and local resources specific to your business type, location, and industry. This feature is online only.',
        aEs: 'Use la categoría de Servicios Empresariales en la pantalla principal. Abre el RVA BizNavigator, una guía paso a paso para registro, permisos, licencias y zonificación.'
      },
      {
        q: 'Can I get business support over the phone?',
        qEs: '¿Puedo obtener apoyo empresarial por teléfono?',
        a: 'The Business Support Services tool is currently online only. For phone-based business assistance, contact the City of Richmond Department of Economic Development or call 311 during business hours.',
        aEs: 'La herramienta de servicios empresariales es solo en línea. Para asistencia por teléfono, llame al 311 en horario de oficina.'
      },
    ]
  },
  {
    id: 'privacy',
    title: 'Privacy & Data',
    titleEs: 'Privacidad y Datos',
    icon: '🔒',
    color: '#f0fdf4',
    borderColor: '#166534',
    questions: [
      {
        q: 'Is my personal information kept private?',
        qEs: '¿Mi información personal es privada?',
        a: 'Yes. RVA 311 Bridge is designed with privacy-first principles. No personally identifiable information (PII) is collected or stored. Chat conversations are processed with automatic PII redaction using AWS Comprehend before any data is logged.',
        aEs: 'Sí. RVA 311 Bridge está diseñado con privacidad primero. No se recopila ni almacena información personal identificable (PII).'
      },
      {
        q: 'Will my request be visible to others?',
        qEs: '¿Mi solicitud será visible para otros?',
        a: 'The Service Requests Dashboard shows aggregate anonymized data only (category counts, language distribution, etc.). Individual conversations are private and are not displayed publicly.',
        aEs: 'El panel muestra solo datos anónimos agregados. Las conversaciones individuales son privadas.'
      },
      {
        q: 'What data is collected during a chat?',
        qEs: '¿Qué datos se recopilan durante un chat?',
        a: 'The system logs: category selected, language used, message count, and session timestamps. All message content is PII-redacted before storage. No names, addresses, phone numbers, or immigration status are stored. Sessions expire automatically after 7 days.',
        aEs: 'El sistema registra: categoría, idioma, conteo de mensajes y marcas de tiempo. Todo contenido se redacta de PII antes de almacenarse. Las sesiones expiran en 7 días.'
      },
      {
        q: 'Can I use this tool anonymously?',
        qEs: '¿Puedo usar esta herramienta de forma anónima?',
        a: 'Yes. No login, account, or personal information is required to use the chat assistant. You can browse categories and ask questions completely anonymously.',
        aEs: 'Sí. No se requiere inicio de sesión ni información personal. Puede navegar y hacer preguntas de forma completamente anónima.'
      },
    ]
  },
  {
    id: 'tracking',
    title: 'Tracking & Account',
    titleEs: 'Seguimiento y Cuenta',
    icon: '📊',
    color: '#eff6ff',
    borderColor: '#2563eb',
    questions: [
      {
        q: 'Do I need an account to submit a request?',
        qEs: '¿Necesito una cuenta para enviar una solicitud?',
        a: 'No. You can chat and get assistance without signing in. However, creating a free account lets you view your request history and receive status updates via email.',
        aEs: 'No. Puede chatear sin iniciar sesión. Crear una cuenta gratuita le permite ver su historial y recibir actualizaciones.'
      },
      {
        q: 'How do I check the status of my request?',
        qEs: '¿Cómo verifico el estado de mi solicitud?',
        a: 'Visit the Dashboard page from the sidebar. The public dashboard shows all sessions in anonymized form. If you have admin access, you can view full session details.',
        aEs: 'Visite el Panel de Control desde la barra lateral. El panel público muestra sesiones anónimas.'
      },
      {
        q: 'Can I get a summary of my conversation sent to me?',
        qEs: '¿Puedo recibir un resumen de mi conversación?',
        a: 'Yes. At the end of a conversation, you can request a summary to be delivered to your email address. This is optional and your email is only used for delivery — it is not stored permanently.',
        aEs: 'Sí. Al final de una conversación, puede solicitar un resumen por correo electrónico. Es opcional y su correo no se almacena permanentemente.'
      },
    ]
  },
]

const QUICK_CONTACTS = [
  { name: 'Emergency', nameEs: 'Emergencia', phone: '911', desc: 'Life-threatening emergencies only', descEs: 'Solo emergencias que amenazan la vida' },
  { name: 'Richmond 311', nameEs: 'Richmond 311', phone: '311', desc: 'City services during business hours', descEs: 'Servicios de la ciudad en horario de oficina' },
  { name: 'Non-Emergency Police', nameEs: 'Policía No Urgente', phone: '804-646-5100', desc: 'Storm damage, road hazards', descEs: 'Daños por tormenta, peligros viales' },
  { name: 'Richmond BHA Crisis', nameEs: 'Crisis BHA Richmond', phone: '804-819-4100', desc: '24/7 mental health crisis line', descEs: 'Línea de crisis de salud mental 24/7' },
  { name: 'Central VA Legal Aid', nameEs: 'Ayuda Legal VA Central', phone: '804-648-1012', desc: 'Free legal help', descEs: 'Ayuda legal gratuita' },
  { name: 'Immigration Emergency', nameEs: 'Emergencia Migratoria', phone: '1-855-435-7693', desc: '24/7 — 1-855-HELP-MY-FAMILY', descEs: '24/7 — 1-855-HELP-MY-FAMILY' },
  { name: 'Central VA Foodbank', nameEs: 'Banco de Alimentos VA', phone: '804-521-2500', desc: 'Food assistance for all residents', descEs: 'Asistencia alimentaria' },
  { name: 'CrossOver Healthcare', nameEs: 'CrossOver Healthcare', phone: '804-655-4800', desc: 'Free primary care', descEs: 'Atención primaria gratuita' },
]

export default function FAQs({ lang }) {
  const [search, setSearch] = useState('')
  const [openItem, setOpenItem] = useState(null)

  const toggle = (sectionId, idx) => {
    const key = `${sectionId}-${idx}`
    setOpenItem(openItem === key ? null : key)
  }

  const filteredSections = FAQ_SECTIONS.map(section => ({
    ...section,
    questions: section.questions.filter(q => {
      if (!search) return true
      const s = search.toLowerCase()
      const question = lang === 'es' ? q.qEs : q.q
      const answer = lang === 'es' ? q.aEs : q.a
      return question.toLowerCase().includes(s) || answer.toLowerCase().includes(s)
    })
  })).filter(s => s.questions.length > 0)

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      {/* Disclaimer */}
      <div style={{ background: '#fff7ed', border: '1.5px solid #fed7aa', borderRadius: 10, padding: '14px 18px', fontSize: 13, color: '#9a3412', display: 'flex', alignItems: 'flex-start', gap: 10, lineHeight: 1.5, marginBottom: 20 }}>
        <span style={{ fontSize: 18, flexShrink: 0 }}>⚠️</span>
        <div>
          <strong>{lang === 'es' ? 'Nota:' : 'Note:'}</strong>{' '}
          {lang === 'es'
            ? 'Algunas respuestas pueden ser limitadas ya que no tuvimos acceso a toda la documentación de Richmond 311 durante este hackathon. Para respuestas completas, llame al 311 o visite rva.gov.'
            : 'Some responses may be limited as we did not have access to all documentation from Richmond 311 during this hackathon build. For complete and authoritative answers, please call 311 during business hours or visit rva.gov.'}
        </div>
      </div>

      {/* Search */}
      <div style={{ marginBottom: 24 }}>
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder={lang === 'es' ? 'Buscar en las preguntas frecuentes...' : 'Search FAQs...'}
          style={{ width: '100%', padding: '12px 16px', border: '1.5px solid #e5e7eb', borderRadius: 10, fontSize: 14, fontFamily: 'inherit', outline: 'none', transition: 'border-color 0.2s' }}
          onFocus={e => e.target.style.borderColor = '#2563eb'}
          onBlur={e => e.target.style.borderColor = '#e5e7eb'}
        />
      </div>

      {/* Sections */}
      {filteredSections.map(section => (
        <div key={section.id} style={{ marginBottom: 28 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12, paddingBottom: 8, borderBottom: '2px solid #e5e7eb' }}>
            <div style={{ width: 36, height: 36, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, background: section.color, flexShrink: 0 }}>
              {section.icon}
            </div>
            <span style={{ fontSize: 16, fontWeight: 700, color: '#004080' }}>
              {lang === 'es' ? section.titleEs : section.title}
            </span>
            <span style={{ fontSize: 11, background: '#f9fafb', color: '#6b7280', padding: '2px 8px', borderRadius: 10, fontWeight: 600 }}>
              {section.questions.length}
            </span>
          </div>

          {section.questions.map((q, idx) => {
            const key = `${section.id}-${idx}`
            const isOpen = openItem === key
            return (
              <div key={idx} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, marginBottom: 8, overflow: 'hidden', boxShadow: isOpen ? '0 2px 8px rgba(0,0,0,0.06)' : 'none', transition: 'box-shadow 0.2s' }}>
                <div
                  onClick={() => toggle(section.id, idx)}
                  style={{ padding: '14px 18px', fontWeight: 600, fontSize: 14, cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, color: isOpen ? '#2563eb' : '#1f2937', userSelect: 'none' }}
                >
                  {lang === 'es' ? q.qEs : q.q}
                  <span style={{ fontSize: 12, color: isOpen ? '#2563eb' : '#6b7280', transition: 'transform 0.2s', transform: isOpen ? 'rotate(180deg)' : 'none', flexShrink: 0 }}>▼</span>
                </div>
                {isOpen && (
                  <div style={{ padding: '0 18px 16px', fontSize: 13.5, color: '#374151', lineHeight: 1.7, borderTop: '1px solid #f3f4f6', animation: 'fadeIn 0.2s ease' }}>
                    {lang === 'es' ? q.aEs : q.a}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ))}

      {/* Quick Contacts */}
      <div style={{ background: '#fff', border: '1.5px solid #e5e7eb', borderRadius: 12, padding: '20px 24px', marginTop: 32 }}>
        <h3 style={{ fontSize: 15, fontWeight: 700, color: '#004080', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
          📞 {lang === 'es' ? 'Números de Contacto Rápido' : 'Quick Contact Numbers'}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 10 }}>
          {QUICK_CONTACTS.map((c, i) => (
            <div key={i} style={{ background: '#f9fafb', borderRadius: 8, padding: 12, fontSize: 13 }}>
              <div style={{ fontWeight: 600, color: '#1f2937', marginBottom: 2 }}>{lang === 'es' ? c.nameEs : c.name}</div>
              <div style={{ color: '#2563eb', fontWeight: 500 }}>{c.phone}</div>
              <div style={{ color: '#6b7280', fontSize: 12 }}>{lang === 'es' ? c.descEs : c.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ textAlign: 'center', padding: 24, color: '#6b7280', fontSize: 12, borderTop: '1px solid #e5e7eb', marginTop: 32 }}>
        RVA 311 Bridge — Hack4RVA 2026 · Thriving & Inclusive Communities Pillar
      </div>
    </div>
  )
}
