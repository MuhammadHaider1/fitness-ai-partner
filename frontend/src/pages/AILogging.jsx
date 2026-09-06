import { useEffect, useState } from 'react'
import api from '../services/api'
import { ErrBanner, Spinner } from '../components/ui'
import { fmtNumber } from '../services/format'

const suggestions = [
  { label: '🍞', text: '2 roti aur daal khai' },
  { label: '🍗', text: 'chicken karahi with 1 naan' },
  { label: '🏃', text: '30 min running' },
  { label: '🏋️', text: 'bench press 3 sets 10 reps 60kg' },
  { label: '🥛', text: '1 glass milk and 2 eggs' },
]

export default function AILogging() {
  const [text, setText] = useState('')
  const [draft, setDraft] = useState(null) // {intent, meal_draft, workout_draft}
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [done, setDone] = useState(false)
  const [recent, setRecent] = useState([])

  useEffect(() => {
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
  }, [done])

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
    } finally {
      setBusy(false)
    }
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
    } finally {
      setBusy(false)
    }
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
    } finally {
      setBusy(false)
    }
  }

  const discard = () => { setDraft(null); setText(''); setDone(false) }

  const confused = d && !d.is_confident

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 22 }}>
        <h1 style={{ fontSize: 26, fontWeight: 800 }}>Log with AI 🗣️</h1>
        <p className="muted">Describe what you ate or did in plain language — AI turns it into structured data.</p>
      </div>

      <ErrBanner message={err} />

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