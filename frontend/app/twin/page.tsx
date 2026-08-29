import Link from 'next/link'
import { Simulator } from '@/components/twin/simulator'
import { Pill } from '@/components/kuber/primitives'
import { scenarios } from '@/lib/kuber-data'
import { ShieldAlert, TrendingDown, CheckCircle2, ArrowRight } from 'lucide-react'

export default function TwinPage() {
  return (
    <div className="mx-auto max-w-[1400px] px-5 py-8 space-y-6">
      <header>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Pill tone="gold">Causal Inference · What-If Stress Engine</Pill>
          <div className="flex items-center gap-3 font-mono text-xs">
            <Link href="/apex" className="text-muted-foreground hover:text-primary transition flex items-center gap-1">
              <span>Assurance Radar</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
            <span className="text-muted-foreground/40">•</span>
            <Link href="/escrow" className="text-muted-foreground hover:text-primary transition flex items-center gap-1">
              <span>Gateway Escrow Rail</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>

        <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">Causal Digital Twin</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          Move from reporting the past to stress-testing the future. The twin models causal shocks —
          bank-holiday freezes, vendor GSTR-1 defaults, chargeback surges — and projects their impact
          on liquidity before they ever hit the books.
        </p>
      </header>

      {/* 🔴 P2: What This Proves Callout Banner */}
      <div className="rounded-xl border border-border bg-panel p-4 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="rounded-lg border border-border bg-background p-3.5 space-y-1.5">
            <div className="font-bold text-muted-foreground uppercase text-[10px] tracking-wider">
              Traditional Risk &amp; Treasury:
            </div>
            <p className="text-muted-foreground leading-relaxed">
              Discovers liquidity crunches and supplier GST defaults days after settlement, triggering retroactive penalties and cascading working capital freezes.
            </p>
          </div>
          <div className="rounded-lg border border-gold/40 bg-gold/5 p-3.5 space-y-1.5">
            <div className="font-bold text-gold uppercase text-[10px] tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5" />
              APEX Causal Twin Invariant:
            </div>
            <p className="text-foreground/90 leading-relaxed">
              Runs Monte Carlo stress simulations before disbursement — calculating liquidity survival horizons and preemptively dynamically withholding high-risk tax liability.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {scenarios.map((s) => (
          <div key={s.id} className="rounded-lg border border-border bg-panel p-4">
            <div className="font-mono text-[10px] uppercase tracking-widest text-warn">Scenario</div>
            <div className="mt-1 text-sm font-semibold text-foreground">{s.label}</div>
            <div className="mt-1 text-xs leading-relaxed text-muted-foreground">{s.desc}</div>
          </div>
        ))}
      </div>

      <Simulator />
    </div>
  )
}

