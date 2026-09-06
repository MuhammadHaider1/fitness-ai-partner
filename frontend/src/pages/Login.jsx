import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ErrBanner } from '../components/ui'

export default function Login() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    setBusy(true)
    try {
      await login(form.email, form.password)
      nav('/')
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'Login failed. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-wrap">
      <AuthHero />
      <div className="auth-form-side">
        <div className="auth-card">
          <h2>Welcome back 👋</h2>
          <p className="sub">Log in to continue tracking your fitness journey</p>
          <ErrBanner message={err} />
          <form onSubmit={submit}>
            <div className="field">
              <label>Email</label>
              <input
                className="input" type="email" required placeholder="you@example.com"
                value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Password</label>
              <input
                className="input" type="password" required placeholder="••••••••"
                value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </div>
            <button className="btn btn--block" disabled={busy}>
              {busy ? <span className="spinner" /> : 'Login'}
            </button>
          </form>
          <p className="muted" style={{ textAlign: 'center', marginTop: 18 }}>
            New here? <a href="/register" style={{ color: 'var(--primary-2)', fontWeight: 600 }}>Create an account</a>
          </p>
        </div>
      </div>
    </div>
  )
}

export function AuthHero() {
  return (
    <div className="auth-hero">
      <div style={{ position: 'relative', zIndex: 1 }}>
        <h1>Your AI <span>Fitness</span> Partner</h1>
        <p>Log meals &amp; workouts in plain language — let AI do the tracking and get smart coach insights.</p>
        <div className="auth-feature">
          <div className="auth-feature-icon">🗣️</div>
          <div>
            <b>Natural-language logging</b>
            <span>Just say what you ate or did — AI parses it for you.</span>
          </div>
        </div>
        <div className="auth-feature">
          <div className="auth-feature-icon">🎯</div>
          <div>
            <b>Smart nutrition estimates</b>
            <span>RAG-grounded, verified food data — not random guessing.</span>
          </div>
        </div>
        <div className="auth-feature">
          <div className="auth-feature-icon">🤖</div>
          <div>
            <b>AI Coach</b>
            <span>Daily &amp; weekly insights, targets, and suggestions.</span>
          </div>
        </div>
      </div>
    </div>
  )
}