import './InfoPanel.css'

const ICONS = ['🏠','🍎','🏥','⚖️','💡','🧠','💼','👶']

export default function InfoPanel({ connectPhone, t }) {
  const steps = [
    { num: '1', label: t.step1, desc: t.step1d },
    { num: '2', label: t.step2, desc: t.step2d },
    { num: '3', label: t.step3, desc: t.step3d },
  ]

  return (
    <aside className="info-panel">
      <div className="info-card">
        <div className="info-available">
          <span className="dot-green"></span>
          {t.available}
        </div>
      </div>

      <div className="info-card">
        <h2 className="info-card-title">{t.howItWorks}</h2>
        {steps.map(s => (
          <div className="step" key={s.num}>
            <span className="step-num">{s.num}</span>
            <div><strong>{s.label}</strong><p>{s.desc}</p></div>
          </div>
        ))}
      </div>

      <div className="info-card call-card">
        <h2 className="info-card-title">{t.callTitle}</h2>
        <p className="call-number">{connectPhone}</p>
        <p className="call-note">{t.callNote}</p>
      </div>

      <div className="info-card">
        <h2 className="info-card-title">{t.resourcesTitle}</h2>
        <ul className="resource-list">
          {t.resources.map((label, i) => (
            <li key={label}><span>{ICONS[i]}</span> {label}</li>
          ))}
        </ul>
      </div>

      <div className="info-card lang-card"><p>{t.langNote}</p></div>
    </aside>
  )
}
