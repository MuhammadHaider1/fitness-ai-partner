/** @type {import('tailwindcss').Config} */
export default {
  prefix: 'lp-',
  corePlugins: { preflight: false },
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        base: '#05070c',
        surface: 'rgba(255,255,255,0.04)',
        limev: '#a3e635',
        tealg: '#2dd4bf',
        ink: '#e6edf7',
        muted: '#9fb0c7',
      },
      borderRadius: { xl2: '1.25rem' },
      keyframes: {
        floaty: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-10px)' } },
        glowPulse: {
          '0%,100%': { opacity: '0.55' },
          '50%': { opacity: '1' },
        },
        dash: { to: { strokeDashoffset: '0' } },
      },
      animation: {
        floaty: 'floaty 6s ease-in-out infinite',
        glow: 'glowPulse 3.5s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}