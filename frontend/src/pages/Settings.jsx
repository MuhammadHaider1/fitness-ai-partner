import { useEffect, useState } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { ErrBanner, Spinner } from '../components/ui'
import { todayISO } from '../services/format'

const levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']
const goals = ['weight_loss', 'maintenance', 'muscle_gain', 'recomp']

export default function Settings() {
  const { user } = useAuth()
  const [profile, setProfile] = useState({})
  const [log, setLog] = useState(null)
  const [logForm, setLogForm] = useState({ water_intake_ml: 0, mood: '', notes: '', calorie_target: '' })
  const [err, setErr] = useState('')
  const [ok, setOk] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (user) setProfile(user)
    const q = new URLSearchParams({ date: todayISO() }).toString()
    api.get(`/daily-log/?${q}`)
      .then((r) => {
        setLog(r.data)
        setLogForm({
          water_intake_ml: r.data.water_intake_ml || 0,
          mood: r.data.mood || '',
          notes: r.data.notes || '',
          calorie_target: r.data.calorie_target ?? '',
        })
      })
      .catch(() => {})
  }, [user])

  const saveProfile = async (e) => {
    e.preventDefault()
    setErr(''); setOk(''); setBusy(true)
    try {
      const { data } = await api.patch('/auth/me', {
        full_name: profile.full_name,
        age: profile.age ? Number(profile.age) : null,
        height_cm: profile.height_cm ? Number(profile.height_cm) : null,
        weight_kg: profile.weight_kg ? Number(profile.weight_kg) : null,
        gender: profile.gender,
        goal: profile.goal,
        activity_level: profile.activity_level,
      })
      setOk('Profile saved ✅')
      setBusy(false)
      return data
    } catch (e2) {
      setOk('')
      setBusy(false)
      return null
    }
  }

  const saveLog = async (e) => {
    e.preventDefault()
    setErr(''); setOk(''); setBusy(true)
    try {
      const { data } = await api.patch('/daily-log/', {
        calorie_target: logForm.calorie_target ? Number(logForm.calorie_target) : null,
        water_intake_ml: Number(logForm.water_intake_ml),
        mood: logForm.mood || null,
        notes: logForm.notes || null,
      })
      setLog(data)
      setOk('Today&apos;s log updated ✅')
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'Could not update daily log.')
    } finally { setBusy(false) }
  }

  const set = (k, v) => setLogForm((f) => ({ ...f, [k]: v }))

  return (
    <div style={{ maxWidth: 760, margin: '0 auto' }}>
      <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 4 }}>Settings ⚙️</h1>
      <p className="muted" style={{ marginBottom: 20 }}>Your profile feeds the AI — the more accurate it is, the better your coach.</p>
      <ErrBanner message={err} />
      {ok && <div className="card" style={{ padding: 14, background: 'var(--primary-soft)', borderColor: 'var(--primary)', marginBottom: 16 }}>{ok}</div>}

      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 14 }}>👤 Fitness Profile</h3>
        <p className="muted" style={{ marginBottom: 14 }}>
          Used to calculate your BMR/TDEE and macro targets. Profile editing endpoint isn&apos;t exposed yet in the backend — suggest the AI targets from here instead.
        </p>
        <form onSubmit={saveProfile}>
          <div className="grid grid--2" style={{ gap: 14 }}>
            <div className="field"><label>Full name</label><input className="input" value={profile.full_name || ''} onChange={(e) => setProfile({ ...profile, full_name: e.target.value })} /></div>
            <div className="field"><label>Email</label><input className="input" disabled value={profile.email || ''} /></div>
            <div className="field"><label>Age</label><input className="input" type="number" value={profile.age ?? ''} onChange={(e) => setProfile({ ...profile, age: e.target.value })} /></div>
            <div className="field"><label>Gender</label>
              <select className="select" value={profile.gender || 'male'} onChange={(e) => setProfile({ ...profile, gender: e.target.value })}>
                <option value="male">Male</option><option value="female">Female</option><option value="other">Other</option>
              </select>
            </div>
            <div className="field"><label>Height (cm)</label><input className="input" type="number" value={profile.height_cm ?? ''} onChange={(e) => setProfile({ ...profile, height_cm: e.target.value })} /></div>
            <div className="field"><label>Weight (kg)</label><input className="input" type="number" value={profile.weight_kg ?? ''} onChange={(e) => setProfile({ ...profile, weight_kg: e.target.value })} /></div>
            <div className="field"><label>Activity level</label>
              <select className="select" value={profile.activity_level || 'light'} onChange={(e) => setProfile({ ...profile, activity_level: e.target.value })}>
                {levels.map((l) => <option key={l} value={l}>{l.replace('_', ' ')}</option>)}
              </select>
            </div>
            <div className="field"><label>Goal</label>
              <select className="select" value={profile.goal || 'weight_loss'} onChange={(e) => setProfile({ ...profile, goal: e.target.value })}>
                {goals.map((g) => <option key={g} value={g}>{g.replace('_', ' ')}</option>)}
              </select>
            </div>
          </div>
          <button className="btn" disabled={busy}>{busy ? <Spinner /> : 'Save profile'}</button>
        </form>
      </div>

      <div className="card">
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 4 }}>📅 Today&apos;s Log</h3>
        <p className="muted" style={{ marginBottom: 14 }}>Set your daily calorie target, water intake, mood &amp; notes.</p>
        <form onSubmit={saveLog}>
          <div className="grid grid--2" style={{ gap: 14 }}>
            <div className="field"><label>Calorie target</label><input className="input" type="number" placeholder="2000" value={logForm.calorie_target} onChange={(e) => set('calorie_target', e.target.value)} /></div>
            <div className="field"><label>Water intake (ml)</label><input className="input" type="number" value={logForm.water_intake_ml} onChange={(e) => set('water_intake_ml', e.target.value)} /></div>
            <div className="field"><label>Mood</label>
              <select className="select" value={logForm.mood} onChange={(e) => set('mood', e.target.value)}>
                <option value="">— Select —</option>
                <option value="good">😊 Good</option><option value="tired">😫 Tired</option><option value="low">😔 Low</option>
                <option value="energetic">⚡ Energetic</option><option value="neutral">😐 Neutral</option>
              </select>
            </div>
            <div className="field"><label>Notes</label><input className="input" placeholder="Feeling great today!" value={logForm.notes} onChange={(e) => set('notes', e.target.value)} /></div>
          </div>
          <button className="btn" disabled={busy}>{busy ? <Spinner /> : 'Update daily log'}</button>
        </form>
      </div>
    </div>
  )
}