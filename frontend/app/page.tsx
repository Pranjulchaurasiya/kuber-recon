import Link from 'next/link'
import { Panel, SectionLabel, StatTile, StatusDot, Pill } from '@/components/kuber/primitives'
import { LiveDashboard } from '@/components/kuber/live-dashboard'
import { systemStats, railHealth, navItems, inr } from '@/lib/kuber-data'

export default function CommandCenter() {
  return (
    <div className="mx-auto max-w-[1400px] px-5 py-8">
      {/* Hero band */}
      <section className="relative overflow-hidden rounded-xl border border-border bg-panel">
        <div className="bg-blueprint pointer-events-none absolute inset-0 opacity-40" />
        <div className="relative flex flex-col gap-6 p-8 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <Pill tone="gold">Autonomous Financial Integrity OS</Pill>
            <h1 className="mt-4 text-balance text-3xl font-semibold leading-tight tracking-tight md:text-4xl">
              Every rupee tracked to its statutory root.
            </h1>
            <p className="mt-3 text-pretty text-sm leading-relaxed text-muted-foreground">
              Zero tax lost, zero math guessed. KuberRecon prevents loss at the gateway, proves
              lineage with exact math, and stress-tests future liquidity — a closed-loop financial
              controller built on the Razorpay rail.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href="/escrow"
                className="rounded-md bg-gold px-4 py-2 text-sm font-medium text-gold-foreground transition-opacity hover:opacity-90"
              >
                Enter the Rail
              </Link>
              <Link
                href="/lineage"
                className="rounded-md border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
              >
                Trace a Settlement
              </Link>
            </div>
          </div>

          <div className="shrink-0 rounded-lg border border-gold/30 bg-gold/5 p-5">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
              False Match Rate
            </div>
            <div className="mt-1 font-mono text-5xl font-semibold tabular-nums text-gain">
              {systemStats.fmr.toFixed(3)}
            </div>
            <div className="mt-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              <StatusDot status="ok" />
              Knuth Algorithm X · exact cover
            </div>
          </div>
        </div>
      </section>

      {/* Headline stats */}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Protected today"
          value={inr(systemStats.protectedToday, { compact: true })}
          hint="Escrow-guarded before payout"
          accent="gold"
        />
        <StatTile
          label="Tax loss prevented"
          value={inr(systemStats.taxLossPrevented, { compact: true })}
          hint="Rolling 30-day statutory recovery"
          accent="gain"
        />
        <StatTile
          label="Orders processed"
          value={systemStats.ordersProcessed.toLocaleString('en-IN')}
          hint="Split at T=0 across the rail"
        />
        <StatTile
          label="Escrow held now"
          value={inr(systemStats.escrowHeld, { compact: true })}
          hint={`Resolves GSTR-2B · ${systemStats.gstr2bResolveDay}th`}
        />
      </div>

      {/* Live metrics dashboard */}
      <div className="mt-6">
        <LiveDashboard />
      </div>

      {/* Rail health + module map */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Panel className="lg:col-span-1">
          <SectionLabel right={<Pill tone="gain">4 rails</Pill>}>Rail Health</SectionLabel>
          <ul className="flex flex-col divide-y divide-border">
            {railHealth.map((h) => (
              <li key={h.label} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
                <div className="flex items-center gap-3">
                  <StatusDot status={h.status} />
                  <span className="text-sm">{h.label}</span>
                </div>
                <span
                  className={`font-mono text-xs ${
                    h.status === 'ok'
                      ? 'text-gain'
                      : h.status === 'warn'
                        ? 'text-warn'
                        : 'text-danger'
                  }`}
                >
                  {h.value}
                </span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel className="lg:col-span-2" flush>
          <div className="flex items-center justify-between border-b border-border p-5">
            <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              Control Modules
            </h2>
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              closed loop
            </span>
          </div>
          <div className="grid grid-cols-1 divide-y divide-border sm:grid-cols-2 sm:divide-y-0 sm:[&>*:nth-child(-n+2)]:border-b sm:[&>*:nth-child(odd)]:border-r sm:[&>*]:border-border">
            {navItems.slice(1).map((item, i) => (
              <Link
                key={item.href}
                href={item.href}
                className="group flex flex-col gap-2 p-5 transition-colors hover:bg-accent/40"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] tracking-widest text-gold">
                    {item.code}
                  </span>
                  <span className="font-mono text-[10px] text-muted-foreground">
                    0{i + 1}
                  </span>
                </div>
                <span className="text-sm font-medium">{item.label}</span>
                <span className="text-xs leading-relaxed text-muted-foreground">
                  {moduleBlurbs[item.href]}
                </span>
                <span className="mt-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground/70 transition-colors group-hover:text-gold">
                  Open →
                </span>
              </Link>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  )
}

const moduleBlurbs: Record<string, string> = {
  '/escrow': 'Live split of incoming orders into principal, TDS and GST escrow — money protected before it leaves the account.',
  '/lineage': 'Interactive node graph tracing bank lump-sum UTRs down to gross GMV, MDR, GST and TDS with FMR = 0.000.',
  '/twin': 'What-if sliders simulating bank-holiday freezes and vendor GSTR-1 default cascades against liquidity.',
  '/ledger': 'One-click CFO approvals with hard spend caps, KYC whitelists and Ed25519-signed Merkle audit certificates.',
}
