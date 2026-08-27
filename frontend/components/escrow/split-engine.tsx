'use client'

import { useEffect, useState } from 'react'
import { inr } from '@/lib/kuber-data'

const LANES = [
  { key: 'principal', label: 'Principal → Merchant', pct: 0.817, color: 'var(--gain)', y: 60, hold: false },
  { key: 'gst', label: 'GST Escrow (18%) → Hold', pct: 0.153, color: 'var(--gold)', y: 150, hold: true },
  { key: 'tds', label: 'TDS Escrow (1%) → Hold', pct: 0.03, color: 'var(--chart-3)', y: 240, hold: true },
]

const SAMPLE_ORDERS = [118000, 47200, 23600, 295000, 59000, 88500, 176400, 34900]

export function SplitEngine() {
  const [idx, setIdx] = useState(0)
  const [tick, setTick] = useState(0)

  useEffect(() => {
    const t = setInterval(() => {
      setIdx((i) => (i + 1) % SAMPLE_ORDERS.length)
      setTick((k) => k + 1)
    }, 2600)
    return () => clearInterval(t)
  }, [])

  const gross = SAMPLE_ORDERS[idx]

  return (
    <div className="rounded-lg border border-border bg-panel">
      <div className="flex items-center justify-between border-b border-border p-5">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
          Sovereign Split Engine · T=0
        </h2>
        <div className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-gain" />
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            preventative control
          </span>
        </div>
      </div>

      <div className="relative overflow-hidden p-5">
        <svg viewBox="0 0 640 300" className="h-auto w-full" role="img" aria-label="Order split diagram">
          {/* incoming node */}
          <g key={`in-${tick}`}>
            <rect x="8" y="120" width="150" height="60" rx="6" fill="var(--accent)" stroke="var(--border)" />
            <text x="83" y="145" textAnchor="middle" className="fill-muted-foreground" fontSize="9" fontFamily="var(--font-mono)" letterSpacing="1.5">
              INCOMING ORDER
            </text>
            <text x="83" y="167" textAnchor="middle" className="fill-foreground" fontSize="15" fontWeight="600" fontFamily="var(--font-mono)">
              {inr(gross)}
            </text>
          </g>

          {LANES.map((lane) => {
            const path = `M158 150 C 300 150, 320 ${lane.y + 20}, 460 ${lane.y + 20}`
            return (
              <g key={lane.key}>
                <path d={path} fill="none" stroke={lane.color} strokeWidth="1.5" opacity="0.35" />
                <path d={path} fill="none" stroke={lane.color} strokeWidth="1.5" className="animate-flow" opacity="0.9" />
                {/* travelling packet */}
                <circle r="3.5" fill={lane.color}>
                  <animateMotion key={`m-${lane.key}-${tick}`} dur="2.2s" repeatCount="1" path={path} />
                </circle>

                {/* destination */}
                <rect
                  x="460"
                  y={lane.y}
                  width="172"
                  height="46"
                  rx="6"
                  fill={lane.hold ? 'color-mix(in oklch, var(--gold) 8%, var(--panel))' : 'color-mix(in oklch, var(--gain) 8%, var(--panel))'}
                  stroke={lane.color}
                  strokeOpacity="0.5"
                />
                <text x="472" y={lane.y + 19} className="fill-foreground" fontSize="9.5" fontFamily="var(--font-mono)" letterSpacing="0.5">
                  {lane.label}
                </text>
                <text x="472" y={lane.y + 35} className="fill-foreground" fontSize="13" fontWeight="600" fontFamily="var(--font-mono)">
                  {inr(Math.round(gross * lane.pct))}
                </text>
                {lane.hold && (
                  <g>
                    <circle cx="618" cy={lane.y + 12} r="7" fill="none" stroke="var(--gold)" strokeWidth="1.2" />
                    <path d={`M615 ${lane.y + 12} l2 2 l4 -4`} stroke="var(--gold)" strokeWidth="1.2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                  </g>
                )}
              </g>
            )
          })}
        </svg>
      </div>

      <div className="grid grid-cols-3 divide-x divide-border border-t border-border">
        <Foot label="Released now" value={inr(Math.round(gross * 0.817))} tone="gain" />
        <Foot label="Held to 14th" value={inr(Math.round(gross * 0.183))} tone="gold" />
        <Foot label="Loss risk" value="₹0" tone="gain" />
      </div>
    </div>
  )
}

function Foot({ label, value, tone }: { label: string; value: string; tone: 'gain' | 'gold' }) {
  return (
    <div className="p-4">
      <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className={`mt-1 font-mono text-base font-semibold ${tone === 'gain' ? 'text-gain' : 'text-gold'}`}>
        {value}
      </div>
    </div>
  )
}
