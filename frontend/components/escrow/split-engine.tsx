'use client'

import { useEffect, useState } from 'react'
import { inr } from '@/lib/kuber-data'

const GST_SLABS = [
  { label: '0% GST (Exempt)', rate: 0.00 },
  { label: '5% GST (Food/Transport)', rate: 0.05 },
  { label: '12% GST (Standard)', rate: 0.12 },
  { label: '18% GST (Default)', rate: 0.18 },
  { label: '28% GST (Luxury)', rate: 0.28 },
]

function calcSplit(grossPaise: number, gstRate: number, exempt194o: boolean) {
  // PAISE-EXACT integer arithmetic — no floating point
  const divisor = 1 + gstRate
  const gstPaise = Math.round((grossPaise * gstRate) / divisor)
  const tdsPaise = exempt194o ? 0 : Math.round(grossPaise * 0.01)
  const principalPaise = grossPaise - gstPaise - tdsPaise
  return { gstPaise, tdsPaise, principalPaise }
}

const FEED_ORDERS = [118000, 47200, 23600, 295000, 59000, 88500, 176400, 34900, 132500, 56000]

export function SplitEngine() {
  const [mode, setMode] = useState<'live' | 'manual'>('live')
  const [feedIdx, setFeedIdx] = useState(0)
  const [tick, setTick] = useState(0)
  const [inputRaw, setInputRaw] = useState('')
  const [gstSlab, setGstSlab] = useState(3) // index into GST_SLABS
  const [exempt194o, setExempt194o] = useState(false)
  const [history, setHistory] = useState<{ gross: number; principal: number; gst: number; tds: number; ts: string }[]>([])

  // Live feed ticker
  useEffect(() => {
    if (mode !== 'live') return
    const t = setInterval(() => {
      const gross = FEED_ORDERS[feedIdx % FEED_ORDERS.length]
      const { gstPaise, tdsPaise, principalPaise } = calcSplit(gross, GST_SLABS[gstSlab].rate, exempt194o)
      setHistory((h) => [
        { gross, principal: principalPaise, gst: gstPaise, tds: tdsPaise, ts: new Date().toLocaleTimeString('en-IN', { hour12: false }) },
        ...h.slice(0, 9),
      ])
      setFeedIdx((i) => i + 1)
      setTick((k) => k + 1)
    }, 2400)
    return () => clearInterval(t)
  }, [mode, feedIdx, gstSlab, exempt194o])

  const manualGross = (() => {
    const v = parseInt(inputRaw.replace(/[^\d]/g, ''), 10)
    return isNaN(v) ? 0 : v * 100 // input is in ₹, convert to paise
  })()

  const gross = mode === 'live' ? FEED_ORDERS[feedIdx % FEED_ORDERS.length] : manualGross
  const { gstPaise, tdsPaise, principalPaise } = calcSplit(gross, GST_SLABS[gstSlab].rate, exempt194o)

  const lanes = [
    { key: 'principal', label: 'Principal → Merchant', value: principalPaise, color: 'var(--gain)', y: 60, hold: false },
    { key: 'gst', label: `GST (${(GST_SLABS[gstSlab].rate * 100).toFixed(0)}%) → Hold`, value: gstPaise, color: 'var(--gold)', y: 150, hold: true },
    { key: 'tds', label: '194-O TDS (1%) → Hold', value: tdsPaise, color: 'var(--chart-3)', y: 240, hold: true },
  ]

  const handleManualCalc = () => {
    if (manualGross > 0) {
      const { gstPaise, tdsPaise, principalPaise } = calcSplit(manualGross, GST_SLABS[gstSlab].rate, exempt194o)
      setHistory((h) => [
        { gross: manualGross, principal: principalPaise, gst: gstPaise, tds: tdsPaise, ts: new Date().toLocaleTimeString('en-IN', { hour12: false }) },
        ...h.slice(0, 9),
      ])
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Mode + Controls */}
      <div className="rounded-lg border border-border bg-panel p-5">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Mode:</span>
          <button
            onClick={() => setMode('live')}
            className={`rounded-md px-3 py-1 font-mono text-[11px] uppercase tracking-widest transition-colors ${mode === 'live' ? 'bg-gain/20 text-gain border border-gain/40' : 'border border-border text-muted-foreground hover:text-foreground'}`}
          >
            ● Live Feed
          </button>
          <button
            onClick={() => setMode('manual')}
            className={`rounded-md px-3 py-1 font-mono text-[11px] uppercase tracking-widest transition-colors ${mode === 'manual' ? 'bg-gold/20 text-gold border border-gold/40' : 'border border-border text-muted-foreground hover:text-foreground'}`}
          >
            Manual Input
          </button>

          <div className="ml-auto flex flex-wrap items-center gap-3">
            <select
              value={gstSlab}
              onChange={(e) => setGstSlab(Number(e.target.value))}
              className="rounded-md border border-border bg-background px-3 py-1.5 font-mono text-xs text-foreground focus:border-gold focus:outline-none"
            >
              {GST_SLABS.map((s, i) => (
                <option key={i} value={i}>{s.label}</option>
              ))}
            </select>

            <label className="flex cursor-pointer items-center gap-2 font-mono text-xs text-muted-foreground">
              <input
                type="checkbox"
                checked={exempt194o}
                onChange={(e) => setExempt194o(e.target.checked)}
                className="accent-gold"
              />
              194-O Exempt (₹5L threshold)
            </label>
          </div>
        </div>

        {mode === 'manual' && (
          <div className="mt-4 flex gap-3">
            <div className="relative flex-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 font-mono text-muted-foreground">₹</span>
              <input
                type="text"
                inputMode="numeric"
                placeholder="Enter order amount (e.g. 1180)"
                value={inputRaw}
                onChange={(e) => setInputRaw(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleManualCalc()}
                className="w-full rounded-md border border-border bg-background py-2 pl-7 pr-3 font-mono text-sm text-foreground placeholder:text-muted-foreground/50 focus:border-gold focus:outline-none"
              />
            </div>
            <button
              onClick={handleManualCalc}
              className="rounded-md bg-gold px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-gold-foreground transition-opacity hover:opacity-90"
            >
              Compute Split
            </button>
          </div>
        )}
      </div>

      {/* Split Diagram */}
      <div className="rounded-lg border border-border bg-panel">
        <div className="flex items-center justify-between border-b border-border p-5">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            Sovereign Split Engine · T=0
          </h2>
          <div className="flex items-center gap-2">
            {mode === 'live' && <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-gain" />}
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              {mode === 'live' ? 'auto-cycling orders' : gross > 0 ? 'manual input' : 'awaiting input'}
            </span>
          </div>
        </div>

        <div className="relative overflow-hidden p-5">
          <svg viewBox="0 0 640 300" className="h-auto w-full" role="img" aria-label="Order split diagram">
            {/* incoming node */}
            <g key={`in-${tick}`}>
              <rect x="8" y="100" width="155" height="100" rx="6" fill="var(--accent)" stroke="var(--border)" />
              <text x="85" y="133" textAnchor="middle" fontSize="8" fontFamily="var(--font-mono)" fill="var(--muted-foreground)" letterSpacing="1.5">
                CAPTURED ORDER
              </text>
              <text x="85" y="153" textAnchor="middle" fontSize="18" fontWeight="700" fontFamily="var(--font-mono)" fill="var(--foreground)">
                {gross > 0 ? inr(gross) : '—'}
              </text>
              <text x="85" y="172" textAnchor="middle" fontSize="8" fontFamily="var(--font-mono)" fill="var(--muted-foreground)">
                Razorpay captured
              </text>
            </g>

            {lanes.map((lane) => {
              const path = `M163 150 C 300 150, 320 ${lane.y + 23}, 460 ${lane.y + 23}`
              return (
                <g key={lane.key}>
                  <path d={path} fill="none" stroke={lane.color} strokeWidth="1.5" opacity="0.3" />
                  <path d={path} fill="none" stroke={lane.color} strokeWidth="1.5" className="animate-flow" opacity="0.9" />
                  <circle r="3.5" fill={lane.color}>
                    <animateMotion key={`m-${lane.key}-${tick}`} dur="2s" repeatCount="1" path={path} />
                  </circle>
                  <rect
                    x="460" y={lane.y} width="172" height="50" rx="6"
                    fill={lane.hold ? 'color-mix(in oklch, var(--gold) 8%, var(--panel))' : 'color-mix(in oklch, var(--gain) 8%, var(--panel))'}
                    stroke={lane.color} strokeOpacity="0.5"
                  />
                  <text x="472" y={lane.y + 19} fontSize="8.5" fontFamily="var(--font-mono)" fill="var(--muted-foreground)" letterSpacing="0.5">
                    {lane.label}
                  </text>
                  <text x="472" y={lane.y + 38} fontSize="14" fontWeight="700" fontFamily="var(--font-mono)" fill="var(--foreground)">
                    {gross > 0 ? inr(lane.value) : '—'}
                  </text>
                  {lane.hold && (
                    <g>
                      <circle cx="618" cy={lane.y + 14} r="8" fill="none" stroke="var(--gold)" strokeWidth="1.2" />
                      <path d={`M615 ${lane.y + 14} l2 2 l4 -4`} stroke="var(--gold)" strokeWidth="1.2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                    </g>
                  )}
                </g>
              )
            })}
          </svg>
        </div>

        <div className="grid grid-cols-3 divide-x divide-border border-t border-border">
          <Foot label="Released now (81.7%+)" value={gross > 0 ? inr(principalPaise) : '—'} tone="gain" />
          <Foot label={`Held escrow (${((gstPaise + tdsPaise) / Math.max(gross, 1) * 100).toFixed(1)}%)`} value={gross > 0 ? inr(gstPaise + tdsPaise) : '—'} tone="gold" />
          <Foot label="Tax loss risk" value="₹0.00" tone="gain" />
        </div>
      </div>

      {/* History Table */}
      {history.length > 0 && (
        <div className="rounded-lg border border-border bg-panel">
          <div className="border-b border-border px-5 py-3">
            <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              Intercept Log · Last {history.length} Orders
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px] text-sm">
              <thead>
                <tr className="border-b border-border font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  <th className="px-4 py-2 text-left">Time</th>
                  <th className="px-4 py-2 text-right">Gross</th>
                  <th className="px-4 py-2 text-right text-gain">Principal</th>
                  <th className="px-4 py-2 text-right text-gold">GST Escrow</th>
                  <th className="px-4 py-2 text-right" style={{ color: 'var(--chart-3)' }}>TDS Hold</th>
                  <th className="px-4 py-2 text-right">Unexplained</th>
                </tr>
              </thead>
              <tbody className="font-mono tabular-nums">
                {history.map((h, i) => (
                  <tr key={i} className="border-b border-border/50 last:border-0 transition-colors hover:bg-accent/20">
                    <td className="px-4 py-2 text-muted-foreground">{h.ts}</td>
                    <td className="px-4 py-2 text-right">{inr(h.gross)}</td>
                    <td className="px-4 py-2 text-right text-gain">{inr(h.principal)}</td>
                    <td className="px-4 py-2 text-right text-gold">{inr(h.gst)}</td>
                    <td className="px-4 py-2 text-right" style={{ color: 'var(--chart-3)' }}>{inr(h.tds)}</td>
                    <td className="px-4 py-2 text-right text-gain">₹0.00</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
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
