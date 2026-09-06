export function Stat({ label, value, icon, color = '#10b981' }) {
  return (
    <div className="stat">
      <div className="stat__top">
        <span className="stat__label">{label}</span>
        {icon && <span style={{ fontSize: 20 }}>{icon}</span>}
      </div>
      <div className="stat__value">{value}</div>
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
        <circle cx="75" cy="75" r={r} fill="none" stroke="#1c2a42" strokeWidth="12" />
        <circle
          cx="75" cy="75" r={r} fill="none"
          stroke={over ? '#ef4444' : '#3b82f6'}
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