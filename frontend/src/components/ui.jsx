export function Stat({ label, value, icon, color = '#a3e635' }) {
  return (
    <div className="stat">
      <div className="stat__top">
        <span className="stat__label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 8, height: 8, borderRadius: 3, background: color, boxShadow: `0 0 8px ${color}` }} />
          {label}
        </span>
        {icon && <span style={{ fontSize: 20 }}>{icon}</span>}
      </div>
      <div className="stat__value">{value}</div>
    </div>
  )
}

export function PageTitle({ children, emoji, sub, center = false }) {
  return (
    <div className={`page-title-wrap${center ? ' page-title-wrap--center' : ''}`}>
      <h1 className="page-title">
        <span className="page-title__txt">{children}</span>
        {emoji && <span className="page-title__emoji" aria-hidden="true">{emoji}</span>}
      </h1>
      {sub && <p className="page-sub">{sub}</p>}
    </div>
  )
}

export function RingProgress({ value, max, label }) {
  const pct = max > 0 ? Math.min(value / max, 1) : 0
  const r = 62
  const c = 2 * Math.PI * r
  const offset = c * (1 - pct)
  const over = max > 0 && value > max

  return (
    <div className="ring">
      <svg width="150" height="150">
        <circle cx="75" cy="75" r={r} fill="none" stroke="#17202f" strokeWidth="12" />
        <circle
          cx="75" cy="75" r={r} fill="none"
          stroke={over ? '#ef4444' : '#a3e635'}
          strokeWidth="12" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <div className="ring__center">
        <div>
          <div className="ring__value">{Math.round(value)}<small> / {Math.round(max)}</small></div>
          <div className="muted">{label}</div>
        </div>
      </div>
    </div>
  )
}

export function Pill({ children, tone = 'mute' }) {
  return <span className={`pill pill--${tone}`}>{children}</span>
}

export function Empty({ emoji = '📭', title, subtitle }) {
  return (
    <div className="empty">
      <div className="empty-emoji">{emoji}</div>
      <b>{title}</b>
      {subtitle && <div className="muted">{subtitle}</div>}
    </div>
  )
}

export function Spinner({ dark = false }) {
  return <span className={`spinner${dark ? ' spinner--dark' : ''}`} />
}

export function LoadingFill() {
  return (
    <div className="loading-fill">
      <Spinner dark />
    </div>
  )
}

export function ErrBanner({ message }) {
  if (!message) return null
  return <div className="err-banner">⚠️ {message}</div>
}