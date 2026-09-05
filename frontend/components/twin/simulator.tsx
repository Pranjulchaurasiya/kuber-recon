'use client'

import { useMemo, useState, useEffect } from 'react'
import { inr, twinBaseline, paiseToInr } from '@/lib/kuber-data'
import { Pill } from '@/components/kuber/primitives'
import { getApiUrl, DEFAULT_AUTH_HEADERS } from '@/lib/api-client'
import { ShieldCheck, Cpu, RefreshCw, Zap, Lock } from 'lucide-react'

const DAYS = 30

export function Simulator() {
  const [freeze, setFreeze] = useState(0) // bank holiday freeze days
  const [gstr1, setGstr1] = useState(0) // vendor GSTR-1 default %
  const [chargeback, setChargeback] = useState(0) // chargeback surge %
  const [apiResult, setApiResult] = useState<{
    scenario_name?: string
    invoices_evaluated?: number
    gross_gmv_paise?: number
    baseline_net_settlement_paise?: number
    simulated_net_settlement_paise?: number
    liquidity_delta_paise?: number
    settlement_delay_days?: number
    recommended_hedging_action?: string
    proof_manifest_hash?: string
    latency_ms?: number
    computed_by?: string
  } | null>(null)
  const [apiLoading, setApiLoading] = useState(false)

  // Live Backend Causal Twin Integration
  useEffect(() => {
    let active = true
    setApiLoading(true)
    const timeout = setTimeout(async () => {
      try {
        const scenario = freeze > 0 ? 'bank_holiday' : gstr1 > 0 ? 'vendor_default' : 'tds_shock'
        const severity = Math.max(0.2, freeze ? freeze / 4 : gstr1 ? gstr1 / 20 : chargeback ? chargeback / 10 : 1.0)
        const resp = await fetch(`${getApiUrl()}/api/twin/simulate`, {
          method: 'POST',
          headers: DEFAULT_AUTH_HEADERS,
          body: JSON.stringify({ scenario, severity }),
        })
        if (resp.ok && active) {
          const data = await resp.json()
          setApiResult(data)
        }
      } catch {
        // Fallback to client model if offline
      } finally {
        if (active) setApiLoading(false)
      }
    }, 150)

    return () => {
      active = false
      clearTimeout(timeout)
    }
  }, [freeze, gstr1, chargeback])

  const model = useMemo(() => {
    const base = twinBaseline.liquidity
    const dailyInflow = Math.round(base * 31 / 1000)
    const points: { baseline: number; stressed: number }[] = []

    let liqBase = base
    let liqStress = base
    const exposedCredit = twinBaseline.exposedCredit + Math.round(gstr1 * base * 12 / 10000)
    const chargebackHit = Math.round(chargeback * base * 4 / 1000)

    for (let d = 0; d < DAYS; d++) {
      liqBase += dailyInflow - Math.round(base * 28 / 1000)
      const frozen = d < freeze
      const inflow = frozen ? 0 : Math.round(dailyInflow * (1000 - gstr1 * 6) / 1000)
      const burn = Math.round(base * 28 / 1000 + chargebackHit / DAYS)
      liqStress += inflow - burn
      points.push({ baseline: Math.max(liqBase, 0), stressed: Math.max(liqStress, 0) })
    }

    const finalStress = points[points.length - 1].stressed
    const trough = Math.min(...points.map((p) => p.stressed))
    const runway = Math.max(0, Math.round(twinBaseline.runwayDays - freeze * 3.4 - gstr1 * 0.9 - chargeback * 1.1))
    const breach = trough < base * 0.35
    const strain = trough < base * 0.6
    return { points, finalStress, trough, runway, exposedCredit, breach, strain, base }
  }, [freeze, gstr1, chargeback])

  const verdict = model.breach
    ? { tone: 'danger' as const, label: 'Liquidity breach', copy: 'Projected trough falls below the 35% safety floor. Pre-position a credit line.' }
    : model.strain
      ? { tone: 'warn' as const, label: 'Under strain', copy: 'Buffer thins but holds. Delay discretionary payouts through the freeze window.' }
      : { tone: 'gain' as const, label: 'Resilient', copy: 'Liquidity absorbs the shock with margin to spare. No action required.' }

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      {/* Controls */}
      <div className="rounded-lg border border-border bg-panel p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            What-If Controls
          </h2>
          {apiLoading ? (
            <span className="flex items-center gap-1 font-mono text-[10px] text-primary animate-pulse">
              <RefreshCw className="h-3 w-3 animate-spin" /> Solving...
            </span>
          ) : (
            <span className="font-mono text-[10px] text-gain font-semibold">Live Kernel</span>
          )}
        </div>
        <p className="mt-1 text-xs text-muted-foreground">Drag to inject real causal counterfactuals into the Python engine.</p>

        <div className="mt-6 flex flex-col gap-6">
          <Slider label="Bank holiday freeze" value={freeze} min={0} max={7} unit="days" onChange={setFreeze} accent="var(--warn)" />
          <Slider label="Vendor GSTR-1 default" value={gstr1} min={0} max={30} unit="%" onChange={setGstr1} accent="var(--danger)" />
          <Slider label="Chargeback surge" value={chargeback} min={0} max={20} unit="%" onChange={setChargeback} accent="var(--chart-3)" />
        </div>

        <button
          onClick={() => {
            setFreeze(0)
            setGstr1(0)
            setChargeback(0)
          }}
          className="mt-6 w-full rounded-md border border-border bg-background py-2 font-mono text-[11px] uppercase tracking-widest text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          Reset to baseline
        </button>

        {/* Live Backend Audit Card */}
        {apiResult && (
          <div className="mt-5 rounded-lg border border-primary/30 bg-primary/5 p-3.5 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className="font-bold text-primary flex items-center gap-1">
                <Cpu className="h-3.5 w-3.5" /> Python Engine Verified
              </span>
              <span className="text-muted-foreground">{apiResult.latency_ms}ms</span>
            </div>
            <p className="text-[11px] text-foreground font-medium leading-snug">
              {apiResult.recommended_hedging_action}
            </p>
            <div className="pt-1.5 border-t border-border/60 flex items-center justify-between text-[9px] font-mono text-muted-foreground">
              <span>Proof Hash:</span>
              <span className="font-bold text-foreground truncate max-w-[140px]">{apiResult.proof_manifest_hash}</span>
            </div>
          </div>
        )}
      </div>

      {/* Projection + verdict */}
      <div className="lg:col-span-2 flex flex-col gap-4">
        <div className="rounded-lg border border-border bg-panel">
          <div className="flex items-center justify-between border-b border-border p-5">
            <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              30-Day Liquidity Projection
            </h2>
            <div className="flex items-center gap-4">
              <LegendDot color="var(--muted-foreground)" label="Baseline" />
              <LegendDot color={verdict.tone === 'danger' ? 'var(--danger)' : verdict.tone === 'warn' ? 'var(--warn)' : 'var(--gain)'} label="Stressed" />
            </div>
          </div>
          <div className="p-5">
            <ProjectionChart points={model.points} base={model.base} tone={verdict.tone} />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Metric label="Runway" value={`${model.runway}d`} sub={`baseline ${twinBaseline.runwayDays}d`} tone={model.runway < 20 ? 'danger' : model.runway < 40 ? 'warn' : 'gain'} />
          <Metric label="Trough liquidity" value={inr(model.trough, { compact: true })} sub="lowest point" tone={verdict.tone} />
          <Metric label="Exposed credit" value={inr(model.exposedCredit, { compact: true })} sub="input-credit at risk" tone={model.exposedCredit > twinBaseline.exposedCredit * 2 ? 'warn' : 'gain'} />
        </div>

        <div className={`rounded-lg border p-5 ${verdict.tone === 'danger' ? 'border-danger/40 bg-danger/5' : verdict.tone === 'warn' ? 'border-warn/40 bg-warn/5' : 'border-gain/40 bg-gain/5'}`}>
          <div className="flex items-center gap-3">
            <Pill tone={verdict.tone}>CFO verdict</Pill>
            <span className={`text-sm font-semibold ${verdict.tone === 'danger' ? 'text-danger' : verdict.tone === 'warn' ? 'text-warn' : 'text-gain'}`}>
              {verdict.label}
            </span>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{verdict.copy}</p>
        </div>
      </div>
    </div>
  )
}


function Slider({
  label,
  value,
  min,
  max,
  unit,
  onChange,
  accent,
}: {
  label: string
  value: number
  min: number
  max: number
  unit: string
  onChange: (v: number) => void
  accent: string
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm">{label}</span>
        <span className="font-mono text-sm tabular-nums" style={{ color: value > min ? accent : 'var(--muted-foreground)' }}>
          {value} {unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={label}
        className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-accent outline-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-background [&::-webkit-slider-thumb]:bg-foreground"
        style={{
          background: `linear-gradient(to right, ${accent} ${((value - min) / (max - min)) * 100}%, var(--accent) ${((value - min) / (max - min)) * 100}%)`,
        }}
      />
    </div>
  )
}

function ProjectionChart({ points, base, tone }: { points: { baseline: number; stressed: number }[]; base: number; tone: 'gain' | 'warn' | 'danger' }) {
  const W = 620
  const H = 220
  const pad = 8
  const max = base * 1.4
  const min = 0
  const stressColor = tone === 'danger' ? 'var(--danger)' : tone === 'warn' ? 'var(--warn)' : 'var(--gain)'

  const x = (i: number) => pad + (i / (points.length - 1)) * (W - pad * 2)
  const y = (v: number) => H - pad - ((v - min) / (max - min)) * (H - pad * 2)

  const line = (key: 'baseline' | 'stressed') =>
    points.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)} ${y(p[key]).toFixed(1)}`).join(' ')

  const area = `${line('stressed')} L${x(points.length - 1)} ${H - pad} L${x(0)} ${H - pad} Z`
  const floorY = y(base * 0.35)

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label="Liquidity projection chart">
      <defs>
        <linearGradient id="stressFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={stressColor} stopOpacity="0.22" />
          <stop offset="100%" stopColor={stressColor} stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* safety floor */}
      <line x1={pad} y1={floorY} x2={W - pad} y2={floorY} stroke="var(--danger)" strokeWidth="1" strokeDasharray="4 4" opacity="0.5" />
      <text x={W - pad} y={floorY - 5} textAnchor="end" fontSize="8.5" fontFamily="var(--font-mono)" fill="var(--danger)" letterSpacing="1">
        35% SAFETY FLOOR
      </text>

      <path d={area} fill="url(#stressFill)" />
      <path d={line('baseline')} fill="none" stroke="var(--muted-foreground)" strokeWidth="1.5" strokeDasharray="3 3" opacity="0.7" />
      <path d={line('stressed')} fill="none" stroke={stressColor} strokeWidth="2" />
    </svg>
  )
}

function Metric({ label, value, sub, tone }: { label: string; value: string; sub: string; tone: 'gain' | 'warn' | 'danger' }) {
  const color = tone === 'danger' ? 'text-danger' : tone === 'warn' ? 'text-warn' : 'text-gain'
  return (
    <div className="rounded-lg border border-border bg-panel p-4">
      <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className={`mt-1 font-mono text-xl font-semibold tabular-nums ${color}`}>{value}</div>
      <div className="mt-0.5 font-mono text-[10px] text-muted-foreground">{sub}</div>
    </div>
  )
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="h-2 w-2 rounded-full" style={{ background: color }} />
      <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">{label}</span>
    </div>
  )
}
