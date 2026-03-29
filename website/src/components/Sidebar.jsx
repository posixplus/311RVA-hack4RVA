import { useState } from 'react'
import { Link } from 'react-router-dom'

export default function Sidebar({ lang, onLangChange, isOpen, onClose, onGoHome }) {
  const [expandedMenu, setExpandedMenu] = useState(null)

  const toggleSubmenu = (menuName) => {
    setExpandedMenu(expandedMenu === menuName ? null : menuName)
  }

  const navItems = lang === 'es' ? [
    { label: 'Inicio', path: '/' },
    { label: 'Panel de Control', path: '/dashboard' },
    { label: 'Preguntas Frecuentes', path: '/faqs' }
  ] : [
    { label: 'Home', path: '/' },
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'FAQs', path: '/faqs' }
  ]

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-logo">
        <span className="sidebar-logo-icon">🛡️</span>
        <span>RVA 311 Bridge</span>
      </div>

      <nav>
        <ul className="sidebar-nav">
          {navItems.map((item, idx) => (
            <li key={idx} className="sidebar-nav-item">
              {item.external ? (
                <a href={item.path} className="sidebar-nav-link" target="_blank" rel="noopener noreferrer" onClick={onClose}>
                  {item.label}
                </a>
              ) : (
                <Link to={item.path} className="sidebar-nav-link" onClick={() => { if (item.path === '/') { onGoHome?.(); } onClose(); }}>
                  {item.label}
                </Link>
              )}
            </li>
          ))}

          <li className="sidebar-nav-item sidebar-expandable">
            <button
              className="sidebar-nav-link"
              onClick={() => toggleSubmenu('requests')}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <span>{lang === 'es' ? 'Solicitudes' : 'Service Requests'}</span>
              <span className={`sidebar-expandable-arrow ${expandedMenu === 'requests' ? 'expanded' : ''}`}>▼</span>
            </button>
            <ul className={`sidebar-submenu ${expandedMenu === 'requests' ? 'open' : ''}`}>
              <li className="sidebar-submenu-item">
                <Link to="/" className="sidebar-submenu-link" onClick={onClose}>
                  {lang === 'es' ? 'Ver Todo' : 'View All'}
                </Link>
              </li>
              <li className="sidebar-submenu-item">
                <Link to="/" className="sidebar-submenu-link" onClick={onClose}>
                  {lang === 'es' ? 'Crear Nuevo' : 'Create New'}
                </Link>
              </li>
            </ul>
          </li>
        </ul>
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-language-selector">
          <div style={{ fontSize: '11px', marginBottom: '8px', opacity: 0.8 }}>
            {lang === 'es' ? 'Idioma' : 'Language'}
          </div>
          <div className="language-buttons">
            <button
              className={`language-btn ${lang === 'en' ? 'active' : ''}`}
              onClick={() => onLangChange('en')}
            >
              EN
            </button>
            <button
              className={`language-btn ${lang === 'es' ? 'active' : ''}`}
              onClick={() => onLangChange('es')}
            >
              ES
            </button>
            <button
              className={`language-btn ${lang === 'ar' ? 'active' : ''}`}
              onClick={() => onLangChange('ar')}
            >
              AR
            </button>
          </div>
        </div>

        <button className="create-account-btn">
          {lang === 'es' ? 'Crear Cuenta' : 'Create Account'}
        </button>
      </div>
    </aside>
  )
}
