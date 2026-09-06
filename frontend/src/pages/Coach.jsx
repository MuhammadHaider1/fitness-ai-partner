import { useEffect, useRef, useState } from 'react'
import api from '../services/api'
import { ErrBanner, Spinner, Pill, Empty, LoadingFill } from '../components/ui'
import { fmtNumber, weekdayLabel } from '../services/format'
import { useAuth } from '../context/AuthContext'

export default function Coach() {
  const { user } = useAuth()
  const [daily, setDaily] = useState(null)
  const [target, setTarget] = useState(null)
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [tab, setTab] = useState('daily')
  const [logs, setLogs] = useState([])
  const bottomRef = useRef(null)

  useEffect(() => {
    Promise.all([
      api.get('/coach/daily').then((r) => setDaily(r.data)).catch(() => setDaily(null)),
      api.get('/coach/suggest-target').then((r) => setTarget(r.data)).catch(() => setTarget(null)),
      api.get('/weekly-report/').then((r) => setReports(r.data)).catch(() => setReports([])),
      api.get('/daily-log/history').then((r) => setLogs(r.data)).catch(() => setLogs([])),
    ])
      .catch(() => setErr('Some AI features need your profile to be complete. Go to Settings to add age, height & weight.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [daily])

  const generateReport = async () => {
    setBusy(true); setErr('')
    try {
      const { data } = await api.post('/weekly-report/generate')
      setReports((r) => [data, ...r])
      setTab('weekly')
    } catch (e2) {
      setErr(e2.response?.data?.detail || 'Could not generate weekly report.')
    } finally { setBusy(false) }
  }

  if (loading) return <LoadingFill />

  return (
    <div style={{ maxWidth: 760, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 8 }}>
        <h1 style={{ fontSize: 26, fontWeight: 800 }}>AI Coach 🤖</h1>
        <p className="muted">Your personal fitness intelligence — daily insights, targets &amp; weekly reviews.</p>
      </div>
      <ErrBanner message={err} />

      <div className="tabs" style={{ justifyContent: 'center' }}>
        <button className={`tab${tab === 'daily' ? ' tab--active' : ''}`} onClick={() => setTab('daily')}>✨ Daily Insight</button>
        <button className={`tab${tab === 'targets' ? ' tab--active' : ''}`} onClick={() => setTab('targets')}>🎯 Suggestions</button>
        <button className={`tab${tab === 'weekly' ? ' tab--active' : ''}`} onClick={() => setTab('weekly')}>📅 Weekly Reports</button>
      </div>

      {tab === 'daily' && (
        <div className="chat-scroll" style={{ marginTop: 4 }}>
          <div className="msg msg--ai">
            <div className="msg-avatar">🤖</div>
            <div className="msg-body">
              <b>Assalam-o-Alaikum {user?.full_name?.split(' ')[0] || 'friend'}!</b>
              <p className="muted">Here&apos;s your coaching for {weekdayLabel(new Date().toISOString().slice(0, 10))}</p>
              {daily ? (
                <>
                  <p>{daily.summary}</p>
                  {daily.highlights?.length > 0 && (
                    <div style={{ marginBottom: 8 }}>
                      <b style={{ fontSize: 13 }}>🌟 Highlights</b>
                      <ul style={{ paddingLeft: 20, fontSize: 13 }}>
                        {daily.highlights.map((h, i) => <li key={i}>{h}</li>)}
                      </ul>
                    </div>
                  )}
                  {daily.suggestions?.length > 0 && (
                    <div>
                      <b style={{ fontSize: 13 }}>💡 Suggestions</b>
                      <ul style={{ paddingLeft: 20, fontSize: 13 }}>
                        {daily.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                      </ul>
                    </div>
                  )}
                </>
              ) : (
                <p className="muted">Complete your profile (age/height/weight) to get a personalized daily coach insight.</p>
              )}
            </div>
          </div>

          {logs.length > 0 && (
            <div className="msg msg--ai">
              <div className="msg-avatar">📊</div>
              <div className="msg-body">
                <b>Your recent consistency</b>
                <p className="muted">Last few days at a glance.</p>
                {logs.slice(-5).reverse().map((l) => (
                  <div className="list-item" key={l.id} style={{ padding: '6px 0' }}>
                    <span style={{ fontSize: 13 }}>{weekdayLabel(l.log_date)}</span>
                    <span className="pill pill--green">{fmtNumber(l.total_calories)} kcal</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      )}

      {tab === 'targets' && (
        <div>
          {target ? (
            <div>
              <div className="grid grid--4" style={{ marginBottom: 16 }}>
                <div className="card" style={{ textAlign: 'center' }}>
                  <div className="stat__label">Calories</div>
                  <div className="stat__value" style={{ fontSize: 22 }}>{fmtNumber(target.calorie_target)}</div>
                </div>
                <div className="card" style={{ textAlign: 'center' }}>
                  <div className="stat__label">Protein</div>
                  <div className="stat__value" style={{ fontSize: 22 }}>{fmtNumber(target.protein_target_g)}g</div>
                </div>
                <div className="card" style={{ textAlign: 'center' }}>
                  <div className="stat__label">Carbs</div>
                  <div className="stat__value" style={{ fontSize: 22 }}>{fmtNumber(target.carbs_target_g)}g</div>
                </div>
                <div className="card" style={{ textAlign: 'center' }}>
                  <div className="stat__label">Fats</div>
                  <div className="stat__value" style={{ fontSize: 22 }}>{fmtNumber(target.fats_target_g)}g</div>
                </div>
              </div>
              <div className="card">
                <b>🧠 AI reasoning</b>
                <p className="muted" style={{ marginTop: 6 }}>{target.reasoning}</p>
              </div>
              <div className="card" style={{ marginTop: 14, background: 'var(--primary-soft)', borderColor: 'var(--primary)' }}>
                <b>💡 Tip:</b>
                <p className="muted" style={{ marginTop: 4 }}>Use these targets in your daily log (Settings → Calorie target) to measure whether you&apos;re on track. The weekly report will tell you how often you hit them.</p>
              </div>
            </div>
          ) : (
            <Empty emoji="🎯" title="No targets available" subtitle="Add your height, weight & activity to Settings and the AI will compute your BMR/TDEE-based targets." />
          )}
        </div>
      )}

      {tab === 'weekly' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
            <div>
              <h3 style={{ fontSize: 17, fontWeight: 700 }}>Weekly AI Reports</h3>
              <p className="muted">Generated automatically every Monday morning — or generate on demand.</p>
            </div>
            <button className="btn btn--accent" onClick={generateReport} disabled={busy}>
              {busy ? <Spinner /> : '✨ Generate now'}
            </button>
          </div>

          {reports.length === 0 ? (
            <Empty emoji="📅" title="No weekly reports yet" subtitle="Generate one to see your weekly AI review." />
          ) : (
            reports.map((r) => (
              <div className="card" key={r.id} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
                  <b>{new Date(r.week_start).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })} — {new Date(r.week_end).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}</b>
                  <Pill tone="green">Week {Math.ceil((new Date(r.week_start) - new Date(new Date(r.week_start).getFullYear(), 0, 1)) / 604800000)}</Pill>
                </div>
                <p>{r.summary}</p>
                {r.highlights?.length > 0 && (
                  <div style={{ margin: '10px 0' }}>
                    <b style={{ fontSize: 13 }}>🌟 Highlights</b>
                    <ul style={{ paddingLeft: 20, fontSize: 13 }}>
                      {r.highlights.map((h, i) => <li key={i}>{h}</li>)}
                    </ul>
                  </div>
                )}
                {r.suggestions?.length > 0 && (
                  <div>
                    <b style={{ fontSize: 13 }}>💡 Suggestions</b>
                    <ul style={{ paddingLeft: 20, fontSize: 13 }}>
                      {r.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}