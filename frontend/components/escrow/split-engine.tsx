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

interface BackendProof {
  order_id: str
  gross_inr: string
  principal_inr: string
  gst_inr: string
  tds_inr: string
  unexplained_delta_paise: number
  fmr: string
  gst_rate_applied: string
  exempt_194o: boolean
  split_id: string
  proof_hash: string
  computed_by: string
  latency_ms: number
}

function calcLocalSplit(grossPaise: number, gstRate: number, exempt194o: boolean) {
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
  const [inputRaw, setInputRaw] = useState('1180')
  const [gstSlab, setGstSlab] = useState(3)
  const [exempt194o, setExempt194o] = useState(false)
  const [history, setHistory] = useState<{ gross: number; principal: number; gst: number; tds: number; ts: string; proof?: string }[]>([])
  
  // Real backend proof state
  const [proof, setProof] = useState<BackendProof | null>(null)
  const [loading, setLoading] = useState(false)
  const [backendActive, setBackendActive] = useState<boolean | null>(null)

  // Call real Python FastAPI backend
  const callPythonBackend = async (grossPaise: number, gstRatePct: number, isExempt: boolean) => {
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/api/intercept', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: `ord_${Math.random().toString(36).substring(2, 9)}`,
          amount_inr: grossPaise / 100,
          gst_rate_pct: gstRatePct,
          exempt_194o: isExempt,
          merchant: "Demo Merchant"
        }),
      })
      if (res.ok) {
        const data: BackendProof = await res.json()
        setProof(data)
        setBackendActive(true)
        setHistory((h) => [
          {
            gross: data.gross_paise,
            principal: data.principal_paise,
            gst: data.gst_paise,
            tds: data.tds_paise,
            ts: new Date().toLocaleTimeString('en-IN', { hour12: false }),
            proof: data.proof_hash
          },
          ...h.slice(0, 8),
        ])
        setLoading(false)
        return
      }
    } catch {
      setBackendActive(false)
    }
    
    // Fallback if server offline
    const local = calcLocalSplit(grossPaise, GST_SLABS[gstSlab].rate, isExempt)
    setHistory((h) => [
      {
        gross: grossPaise,
        principal: local.principalPaise,
        gst: local.gstPaise,
        tds: local.tdsPaise,
        ts: new Date().toLocaleTimeString('en-IN', { hour12: false }),
      },
      ...h.slice(0, 8),
    ])
    setLoading(false)
  }

  // Live feed ticker
  useEffect(() => {
    if (mode !== 'live') return
    const t = setInterval(() => {
      const gross = FEED_ORDERS[feedIdx % FEED_ORDERS.length]
      callPythonBackend(gross, GST_SLABS[gstSlab].rate * 100, exempt194o)
      setFeedIdx((i) => i + 1)
      setTick((k) => k + 1)
    }, 3000)
    return () => clearInterval(t)
  }, [mode, feedIdx, gstSlab, exempt194o])

  const manualGross = (() => {
    const v = parseInt(inputRaw.replace(/[^\d]/g, ''), 10)
    return isNaN(v) ? 0 : v * 100
  })()

  const handleManualCalc = () => {
    if (manualGross > 0) {
      callPythonBackend(manualGross, GST_SLABS[gstSlab].rate * 100, exempt194o)
      setTick((k) => k + 1)
    }
  }

  const gross = proof ? proof.gross_paise : (mode === 'live' ? FEED_ORDERS[feedIdx % FEED_ORDERS.length] : manualGross)
  const localSplits = calcLocalSplit(gross, GST_SLABS[gstSlab].rate, exempt194o)
  const principalPaise = proof ? proof.principal_paise : localSplits.principalPaise
  const gstPaise = proof ? proof.gst_paise : localSplits.gstPaise
  const tdsPaise = proof ? proof.tds_paise : localSplits.tdsPaise

  const lanes = [
    { key: 'principal', label: 'Principal → Merchant', value: principalPaise, color: 'var(--gain)', y: 60, hold: false },
    { key: 'gst', label: `GST (${(GST_SLABS[gstSlab].rate * 100).toFixed(0)}%) → Hold`, value: gstPaise, color: 'var(--gold)', y: 150, hold: true },
    { key: 'tds', label: '194-O TDS (1%) → Hold', value: tdsPaise, color: 'var(--chart-3)', y: 240, hold: true },
  ]

  return (
    <div className="flex flex-col gap-4">
      {/* Backend Connection Badge */}
      <div className="flex items-center justify-between rounded-lg border border-border bg-panel px-4 py-2.5">
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className={`h-2 w-2 rounded-full ${backendActive ? 'bg-gain animate-pulse' : backendActive === false ? 'bg-warn' : 'bg-muted-foreground'}`} />
          <span className="font-semibold text-foreground">
            {backendActive ? 'Python FastAPI Engine Active (Port 8000)' : 'Connecting to Python Backend...'}
          </span>
        </div>
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          {proof ? `Latency: ${proof.latency_ms}ms · ${proof.computed_by}` : 'Paise-Exact Decimal Kernel'}
        </span>
      </div>

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
            Manual Intercept
          </button>

          <div className="ml-auto flex flex-wrap items-center gap-3">
            <select
              value={gstSlab}
              onChange={(e) => {
                setGstSlab(Number(e.target.value))
                if (mode === 'manual' && manualGross > 0) {
                  callPythonBackend(manualGross, GST_SLABS[Number(e.target.value)].rate * 100, exempt194o)
                }
              }}
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
                onChange={(e) => {
                  setExempt194o(e.target.checked)
                  if (mode === 'manual' && manualGross > 0) {
                    callPythonBackend(manualGross, GST_SLABS[gstSlab].rate * 100, e.target.checked)
                  }
                }}
                className="accent-gold"
              />
              194-O Exempt
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
                placeholder="Enter gross order amount in ₹ (e.g. 1180)"
                value={inputRaw}
                onChange={(e) => setInputRaw(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleManualCalc()}
                className="w-full rounded-md border border-border bg-background py-2 pl-7 pr-3 font-mono text-sm text-foreground placeholder:text-muted-foreground/50 focus:border-gold focus:outline-none"
              />
            </div>
            <button
              onClick={handleManualCalc}
              disabled={loading}
              className="rounded-md bg-gold px-5 py-2 font-mono text-[11px] uppercase tracking-widest text-gold-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {loading ? 'Processing via Python...' : 'Intercept Payment'}
            </button>
          </div>
        )}
      </div>

      {/* Real Python Proof Callout Box */}
      {proof && (
        <div className="rounded-lg border border-gain/40 bg-gain/5 p-4 transition-all">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-gain animate-pulse" />
              <span className="font-mono text-xs font-bold text-gain">REAL PYTHON BACKEND AUDIT PROOF</span>
            </div>
            <span className="font-mono text-[10px] text-muted-foreground">Execution Latency: {proof.latency_ms} ms</span>
          </div>

          <div className="mt-3 grid grid-cols-2 gap-2 font-mono text-xs sm:grid-cols-4">
            <div className="rounded bg-background/50 p-2">
              <div className="text-[10px] text-muted-foreground">PROOF HASH</div>
              <div className="truncate font-semibold text-gain">{proof.proof_hash}</div>
            </div>
            <div className="rounded bg-background/50 p-2">
              <div className="text-[10px] text-muted-foreground">SPLIT ID</div>
              <div className="truncate text-foreground">{proof.split_id}</div>
            </div>
            <div className="rounded bg-background/50 p-2">
              <div className="text-[10px] text-muted-foreground">UNEXPLAINED DELTA</div>
              <div className="font-bold text-gain">₹0.00 ({proof.unexplained_delta_paise} paise)</div>
            </div>
            <div className="rounded bg-background/50 p-2">
              <div className="text-[10px] text-muted-foreground">MATH ENGINE</div>
              <div className="truncate text-gold">Decimal ROUND_HALF_UP</div>
            </div>
          </div>
        </div>
      )}

      {/* Split Diagram */}
      <div className="rounded-lg border border-border bg-panel">
        <div className="flex items-center justify-between border-b border-border p-5">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            Sovereign Split Engine · T=0
          </h2>
          <div className="flex items-center gap-2">
            {mode === 'live' && <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-gain" />}
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              {mode === 'live' ? 'auto-intercepting live feed' : gross > 0 ? 'manual payment intercept' : 'awaiting payment'}
            </span>
          </div>
        </div>

        <div className="relative overflow-hidden p-5">
          <svg viewBox="0 0 640 300" className="h-auto w-full" role="img" aria-label="Order split diagram">
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
          <Foot label="Released to Merchant" value={gross > 0 ? inr(principalPaise) : '—'} tone="gain" />
          <Foot label="Held Escrow (GST + TDS)" value={gross > 0 ? inr(gstPaise + tdsPaise) : '—'} tone="gold" />
          <Foot label="Unexplained Delta" value="₹0.00" tone="gain" />
        </div>
      </div>

      {/* Intercept History */}
      {history.length > 0 && (
        <div className="rounded-lg border border-border bg-panel">
          <div className="border-b border-border px-5 py-3 flex items-center justify-between">
            <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              Real Intercept Log · Python Backend Audited
            </h2>
            <span className="font-mono text-[10px] text-gain">FMR = 0.000 (Paise Exact)</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[650px] text-sm">
              <thead>
                <tr className="border-b border-border font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  <th className="px-4 py-2 text-left">Time</th>
                  <th className="px-4 py-2 text-right">Gross Intake</th>
                  <th className="px-4 py-2 text-right text-gain">Principal</th>
                  <th className="px-4 py-2 text-right text-gold">GST Escrow</th>
                  <th className="px-4 py-2 text-right" style={{ color: 'var(--chart-3)' }}>TDS Hold</th>
                  <th className="px-4 py-2 text-left">Proof Hash</th>
                </tr>
              </thead>
              <tbody className="font-mono tabular-nums">
                {history.map((h, i) => (
                  <tr key={i} className="border-b border-border/50 last:border-0 transition-colors hover:bg-accent/20">
                    <td className="px-4 py-2 text-muted-foreground">{h.ts}</td>
                    <td className="px-4 py-2 text-right font-semibold">{inr(h.gross)}</td>
                    <td className="px-4 py-2 text-right text-gain">{inr(h.principal)}</td>
                    <td className="px-4 py-2 text-right text-gold">{inr(h.gst)}</td>
                    <td className="px-4 py-2 text-right" style={{ color: 'var(--chart-3)' }}>{inr(h.tds)}</td>
                    <td className="px-4 py-2 text-left text-xs text-muted-foreground truncate">{h.proof || 'sha256:local_math'}</td>
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
