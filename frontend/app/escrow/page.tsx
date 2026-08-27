import { SplitEngine } from '@/components/escrow/split-engine'
import { Panel, SectionLabel, StatTile, Pill } from '@/components/kuber/primitives'
import { escrowSplits, escrowBuckets, inr } from '@/lib/kuber-data'

export default function EscrowPage() {
  const held = escrowSplits.filter((s) => s.onHold)
  const totalHeld = held.reduce((a, s) => a + s.gst + s.tds, 0)
  const totalGross = escrowSplits.reduce((a, s) => a + s.gross, 0)

  return (
    <div className="mx-auto max-w-[1400px] px-5 py-8">
      <header className="mb-6 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Pill tone="gold">Razorpay Route · T=0 Statutory Escrow</Pill>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">Gateway Escrow Rail</h1>
          <p className="mt-1 max-w-xl text-sm text-muted-foreground">
            Money is protected <span className="text-foreground">before</span> it leaves the merchant&apos;s
            account. Every incoming order is split at T=0, with statutory dues held in escrow until the
            GSTR-2B resolves on the 14th.
          </p>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Gross intake" value={inr(totalGross, { compact: true })} hint={`${escrowSplits.length} orders in window`} />
        <StatTile label="Held in escrow" value={inr(totalHeld, { compact: true })} accent="gold" hint="Statutory dues on_hold" />
        <StatTile label="Orders on hold" value={held.length} accent="warn" hint="Awaiting GSTR-2B" />
        <StatTile label="Leakage" value="₹0" accent="gain" hint="Prevented at gateway" />
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
                  <td className="px-5 py-3 text-right">{inr(s.gross)}</td>
                  <td className="px-5 py-3 text-right text-gain">{inr(s.principal)}</td>
                  <td className="px-5 py-3 text-right text-gold">{inr(s.gst)}</td>
                  <td className="px-5 py-3 text-right text-muted-foreground">{inr(s.tds)}</td>
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
