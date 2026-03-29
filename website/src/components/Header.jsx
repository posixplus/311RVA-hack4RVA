import { useLocation, Link } from 'react-router-dom'

const getCurrentDate = () => {
  const now = new Date(2026, 2, 28)
  const days = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
  const months = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']
  return `TODAY IS ${days[now.getDay()]}, ${months[now.getMonth()]} ${now.getDate()}, ${now.getFullYear()}`
}

export default function Header({ lang, onLangChange, onToggleSidebar, onGoHome }) {
  const location = useLocation()
  const isChat = location.pathname === '/'

  const breadcrumbs = {
    en: 'Create New Request / What',
    es: 'Crear Nueva Solicitud / Qué'
  }

  return (
    <header className="header">
      <div className="header-top">
        <Link to="/" className="header-home-link" onClick={onGoHome} style={{ textDecoration: 'none', color: 'inherit', cursor: 'pointer', marginRight: '16px', fontWeight: 600, fontSize: '14px' }}>
          🏠 {lang === 'es' ? 'Inicio' : 'Home'}
        </Link>
        <div className="header-date">{getCurrentDate()}</div>
        <div className="header-actions">
          <button className="header-icon-btn" title="Notifications">🔔</button>
          <button className="header-icon-btn" title="Messages">💬</button>
          <div className="header-language">
            <button
              className={`lang-btn ${lang === 'en' ? 'active' : ''}`}
              onClick={() => onLangChange('en')}
            >
              EN
            </button>
            <button
              className={`lang-btn ${lang === 'es' ? 'active' : ''}`}
              onClick={() => onLangChange('es')}
            >
              ES
            </button>
          </div>
          <button className="header-signin">
            {lang === 'es' ? 'Iniciar Sesión' : 'Sign In'}
          </button>
        </div>
      </div>

      {isChat && (
        <>
          <div className="header-breadcrumb">
            {breadcrumbs[lang]}
          </div>
          <div className="header-progress">
            <div className="progress-step active">
              <div className="progress-step-number">1</div>
              <span>WHAT</span>
            </div>
            <div className="progress-divider"></div>
            <div className="progress-step">
              <div className="progress-step-number">2</div>
              <span>WHERE</span>
            </div>
            <div className="progress-divider"></div>
            <div className="progress-step">
              <div className="progress-step-number">3</div>
              <span>WHY</span>
            </div>
            <div className="progress-divider"></div>
            <div className="progress-step">
              <div className="progress-step-number">4</div>
              <span>WHO</span>
            </div>
          </div>
        </>
      )}
    </header>
  )
}
