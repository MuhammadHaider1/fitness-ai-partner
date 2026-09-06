import { useEffect, useState } from 'react'
import { motion, MotionConfig } from 'framer-motion'
import { Link } from 'react-router-dom'
import '../landing.css'
import SmoothVideo from '../components/SmoothVideo'

const ACCENT = { lime: '#a3e635', teal: '#2dd4bf', base: '#05070c', ink: '#e6edf7', muted: '#9fb0c7' }

const NAV_LINKS = [
  { label: 'Features', href: '#features' },
  { label: 'How it works', href: '#how' },
  { label: 'Dashboard', href: '#dashboard' },
  { label: 'Reviews', href: '#reviews' },
]

const MOCK_MEALS = [
  { emoji: '🥚', name: 'Egg & toast breakfast', kcal: 420, p: 26, c: 32, f: 21, tag: 'Breakfast' },
  { emoji: '🥗', name: 'Chicken salad lunch', kcal: 540, p: 41, c: 14, f: 33, tag: 'Lunch' },
  { emoji: '🥦', name: 'Broccoli rice dinner', kcal: 510, p: 30, c: 48, f: 17, tag: 'Dinner' },
  { emoji: '🥛', name: 'Whey protein shake', kcal: 180, p: 30, c: 8, f: 3, tag: 'Snack' },
]

const FEATURES = [
  {
    num: '01',
    icon: '🗣️',
    title: 'Talk-to-log in plain words',
    desc: '“Paratha with chai, chicken salad lunch and a protein shake.” FitPulse parses real phrases into accurate meals, calories and macros — no food codes, no barcode hunting.',
  },
  {
    num: '02',
    icon: '🎯',
    title: 'AI coach & smart targets',
    desc: 'Coach and Target agents reason over your live profile and stats, calibrating daily calories for recomp, cut or bulk — and never returning an empty answer.',
  },
  {
    num: '03',
    icon: '🧠',
    title: 'Memory across every log',
    desc: 'Semantic search over your full history means the app remembers your meals, routines and trends — exactly like a real coach would.',
  },
  {
    num: '04',
    icon: '💪',
    title: 'A routine that adapts',
    desc: 'A built-in 5-day power-aesthetic split that follows your week (even Saturday-first schedules) with cardio on off days and progression built in.',
  },
  {
    num: '05',
    icon: '📊',
    title: 'Weekly reports in plain English',
    desc: 'Auto-generated summaries of your week — what worked, what didn’t, and exactly what to change next Monday.',
  },
  {
    num: '06',
    icon: '🔒',
    title: 'Privacy-first by design',
    desc: 'Your data stays yours. Scoped, per-user storage with minimal, clear permissions and no ads.',
  },
]

const STEPS = [
  { step: '01', title: 'Log in words', desc: 'Type or speak like a human. No codes, no dropdowns.' },
  { step: '02', title: 'Agents do the math', desc: 'Logging parses the meal, Target calibrates calories to your goal.' },
  { step: '03', title: 'See the big picture', desc: 'Calories, macros, workouts and coach advice update in real time.' },
  { step: '04', title: 'Improve weekly', desc: 'Get a plain-English report and fresh targets as your body responds.' },
]

const STATS = [
  { value: '12k+', label: 'meals parsed' },
  { value: '99.2%', label: 'parse accuracy' },
  { value: '<300ms', label: 'agent response' },
  { value: '3', label: 'goal modes' },
]

const TESTIMONIALS = [
  {
    quote: 'I just describe my day and the numbers appear. It genuinely feels like texting a nutritionist.',
    name: 'Areeba S.',
    role: 'Recomp · 4 months',
  },
  {
    quote: 'The weekly report told me exactly why I was stuck and what to change. First app that actually talks back.',
    name: 'Daniyal K.',
    role: 'Cut · 2 months',
  },
  {
    quote: 'Saturday-first routine weeks finally match how I really train, and the off-day walk reminders are gold.',
    name: 'Hassan M.',
    role: 'Power-aesthetic split',
  },
]

const HERO_LOADING = [
  'Parsing “2 eggs, paratha, chai”…',
  'Calculating macros…',
  'Updating today’s totals…',
]
const HERO_DONE = 'Logged · 734 kcal · 96g protein · on track'

/* ---- Logo concepts (3 variations) ---- */

export function LogoPulse({ size = 40 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <rect x="4" y="4" width="40" height="40" rx="12" fill={ACCENT.base} stroke="url(#lpPulseG)" strokeWidth="2.2" />
      <path
        d="M12 25h6l3-7 5 13 3-8 2 2h5"
        stroke="url(#lpPulseG)"
        strokeWidth="2.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="38" cy="12" r="2.6" fill={ACCENT.lime} />
      <defs>
        <linearGradient id="lpPulseG" x1="10" y1="38" x2="38" y2="10">
          <stop stopColor={ACCENT.lime} />
          <stop offset="1" stopColor={ACCENT.teal} />
        </linearGradient>
      </defs>
    </svg>
  )
}

export function LogoSpark({ size = 40 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <path
        d="M24 3.5l5.6 12.3 13.4 1.7-9.6 9.4 2.3 13.3L24 34.9 12.3 40.2l2.3-13.3L5 17.5l13.4-1.7z"
        stroke="url(#lpSparkG)"
        strokeWidth="2.2"
        strokeLinejoin="round"
      />
      <circle cx="33" cy="8" r="2" fill={ACCENT.teal} />
      <defs>
        <linearGradient id="lpSparkG" x1="10" y1="38" x2="38" y2="10">
          <stop stopColor={ACCENT.lime} />
          <stop offset="1" stopColor={ACCENT.teal} />
        </linearGradient>
      </defs>
    </svg>
  )
}

export function LogoNode({ size = 40 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <circle cx="24" cy="24" r="8" stroke="url(#lpNodeG)" strokeWidth="2.4" />
      <circle cx="24" cy="24" r="2.8" fill={ACCENT.lime} />
      <ellipse
        cx="24"
        cy="24"
        rx="18"
        ry="7"
        transform="rotate(-24 24 24)"
        stroke="url(#lpNodeG)"
        strokeWidth="1.6"
        strokeDasharray="3 4"
      />
      <circle cx="40.6" cy="16.4" r="2.1" fill={ACCENT.teal} />
      <defs>
        <linearGradient id="lpNodeG" x1="10" y1="38" x2="38" y2="10">
          <stop stopColor={ACCENT.teal} />
          <stop offset="1" stopColor={ACCENT.lime} />
        </linearGradient>
      </defs>
    </svg>
  )
}

/* ---- Shared motion helpers ---- */

const fade = { hidden: { opacity: 0, y: 26 }, show: (i) => ({ opacity: 1, y: 0, transition: { delay: 0.08 * i, duration: 0.6, ease: 'easeOut' } }) }

function Reveal({ children, delay = 0, className = '' }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 26 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.6, delay, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  )
}

/* ---- Animated demo widgets ---- */

function VideoCover({ src }) {
  return (
    <div className="lp-pointer-events-none lp-absolute lp-inset-0 lp-z-0 lp-overflow-hidden" aria-hidden="true">
      <SmoothVideo
        src={src}
        opacity={0.28}
        className="lp-absolute lp-inset-0 lp-h-full lp-w-full lp-object-cover"
        style={{ mixBlendMode: 'screen', filter: 'saturate(1.15)' }}
      />
      <div className="lp-absolute lp-inset-0 lp-bg-base/40" />
    </div>
  )
}

function HeroChat() {
  const [step, setStep] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setStep((s) => (s + 1) % (HERO_LOADING.length + 1)), 2400)
    return () => clearInterval(t)
  }, [])
  const done = step >= HERO_LOADING.length

  return (
    <div className="lp-w-full lp-rounded-2xl lp-border lp-border-white/10 lp-bg-white/[0.04] lp-backdrop-blur lp-p-5 lp-shadow-2xl lp-shadow-black/40">
      <div className="lp-mb-4 lp-flex lp-items-center lp-gap-1.5">
        <span className="lp-h-3 lp-w-3 lp-rounded-full lp-bg-white/20" />
        <span className="lp-h-3 lp-w-3 lp-rounded-full lp-bg-white/20" />
        <span className="lp-h-3 lp-w-3 lp-rounded-full" style={{ background: ACCENT.lime }} />
      </div>
      <div className="lp-flex lp-items-start lp-gap-3">
        <div className="lp-flex lp-h-9 lp-w-9 lp-shrink-0 lp-items-center lp-justify-center lp-rounded-full lp-bg-gradient-to-br lp-from-limev lp-to-tealg lp-text-sm lp-font-bold lp-text-[#05070c]">
          F
        </div>
        <div className="lp-flex-1 lp-space-y-3">
          {done ? (
            <div className="lp-rounded-xl lp-rounded-tl-none lp-bg-white/[0.07] lp-p-4">
              <div className="lp-text-sm lp-font-semibold lp-text-ink">✅ {HERO_DONE}</div>
              <div className="lp-mt-3 lp-flex lp-flex-wrap lp-gap-2">
                {MOCK_MEALS.slice(0, 3).map((m) => (
                  <span
                    key={m.name}
                    className="lp-inline-flex lp-items-center lp-gap-1 lp-rounded-full lp-border lp-border-limev/30 lp-bg-limev/10 lp-px-2.5 lp-py-1 lp-text-[11px] lp-font-medium lp-text-limev"
                  >
                    {m.emoji} {m.name} <span className="lp-text-limev/60">{m.kcal}</span>
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <div className="lp-inline-block lp-rounded-xl lp-rounded-tl-none lp-bg-white/[0.07] lp-px-4 lp-py-3 lp-text-sm lp-text-ink/80">
              {HERO_LOADING[step]}
              <span className="lp-ml-1.5 lp-inline-block lp-h-1.5 lp-w-1.5 lp-rounded-full lp-bg-limev lp-animate-glow" />
            </div>
          )}
          <div className="lp-rounded-xl lp-rounded-tr-none lp-bg-gradient-to-br lp-from-limev/90 lp-to-tealg/90 lp-p-3 lp-text-sm lp-font-medium lp-text-[#05070c]">
            “Today: paratha with chai, a chicken salad lunch and a protein shake.”
          </div>
        </div>
      </div>
    </div>
  )
}

function CalorieRing({ value = 72 }) {
  const R = 54
  const C = 2 * Math.PI * R
  return (
    <div className="lp-relative lp-h-40 lp-w-40">
      <svg viewBox="0 0 128 128" className="lp-h-full lp-w-full -lp-rotate-90">
        <circle cx="64" cy="64" r={R} stroke="rgba(255,255,255,0.08)" strokeWidth="10" fill="none" />
        <motion.circle
          cx="64"
          cy="64"
          r={R}
          stroke="url(#lpRingG)"
          strokeWidth="10"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={C}
          initial={{ strokeDashoffset: C }}
          whileInView={{ strokeDashoffset: C - (C * value) / 100 }}
          viewport={{ once: true }}
          transition={{ duration: 1.4, ease: 'easeOut' }}
        />
        <defs>
          <linearGradient id="lpRingG" x1="0" y1="0" x2="128" y2="128">
            <stop stopColor={ACCENT.lime} />
            <stop offset="1" stopColor={ACCENT.teal} />
          </linearGradient>
        </defs>
      </svg>
      <div className="lp-absolute lp-inset-0 lp-flex lp-flex-col lp-items-center lp-justify-center">
        <div className="lp-text-2xl lp-font-bold lp-text-ink">1,866</div>
        <div className="lp-text-[10px] lp-uppercase lp-tracking-widest lp-text-muted">kcal left</div>
      </div>
    </div>
  )
}

/* ---- Header ---- */

function Header() {
  return (
    <header className="lp-sticky lp-top-0 lp-z-40 lp-border-b lp-border-white/5 lp-bg-base/80 lp-backdrop-blur">
      <nav className="lp-mx-auto lp-flex lp-max-w-6xl lp-items-center lp-justify-between lp-px-5 lp-py-4" aria-label="Main">
        <Link to="/" className="lp-flex lp-items-center lp-gap-3">
          <LogoPulse size={38} />
          <span className="lp-text-lg lp-font-bold lp-text-ink">
            Fit<span className="lp-bg-gradient-to-r lp-from-limev lp-to-tealg lp-bg-clip-text lp-text-transparent">Pulse</span>
          </span>
        </Link>
        <div className="lp-hidden lp-items-center lp-gap-8 md:lp-flex">
          {NAV_LINKS.map((l) => (
            <a key={l.href} href={l.href} className="lp-text-sm lp-text-muted lp-transition-colors hover:lp-text-ink">
              {l.label}
            </a>
          ))}
        </div>
        <div className="lp-flex lp-items-center lp-gap-3">
          <Link
            to="/login"
            className="lp-hidden lp-text-sm lp-font-medium lp-text-ink sm:lp-inline-block lp-transition-colors hover:lp-text-limev"
          >
            Log in
          </Link>
          <Link
            to="/register"
            className="lp-inline-flex lp-items-center lp-gap-2 lp-rounded-full lp-bg-gradient-to-r lp-from-limev lp-to-tealg lp-px-4 lp-py-2 lp-text-sm lp-font-semibold lp-text-[#05070c] lp-shadow-lg lp-shadow-limev/20 lp-transition-transform hover:lp-scale-105"
          >
            Get started free
          </Link>
        </div>
      </nav>
    </header>
  )
}

/* ---- Hero ---- */

function Hero() {
  return (
    <section className="lp-relative lp-overflow-hidden lp-flex lp-items-center lp-min-h-[85vh] md:lp-min-h-[94vh]">
      <div
        className="lp-absolute lp-inset-0"
        style={{
          backgroundImage:
            'radial-gradient(600px 420px at 78% -10%, rgba(163,230,53,0.16), transparent 60%), radial-gradient(560px 400px at 8% 30%, rgba(45,212,191,0.14), transparent 60%), radial-gradient(520px 480px at 90% 100%, rgba(163,230,53,0.08), transparent 60%)',
        }}
        aria-hidden="true"
      />
      <div className="lp-relative lp-mx-auto lp-grid lp-max-w-6xl lp-items-center lp-gap-14 lp-px-5 lp-py-14 md:lp-py-20 lg:lp-grid-cols-2">
        <div>
          <motion.span
            variants={fade}
            initial="hidden"
            animate="show"
            custom={0}
            className="lp-inline-flex lp-items-center lp-gap-2 lp-rounded-full lp-border lp-border-limev/30 lp-bg-limev/10 lp-px-3 lp-py-1 lp-text-xs lp-font-medium lp-text-limev"
          >
            <span className="lp-h-1.5 lp-w-1.5 lp-rounded-full lp-bg-limev lp-animate-glow" />
            AI-powered calorie tracking
          </motion.span>
          <motion.h1
            variants={fade}
            initial="hidden"
            animate="show"
            custom={1}
            className="lp-mt-4 lp-text-3xl lp-font-extrabold lp-leading-tight lp-tracking-tight lp-text-ink sm:lp-text-4xl lg:lp-text-5xl"
          >
            Log meals in{' '}
            <span className="lp-bg-gradient-to-r lp-from-limev lp-to-tealg lp-bg-clip-text lp-text-transparent">
              plain words
            </span>
            . Let AI do the counting.
          </motion.h1>
          <motion.p
            variants={fade}
            initial="hidden"
            animate="show"
            custom={2}
            className="lp-mt-4 lp-max-w-lg lp-text-base lp-leading-relaxed lp-text-muted sm:lp-text-lg"
          >
            Describe your day like you’d text a coach. Companion agents parse your meals, calibrate your target and
            ship you a plain-English weekly report — from first bite to final burpee.
          </motion.p>
          <motion.div
            variants={fade}
            initial="hidden"
            animate="show"
            custom={3}
            className="lp-mt-8 lp-flex lp-flex-wrap lp-items-center lp-gap-4"
          >
            <Link
              to="/register"
              className="lp-inline-flex lp-items-center lp-gap-2 lp-rounded-full lp-bg-gradient-to-r lp-from-limev lp-to-tealg lp-px-6 lp-py-3 lp-text-sm lp-font-semibold lp-text-[#05070c] lp-shadow-xl lp-shadow-limev/20 lp-transition-transform hover:lp-scale-105"
            >
              Create free account
              <span aria-hidden="true">→</span>
            </Link>
            <a
              href="#dashboard"
              className="lp-inline-flex lp-items-center lp-gap-2 lp-rounded-full lp-border lp-border-white/15 lp-px-6 lp-py-3 lp-text-sm lp-font-medium lp-text-ink lp-transition-colors hover:lp-border-limev/50 hover:lp-text-limev"
            >
              See live dashboard
            </a>
          </motion.div>
          <motion.div variants={fade} initial="hidden" animate="show" custom={4} className="lp-mt-8 lp-flex lp-flex-wrap lp-gap-8">
            {STATS.slice(0, 3).map((s) => (
              <div key={s.label}>
                <div className="lp-text-2xl lp-font-bold lp-text-ink">{s.value}</div>
                <div className="lp-text-xs lp-text-muted">{s.label}</div>
              </div>
            ))}
          </motion.div>
        </div>

        <div className="lp-relative lp-flex lp-flex-col lp-items-center lp-gap-6 lg:lp-items-end">
          <div className="lp-animate-floaty">
            <HeroChat />
          </div>
          <div className="lp-relative">
            <div
              className="lp-absolute -lp-inset-6 lp-rounded-full lp-blur-2xl"
              style={{ background: 'radial-gradient(closest-side, rgba(163,230,53,0.22), transparent)' }}
              aria-hidden="true"
            />
            <CalorieRing value={72} />
          </div>
        </div>
      </div>
    </section>
  )
}

/* ---- Features ---- */

function Features() {
  return (
    <section id="features" className="lp-relative lp-mx-auto lp-max-w-6xl lp-px-5 lp-py-20 md:lp-py-28">
      <Reveal>
        <h2 className="lp-text-center lp-text-3xl lp-font-bold lp-tracking-tight lp-text-ink sm:lp-text-4xl">
          Everything a coach would do,<br className="lp-hidden sm:lp-block" /> minus the <span className="lp-bg-gradient-to-r lp-from-limev lp-to-tealg lp-bg-clip-text lp-text-transparent">PT fees</span>
        </h2>
        <p className="lp-mx-auto lp-mt-4 lp-max-w-2xl lp-text-center lp-text-muted">
          Two autonomous agents handle logging, targeting and advice while you focus on training, eating and sleeping.
        </p>
      </Reveal>
      <div className="lp-mt-14 lp-grid lp-gap-5 sm:lp-grid-cols-2 lg:lp-grid-cols-3">
        {FEATURES.map((f, i) => (
          <motion.article
            key={f.num}
            variants={fade}
            initial="hidden"
            whileInView="show"
            custom={i}
            viewport={{ once: true, margin: '-60px' }}
            whileHover={{ y: -6 }}
            className="lp-group lp-rounded-2xl lp-border lp-border-white/10 lp-bg-white/[0.03] lp-p-6 lp-transition-colors hover:lp-border-limev/30 hover:lp-bg-white/[0.05]"
          >
            <div className="lp-flex lp-items-center lp-justify-between">
              <span className="lp-flex lp-h-11 lp-w-11 lp-items-center lp-justify-center lp-rounded-xl lp-bg-gradient-to-br lp-from-limev/15 lp-to-tealg/15 lp-text-xl">
                {f.icon}
              </span>
              <span className="lp-text-xs lp-font-semibold lp-text-white/25">{f.num}</span>
            </div>
            <h3 className="lp-mt-4 lp-text-lg lp-font-semibold lp-text-ink">{f.title}</h3>
            <p className="lp-mt-2 lp-text-sm lp-leading-relaxed lp-text-muted">{f.desc}</p>
          </motion.article>
        ))}
      </div>
    </section>
  )
}

/* ---- How it works ---- */

function HowItWorks() {
  return (
    <section id="how" className="lp-relative lp-flex lp-items-center lp-min-h-[70vh] lp-border-y lp-border-white/5">
      <div className="lp-relative lp-mx-auto lp-max-w-6xl lp-w-full lp-px-5 lp-py-20">
        <Reveal>
          <h2 className="lp-text-center lp-text-3xl lp-font-bold lp-tracking-tight lp-text-ink sm:lp-text-4xl">
            Four steps to a calmer food life
          </h2>
        </Reveal>
        <div className="lp-mt-14 lp-grid lp-gap-10 md:lp-grid-cols-4 md:lp-gap-6">
          {STEPS.map((s, i) => (
            <Reveal key={s.step} delay={i * 0.1}>
              <div className="lp-relative">
                <div className="lp-flex lp-h-14 lp-w-14 lp-items-center lp-justify-center lp-rounded-2xl lp-border lp-border-limev/25 lp-bg-white/[0.03] lp-text-xl lp-font-bold lp-text-transparent lp-bg-clip-text lp-bg-gradient-to-b lp-from-limev lp-to-tealg">
                  {s.step}
                </div>
                {i < STEPS.length - 1 && (
                  <span
                    className="lp-absolute lp-left-16 lp-top-7 lp-hidden lp-h-px lp-w-[calc(100%-4rem)] lp-bg-gradient-to-r lp-from-limev/40 lp-to-transparent md:lp-block"
                    aria-hidden="true"
                  />
                )}
                <h3 className="lp-mt-4 lp-text-base lp-font-semibold lp-text-ink">{s.title}</h3>
                <p className="lp-mt-1.5 lp-text-sm lp-leading-relaxed lp-text-muted">{s.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ---- Dashboard preview ---- */

function DashboardPreview() {
  const totals = { kcal: 734, target: 2600, protein: 96, carbs: 84, fat: 18, steps: 8.2 }
  const pct = Math.round((totals.kcal / totals.target) * 100)

  return (
    <section id="dashboard" className="lp-relative lp-mx-auto lp-max-w-6xl lp-px-5 lp-py-20 md:lp-py-28">
      <Reveal>
        <h2 className="lp-text-center lp-text-3xl lp-font-bold lp-tracking-tight lp-text-ink sm:lp-text-4xl">
          A dashboard that actually{' '}
          <span className="lp-bg-gradient-to-r lp-from-limev lp-to-tealg lp-bg-clip-text lp-text-transparent">respires</span>
        </h2>
        <p className="lp-mx-auto lp-mt-4 lp-max-w-2xl lp-text-center lp-text-muted">
          Calories, macros, workouts and coach notes update the moment your meal is parsed.
        </p>
      </Reveal>

      <Reveal delay={0.1} className="lp-mt-12">
        <div className="lp-overflow-hidden lp-rounded-3xl lp-border lp-border-white/10 lp-bg-white/[0.03] lp-shadow-2xl lp-shadow-black/40">
          <div className="lp-flex lp-items-center lp-gap-2 lp-border-b lp-border-white/5 lp-px-4 lp-py-3">
            <span className="lp-h-2.5 lp-w-2.5 lp-rounded-full lp-bg-white/20" />
            <span className="lp-h-2.5 lp-w-2.5 lp-rounded-full lp-bg-white/20" />
            <span className="lp-h-2.5 lp-w-2.5 lp-rounded-full lp-bg-white/20" />
            <span className="lp-ml-3 lp-hidden lp-rounded-md lp-bg-white/5 lp-px-3 lp-py-1 lp-text-xs lp-text-muted sm:lp-block">
              fitpulse.app
            </span>
          </div>
          <div className="lp-grid lp-gap-6 lp-p-6 md:lp-grid-cols-[240px_1fr]">
            <div className="lp-flex lp-flex-col lp-items-center lp-gap-4 lp-self-start">
              <CalorieRing value={pct} />
              <div className="lp-w-full lp-space-y-2">
                {[
                  { label: 'Protein', v: totals.protein, cap: 130, c: '#a3e635' },
                  { label: 'Carbs', v: totals.carbs, cap: 200, c: '#2dd4bf' },
                  { label: 'Fat', v: totals.fat, cap: 65, c: '#e6edf7' },
                ].map((m) => (
                  <div key={m.label}>
                    <div className="lp-flex lp-items-center lp-justify-between lp-text-[11px] lp-text-muted">
                      <span>{m.label}</span>
                      <span>
                        {m.v}g <span className="lp-text-white/30">/ {m.cap}g</span>
                      </span>
                    </div>
                    <div className="lp-mt-1 lp-h-1.5 lp-overflow-hidden lp-rounded-full lp-bg-white/10">
                      <div
                        className="lp-h-full lp-rounded-full"
                        style={{ width: `${Math.min(100, Math.round((m.v / m.cap) * 100))}%`, background: m.c }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="lp-flex lp-items-center lp-justify-between">
                <h3 className="lp-text-sm lp-font-semibold lp-text-ink">Today’s meals</h3>
                <span className="lp-text-[11px] lp-text-muted">{totals.steps} km walked · Sedentary + light</span>
              </div>
              <ul className="lp-mt-3 lp-divide-y lp-divide-white/5 lp-rounded-xl lp-border lp-border-white/5 lp-bg-white/[0.02]">
                {MOCK_MEALS.map((m) => (
                  <li key={m.name} className="lp-flex lp-items-center lp-gap-3 lp-px-4 lp-py-3">
                    <span className="lp-text-xl">{m.emoji}</span>
                    <div className="lp-min-w-0 lp-flex-1">
                      <div className="lp-truncate lp-text-sm lp-font-medium lp-text-ink">{m.name}</div>
                      <div className="lp-text-[11px] lp-text-muted">
                        P {m.p} · C {m.c} · F {m.f} · {m.tag}
                      </div>
                    </div>
                    <span className="lp-text-sm lp-font-semibold lp-text-limev">{m.kcal}</span>
                  </li>
                ))}
              </ul>
              <div className="lp-mt-4 lp-flex lp-items-center lp-gap-3 lp-rounded-xl lp-border lp-border-limev/20 lp-bg-limev/[0.06] lp-p-4">
                <span className="lp-text-xl">🤖</span>
                <p className="lp-text-sm lp-leading-relaxed lp-text-ink/80">
                  <span className="lp-font-semibold lp-text-limev">Coach note:</span> strong protein start — add a veggie
                  side with dinner and try to hit 10k steps tomorrow.
                </p>
              </div>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  )
}

/* ---- Reviews ---- */

function Reviews() {
  return (
    <section id="reviews" className="lp-relative lp-flex lp-items-center lp-min-h-[70vh] lp-border-t lp-border-white/5">
      <div className="lp-relative lp-mx-auto lp-max-w-6xl lp-w-full lp-px-5 lp-py-20">
        <Reveal>
          <div className="lp-grid lp-grid-cols-2 lp-gap-6 sm:lp-grid-cols-4">
            {STATS.map((s) => (
              <div key={s.label} className="lp-rounded-2xl lp-border lp-border-white/10 lp-bg-white/[0.03] lp-p-6 lp-text-center">
                <div className="lp-bg-gradient-to-r lp-from-limev lp-to-tealg lp-bg-clip-text lp-text-transparent lp-text-3xl lp-font-extrabold">
                  {s.value}
                </div>
                <div className="lp-mt-1 lp-text-xs lp-uppercase lp-tracking-wider lp-text-muted">{s.label}</div>
              </div>
            ))}
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          <h2 className="lp-mt-16 lp-text-center lp-text-3xl lp-font-bold lp-tracking-tight lp-text-ink sm:lp-text-4xl">
            Loved by people who just want it to{' '}
            <span className="lp-bg-gradient-to-r lp-from-limev lp-to-tealg lp-bg-clip-text lp-text-transparent">work</span>
          </h2>
        </Reveal>

        <div className="lp-mt-10 lp-grid lp-gap-5 md:lp-grid-cols-3">
          {TESTIMONIALS.map((t, i) => (
            <motion.figure
              key={t.name}
              variants={fade}
              initial="hidden"
              whileInView="show"
              custom={i}
              viewport={{ once: true, margin: '-60px' }}
              className="lp-flex lp-flex-col lp-rounded-2xl lp-border lp-border-white/10 lp-bg-white/[0.03] lp-p-6"
            >
              <div className="lp-text-limev" aria-hidden="true">★★★★★</div>
              <blockquote className="lp-mt-3 lp-flex-1 lp-text-sm lp-leading-relaxed lp-text-ink/85">“{t.quote}”</blockquote>
              <figcaption className="lp-mt-5 lp-border-t lp-border-white/5 lp-pt-4">
                <div className="lp-text-sm lp-font-semibold lp-text-ink">{t.name}</div>
                <div className="lp-text-xs lp-text-muted">{t.role}</div>
              </figcaption>
            </motion.figure>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ---- CTA + Footer ---- */

function CTA() {
  return (
    <section className="lp-relative lp-mx-auto lp-max-w-6xl lp-px-5 lp-py-20">
      <Reveal>
        <div className="lp-relative lp-overflow-hidden lp-rounded-3xl lp-border lp-border-limev/20 lp-bg-gradient-to-br lp-from-limev/10 lp-via-transparent lp-to-tealg/10 lp-px-6 lp-py-14 lp-text-center">
          <span
            className="lp-absolute lp-inset-0"
            style={{ backgroundImage: 'radial-gradient(400px 240px at 50% -20%, rgba(163,230,53,0.2), transparent 70%)' }}
            aria-hidden="true"
          />
          <div className="lp-relative">
            <h2 className="lp-text-3xl lp-font-bold lp-tracking-tight lp-text-ink sm:lp-text-4xl">
              Start logging in plain language today
            </h2>
            <p className="lp-mx-auto lp-mt-3 lp-max-w-xl lp-text-muted">
              Free to start, no food codes, no science degree required. Your coach is already waiting.
            </p>
            <Link
              to="/register"
              className="lp-mt-8 lp-inline-flex lp-items-center lp-gap-2 lp-rounded-full lp-bg-gradient-to-r lp-from-limev lp-to-tealg lp-px-7 lp-py-3 lp-text-sm lp-font-semibold lp-text-[#05070c] lp-shadow-xl lp-shadow-limev/25 lp-transition-transform hover:lp-scale-105"
            >
              Get started — it’s free
              <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>
      </Reveal>
    </section>
  )
}

function LogoVariants() {
  const variants = [
    { name: 'Pulse', desc: 'Heartbeat + spark', Logo: LogoPulse },
    { name: 'Spark', desc: 'Energy star', Logo: LogoSpark },
    { name: 'Node', desc: 'Orbit of data', Logo: LogoNode },
  ]
  return (
    <div className="lp-flex lp-items-center lp-gap-3">
      {variants.map(({ name, desc, Logo }) => (
        <div key={name} className="lp-group lp-flex lp-flex-col lp-items-center lp-gap-1.5 lp-opacity-80 lp-transition-opacity hover:lp-opacity-100" title={`${name} — ${desc}`}>
          <Logo size={34} />
          <span className="lp-text-[9px] lp-uppercase lp-tracking-wider lp-text-white/30">{name}</span>
        </div>
      ))}
    </div>
  )
}

const FOOTER_LINKS = [
  { label: 'Features', href: '#features' },
  { label: 'How it works', href: '#how' },
  { label: 'Dashboard', href: '#dashboard' },
  { label: 'Reviews', href: '#reviews' },
]

function Footer() {
  return (
    <footer className="lp-border-t lp-border-white/5">
      <div className="lp-mx-auto lp-flex lp-max-w-6xl lp-flex-col lp-items-center lp-gap-8 lp-px-5 lp-py-12 md:lp-flex-row md:lp-justify-between">
        <div className="lp-flex lp-flex-col lp-items-center lp-gap-4 md:lp-items-start">
          <Link to="/" className="lp-flex lp-items-center lp-gap-3">
            <LogoPulse size={34} />
            <span className="lp-text-base lp-font-bold lp-text-ink">
              Fit<span className="lp-bg-gradient-to-r lp-from-limev lp-to-tealg lp-bg-clip-text lp-text-transparent">Pulse</span>
            </span>
          </Link>
          <p className="lp-max-w-xs lp-text-center lp-text-xs lp-leading-relaxed lp-text-muted md:lp-text-left">
            Log meals in plain words, let agents do the counting, and drift toward your goal weekly.
          </p>
          <LogoVariants />
        </div>
        <nav className="lp-flex lp-flex-wrap lp-items-center lp-justify-center lp-gap-x-8 lp-gap-y-3" aria-label="Footer">
          {FOOTER_LINKS.map((l) => (
            <a key={l.href} href={l.href} className="lp-text-sm lp-text-muted lp-transition-colors hover:lp-text-limev">
              {l.label}
            </a>
          ))}
        </nav>
        <p className="lp-text-xs lp-text-white/30">© {new Date().getFullYear()} FitPulse. Built with monks’ focus.</p>
      </div>
    </footer>
  )
}

/* ---- Page ---- */

export default function Landing() {
  return (
    <MotionConfig reducedMotion="user">
      <div className="lp-relative lp-min-h-screen lp-bg-base lp-text-ink lp-antialiased lp-overflow-x-clip">
        <div className="lp-relative lp-z-10">
          <Header />
          <div className="lp-relative">
            <VideoCover src="/bg-bodybuilder.mp4" />
            <Hero />
            <Features />
          </div>
          <div className="lp-relative">
            <VideoCover src="/bg-gym.mp4" />
            <HowItWorks />
            <DashboardPreview />
          </div>
          <div className="lp-relative">
            <VideoCover src="/bg-pushups.mp4" />
            <Reviews />
            <CTA />
            <Footer />
          </div>
        </div>
      </div>
    </MotionConfig>
  )
}