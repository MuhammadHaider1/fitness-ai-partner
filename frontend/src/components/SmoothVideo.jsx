import { useEffect, useRef } from 'react'

const FADE_MS = 720
const NEAR_END = 0.75

export default function SmoothVideo({ src, className = '', style, opacity = 1 }) {
  const refs = [useRef(null), useRef(null)]
  const toggleRef = useRef(false)
  const busyRef = useRef(false)

  const crossfade = () => {
    const cur = refs[Number(toggleRef.current)].current
    const nxt = refs[Number(!toggleRef.current)].current
    if (!cur || !nxt || busyRef.current) return
    busyRef.current = true
    nxt.currentTime = 0.001
    nxt.play().catch(() => {})
    nxt.style.transition = `opacity ${FADE_MS}ms ease`
    cur.style.transition = `opacity ${FADE_MS}ms ease`
    nxt.style.opacity = opacity
    cur.style.opacity = 0
    toggleRef.current = !toggleRef.current
    setTimeout(() => {
      cur.pause()
      cur.currentTime = 0
      cur.style.transition = 'none'
      cur.style.opacity = 0
      busyRef.current = false
    }, FADE_MS + 40)
  }

  useEffect(() => {
    const onTime = (e) => {
      if (busyRef.current) return
      const el = e.target
      if (el !== refs[Number(toggleRef.current)].current) return
      const d = el.duration
      if (d && el.currentTime > 0 && d - el.currentTime < NEAR_END) crossfade()
    }
    const [a, b] = refs
    a.current.addEventListener('timeupdate', onTime)
    b.current.addEventListener('timeupdate', onTime)
    return () => {
      a.current?.removeEventListener('timeupdate', onTime)
      b.current?.removeEventListener('timeupdate', onTime)
    }
  }, [])

  return (
    <>
      <video ref={refs[0]} src={src} muted autoPlay playsInline loop preload="auto" tabIndex={-1} className={className} style={{ ...style, opacity }} />
      <video ref={refs[1]} src={src} muted playsInline loop preload="auto" tabIndex={-1} className={className} style={{ ...style, opacity: 0 }} />
    </>
  )
}