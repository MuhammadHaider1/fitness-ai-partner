import { useEffect, useState } from 'react'
import api from '../services/api'
import { ErrBanner, Spinner, Empty, PageTitle } from '../components/ui'
import { fmtNumber, DAY_NAMES, isoWeekday, WEEK_START_SAT } from '../services/format'

const suggestions = [
  { label: '🍞', text: '2 roti aur daal khai' },
  { label: '🍗', text: 'chicken karahi with 1 naan' },
  { label: '🏃', text: '30 min running' },
  { label: '🏋️', text: 'bench press 3 sets 10 reps 60kg' },
  { label: '🥛', text: '1 glass milk and 2 eggs' },
]

const mealTypes = ['breakfast', 'lunch', 'dinner', 'snack']

export default function AILogging() {
  const [tab, setTab] = useState('ai') // ai | manual | routine
  const [text, setText] = useState('')
  const [draft, setDraft] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [ok, setOk] = useState('')
  const [done, setDone] = useState(false)
  const [recent, setRecent] = useState([])

  // manual meal form
  const [mealForm, setMealForm] = useState({ food_name: '', meal_type: 'breakfast', calories: '', protein_g: '', carbs_g: '', fats_g: '' })
  // manual workout form
  const [woForm, setWoForm] = useState({ name: '', workout_type: 'strength', sets: '', reps: '', weight_kg: '', duration_minutes: '', distance_km: '', intensity: 'moderate', calories_burned: '' })
  // routine logging
  const [routine, setRoutine] = useState({})
  const [rtDay, setRtDay] = useState(isoWeekday())
  const [checked, setChecked] = useState([])

  const loadRecent = () => {
    Promise.all([
      api.get('/meals/').then((r) => r.data.slice(-3).reverse()),
      api.get('/workouts/').then((r) => r.data.slice(-3).reverse()),
    ])
      .then(([meals, workouts]) => {
        const merged = [
          ...meals.map((m) => ({ id: m.id, kind: 'meal', text: m.food_name, sub: `${fmtNumber(m.calories)} kcal`, raw: m.raw_text })),
          ...workouts.map((w) => ({ id: w.id, kind: 'workout', text: w.name, sub: `${fmtNumber(w.calories_burned)} kcal burned`, raw: w.raw_text })),
        ].sort((a, b) => b.id.localeCompare(a.id)).slice(0, 4)
        setRecent(merged)
      })
      .catch(() => {})
  }

  useEffect(() => { loadRecent() }, [done])

  useEffect(() => {
    if (tab === 'routine') {
      api.get('/workout-routine/')
        .then(({ data }) => {
          const map = {}
          data.forEach((d) => { map[d.day_of_week] = d.exercises })
          setRoutine(map)
        })
        .catch(() => {})
    }
  }, [tab])

  const rtExercises = routine[rtDay] || []

  const toggleCheck = (i) => {
    setChecked((c) => (c.includes(i) ? c.filter((x) => x !== i) : [...c, i]))
  }

  const logRoutine = async () => {
    setErr(''); setOk(''); setBusy(true)
    const selected = checked.map((i) => rtExercises[i]).filter(Boolean)
    try {
      for (const ex of selected) {
        await api.post('/workouts/', {
          workout_type: ex.workout_type,
          name: ex.name,
          duration_minutes: ex.duration_minutes || null,
          distance_km: ex.distance_km || null,
          sets: ex.sets || null,
          reps: ex.reps || null,
          weight_kg: ex.weight_kg || null,
          intensity: ex.intensity || null,
          calories_burned: ex.calories_burned || 0,
        })
      }
      setOk(`✅ ${selected.length} workout${selected.length === 1 ? '' : 's'} log ho gaye!`)
      setChecked([]); setDone(true); loadRecent()
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'Log nahi ho saka — try karo.')
    } finally { setBusy(false) }
  }

  const saveManualMeal = async (e) => {
    e?.preventDefault()
    setErr(''); setOk(''); setBusy(true)
    try {
      await api.post('/meals/', {
        food_name: mealForm.food_name,
        meal_type: mealForm.meal_type,
        calories: Number(mealForm.calories) || 0,
        protein_g: Number(mealForm.protein_g) || null,
        carbs_g: Number(mealForm.carbs_g) || null,
        fats_g: Number(mealForm.fats_g) || null,
      })
      setOk('✅ Meal log ho gayi!')
      setMealForm({ food_name: '', meal_type: 'breakfast', calories: '', protein_g: '', carbs_g: '', fats_g: '' })
      setDone(true); loadRecent()
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'Meal save nahi hui.')
    } finally { setBusy(false) }
  }

  const saveManualWorkout = async (e) => {
    e?.preventDefault()
    setErr(''); setOk(''); setBusy(true)
    try {
      await api.post('/workouts/', {
        workout_type: woForm.workout_type,
        name: woForm.name,
        duration_minutes: Number(woForm.duration_minutes) || null,
        distance_km: Number(woForm.distance_km) || null,
        sets: Number(woForm.sets) || null,
        reps: Number(woForm.reps) || null,
        weight_kg: Number(woForm.weight_kg) || null,
        intensity: woForm.intensity || null,
        calories_burned: Number(woForm.calories_burned) || 0,
      })
      setOk('✅ Workout log ho gaya!')
      setWoForm({ name: '', workout_type: 'strength', sets: '', reps: '', weight_kg: '', duration_minutes: '', distance_km: '', intensity: 'moderate', calories_burned: '' })
      setDone(true); loadRecent()
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'Workout save nahi hua.')
    } finally { setBusy(false) }
  }

  const d = draft ? (draft.intent === 'workout' ? draft.workout_draft : draft.meal_draft) : null

  const parse = async (e) => {
    e?.preventDefault()
    if (!text.trim() || busy) return
    setErr(''); setBusy(true); setDone(false); setDraft(null)
    try {
      const { data } = await api.post('/agent/parse', { raw_text: text.trim() })
      setDraft(data)
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'AI could not parse that — please try again.')
    } finally { setBusy(false) }
  }

  const adjust = async () => {
    setErr(''); setBusy(true)
    try {
      const isWorkout = draft.intent === 'workout'
      const { data } = await api.post(isWorkout ? '/agent/workouts/adjust' : '/agent/meals/adjust', {
        adjustment_text: text.trim(),
        previous_draft: isWorkout ? draft.workout_draft : draft.meal_draft,
      })
      setDraft({ ...draft, [isWorkout ? 'workout_draft' : 'meal_draft']: data })
      setText('')
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'Could not adjust — try again.')
    } finally { setBusy(false) }
  }

  const confirm = async () => {
    setErr(''); setBusy(true)
    try {
      const isWorkout = draft.intent === 'workout'
      const body = isWorkout
        ? {
            workout_type: draft.workout_draft.workout_type,
            name: draft.workout_draft.name,
            duration_minutes: draft.workout_draft.duration_minutes,
            distance_km: draft.workout_draft.distance_km,
            sets: draft.workout_draft.sets,
            reps: draft.workout_draft.reps,
            weight_kg: draft.workout_draft.weight_kg,
            intensity: draft.workout_draft.intensity,
            calories_burned: draft.workout_draft.calories_burned,
          }
        : {
            food_name: draft.meal_draft.food_name,
            meal_type: draft.meal_draft.meal_type,
            calories: draft.meal_draft.calories,
            protein_g: draft.meal_draft.protein_g,
            carbs_g: draft.meal_draft.carbs_g,
            fats_g: draft.meal_draft.fats_g,
          }
      await api.post(isWorkout ? '/agent/workouts/confirm' : '/agent/meals/confirm', body)
      setDone(true); setDraft(null); setText('')
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'Could not save — try again.')
    } finally { setBusy(false) }
  }

  const discard = () => { setDraft(null); setText(''); setDone(false) }
  const confused = d && !d.is_confident
  const today = isoWeekday()

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <PageTitle center emoji="📝" sub="AI se log karo, manual daalo, ya routine se aaj ka workout pick karo.">
        Log Entry
      </PageTitle>

      <div className="tabs" style={{ justifyContent: 'center' }}>
        {[
          ['ai', '✨ AI Log'],
          ['manual', '✍️ Manual'],
          ['routine', '🗓️ Routine'],
        ].map(([k, label]) => (
          <button key={k} className={`tab${tab === k ? ' tab--active' : ''}`} onClick={() => { setTab(k); setErr(''); setOk('') }}>
            {label}
          </button>
        ))}
      </div>

      <ErrBanner message={err} />
      {ok && <div className="ok-banner">{ok}</div>}

      {tab === 'ai' && (
        <>
          <form className="ai-logger" onSubmit={parse}>
            <div className="ai-input">
              <input
                className="input"
                placeholder="e.g. 2 roti aur daal khai, ya 45 min cycling"
                value={text}
                onChange={(e) => setText(e.target.value)}
                disabled={busy}
              />
              <button className="btn" type="submit" disabled={busy || !text.trim()}>
                {busy ? <Spinner /> : '✨ Parse'}
              </button>
            </div>

            {!draft && !done && (
              <div className="label--inline" style={{ flexWrap: 'wrap', gap: 6, marginTop: 14 }}>
                <span className="muted" style={{ marginRight: 4 }}>Try:</span>
                {suggestions.map((s) => (
                  <button key={s.text} type="button" className="btn btn--ghost btn--sm" onClick={() => setText(s.text)}>
                    {s.label} {s.text}
                  </button>
                ))}
              </div>
            )}
          </form>

          {done && (
            <div className="card" style={{ marginTop: 18, background: 'var(--primary-soft)', borderColor: 'var(--primary)' }}>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <span style={{ fontSize: 26 }}>✅</span>
                <div>
                  <b>Saved!</b>
                  <div className="muted">Your entry was logged. Want to log another?</div>
                </div>
                <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                  <button className="btn btn--sm" onClick={() => setDone(false)}>Log another</button>
                  <a href="/" className="btn btn--ghost btn--sm">Dashboard</a>
                </div>
              </div>
            </div>
          )}

          {draft && d && (
            <div className={`draft-card${confused ? ' draft-card--confused' : ''}`}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <span className="pill pill--green">
                  {draft.intent === 'workout' ? '🏋️ Workout draft' : '🍽️ Meal draft'}
                </span>
                {confused ? <span className="pill pill--amber">⚠️ Needs clarification</span> : <span className="pill pill--cyan">Confident estimate</span>}
              </div>

              {confused && (
                <div className="confused">
                  <span>🤔</span>
                  <div>
                    <b>I need a bit more info</b>
                    <p style={{ marginTop: 2 }}>{d.clarification_question}</p>
                  </div>
                </div>
              )}

              {draft.intent === 'workout' ? (
                <div>
                  <div className="grid grid--2">
                    <div className="field" style={{ marginBottom: 0 }}><label>Exercise</label><div className="input" style={{ background: 'var(--bg-soft)' }}>{d.name}</div></div>
                    <div className="field" style={{ marginBottom: 0 }}><label>Type</label><div className="input" style={{ background: 'var(--bg-soft)' }}>{d.workout_type}</div></div>
                    {d.duration_minutes != null && <div className="field" style={{ marginBottom: 0 }}><label>Duration</label><div className="input" style={{ background: 'var(--bg-soft)' }}>{d.duration_minutes} min</div></div>}
                    {d.sets != null && <div className="field" style={{ marginBottom: 0 }}><label>Volume</label><div className="input" style={{ background: 'var(--bg-soft)' }}>{d.sets}×{d.reps}{d.weight_kg ? ` @ ${d.weight_kg}kg` : ''}</div></div>}
                    {d.intensity && <div className="field" style={{ marginBottom: 0 }}><label>Intensity</label><div className="input" style={{ background: 'var(--bg-soft)' }}>{d.intensity}</div></div>}
                    <div className="field" style={{ marginBottom: 0 }}><label>Calories burned</label><div className="input" style={{ background: 'var(--bg-soft)', fontWeight: 700, color: '#f59e0b' }}>{fmtNumber(d.calories_burned)} kcal</div></div>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="field"><label>Food</label><div className="input" style={{ background: 'var(--bg-soft)' }}>{d.food_name}</div></div>
                  <div className="grid grid--4" style={{ gap: 10 }}>
                    <div className="field" style={{ marginBottom: 0 }}><label>Calories</label><div className="input" style={{ background: 'var(--bg-soft)', fontWeight: 700 }}>{fmtNumber(d.calories)} kcal</div></div>
                    <div className="field" style={{ marginBottom: 0 }}><label>Protein</label><div className="input" style={{ background: 'var(--bg-soft)' }}>{fmtNumber(d.protein_g)}g</div></div>
                    <div className="field" style={{ marginBottom: 0 }}><label>Carbs</label><div className="input" style={{ background: 'var(--bg-soft)' }}>{fmtNumber(d.carbs_g)}g</div></div>
                    <div className="field" style={{ marginBottom: 0 }}><label>Fats</label><div className="input" style={{ background: 'var(--bg-soft)' }}>{fmtNumber(d.fats_g)}g</div></div>
                  </div>
                </div>
              )}

              {d.reasoning && (
                <div className="muted" style={{ marginTop: 12, fontStyle: 'italic' }}>
                  💡 {d.reasoning}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16 }}>
                <button className="btn btn--ghost" onClick={discard} disabled={busy}>Discard</button>
                <button className="btn btn--ghost" onClick={adjust} disabled={busy || !text.trim()}>
                  🔧 Adjust{!text.trim() ? ' (type feedback)' : ''}
                </button>
                <button className="btn" onClick={confirm} disabled={busy}>
                  {busy ? <Spinner /> : '✅ Confirm & Save'}
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {tab === 'manual' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="card">
            <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 4 }}>🍽️ Manual meal</h3>
            <p className="muted" style={{ marginBottom: 14 }}>Bina AI ke seedha calories/macros daal ke log karo.</p>
            <form onSubmit={saveManualMeal}>
              <div className="grid grid--2" style={{ gap: 12 }}>
                <div className="field" style={{ marginBottom: 10 }}><label>Food name</label><input className="input" required placeholder="Daal + 2 roti" value={mealForm.food_name} onChange={(e) => setMealForm({ ...mealForm, food_name: e.target.value })} /></div>
                <div className="field" style={{ marginBottom: 10 }}><label>Meal type</label>
                  <select className="select" value={mealForm.meal_type} onChange={(e) => setMealForm({ ...mealForm, meal_type: e.target.value })}>
                    {mealTypes.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="field" style={{ marginBottom: 10 }}><label>Calories</label><input className="input" type="number" required placeholder="500" value={mealForm.calories} onChange={(e) => setMealForm({ ...mealForm, calories: e.target.value })} /></div>
                <div className="field" style={{ marginBottom: 10 }}><label>Protein (g)</label><input className="input" type="number" placeholder="30" value={mealForm.protein_g} onChange={(e) => setMealForm({ ...mealForm, protein_g: e.target.value })} /></div>
                <div className="field" style={{ marginBottom: 10 }}><label>Carbs (g)</label><input className="input" type="number" placeholder="60" value={mealForm.carbs_g} onChange={(e) => setMealForm({ ...mealForm, carbs_g: e.target.value })} /></div>
                <div className="field" style={{ marginBottom: 10 }}><label>Fats (g)</label><input className="input" type="number" placeholder="15" value={mealForm.fats_g} onChange={(e) => setMealForm({ ...mealForm, fats_g: e.target.value })} /></div>
              </div>
              <button className="btn" disabled={busy}>{busy ? <Spinner /> : '💾 Save meal'}</button>
            </form>
          </div>

          <div className="card">
            <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 4 }}>🏋️ Manual workout</h3>
            <p className="muted" style={{ marginBottom: 14 }}>Exercise ke naam aur details daal ke log karo.</p>
            <form onSubmit={saveManualWorkout}>
              <div className="grid grid--2" style={{ gap: 12 }}>
                <div className="field" style={{ marginBottom: 10 }}><label>Workout name</label><input className="input" required placeholder="Deadlift / Running" value={woForm.name} onChange={(e) => setWoForm({ ...woForm, name: e.target.value })} /></div>
                <div className="field" style={{ marginBottom: 10 }}><label>Type</label>
                  <select className="select" value={woForm.workout_type} onChange={(e) => setWoForm({ ...woForm, workout_type: e.target.value })}>
                    <option value="strength">Strength</option>
                    <option value="cardio">Cardio</option>
                  </select>
                </div>
                {woForm.workout_type === 'strength' ? (
                  <>
                    <div className="field" style={{ marginBottom: 10 }}><label>Sets</label><input className="input" type="number" value={woForm.sets} onChange={(e) => setWoForm({ ...woForm, sets: e.target.value })} /></div>
                    <div className="field" style={{ marginBottom: 10 }}><label>Reps</label><input className="input" type="number" value={woForm.reps} onChange={(e) => setWoForm({ ...woForm, reps: e.target.value })} /></div>
                    <div className="field" style={{ marginBottom: 10 }}><label>Weight (kg)</label><input className="input" type="number" value={woForm.weight_kg} onChange={(e) => setWoForm({ ...woForm, weight_kg: e.target.value })} /></div>
                  </>
                ) : (
                  <>
                    <div className="field" style={{ marginBottom: 10 }}><label>Duration (min)</label><input className="input" type="number" value={woForm.duration_minutes} onChange={(e) => setWoForm({ ...woForm, duration_minutes: e.target.value })} /></div>
                    <div className="field" style={{ marginBottom: 10 }}><label>Distance (km)</label><input className="input" type="number" value={woForm.distance_km} onChange={(e) => setWoForm({ ...woForm, distance_km: e.target.value })} /></div>
                  </>
                )}
                <div className="field" style={{ marginBottom: 10 }}><label>Intensity</label>
                  <select className="select" value={woForm.intensity} onChange={(e) => setWoForm({ ...woForm, intensity: e.target.value })}>
                    <option value="low">Low</option>
                    <option value="moderate">Moderate</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <div className="field" style={{ marginBottom: 10 }}><label>Calories burned</label><input className="input" type="number" placeholder="200" value={woForm.calories_burned} onChange={(e) => setWoForm({ ...woForm, calories_burned: e.target.value })} /></div>
              </div>
              <button className="btn" disabled={busy}>{busy ? <Spinner /> : '💾 Save workout'}</button>
            </form>
          </div>
        </div>
      )}

      {tab === 'routine' && (
        <>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="day-picker">
              {WEEK_START_SAT.map((i) => (
                <button
                  key={DAY_NAMES[i]}
                  type="button"
                  className={`day-pill${rtDay === i ? ' day-pill--active' : ''}${i === today ? ' day-pill--today' : ''}`}
                  onClick={() => { setRtDay(i); setChecked([]) }}
                >
                  {DAY_NAMES[i].slice(0, 3)}
                  {i === today && <span style={{ display: 'block', fontSize: 10, opacity: 0.8 }}>today</span>}
                </button>
              ))}
            </div>
            <p className="muted" style={{ marginTop: 8, textAlign: 'center' }}>
              {rtDay === today ? 'Ye aaj ka routine hai — jo kiya wo check kar ke log karo 💪' : `${DAY_NAMES[rtDay]} ka routine — jo kiya wo check karo`}
            </p>
          </div>

          {rtExercises.length === 0 ? (
            <Empty
              emoji="🗓️"
              title={`${DAY_NAMES[rtDay]} par routine set nahi hai`}
              subtitle={<span>Pehle <a href="/routine" style={{ color: 'var(--primary)', fontWeight: 700 }}>Routine</a> mein apna plan banao.</span>}
            />
          ) : (
            <div className="card">
              {rtExercises.map((ex, i) => (
                <label className="list-item" key={i} style={{ cursor: 'pointer' }}>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                    <input type="checkbox" checked={checked.includes(i)} onChange={() => toggleCheck(i)} style={{ width: 18, height: 18, accentColor: 'var(--primary)' }} />
                    <div>
                      <b>{ex.name}</b>
                      <div className="muted">
                        {ex.workout_type === 'cardio'
                          ? `${ex.duration_minutes || '—'} min${ex.distance_km ? ` / ${ex.distance_km} km` : ''}`
                          : `${ex.sets || '—'}×${ex.reps || '—'}${ex.weight_kg ? ` @ ${ex.weight_kg}kg` : ''}`}
                        {ex.intensity ? ` · ${ex.intensity}` : ''}
                      </div>
                    </div>
                  </div>
                  <div className="muted">{fmtNumber(ex.calories_burned)} kcal</div>
                </label>
              ))}
              <button className="btn btn--block" style={{ marginTop: 16 }} onClick={logRoutine} disabled={busy || checked.length === 0}>
                {busy ? <Spinner /> : `🔥 Log ${checked.length} workout${checked.length === 1 ? '' : 's'}`}
              </button>
            </div>
          )}
        </>
      )}

      {recent.length > 0 && (
        <div className="card" style={{ marginTop: 24 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 10 }}>Recent entries</h3>
          {recent.map((r) => (
            <div className="list-item" key={r.id}>
              <div>
                <b>{r.text}</b>
                {r.raw ? <div className="muted">"{r.raw}"</div> : <div className="muted">Structured entry</div>}
              </div>
              <div className="muted">{r.sub}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}