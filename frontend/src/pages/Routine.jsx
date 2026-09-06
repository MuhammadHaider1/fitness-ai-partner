import { useEffect, useState } from 'react'
import api from '../services/api'
import { ErrBanner, Spinner, Empty, LoadingFill, PageTitle } from '../components/ui'
import { DAY_NAMES, isoWeekday, fmtNumber, WEEK_START_SAT } from '../services/format'

const EMPTY_EX = { name: '', workout_type: 'strength', sets: 3, reps: 10, weight_kg: '', duration_minutes: '', intensity: 'moderate', calories_burned: '' }

export default function Routine() {
  const [day, setDay] = useState(isoWeekday())
  const [days, setDays] = useState({})          // { day: [exercises] }
  const [pending, setPending] = useState({})     // unsaved edits per day
  const [saved, setSaved] = useState({})
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [ok, setOk] = useState('')

  useEffect(() => {
    api.get('/workout-routine/')
      .then(({ data }) => {
        const map = {}
        data.forEach((d) => { map[d.day_of_week] = d.exercises })
        setDays(map)
        setPending(map)
        setSaved(map)
      })
      .catch(() => setErr('Routine load nahi hui — thori der baad try karo.'))
      .finally(() => setLoading(false))
  }, [])

  const today = isoWeekday()
  const exercises = pending[day] || []
  const hasChanges = JSON.stringify(pending[day] || []) !== JSON.stringify(saved[day] || [])
  const daySaved = (saved[day] || []).length > 0

  const updateEx = (i, key, value) => {
    setOk('')
    setPending((p) => {
      const list = [...(p[day] || [])]
      list[i] = { ...list[i], [key]: value }
      return { ...p, [day]: list }
    })
  }

  const addEx = () => {
    setOk('')
    setPending((p) => ({ ...p, [day]: [...(p[day] || []), { ...EMPTY_EX }] }))
  }

  const removeEx = (i) => {
    setOk('')
    setPending((p) => ({ ...p, [day]: (p[day] || []).filter((_, idx) => idx !== i) }))
  }

  const save = async () => {
    setErr(''); setOk(''); setBusy(true)
    const clean = (exercises || [])
      .filter((e) => e.name.trim())
      .map((e) => ({
        name: e.name.trim(),
        workout_type: e.workout_type,
        sets: e.sets ? Number(e.sets) : null,
        reps: e.reps ? Number(e.reps) : null,
        weight_kg: e.weight_kg ? Number(e.weight_kg) : null,
        duration_minutes: e.duration_minutes ? Number(e.duration_minutes) : null,
        intensity: e.intensity || null,
        calories_burned: e.calories_burned ? Number(e.calories_burned) : null,
      }))
    try {
      await api.put(`/workout-routine/${day}`, { day_of_week: day, exercises: clean })
      const next = { ...pending, [day]: clean }
      setPending(next); setDays(next); setSaved(next)
      setOk(`✅ ${DAY_NAMES[day]} ki routine save ho gayi!`)
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'Save nahi ho saki — try karo.')
    } finally { setBusy(false) }
  }

  const clearDay = async () => {
    setErr(''); setBusy(true)
    try {
      await api.delete(`/workout-routine/${day}`)
      const next = { ...pending, [day]: [] }
      setPending(next); setDays(next); setSaved(next)
      setOk('🗑️ Day clear kar diya.')
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'Clear nahi ho saka.')
    } finally { setBusy(false) }
  }

  if (loading) return <LoadingFill />

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      <PageTitle center emoji="🗓️" sub="Har day ke liye apna routine set karo — phir AI Log mein us day ka aaj ka workout pick kar sako.">
        Weekly Workout Routine
      </PageTitle>

      <ErrBanner message={err} />
      {ok && <div className="ok-banner">{ok}</div>}

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="day-picker">
          {WEEK_START_SAT.map((i) => (
            <button
              key={DAY_NAMES[i]}
              type="button"
              className={`day-pill${day === i ? ' day-pill--active' : ''}${i === today ? ' day-pill--today' : ''}`}
              onClick={() => { setDay(i); setErr(''); setOk('') }}
            >
              {DAY_NAMES[i].slice(0, 3)}
              {i === today && <span style={{ display: 'block', fontSize: 10, opacity: 0.8 }}>today</span>}
            </button>
          ))}
        </div>
        <div className="muted" style={{ marginTop: 8, textAlign: 'center' }}>{DAY_NAMES[day]} · {exercises.length} exercise{exercises.length === 1 ? '' : 's'}</div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
          <h3 style={{ fontSize: 17, fontWeight: 700 }}>💪 {DAY_NAMES[day]} workout</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn--ghost btn--sm" onClick={addEx}>+ Add exercise</button>
            {daySaved && (
              <button className="btn btn--ghost btn--sm btn--danger" onClick={clearDay} disabled={busy}>Clear day</button>
            )}
          </div>
        </div>

        {exercises.length === 0 ? (
          <Empty emoji="🏋️" title={`${DAY_NAMES[day]} par abhi koi exercise nahi`} subtitle="Add exercise kar ke apna plan banao" />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {exercises.map((ex, i) => (
              <div key={i} className="draft-card" style={{ marginTop: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <span className="pill pill--violet">{ex.workout_type === 'cardio' ? '🏃 Cardio' : '🏋️ Strength'}</span>
                  <button className="btn btn--ghost btn--sm btn--danger" type="button" onClick={() => removeEx(i)}>✕</button>
                </div>
                <div className="grid grid--2" style={{ gap: 12 }}>
                  <div className="field" style={{ marginBottom: 10 }}><label>Exercise name</label><input className="input" placeholder="Bench Press" value={ex.name} onChange={(e) => updateEx(i, 'name', e.target.value)} /></div>
                  <div className="field" style={{ marginBottom: 10 }}><label>Type</label>
                    <select className="select" value={ex.workout_type} onChange={(e) => updateEx(i, 'workout_type', e.target.value)}>
                      <option value="strength">Strength</option>
                      <option value="cardio">Cardio</option>
                    </select>
                  </div>
                  {ex.workout_type === 'strength' ? (
                    <>
                      <div className="field" style={{ marginBottom: 10 }}><label>Sets</label><input className="input" type="number" min="1" value={ex.sets} onChange={(e) => updateEx(i, 'sets', e.target.value)} /></div>
                      <div className="field" style={{ marginBottom: 10 }}><label>Reps</label><input className="input" type="number" min="1" value={ex.reps} onChange={(e) => updateEx(i, 'reps', e.target.value)} /></div>
                      <div className="field" style={{ marginBottom: 10 }}><label>Weight (kg)</label><input className="input" type="number" value={ex.weight_kg} onChange={(e) => updateEx(i, 'weight_kg', e.target.value)} /></div>
                    </>
                  ) : (
                    <div className="field" style={{ marginBottom: 10 }}><label>Duration (min)</label><input className="input" type="number" value={ex.duration_minutes} onChange={(e) => updateEx(i, 'duration_minutes', e.target.value)} /></div>
                  )}
                  <div className="field" style={{ marginBottom: 10 }}><label>Intensity</label>
                    <select className="select" value={ex.intensity || 'moderate'} onChange={(e) => updateEx(i, 'intensity', e.target.value)}>
                      <option value="low">Low</option>
                      <option value="moderate">Moderate</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                  <div className="field" style={{ marginBottom: 10 }}><label>Est. calories burned</label><input className="input" type="number" placeholder="200" value={ex.calories_burned} onChange={(e) => updateEx(i, 'calories_burned', e.target.value)} /></div>
                </div>
              </div>
            ))}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 18 }}>
          {hasChanges && <span className="muted" style={{ alignSelf: 'center' }}>Unsaved changes</span>}
          <button className="btn" onClick={save} disabled={busy || !hasChanges}>
            {busy ? <Spinner /> : `💾 Save ${DAY_NAMES[day]}`}
          </button>
        </div>
      </div>

      {Object.values(days).some((e) => e.length > 0) && (
        <div className="card" style={{ marginTop: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 10 }}>📋 Week overview</h3>
          {WEEK_START_SAT.map((i) => (
            <div className="list-item" key={DAY_NAMES[i]}>
              <div>
                <b>{DAY_NAMES[i]}</b>
                {i === today && <span className="pill pill--cyan" style={{ marginLeft: 6 }}>today</span>}
              </div>
              <div className="muted">
                {(days[i] || []).length > 0
                  ? `${(days[i] || []).length} exercises · ${fmtNumber((days[i] || []).reduce((s, e) => s + (Number(e.calories_burned) || 0), 0))} kcal`
                  : 'Rest day'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}