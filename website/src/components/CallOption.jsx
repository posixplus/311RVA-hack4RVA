import { CONNECT_PHONE, PRIVACY_NOTICE_EN, PRIVACY_NOTICE_ES } from '../config'

export default function CallOption({ lang }) {
  const privacy = lang === 'es' ? PRIVACY_NOTICE_ES : PRIVACY_NOTICE_EN

  return (
    <div className="call-option">
      <div className="call-option-icon">📞</div>
      <h2 className="call-option-title">
        {lang === 'es' ? 'Llamar a la Línea 311' : 'Call the 311 Line'}
      </h2>
      <div className="call-option-number">{CONNECT_PHONE}</div>
      <div className="call-option-availability">
        {lang === 'es'
          ? 'Disponible 24/7 en inglés, español y árabe'
          : 'Available 24/7 in English, Spanish, and Arabic'
        }
      </div>

      <div className="language-badges">
        <span className="language-badge">🇺🇸 English</span>
        <span className="language-badge">🇪🇸 Español</span>
        <span className="language-badge">🇸🇦 العربية</span>
      </div>

      <div className="ivr-flow">
        <div className="flow-step">
          <div className="flow-number">1</div>
          <div className="flow-text">
            {lang === 'es'
              ? 'Seleccione su idioma (Inglés, Español, Árabe)'
              : 'Select your language (English, Spanish, Arabic)'
            }
          </div>
        </div>
        <div className="flow-step">
          <div className="flow-number">2</div>
          <div className="flow-text">
            {lang === 'es'
              ? 'Describa brevemente su solicitud'
              : 'Briefly describe your request'
            }
          </div>
        </div>
        <div className="flow-step">
          <div className="flow-number">3</div>
          <div className="flow-text">
            {lang === 'es'
              ? 'Será conectado con un representante o recibirá orientación de recursos'
              : 'You will be connected with a representative or receive resource guidance'
            }
          </div>
        </div>
      </div>

      <button className="call-button" onClick={() => alert(lang === 'es' ? 'Llamada iniciada' : 'Call initiated')}>
        {lang === 'es' ? 'Llamar Ahora' : 'Call Now'}
      </button>

      <div className="privacy-notice" style={{ marginTop: '25px' }}>
        {privacy}
      </div>
    </div>
  )
}
