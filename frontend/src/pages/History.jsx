import { useEffect, useState } from 'react'
import api from '../services/api'
import { Stat, Pill, Empty, LoadingFill, ErrBanner, Spinner } from '../components/ui'
import { fmtNumber, todayISO, fmtDate } from '../services/format'
import { useAuth } from '../context/AuthContext'

export default function History() {
  const [tab, setTab] = useState('summary')
  const [summary, setSummary] = useState(null)
  const [logs, setLogs] = useState([])
  const [meals, setMeals] = useState([])
  const [workouts, setWorkouts] = useState([])
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const { token } = useAuth()

  const load = () => {
    setErr('')
    const end = todayISO()
    const start = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10)
    const range = `start_date=${start}&end_date=${end}`
    Promise.all([
      api.get(`/daily-log/summary?${range}`).then((r) => setSummary(r.data)),
      api.get(`/daily-log/history?${range}`).then((r) => setLogs(r.data)),
      api.get('/meals/').then((r) => setMeals(r.data)),
      api.get('/workouts/').then((r) => setWorkouts(r.data)),
    ])
      .catch((e) => setErr(e.response?.data?.detail || 'Could not load history.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { if (token) load() }, [token])

  const del = async (kind, id) => {
    if (!window.confirm(`Delete this ${kind}?`)) return
    setBusy(true); setErr('')
    try {
      await api.delete(kind === 'meal' ? `/meals/${id}` : `/workouts/${id}`)
      load()
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'Could not delete.')
    } finally { setBusy(false) }
  }

  if (loading) return <LoadingFill />

  return (
    <div>
      <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 4 }}>History 📊</h1>
      <p className="muted" style={{ marginBottom: 16 }}>Track your progress over time.</p>
      <ErrBanner message={err} />

      <div className="tabs">
        <button className={`tab${tab === 'summary' ? ' tab--active' : ''}`} onClick={() => setTab('summary')}>Summary</button>
        <button className={`tab${tab === 'meals' ? ' tab--active' : ''}`} onClick={() => setTab('meals')}>Meals</button>
        <button className={`tab${tab === 'workouts' ? ' tab--active' : ''}`} onClick={() => setTab('workouts')}>Workouts</button>
      </div>

      {busy && <div style={{ marginBottom: 10 }}><Spinner dark /> <span className="muted">Updating…</span></div>}

      {tab === 'summary' && (
        <div>
          <div className="grid grid--3" style={{ marginBottom: 20 }}>
            <Stat label="Days logged" value={summary?.days_logged ?? 0} icon="📅" color="#10b981" />
            <Stat label="Current streak" value={`${summary?.current_streak ?? 0} days`} icon="🔥" color="#f59e0b" />
            <Stat label="Days on target" value={summary?.days_on_target ?? 0} icon="🎯" color="#8b5cf6" />
          </div>
          <div className="grid grid--4" style={{ marginBottom: 20 }}>
            <Stat label="Avg calories" value={fmtNumber(summary?.average_calories)} icon="🍽️" />
            <Stat label="Avg protein" value={`${fmtNumber(summary?.average_protein_g)}g`} icon="🥩" />
            <Stat label="Avg carbs" value={`${fmtNumber(summary?.average_carbs_g)}g`} icon="🍞" />
            <Stat label="Avg fats" value={`${fmtNumber(summary?.average_fats_g)}g`} icon="🧈" />
          </div>
          {logs.length === 0 ? (
            <Empty emoji="🗓️" title="No daily logs yet" subtitle="Log your first meal or workout to see the timeline" />
          ) : (
            <div className="card">
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 10 }}>Daily timeline</h3>
              {logs.map((l) => {
                const net = l.total_calories - l.total_calories_burned
                const onTarget = l.calorie_target && l.total_calories <= l.calorie_target
                return (
                  <div className="list-item" key={l.id}>
                    <div>
                      <b>{fmtDate(l.log_date)}</b>
                      {l.log_date === todayISO() && <Pill tone="green">today</Pill>}
                      <div className="muted">Net {fmtNumber(net)} kcal · 💧 {fmtNumber(l.water_intake_ml)}ml{onTarget ? ' · 🎯 on target' : ''}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <b>{fmtNumber(l.total_calories)} kcal</b>
                      <div className="muted">{fmtNumber(l.total_protein_g)}g P · {fmtNumber(l.total_carbs_g)}g C · {fmtNumber(l.total_fats_g)}g F</div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {tab === 'meals' && (
        <div className="card">
          {meals.length === 0 ? (
            <Empty emoji="🍽️" title="No meals yet" subtitle="Head to AI Logging to add meals easily" />
          ) : (
            <table className="table">
              <thead><tr><th>Food</th><th>Type</th><th>Date</th><th>Calories</th><th>Source</th><th></th></tr></thead>
              <tbody>
                {meals.map((m) => (
                  <tr key={m.id}>
                    <td>
                      <b>{m.food_name}</b>
                      {m.raw_text && <div className="muted" style={{ fontSize: 12 }}>"{m.raw_text}"</div>}
                    </td>
                    <td>{m.meal_type ? <Pill tone="green">{m.meal_type}</Pill> : <span className="muted">—</span>}</td>
                    <td className="muted">{fmtDate(m.logged_at)}</td>
                    <td><b>{fmtNumber(m.calories)}</b></td>
                    <td><Pill tone={m.source === 'agent' ? 'cyan' : 'mute'}>{m.source}</Pill></td>
                    <td style={{ textAlign: 'right' }}>
                      <button className="btn btn--ghost btn--sm" onClick={() => del('meal', m.id)} disabled={busy}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === 'workouts' && (
        <div className="card">
          {workouts.length === 0 ? (
            <Empty emoji="🏋️" title="No workouts yet" subtitle="Head to AI Logging to add workouts easily" />
          ) : (
            <table className="table">
              <thead><tr><th>Workout</th><th>Type</th><th>Date</th><th>Volume</th><th>Burned</th><th></th></tr></thead>
              <tbody>
                {workouts.map((w) => (
                  <tr key={w.id}>
                    <td>
                      <b>{w.name}</b>
                      {w.raw_text && <div className="muted" style={{ fontSize: 12 }}>"{w.raw_text}"</div>}
                    </td>
                    <td><Pill tone={w.workout_type === 'cardio' ? 'cyan' : 'violet'}>{w.workout_type}</Pill></td>
                    <td className="muted">{fmtDate(w.logged_at)}</td>
                    <td className="muted">{w.duration_minutes ? `${w.duration_minutes} min` : `${w.sets}×${w.reps}${w.weight_kg ? ` @${w.weight_kg}kg` : ''}`}</td>
                    <td><b style={{ color: '#f59e0b' }}>{fmtNumber(w.calories_burned)}</b></td>
                    <td style={{ textAlign: 'right' }}>
                      <button className="btn btn--ghost btn--sm" onClick={() => del('workout', w.id)} disabled={busy}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}