import Link from 'next/link'
import { LedgerConsole } from '@/components/ledger/console'
import { SettlementForecastCard } from '@/components/kuber/settlement-forecast-card'
import { Pill } from '@/components/kuber/primitives'
import { ShieldCheck, CheckCircle2, ArrowRight, ExternalLink, Sparkles } from 'lucide-react'

export default function LedgerPage() {
  return (
    <div className="mx-auto max-w-[1440px] px-5 py-8 space-y-8">
      {/* Header */}
      <header>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Pill tone="gold">RFC 6962 Audit Ledger · Ed25519 Signed · Statutory Triage</Pill>
          <div className="flex items-center gap-3 font-mono text-xs">
            <Link href="/apex" className="text-muted-foreground hover:text-primary transition flex items-center gap-1">
              <span>Assurance Radar</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
            <span className="text-muted-foreground/40">•</span>
            <Link href="/lineage" className="text-muted-foreground hover:text-primary transition flex items-center gap-1">
              <span>Money Lineage DAG</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>

        <h1 className="mt-3 text-3xl font-bold tracking-tight text-foreground">
          Reconciliation Ledger &amp; Self-Healing Console
        </h1>
        <p className="mt-1.5 max-w-3xl text-sm text-muted-foreground leading-relaxed">
          The autonomous finance controller matches multi-rail settlements, CBIC GSTR-2B Input Tax Credit, and Section 194-O TDS. Ambiguous exceptions are isolated to an Asynchronous Human-in-the-Loop queue with strict spend caps and Ed25519 cryptographic certification.
        </p>
      </header>

      {/* 7-Day Settlement Forecast & Multi-Rail Inflow */}
      <section>
        <SettlementForecastCard />
      </section>

      {/* Proof & Invariant Callout Banner */}
      <div className="rounded-xl border border-border bg-[#0f1626]/90 p-5 shadow-lg backdrop-blur">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="rounded-lg border border-border/70 bg-[#090d16] p-4 space-y-2">
            <div className="font-bold text-muted-foreground uppercase text-[10px] tracking-wider">
              Traditional ERP &amp; Fuzzy Matching (Competitors):
            </div>
            <p className="text-muted-foreground leading-relaxed">
              Accepts 2.8% False Match Rates, leaves unexplained rounding noise, ignores CBIC Rule 36(4) GST ITC mismatches, and relies on LLM guessing when amounts collide.
            </p>
          </div>
          <div className="rounded-lg border border-gain/40 bg-gain/5 p-4 space-y-2">
            <div className="font-bold text-gain uppercase text-[10px] tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4" />
              KuberRecon Invariant Guarantees:
            </div>
            <p className="text-foreground/90 leading-relaxed">
              Knuth DLX Exact-Cover math guarantees FMR = 0.000. All currency is calculated in base-10 paise integers. Every reconciliation block is sealed with RFC 6962 Merkle proofs.
            </p>
          </div>
        </div>
      </div>

      {/* Filterable Reconciliation Ledger Workspace */}
      <section>
        <LedgerConsole />
      </section>
    </div>
  )
}
