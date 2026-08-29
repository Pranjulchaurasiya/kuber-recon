import Link from 'next/link'
import { LedgerConsole } from '@/components/ledger/console'
import { Pill } from '@/components/kuber/primitives'
import { ShieldCheck, CheckCircle2, ArrowRight, ExternalLink } from 'lucide-react'

export default function LedgerPage() {
  return (
    <div className="mx-auto max-w-[1400px] px-5 py-8 space-y-6">
      <header>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Pill tone="gold">RFC 6962 Audit Ledger · Ed25519 Signed</Pill>
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

        <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">Self-Healing &amp; Merkle Ledger</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          The system repairs discrepancies within hard bounds — never autonomously beyond them. Every
          adjustment passes a ₹200 spend cap and KYC whitelist, then requires a human CFO signature
          that seals an Ed25519 certificate into an RFC 6962 Merkle chain.
        </p>
      </header>

      {/* 🔴 P2: What This Proves Callout Banner */}
      <div className="rounded-xl border border-border bg-panel p-4 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="rounded-lg border border-border bg-background p-3.5 space-y-1.5">
            <div className="font-bold text-muted-foreground uppercase text-[10px] tracking-wider">
              Traditional ERP &amp; Manual Recon:
            </div>
            <p className="text-muted-foreground leading-relaxed">
              Leaves ₹0.xx rounding noise, unexplained batch deltas, and unverified bank lump-sums. Reconciliation reports are generated retroactively after funds have already settled.
            </p>
          </div>
          <div className="rounded-lg border border-gain/40 bg-gain/5 p-3.5 space-y-1.5">
            <div className="font-bold text-gain uppercase text-[10px] tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5" />
              APEX Merkle Ledger Guarantee:
            </div>
            <p className="text-foreground/90 leading-relaxed">
              Cryptographically proves every single paisa with Ed25519 signatures, RFC 6962 SHA-256 Merkle root, and an immutable ₹0.00 closure guarantee before nodal release.
            </p>
          </div>
        </div>
      </div>

      <LedgerConsole />
    </div>
  )
}

