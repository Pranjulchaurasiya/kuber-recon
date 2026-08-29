import Link from 'next/link'
import { SplitEngine } from '@/components/escrow/split-engine'
import { RazorpayRouteConsole } from '@/components/escrow/razorpay-console'
import { Panel, SectionLabel, StatTile, Pill } from '@/components/kuber/primitives'
import { escrowSplits, escrowBuckets, paiseToInr } from '@/lib/kuber-data'
import { ShieldCheck, CheckCircle2, ArrowRight } from 'lucide-react'

export default function EscrowPage() {
  const held = escrowSplits.filter((s) => s.onHold)
  const totalHeld = held.reduce((a, s) => a + s.gst + s.tds, 0)
  const totalGross = escrowSplits.reduce((a, s) => a + s.gross, 0)

  return (
    <div className="mx-auto max-w-[1400px] px-5 py-8 space-y-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Pill tone="gold">Razorpay Route · T=0 Statutory Escrow</Pill>
            <div className="flex items-center gap-3 font-mono text-xs">
              <Link href="/apex" className="text-muted-foreground hover:text-primary transition flex items-center gap-1">
                <span>Assurance Radar</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
              <span className="text-muted-foreground/40">•</span>
              <Link href="/ledger" className="text-muted-foreground hover:text-primary transition flex items-center gap-1">
                <span>Merkle Ledger</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </div>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">Gateway Escrow Rail</h1>
          <p className="mt-1 max-w-xl text-sm text-muted-foreground">
            Money is protected <span className="text-foreground">before</span> it leaves the merchant&apos;s
            account. Every incoming order is split at T=0, with statutory dues held in escrow until the
            GSTR-2B resolves on the 14th.
          </p>
        </div>
      </header>

      {/* 🔴 P2: What This Proves Callout Banner */}
      <div className="rounded-xl border border-border bg-panel p-4 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="rounded-lg border border-border bg-background p-3.5 space-y-1.5">
            <div className="font-bold text-muted-foreground uppercase text-[10px] tracking-wider">
              Traditional Payment Gateways:
            </div>
            <p className="text-muted-foreground leading-relaxed">
              Disburse 100% of gross settlement directly to seller accounts. Tax compliance (TDS § 194-O, GST) is left as a post-settlement headache that triggers tax notices and cash leakage.
            </p>
          </div>
          <div className="rounded-lg border border-gold/40 bg-gold/5 p-3.5 space-y-1.5">
            <div className="font-bold text-gold uppercase text-[10px] tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5" />
              APEX Route Escrow Invariant:
            </div>
            <p className="text-foreground/90 leading-relaxed">
              Splits every payment at T=0 directly via Razorpay Route Transfers with `on_hold: true`, holding statutory dues until verified delivery and GSTR-2B matching occurs.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Gross intake" value={paiseToInr(totalGross, { compact: true })} hint={`${escrowSplits.length} orders in window`} />
        <StatTile label="Held in escrow" value={paiseToInr(totalHeld, { compact: true })} accent="gold" hint="Statutory dues on_hold" />
        <StatTile label="Orders on hold" value={held.length} accent="warn" hint="Awaiting GSTR-2B" />
        <StatTile label="Leakage" value="₹0.00" accent="gain" hint="Prevented at gateway" />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <SplitEngine />
        </div>

        <Panel>
          <SectionLabel right={<Pill tone="gold">on_hold: true</Pill>}>Escrow Allocation</SectionLabel>
          <div className="flex flex-col gap-5">
            {escrowBuckets.map((b) => (
              <div key={b.key}>
                <div className="mb-1.5 flex items-center justify-between text-sm">
                  <span>{b.label}</span>
                  <span className="font-mono tabular-nums text-muted-foreground">{b.pct.toFixed(1)}%</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-accent">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${b.pct}%`, background: b.color }}
                  />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-6 rounded-md border border-gold/30 bg-gold/5 p-4">
            <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Resolution trigger
            </div>
            <div className="mt-1 text-sm">
              GSTR-2B reconciliation on the <span className="font-mono text-gold">14th</span> auto-releases
              matched escrow; unmatched dues stay locked.
            </div>
          </div>
        </Panel>
      </div>

      {/* Razorpay Route & Webhook Live Proof Console */}
      <div className="mt-6">
        <RazorpayRouteConsole />
      </div>

      {/* Live split ledger */}
      <Panel className="mt-6" flush>
        <div className="flex items-center justify-between border-b border-border p-5">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            Live Split Ledger
          </h2>
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {escrowSplits.length} records
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-sm">
            <thead>
              <tr className="border-b border-border font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                <th className="px-5 py-3 text-left font-medium">Order</th>
                <th className="px-5 py-3 text-left font-medium">Merchant</th>
                <th className="px-5 py-3 text-right font-medium">Gross</th>
                <th className="px-5 py-3 text-right font-medium">Principal</th>
                <th className="px-5 py-3 text-right font-medium">GST 18%</th>
                <th className="px-5 py-3 text-right font-medium">TDS 1%</th>
                <th className="px-5 py-3 text-left font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="font-mono tabular-nums">
              {escrowSplits.map((s) => (
                <tr key={s.id} className="border-b border-border/60 last:border-0 transition-colors hover:bg-accent/30">
                  <td className="px-5 py-3 text-left text-foreground">{s.order}</td>
                  <td className="px-5 py-3 text-left font-sans text-muted-foreground">{s.merchant}</td>
                  <td className="px-5 py-3 text-right">{paiseToInr(s.gross)}</td>
                  <td className="px-5 py-3 text-right text-gain">{paiseToInr(s.principal)}</td>
                  <td className="px-5 py-3 text-right text-gold">{paiseToInr(s.gst)}</td>
                  <td className="px-5 py-3 text-right text-muted-foreground">{paiseToInr(s.tds)}</td>
                  <td className="px-5 py-3 text-left">
                    {s.onHold ? (
                      <Pill tone="gold">held · {s.resolvesOn}</Pill>
                    ) : (
                      <Pill tone="gain">released</Pill>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  )
}
