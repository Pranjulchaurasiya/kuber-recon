import Link from 'next/link'
import { Panel, SectionLabel, StatTile, StatusDot, Pill } from '@/components/kuber/primitives'
import { LiveDashboard } from '@/components/kuber/live-dashboard'
import { systemStats, railHealth, navItems, inr } from '@/lib/kuber-data'

export default function CommandCenter() {
  return (
    <div className="mx-auto max-w-[1480px] px-5 py-6 md:px-8 md:py-8">
      <section className="kuber-hero relative overflow-hidden border border-gold/25 px-6 py-7 md:px-9 md:py-10">
        <div className="signal-track absolute inset-x-0 top-0 h-px opacity-80" />
        <div className="relative grid gap-9 lg:grid-cols-[minmax(0,1.1fr)_minmax(22rem,0.72fr)] lg:items-end">
          <div className="max-w-3xl">
            <div className="flex flex-wrap items-center gap-3">
              <Pill tone="gold">KuberRecon / 01</Pill>
              <span className="font-mono text-[10px] uppercase tracking-[0.24em] text-muted-foreground">Financial control plane</span>
            </div>
            <h1 className="mt-7 max-w-2xl text-balance text-4xl font-semibold leading-[0.98] tracking-[-0.045em] md:text-6xl">
              Money should leave a <span className="text-gold">proof</span>, not a guess.
            </h1>
            <p className="mt-5 max-w-xl text-pretty text-sm leading-relaxed text-muted-foreground md:text-base">
              KuberRecon seals statutory exposure at capture, proves each settlement with exact-cover lineage,
              then exposes tomorrow&apos;s liquidity risk before the rail moves.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
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

          <div className="border border-border bg-background/45 p-5 backdrop-blur-sm md:p-6">
            <div className="flex items-start justify-between gap-5">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">Settlement confidence</div>
                <div className="mt-2 font-mono text-6xl font-semibold tabular-nums tracking-[-0.06em] text-gain">
                  {systemStats.fmr.toFixed(3)}
                </div>
              </div>
              <div className="border border-gain/30 bg-gain/10 px-2 py-1 font-mono text-[9px] uppercase tracking-widest text-gain">FMR</div>
            </div>
            <div className="mt-6 grid grid-cols-[auto_1fr] gap-x-3 gap-y-3 border-t border-border pt-4 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              <StatusDot status="ok" /><span>DLX exact cover verified</span>
              <StatusDot status="ok" /><span>Paise kernel locked</span>
              <StatusDot status="warn" /><span>GSTR-2B cycle: T−3 days</span>
            </div>
          </div>
        </div>
      </section>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
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

      <div className="mt-4">
        <LiveDashboard />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
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
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
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
                className="group relative flex flex-col gap-2 overflow-hidden p-5 transition-colors hover:bg-accent/40"
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
                <span className="mt-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground/70 transition-colors group-hover:text-gold">
                  <span className="h-px w-5 bg-current" /> Open rail
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
