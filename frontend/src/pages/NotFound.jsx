export default function NotFound() {
  return (
    <div className="notfound">
      <div>
        <div style={{ fontSize: 56 }}>🏃‍♂️</div>
        <h1 style={{ fontSize: 32, margin: '8px 0' }}>404 — Lost in the gym</h1>
        <p className="muted">The page you're looking for doesn't exist.</p>
        <a href="/" className="btn" style={{ marginTop: 16, display: 'inline-flex' }}>Back to Dashboard</a>
      </div>
    </div>
  )
}