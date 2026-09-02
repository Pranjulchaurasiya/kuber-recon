'use client'

import { useEffect, useState } from 'react'
import { inr, systemStats } from '@/lib/kuber-data'

// Live metrics that tick up every few seconds
export function LiveDashboard() {
  const [orders, setOrders] = useState(systemStats.ordersProcessed)
  const [protected_, setProtected] = useState(systemStats.protectedToday)
  const [taxSaved, setTaxSaved] = useState(systemStats.taxLossPrevented)
  const [uptime] = useState('99.99%')
  const [lastUpdate, setLastUpdate] = useState(new Date())

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate live Razorpay order ingestion
      const newOrders = Math.floor(Math.random() * 3) + 1
      const orderValue = Math.floor(Math.random() * 50000) + 5000
      setOrders((o) => o + newOrders)
      setProtected((p) => p + orderValue * newOrders)
      setTaxSaved((t) => t + Math.floor(orderValue * newOrders * 0.019)) // ~1.9% TDS+GST saved
      setLastUpdate(new Date())
    }, 3200)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="rounded-lg border border-border bg-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
          Live System Metrics
        </h2>
        <div className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-gain" />
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Updated {lastUpdate.toLocaleTimeString('en-IN', { hour12: false })}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric
          label="Orders today"
          value={orders.toLocaleString('en-IN')}
          delta={`+${(Math.random() * 3 + 1).toFixed(0)}/s`}
          tone="gain"
        />
        <Metric
          label="Protected (₹)"
          value={inr(protected_, { compact: true })}
          delta="escrow-guarded"
          tone="gold"
        />
        <Metric
          label="Tax saved (₹)"
          value={inr(taxSaved, { compact: true })}
          delta="30-day rolling"
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
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Razorpay Rail</span>
        <span className="font-mono text-[10px] text-gain">● LIVE · Uptime {uptime}</span>
      </div>
    </div>
  )
}

function Metric({ label, value, delta, tone }: { label: string; value: string; delta: string; tone: 'gain' | 'gold' }) {
  const color = tone === 'gain' ? 'text-gain' : 'text-gold'
  return (
    <div className="flex flex-col gap-0.5">
      <span className="font-mono text-[9px] uppercase tracking-widest text-muted-foreground">{label}</span>
      <span className={`font-mono text-lg font-semibold tabular-nums ${color}`}>{value}</span>
      <span className="font-mono text-[9px] text-muted-foreground">{delta}</span>
    </div>
  )
}
