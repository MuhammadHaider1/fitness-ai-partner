import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { RingProgress, Stat, Pill, Empty, LoadingFill, ErrBanner, PageTitle } from '../components/ui'
import { fmtNumber, todayISO, weekdayLabel } from '../services/format'

function MacroBar({ label, grams, kcalPerG, targetKcal, color }) {
  const cal = (grams || 0) * kcalPerG
  const pct = targetKcal > 0 ? Math.min(Math.round((cal / targetKcal) * 100), 100) : 0
  return (
    <div>
      <div className="macro-row">
        <span style={{ fontSize: 12, fontWeight: 700, color }}>{label}</span>
        <span className="muted">
          {fmtNumber(grams || 0)}g · {pct}% of daily
        </span>
      </div>
      <div className="bar">
        <div className="bar__fill" style={{ width: `${pct}%`, background: color, boxShadow: `0 0 10px ${color}66` }} />
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [log, setLog] = useState(null)
  const [meals, setMeals] = useState([])
  const [workouts, setWorkouts] = useState([])
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const today = todayISO()
    const q = new URLSearchParams({ date: today }).toString()
    Promise.all([
      api.get(`/daily-log/?${q}`).then((r) => setLog(r.data)),
      api.get(`/meals/?log_date=${today}`).then((r) => setMeals(r.data.slice(-5).reverse())),
      api.get(`/workouts/?log_date=${today}`).then((r) => setWorkouts(r.data.slice(-5).reverse())),
    ])
      .catch((e) => setErr(e.response?.data?.detail || 'Could not load dashboard.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingFill />

  const remaining = log ? log.calorie_target - log.total_calories : 0
  const target = log?.calorie_target || 0

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <PageTitle emoji="👋" sub={`${weekdayLabel(todayISO())} · Let's crush today's goals 💪`}>
          Assalam-o-Alaikum, {user?.full_name?.split(' ')[0] || 'Athlete'}
        </PageTitle>
        <Link to="/log" className="btn btn--accent">🗣️ Quick AI Log</Link>
      </div>

      <ErrBanner message={err} />

      <div className="grid grid--4" style={{ marginBottom: 20 }}>
        <Stat label="Calories Eaten" value={fmtNumber(log?.total_calories)} icon="🍽️" color="#a3e635" />
        <Stat label="Calories Burned" value={fmtNumber(log?.total_calories_burned)} icon="🔥" color="#f59e0b" />
        <Stat label="Protein" value={`${fmtNumber(log?.total_protein_g)}g`} icon="🥩" color="#8b5cf6" />
        <Stat label="Water Intake" value={`${fmtNumber(log?.water_intake_ml)} ml`} icon="💧" color="#2dd4bf" />
      </div>

      <div className="grid grid--2">
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h3 style={{ fontSize: 17, fontWeight: 700 }}>Today&apos;s Progress</h3>
            <Pill tone={!target ? 'amber' : remaining >= 0 ? 'green' : 'red'}>
              {!target ? 'No target' : remaining >= 0 ? 'On track 🎯' : 'Over target'}
            </Pill>
          </div>
          <div className="ring-wrap">
            <RingProgress value={log?.total_calories || 0} max={target || 2000} label="calories" />
            <div style={{ flex: 1, minWidth: 220 }}>
              <div className="panel">
                <div className="stat__label">Calories remaining</div>
                <div className="stat__value" style={{ color: remaining < 0 ? 'var(--danger)' : '#a3e635' }}>{fmtNumber(remaining)}</div>
                <div className="muted">Target: {fmtNumber(target)} kcal</div>
                <div style={{ height: 1, background: 'rgba(255,255,255,0.07)', margin: '12px 0' }} />
                <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
                  <MacroBar label="Protein" grams={log?.total_protein_g} kcalPerG={4} targetKcal={target} color="#a3e635" />
                  <MacroBar label="Carbs" grams={log?.total_carbs_g} kcalPerG={4} targetKcal={target} color="#2dd4bf" />
                  <MacroBar label="Fats" grams={log?.total_fats_g} kcalPerG={9} targetKcal={target} color="#e6edf7" />
                </div>
              </div>
              {!target && (
                <div className="panel" style={{ marginTop: 12, background: 'var(--warn-soft)', borderColor: 'rgba(245,158,11,0.3)' }}>
                  <span style={{ fontSize: 13 }}>⚠️ No calorie target set yet. <Link to="/settings" style={{ fontWeight: 700, color: '#a3e635' }}>Set a target</Link> for accurate tracking.</span>
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