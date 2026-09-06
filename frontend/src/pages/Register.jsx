import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ErrBanner } from '../components/ui'
import { AuthHero } from './Login'

const levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']
const goals = ['weight_loss', 'maintenance', 'muscle_gain', 'recomp']

export default function Register() {
  const { register } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({
    email: '', password: '', full_name: '', age: '', height_cm: '', weight_kg: '',
    gender: 'male', goal: 'weight_loss', activity_level: 'light',
  })
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    setBusy(true)
    try {
      await register({
        email: form.email,
        password: form.password,
        full_name: form.full_name || null,
        age: form.age ? Number(form.age) : null,
        height_cm: form.height_cm ? Number(form.height_cm) : null,
        weight_kg: form.weight_kg ? Number(form.weight_kg) : null,
        gender: form.gender,
        goal: form.goal,
        activity_level: form.activity_level,
      })
      nav('/')
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  return (
    <div className="auth-wrap">
      <AuthHero />
      <div className="auth-form-side">
        <div className="auth-card">
          <h2>Create account ✨</h2>
          <p className="sub">Set up your profile to get accurate targets &amp; insights</p>
          <ErrBanner message={err} />
          <form onSubmit={submit}>
            <div className="grid grid--2" style={{ gap: 12 }}>
              <div className="field">
                <label>Full name</label>
                <input className="input" placeholder="Ali Khan" value={form.full_name} onChange={(e) => set('full_name', e.target.value)} />
              </div>
              <div className="field">
                <label>Age</label>
                <input className="input" type="number" placeholder="25" value={form.age} onChange={(e) => set('age', e.target.value)} />
              </div>
            </div>
            <div className="field">
              <label>Email</label>
              <input className="input" type="email" required placeholder="you@example.com" value={form.email} onChange={(e) => set('email', e.target.value)} />
            </div>
            <div className="field">
              <label>Password</label>
              <input className="input" type="password" required placeholder="Min 6 characters" value={form.password} onChange={(e) => set('password', e.target.value)} />
            </div>
            <div className="grid grid--2" style={{ gap: 12 }}>
              <div className="field">
                <label>Height (cm)</label>
                <input className="input" type="number" placeholder="172" value={form.height_cm} onChange={(e) => set('height_cm', e.target.value)} />
              </div>
              <div className="field">
                <label>Weight (kg)</label>
                <input className="input" type="number" placeholder="70" value={form.weight_kg} onChange={(e) => set('weight_kg', e.target.value)} />
              </div>
            </div>
            <div className="grid grid--2" style={{ gap: 12 }}>
              <div className="field">
                <label>Gender</label>
                <select className="select" value={form.gender} onChange={(e) => set('gender', e.target.value)}>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="field">
                <label>Activity level</label>
                <select className="select" value={form.activity_level} onChange={(e) => set('activity_level', e.target.value)}>
                  {levels.map((l) => <option key={l} value={l}>{l.replace('_', ' ')}</option>)}
                </select>
              </div>
            </div>
            <div className="field">
              <label>Goal</label>
              <select className="select" value={form.goal} onChange={(e) => set('goal', e.target.value)}>
                {goals.map((g) => <option key={g} value={g}>{g.replace('_', ' ')}</option>)}
              </select>
            </div>
            <button className="btn btn--block" disabled={busy}>
              {busy ? <span className="spinner" /> : 'Create account'}
            </button>
          </form>
          <p className="muted" style={{ textAlign: 'center', marginTop: 18 }}>
            Already have an account? <a href="/login" style={{ color: 'var(--primary-2)', fontWeight: 600 }}>Login</a>
          </p>
        </div>
      </div>
    </div>
  )
}