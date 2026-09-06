const nf = new Intl.NumberFormat('en-US')
const karachiDate = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Karachi',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
})

export const fmtNumber = (n) => nf.format(Math.round(n ?? 0))
export const fmtDate = (iso) => {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}
// Backend har timestamp Asia/Karachi (PKT) ke din bucket karta hai — same yahan
export const todayISO = () => karachiDate.format(new Date())
export const shiftISO = (days) => {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return karachiDate.format(d)
}
export const weekdayLabel = (iso) => new Date(iso).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })

// ISO weekday: 0=Monday ... 6=Sunday (backend convention)
export const isoWeekday = (date = new Date()) => (date.getDay() + 6) % 7
export const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
export const dayName = (iso) => DAY_NAMES[isoWeekday(new Date(iso))]

// Week display order starting Saturday: [Sat, Sun, Mon, Tue, Wed, Thu, Fri]
export const WEEK_START_SAT = [5, 6, 0, 1, 2, 3, 4]

export const bmiLabel = (bmi) => {
  if (!bmi) return '—'
  if (bmi < 18.5) return 'Underweight'
  if (bmi < 25) return 'Healthy'
  if (bmi < 30) return 'Overweight'
  return 'Obese'
}