import Link from 'next/link'
import { CapitalHub } from '@/components/capital/capital-hub'
import { Pill } from '@/components/kuber/primitives'
import { CheckCircle2, ArrowRight, Landmark, ShieldCheck } from 'lucide-react'

export const metadata = {
  title: 'Kuber Capital · 1-Click Working Capital & Split-Settlement Recovery',
  description: 'Underwrite real-time working capital advances against verified delivered ledger truth with automated Razorpay Route settlement recovery sweeps.',
}

export default function CapitalPage() {
  return (
    <div className="mx-auto max-w-[1400px] px-5 py-8 space-y-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Pill tone="gold">Kuber Capital · Autonomous Working Capital</Pill>
            <div className="flex items-center gap-3 font-mono text-xs">
              <Link href="/console" className="text-muted-foreground hover:text-primary transition flex items-center gap-1">
                <span>Assurance Radar</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
              <span className="text-muted-foreground/40">•</span>
              <Link href="/escrow" className="text-muted-foreground hover:text-primary transition flex items-center gap-1">
                <span>Gateway Escrow</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
              <span className="text-muted-foreground/40">•</span>
              <Link href="/twin" className="text-muted-foreground hover:text-primary transition flex items-center gap-1">
                <span>Causal Twin</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </div>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2.5">
            <Landmark className="h-6 w-6 text-primary" />
            Working Capital &amp; Settlement Recovery Hub
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Zero paper underwriting. Credit lines underwritten in 8ms off verified cryptographic ledger truth,
            repaid automatically through 12% split-settlement sweeps via Razorpay Route.
          </p>
        </div>
      </header>

      {/* Proof & Regulatory Architecture Callout */}
      <div className="rounded-xl border border-border bg-panel p-4 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="rounded-lg border border-border bg-background p-3.5 space-y-1.5">
            <div className="font-bold text-muted-foreground uppercase text-[10px] tracking-wider">
              Traditional Merchant Underwriting:
            </div>
            <p className="text-muted-foreground leading-relaxed">
              Requires 6 months of stale audited bank statements and manual credit officer reviews (4-7 business days).
              Rigid fixed monthly EMIs trigger cash flow chokes during seasonal sales dips.
            </p>
          </div>
          <div className="rounded-lg border border-gold/40 bg-gold/5 p-3.5 space-y-1.5">
            <div className="font-bold text-gold uppercase text-[10px] tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Kuber Sovereign Capital Protocol:
            </div>
            <p className="text-foreground/90 leading-relaxed">
              Real-time Bayesian Settlement Reliability Index (SRI) underwrites up to 25% of verified delivered GMV.
              Dynamic automated sweeps amortize principal proportional to real nodal settlement volume under RBI 5% FLDG rules.
            </p>
          </div>
        </div>
      </div>

      {/* Main Capital Hub Engine */}
      <CapitalHub />
    </div>
  )
}
