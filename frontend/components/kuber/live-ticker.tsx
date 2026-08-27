'use client'

import { useEffect, useRef, useState } from 'react'

/**
 * LiveTicker — shows a number counting up/down with an "updating" flash.
 * Purely visual. Makes static stat tiles feel alive.
 */
export function LiveTicker({
  value,
  prefix = '',
  suffix = '',
  className = '',
}: {
  value: number
  prefix?: string
  suffix?: string
  className?: string
}) {
  const [display, setDisplay] = useState(value)
  const [flash, setFlash] = useState(false)
  const prev = useRef(value)

  useEffect(() => {
    if (value === prev.current) return
    setFlash(true)
    const duration = 600
    const start = prev.current
    const diff = value - start
    const startTime = performance.now()
    const step = (now: number) => {
      const t = Math.min((now - startTime) / duration, 1)
      const eased = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
      setDisplay(Math.round(start + diff * eased))
      if (t < 1) requestAnimationFrame(step)
      else {
        setDisplay(value)
        setTimeout(() => setFlash(false), 200)
      }
    }
    requestAnimationFrame(step)
    prev.current = value
  }, [value])

  return (
    <span
      className={`inline-block font-mono tabular-nums transition-colors duration-200 ${flash ? 'text-gold' : ''} ${className}`}
    >
      {prefix}{display.toLocaleString('en-IN')}{suffix}
    </span>
  )
}

/**
 * PulseRow — a data row that briefly highlights when its value changes.
 */
export function PulseRow({
  children,
  trigger,
}: {
  children: React.ReactNode
  trigger: unknown
}) {
  const [pulse, setPulse] = useState(false)
  const first = useRef(true)

  useEffect(() => {
    if (first.current) { first.current = false; return }
    setPulse(true)
    const t = setTimeout(() => setPulse(false), 700)
    return () => clearTimeout(t)
  }, [trigger])

  return (
    <tr
      className={`border-b border-border/60 last:border-0 transition-colors ${pulse ? 'bg-gold/10' : 'hover:bg-accent/30'}`}
    >
      {children}
    </tr>
  )
}
