import { useState } from 'react'

export default function ConversationEnd({ lang, onClose, category }) {
  const [satisfaction, setSatisfaction] = useState(null)
  const [showContact, setShowContact] = useState(false)
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [rating, setRating] = useState(0)

  const handleSatisfaction = (value) => {
    setSatisfaction(value)
    if (value === 'no') {
      setShowContact(false)
    }
  }

  const handleSubmit = () => {
    alert(lang === 'es'
      ? 'Gracias por su retroalimentación. Sus datos se han guardado de forma segura.'
      : 'Thank you for your feedback. Your information has been saved securely.'
    )
    onClose()
  }

  return (
    <div className="conversation-end">
      <h2 className="conversation-end-heading">
        {lang === 'es'
          ? '¿Está satisfecho con la información proporcionada?'
          : 'Are you satisfied with the information provided?'
        }
      </h2>

      <div className="satisfaction-buttons">
        <button
          className={`satisfaction-btn ${satisfaction === 'yes' ? 'selected' : ''}`}
          onClick={() => handleSatisfaction('yes')}
        >
          {lang === 'es' ? 'Sí' : 'Yes'}
        </button>
        <button
          className={`satisfaction-btn ${satisfaction === 'no' ? 'selected' : ''}`}
          onClick={() => handleSatisfaction('no')}
        >
          {lang === 'es' ? 'No, necesito más ayuda' : 'No, I need more help'}
        </button>
      </div>

      {satisfaction === 'yes' && (
        <>
          <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #DDD' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '15px' }}>
              {lang === 'es' ? 'Calificar esta experiencia' : 'Rate this experience'}
            </h3>
            <div className="rating-stars">
              {[1, 2, 3, 4, 5].map(star => (
                <button
                  key={star}
                  className={`star ${rating >= star ? 'filled' : ''}`}
                  onClick={() => setRating(star)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                >
                  ★
                </button>
              ))}
            </div>
          </div>

          {!showContact && (
            <div style={{ marginTop: '20px' }}>
              <button
                className="primary-btn"
                onClick={() => setShowContact(true)}
              >
                {lang === 'es'
                  ? '¿Desea recibir estos detalles por email o SMS?'
                  : 'Would you like to receive these details by email or SMS?'
                }
              </button>
            </div>
          )}

          {showContact && (
            <div className="contact-info-form">
              <div className="form-group">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  className="form-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                />
                <p className="form-note">
                  {lang === 'es'
                    ? 'Se redactará en el tablero público'
                    : 'Will be redacted on public dashboard'
                  }
                </p>
              </div>

              <div className="form-group">
                <label className="form-label">
                  {lang === 'es' ? 'Teléfono' : 'Phone'}
                </label>
                <input
                  type="tel"
                  className="form-input"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="(804) 555-0000"
                />
                <p className="form-note">
                  {lang === 'es'
                    ? 'Se redactará en el tablero público'
                    : 'Will be redacted on public dashboard'
                  }
                </p>
              </div>

              {category && (
                <button className="secondary-btn" style={{ marginTop: '20px' }}>
                  {lang === 'es'
                    ? `Derivar a ${category.parentName || category.name}`
                    : `Hand off to ${category.parentName || category.name}`
                  }
                </button>
              )}

              <div className="action-buttons">
                <button className="primary-btn" onClick={handleSubmit}>
                  {lang === 'es' ? 'Enviar' : 'Submit'}
                </button>
                <button className="secondary-btn" onClick={onClose}>
                  {lang === 'es' ? 'Cancelar' : 'Cancel'}
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {satisfaction === 'no' && (
        <div className="action-buttons" style={{ marginTop: '20px' }}>
          <button
            className="primary-btn"
            onClick={() => {
              alert(lang === 'es'
                ? 'Iniciando conexión con un especialista...'
                : 'Initiating connection with a specialist...'
              )
            }}
          >
            {lang === 'es'
              ? 'Conectar con un Especialista'
              : 'Connect with a Specialist'
            }
          </button>
          <button className="secondary-btn" onClick={onClose}>
            {lang === 'es' ? 'Cerrar' : 'Close'}
          </button>
        </div>
      )}
    </div>
  )
}
