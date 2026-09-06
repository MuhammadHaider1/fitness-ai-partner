const nf = new Intl.NumberFormat('en-US')

export const fmtNumber = (n) => nf.format(Math.round(n ?? 0))
export const fmtDate = (iso) => {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}
export const todayISO = () => new Date().toISOString().slice(0, 10)
export const weekdayLabel = (iso) => new Date(iso).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })

// ISO weekday: 0=Monday ... 6=Sunday (backend convention)
export const isoWeekday = (date = new Date()) => (date.getDay() + 6) % 7
export const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
export const dayName = (iso) => DAY_NAMES[isoWeekday(new Date(iso))]