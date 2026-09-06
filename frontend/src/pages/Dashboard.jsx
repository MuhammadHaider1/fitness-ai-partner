import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { RingProgress, Stat, Pill, Empty, LoadingFill, ErrBanner } from '../components/ui'
import { fmtNumber, todayISO, weekdayLabel } from '../services/format'

export default function Dashboard() {
  const { user } = useAuth()
  const [log, setLog] = useState(null)
  const [meals, setMeals] = useState([])
  const [workouts, setWorkouts] = useState([])
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const q = new URLSearchParams({ date: todayISO() }).toString()
    Promise.all([
      api.get(`/daily-log/?${q}`).then((r) => setLog(r.data)),
      api.get('/meals/').then((r) => setMeals(r.data.slice(-5).reverse())),
      api.get('/workouts/').then((r) => setWorkouts(r.data.slice(-5).reverse())),
    ])
      .catch((e) => setErr(e.response?.data?.detail || 'Could not load dashboard.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingFill />

  const remaining = log ? log.calorie_target - log.total_calories : 0
  const pctProtein = log && log.calorie_target ? (log.total_protein_g * 4) / log.calorie_target || 0 : 0

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 800 }}>Assalam-o-Alaikum, {user?.full_name?.split(' ')[0] || 'Athlete'} 👋</h1>
          <p className="muted">{weekdayLabel(todayISO())} · Let&apos;s crush today&apos;s goals 💪</p>
        </div>
        <Link to="/log" className="btn btn--accent">🗣️ Quick AI Log</Link>
      </div>

      <ErrBanner message={err} />

      <div className="grid grid--4" style={{ marginBottom: 20 }}>
        <Stat label="Calories Eaten" value={fmtNumber(log?.total_calories)} icon="🍽️" color="#10b981" />
        <Stat label="Calories Burned" value={fmtNumber(log?.total_calories_burned)} icon="🔥" color="#f59e0b" />
        <Stat label="Protein" value={`${fmtNumber(log?.total_protein_g)}g`} icon="🥩" color="#8b5cf6" />
        <Stat label="Water Intake" value={`${fmtNumber(log?.water_intake_ml)} ml`} icon="💧" color="#06b6d4" />
      </div>

      <div className="grid grid--2">
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <h3 style={{ fontSize: 17, fontWeight: 700 }}>Today&apos;s Progress</h3>
          <div className="ring-wrap">
            <RingProgress value={log?.total_calories || 0} max={log?.calorie_target || 2000} label="calories" />
            <div>
              <div className="stat" style={{ boxShadow: 'none', border: 'none', padding: 0 }}>
                <div className="stat__label">Calories remaining</div>
                <div className="stat__value" style={{ color: remaining < 0 ? 'var(--danger)' : 'var(--primary-2)', fontSize: 22 }}>{fmtNumber(remaining)}</div>
                <div className="muted">Target: {fmtNumber(log?.calorie_target)} kcal</div>
                <div className="muted">Macros: {fmtNumber(log?.total_carbs_g)}g carbs · {fmtNumber(log?.total_fats_g)}g fats</div>
                {log && pctProtein > 0 && (
                  <div className="muted">Protein hits ~{Math.round(pctProtein * 100)}% of daily goal</div>
                )}
              </div>
              {!log?.calorie_target && (
                <div className="card" style={{ padding: 12, marginTop: 14, background: 'var(--warn-soft)', border: 'none' }}>
                  <span style={{ fontSize: 13 }}>⚠️ No calorie target set yet. <Link to="/settings" style={{ fontWeight: 700, color: '#b45309' }}>Set a target</Link> for accurate tracking.</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <h3 style={{ fontSize: 17, fontWeight: 700 }}>Today&apos;s Meals</h3>
            <Link to="/log" className="btn btn--ghost btn--sm">+ Log meal</Link>
          </div>
          {meals.length === 0 ? (
            <Empty emoji="🍽️" title="No meals logged yet" subtitle="Log one in plain language — try '2 roti aur daal'" />
          ) : (
            meals.map((m) => (
              <div className="list-item" key={m.id}>
                <div>
                  <b>{m.food_name}</b>
                  {m.meal_type && <Pill tone="green" children={m.meal_type} />}
                  <div className="muted">{m.raw_text || 'Manual entry'} · {new Date(m.logged_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <b>{fmtNumber(m.calories)} kcal</b>
                  <div className="muted">{fmtNumber(m.protein_g)}g P · {fmtNumber(m.carbs_g)}g C · {fmtNumber(m.fats_g)}g F</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <h3 style={{ fontSize: 17, fontWeight: 700 }}>Recent Workouts</h3>
          <Link to="/log" className="btn btn--ghost btn--sm">+ Log workout</Link>
        </div>
        {workouts.length === 0 ? (
          <Empty emoji="🏋️" title="No workouts yet" subtitle="Try '30 min running' or 'bench press 3x10 at 60kg'" />
        ) : (
          workouts.map((w) => (
            <div className="list-item" key={w.id}>
              <div>
                <b>{w.name}</b> <Pill tone={w.workout_type === 'cardio' ? 'cyan' : 'violet'}>{w.workout_type}</Pill>
                <div className="muted">
                  {w.duration_minutes ? `${w.duration_minutes} min` : `${w.sets}×${w.reps}`}{w.weight_kg ? ` @ ${w.weight_kg}kg` : ''} {w.intensity ? `· ${w.intensity}` : ''}
                </div>
              </div>
              <b style={{ color: '#f59e0b' }}>🔥 {fmtNumber(w.calories_burned)} kcal</b>
            </div>
          ))
        )}
      </div>
    </div>
  )
}