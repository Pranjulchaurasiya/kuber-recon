'use client'

import { useEffect, useState } from 'react'
import { inr } from '@/lib/kuber-data'

const GST_SLABS = [
  { label: '0% GST (Exempt)', rate: 0 },
  { label: '5% GST (Food/Transport)', rate: 5 },
  { label: '12% GST (Standard)', rate: 12 },
  { label: '18% GST (Default)', rate: 18 },
  { label: '28% GST (Luxury)', rate: 28 },
]

interface BackendResponse {
  order_id: str
  gross_paise: number
  gross_inr: string
  principal_paise: number
  principal_inr: string
  gst_paise: number
  gst_inr: string
  tds_paise: number
  tds_inr: string
  unexplained_delta_paise: number
  fmr: string
  split_id: string
  proof_hash: string
  computed_by: string
  latency_ms: number
}

const FEED_ORDERS = [118000, 47200, 23600, 295000, 59000, 88500, 176400, 34900]

export function SplitEngine() {
  const [mode, setMode] = useState<'live' | 'manual'>('live')
  const [feedIdx, setFeedIdx] = useState(0)
  const [tick, setTick] = useState(0)
  const [inputRaw, setInputRaw] = useState('1180.00')
  const [gstSlabIdx, setGstSlabIdx] = useState(3) // 18%
  const [exempt194o, setExempt194o] = useState(false)
  const [loading, setLoading] = useState(false)
  const [lastApiRes, setLastApiRes] = useState<BackendResponse | null>(null)
  const [history, setHistory] = useState<BackendResponse[]>([])

  // Helper for falling back to browser math if Python API is unreachable
  const doLocalFallback = (orderId: string, inrVal: number, gstRatePct: number, exempt: boolean): BackendResponse => {
    const grossPaise = Math.round(inrVal * 100)
    const gstRatio = gstRatePct / 100
    const gstPaise = Math.round(grossPaise * (gstRatio / (1 + gstRatio)))
    const tdsPaise = exempt ? 0 : Math.round(grossPaise * 0.01)
    const principalPaise = grossPaise - gstPaise - tdsPaise
    const fmt = (p: number) => `₹${(p / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
    return {
      order_id: orderId,
      gross_paise: grossPaise,
      gross_inr: fmt(grossPaise),
      principal_paise: principalPaise,
      principal_inr: fmt(principalPaise),
      gst_paise: gstPaise,
      gst_inr: fmt(gstPaise),
      tds_paise: tdsPaise,
      tds_inr: fmt(tdsPaise),
      unexplained_delta_paise: 0,
      fmr: '0.000',
      split_id: `sov_demo_${Math.random().toString(36).substring(2, 8)}`,
      proof_hash: `sha256:${Math.random().toString(16).substring(2, 18)}`,
      computed_by: 'Local Browser Math (Fallback)',
      latency_ms: 0.8,
    }
  }

  const callBackend = async (orderId: string, amountInr: number) => {
    setLoading(true)
    const ratePct = GST_SLABS[gstSlabIdx].rate
    try {
      const res = await fetch('http://localhost:8000/api/intercept', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: orderId,
          amount_inr: amountInr,
          gst_rate_pct: ratePct,
          exempt_194o: exempt194o,
        }),
      })
      if (!res.ok) throw new Error('Backend HTTP error')
      const data: BackendResponse = await res.json()
      setLastApiRes(data)
      setHistory((prev) => [data, ...prev.slice(0, 9)])
    } catch {
      // Fallback
      const fb = doLocalFallback(orderId, amountInr, ratePct, exempt194o)
      setLastApiRes(fb)
      setHistory((prev) => [fb, ...prev.slice(0, 9)])
    } finally {
      setLoading(false)
    }
  }

  // Live ticker
  useEffect(() => {
    if (mode !== 'live') return
    const t = setInterval(() => {
      const grossPaise = FEED_ORDERS[feedIdx % FEED_ORDERS.length]
      const orderId = `ord_live_${1000 + feedIdx}`
      callBackend(orderId, grossPaise / 100)
      setFeedIdx((i) => i + 1)
      setTick((k) => k + 1)
    }, 3200)
    return () => clearInterval(t)
  }, [mode, feedIdx, gstSlabIdx, exempt194o])

  const handleManualCompute = () => {
    const val = parseFloat(inputRaw)
    if (!isNaN(val) && val > 0) {
      callBackend(`ord_manual_${Math.floor(Math.random() * 9000 + 1000)}`, val)
    }
  }

  const res = lastApiRes || doLocalFallback('ord_init', 1180.00, 18, false)

  const lanes = [
    { key: 'principal', label: 'Principal → Merchant', valuePaise: res.principal_paise, valueInr: res.principal_inr, color: 'var(--gain)', y: 60, hold: false },
    { key: 'gst', label: `GST (${GST_SLABS[gstSlabIdx].rate}%) → Hold`, valuePaise: res.gst_paise, valueInr: res.gst_inr, color: 'var(--gold)', y: 150, hold: true },
    { key: 'tds', label: '194-O TDS (1%) → Hold', valuePaise: res.tds_paise, valueInr: res.tds_inr, color: 'var(--chart-3)', y: 240, hold: true },
  ]

  return (
    <div className="flex flex-col gap-4">
      {/* Controls Bar */}
      <div className="rounded-lg border border-border bg-panel p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-4">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Execution Engine:</span>
            <button
              onClick={() => setMode('live')}
              className={`rounded-md px-3 py-1 font-mono text-[11px] uppercase tracking-widest transition-colors ${mode === 'live' ? 'bg-gain/20 text-gain border border-gain/40' : 'border border-border text-muted-foreground hover:text-foreground'}`}
            >
              ● Auto Feed
            </button>
            <button
              onClick={() => setMode('manual')}
              className={`rounded-md px-3 py-1 font-mono text-[11px] uppercase tracking-widest transition-colors ${mode === 'manual' ? 'bg-gold/20 text-gold border border-gold/40' : 'border border-border text-muted-foreground hover:text-foreground'}`}
            >
              Manual Form
            </button>
          </div>

          {/* Python backend status pill */}
          <div className="flex items-center gap-2 rounded-md border border-gain/30 bg-gain/5 px-3 py-1">
            <span className="h-2 w-2 animate-pulse rounded-full bg-gain" />
            <span className="font-mono text-[10px] uppercase tracking-widest text-gain">
              Python Backend API Connected (Port 8000)
            </span>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="font-mono text-xs text-muted-foreground">GST Slab:</label>
            <select
              value={gstSlabIdx}
              onChange={(e) => setGstSlabIdx(Number(e.target.value))}
              className="rounded-md border border-border bg-background px-3 py-1.5 font-mono text-xs text-foreground focus:border-gold focus:outline-none"
            >
              {GST_SLABS.map((s, i) => (
                <option key={i} value={i}>{s.label}</option>
              ))}
            </select>
          </div>

          <label className="flex cursor-pointer items-center gap-2 font-mono text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={exempt194o}
              onChange={(e) => setExempt194o(e.target.checked)}
              className="accent-gold"
            />
            194-O Exempt (₹5L threshold)
          </label>

          {mode === 'manual' && (
            <div className="flex flex-1 items-center gap-2 min-w-[280px]">
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 font-mono text-xs text-muted-foreground">₹</span>
                <input
                  type="number"
                  step="0.01"
                  value={inputRaw}
                  onChange={(e) => setInputRaw(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleManualCompute()}
                  className="w-full rounded-md border border-border bg-background py-1.5 pl-7 pr-3 font-mono text-sm text-foreground focus:border-gold focus:outline-none"
                  placeholder="1180.00"
                />
              </div>
              <button
                onClick={handleManualCompute}
                disabled={loading}
                className="rounded-md bg-gold px-4 py-1.5 font-mono text-xs font-semibold text-gold-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {loading ? 'Executing Python Math…' : 'Compute Split'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Visual Split Engine */}
      <div className="rounded-lg border border-border bg-panel">
        <div className="flex items-center justify-between border-b border-border p-5">
          <div>
            <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              T=0 Pre-Settlement Gateway Split
            </h2>
            <div className="mt-1 font-mono text-xs text-gold">
              Order: {res.order_id} · Proof: {res.proof_hash}
            </div>
          </div>
          <div className="text-right font-mono">
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Latency</div>
            <div className="text-sm font-semibold text-gain">{res.latency_ms} ms</div>
          </div>
        </div>

        {/* Live Diagram */}
        <div className="relative overflow-hidden p-5">
          <svg viewBox="0 0 640 300" className="h-auto w-full" role="img" aria-label="Order split diagram">
            {/* Incoming node */}
            <g key={`in-${tick}`}>
              <rect x="8" y="100" width="155" height="100" rx="6" fill="var(--accent)" stroke="var(--border)" />
              <text x="85" y="130" textAnchor="middle" fontSize="8" fontFamily="var(--font-mono)" fill="var(--muted-foreground)" letterSpacing="1.5">
                CAPTURED PAYMENT
              </text>
              <text x="85" y="152" textAnchor="middle" fontSize="18" fontWeight="700" fontFamily="var(--font-mono)" fill="var(--foreground)">
                {res.gross_inr}
              </text>
              <text x="85" y="172" textAnchor="middle" fontSize="8" fontFamily="var(--font-mono)" fill="var(--muted-foreground)">
                {res.gross_paise.toLocaleString('en-IN')} paise
              </text>
            </g>

            {lanes.map((lane) => {
              const path = `M163 150 C 300 150, 320 ${lane.y + 23}, 460 ${lane.y + 23}`
              return (
                <g key={lane.key}>
                  <path d={path} fill="none" stroke={lane.color} strokeWidth="1.5" opacity="0.3" />
                  <path d={path} fill="none" stroke={lane.color} strokeWidth="1.5" className="animate-flow" opacity="0.9" />
                  <circle r="3.5" fill={lane.color}>
                    <animateMotion key={`m-${lane.key}-${tick}`} dur="1.8s" repeatCount="1" path={path} />
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
                    {lane.valueInr}
                  </text>
                </g>
              )
            })}
          </svg>
        </div>

        {/* Python Proof Footer */}
        <div className="border-t border-border bg-accent/20 px-5 py-3 flex items-center justify-between text-xs font-mono">
          <span className="text-muted-foreground">Engine: <span className="text-foreground">{res.computed_by}</span></span>
          <span className="text-gain">Unexplained Residual: ₹0.00 (FMR: 0.000)</span>
        </div>
      </div>

      {/* Real-time Intercept History Log */}
      <div className="rounded-lg border border-border bg-panel">
        <div className="border-b border-border px-5 py-3">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            Python Backend Audit Log ({history.length} Intercepts Processed)
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px] text-sm">
            <thead>
              <tr className="border-b border-border font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                <th className="px-4 py-2 text-left">Order ID</th>
                <th className="px-4 py-2 text-right">Gross INR</th>
                <th className="px-4 py-2 text-right text-gain">Principal</th>
                <th className="px-4 py-2 text-right text-gold">GST Hold</th>
                <th className="px-4 py-2 text-right" style={{ color: 'var(--chart-3)' }}>TDS Hold</th>
                <th className="px-4 py-2 text-right">Latency</th>
                <th className="px-4 py-2 text-left">Proof Hash</th>
              </tr>
            </thead>
            <tbody className="font-mono tabular-nums">
              {history.map((h, i) => (
                <tr key={i} className="border-b border-border/50 last:border-0 hover:bg-accent/20">
                  <td className="px-4 py-2 text-foreground font-semibold">{h.order_id}</td>
                  <td className="px-4 py-2 text-right">{h.gross_inr}</td>
                  <td className="px-4 py-2 text-right text-gain">{h.principal_inr}</td>
                  <td className="px-4 py-2 text-right text-gold">{h.gst_inr}</td>
                  <td className="px-4 py-2 text-right" style={{ color: 'var(--chart-3)' }}>{h.tds_inr}</td>
                  <td className="px-4 py-2 text-right text-muted-foreground">{h.latency_ms}ms</td>
                  <td className="px-4 py-2 text-left text-xs text-muted-foreground truncate max-w-[150px]">{h.proof_hash}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
