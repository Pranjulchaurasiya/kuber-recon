import { Panel, SectionLabel, StatTile, StatusDot, Pill } from '@/components/kuber/primitives'
import { SettlementIntervention } from '@/components/kuber/settlement-intervention'
import { systemStats, railHealth, inr } from '@/lib/kuber-data'

export default function CommandCenter() {
  return (
    <div className="mx-auto max-w-[1480px] px-5 py-6 md:px-8 md:py-8">
      <SettlementIntervention />

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
              Evidence rails
            </h2>
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              drill into the proof
            </span>
          </div>
          <div className="grid grid-cols-1 divide-y divide-border sm:grid-cols-2 sm:divide-y-0 sm:[&>*:nth-child(-n+2)]:border-b sm:[&>*:nth-child(odd)]:border-r sm:[&>*]:border-border">
            {[
              { href: '/escrow', label: 'Gateway Escrow Rail', code: 'ESC', description: 'T=0 statutory split and Route hold controls.' },
              { href: '/lineage', label: 'Money Lineage', code: 'DAG', description: 'Exact-cover proof and ambiguity refusal.' },
              { href: '/twin', label: 'Causal Digital Twin', code: 'SIM', description: 'Stress-test the downstream settlement impact.' },
              { href: '/ledger', label: 'Self-Healing Ledger', code: 'MRK', description: 'Guarded, signed financial repair trail.' },
            ].map((item, i) => (
              <a
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
              </a>
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
