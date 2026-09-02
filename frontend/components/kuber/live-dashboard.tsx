'use client'

import { useEffect, useState } from 'react'
import { inr, systemStats } from '@/lib/kuber-data'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function LiveDashboard() {
  const [orders] = useState(systemStats.ordersProcessed)
  const [protected_] = useState(systemStats.protectedToday)
  const [taxSaved] = useState(systemStats.taxLossPrevented)
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)
  const [backendMode, setBackendMode] = useState<string>('sandbox_simulation')
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  useEffect(() => {
    let isMounted = true
    const checkBackend = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/integration-status`, {
          headers: { 'Accept': 'application/json' },
        })
        if (res.ok) {
          const data = await res.json()
          if (isMounted) {
            setBackendOnline(true)
            setBackendMode(data.mode || 'sandbox_simulation')
            setLastUpdate(new Date())
          }
        } else {
          if (isMounted) setBackendOnline(false)
        }
      } catch {
        if (isMounted) setBackendOnline(false)
      }
    }

    checkBackend()
    const interval = setInterval(checkBackend, 5000)
    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [])

  return (
    <div className="rounded-lg border border-border bg-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
          System Status & Test Telemetry
        </h2>
        <div className="flex items-center gap-2">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              backendOnline === true
                ? 'bg-gain animate-pulse-dot'
                : backendOnline === false
                ? 'bg-amber-500'
                : 'bg-muted-foreground'
            }`}
          />
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {backendOnline === true
              ? `Backend Active · ${lastUpdate.toLocaleTimeString('en-IN', { hour12: false })}`
              : backendOnline === false
              ? 'Backend Offline'
              : 'Connecting...'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric
          label="Test Invoices Ingested"
          value={orders.toLocaleString('en-IN')}
          delta="sandbox test corpus"
          tone="gain"
        />
        <Metric
          label="Protected Value (₹)"
          value={inr(protected_, { compact: true })}
          delta="escrow-guarded baseline"
          tone="gold"
        />
        <Metric
          label="Tax Preserved (₹)"
          value={inr(taxSaved, { compact: true })}
          delta="1.9% statutory baseline"
          tone="gain"
        />
        <Metric
          label="False Match Rate"
          value="0.000"
          delta="tested synthetic corpus"
          tone="gain"
        />
      </div>

      <div className="mt-4 flex items-center justify-between rounded-md border border-border bg-background/60 px-4 py-2">
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          Razorpay Integration Rail
        </span>
        <span
          className={`font-mono text-[10px] ${
            backendOnline === true ? 'text-gain' : 'text-amber-500'
          }`}
        >
          {backendOnline === true
            ? `● LIVE · ${backendMode.toUpperCase()} (SQLite WAL Store)`
            : '○ OFFLINE · Standalone Sandbox Demo'}
        </span>
      </div>
    </div>
  )
}

function Metric({
  label,
  value,
  delta,
  tone,
}: {
  label: string
  value: string
  delta: string
  tone: 'gain' | 'gold'
}) {
  const color = tone === 'gain' ? 'text-gain' : 'text-gold'
  return (
    <div className="flex flex-col gap-0.5">
      <span className="font-mono text-[9px] uppercase tracking-widest text-muted-foreground">
        {label}
      </span>
      <span className={`font-mono text-lg font-semibold tabular-nums ${color}`}>{value}</span>
      <span className="font-mono text-[9px] text-muted-foreground">{delta}</span>
    </div>
  )
}
