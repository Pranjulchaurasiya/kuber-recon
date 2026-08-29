'use client'

import { Landmark, FileClock, ShieldAlert, AlertOctagon } from 'lucide-react'

export function GapSection() {
  const silos = [
    {
      icon: Landmark,
      title: 'Commercial Banks',
      subtitle: 'Aggregated lump-sum NEFT/RTGS credits',
      flaw: 'Cannot verify line-item delivery or GSTIN match.',
      verdict: 'Zero Delivery Signal',
      color: 'text-rose-500 bg-rose-500/10 border-rose-500/30',
    },
    {
      icon: FileClock,
      title: 'Credit Bureaus (CIBIL)',
      subtitle: 'Quarterly bureau debt reporting',
      flaw: 'Data lags by 30 to 90 days behind merchant cash velocity.',
      verdict: 'Stale Historical Data',
      color: 'text-amber-500 bg-amber-500/10 border-amber-500/30',
    },
    {
      icon: ShieldAlert,
      title: 'SaaS / Standalone Lenders',
      subtitle: 'Unsecured daily NACH direct debit',
      flaw: 'No control over primary merchant settlement accounts.',
      verdict: 'High Default Risk',
      color: 'text-orange-500 bg-orange-500/10 border-orange-500/30',
    },
    {
      icon: AlertOctagon,
      title: 'Post-Settlement Recon',
      subtitle: 'End-of-month chargeback reconciliation',
      flaw: 'Disputes trigger after money has already left the ecosystem.',
      verdict: 'Unrecoverable Losses',
      color: 'text-red-500 bg-red-500/10 border-red-500/30',
    },
  ]

  return (
    <section className="space-y-10 py-6" id="the-gap">
      {/* Section Header */}
      <div className="text-center space-y-3 max-w-3xl mx-auto animate-fade-up">
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-panel px-3 py-1 text-xs font-mono font-semibold text-primary">
          <span className="h-2 w-2 rounded-full bg-primary animate-status-dot" />
          The Institutional Ownership Moat
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-foreground">
          Every bank sees the money move.<br />
          <span className="text-primary">Nobody knows if the goods arrived.</span>
        </h2>
        <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
          Traditional lenders only inspect aggregate bank balances. They cannot see if an AI buyer agent actually received goods, whether GSTIN checksums match GSTR-2B, or if incoming revenue is already pledged elsewhere.
        </p>
      </div>

      {/* 4 Silo Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {silos.map((silo, i) => {
          const Icon = silo.icon
          return (
            <div
              key={i}
              className={`relative flex flex-col justify-between rounded-xl border border-border bg-panel p-5 shadow-sm hover-glow animate-fade-up stagger-${i + 1}`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent border border-border text-foreground">
                    <Icon className="h-4 w-4" />
                  </div>
                  <span className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-bold border ${silo.color}`}>
                    {silo.verdict}
                  </span>
                </div>
                <div>
                  <h3 className="font-semibold text-foreground text-sm">{silo.title}</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">{silo.subtitle}</p>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-border/60 text-xs text-muted-foreground leading-snug">
                {silo.flaw}
              </div>
            </div>
          )
        })}
      </div>

      {/* Evidence Strip — hard numbers anchored to the blind spots */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 rounded-2xl border border-border bg-panel/60 p-5 max-w-2xl mx-auto text-center animate-fade-up">
        <div>
          <div className="font-mono text-2xl font-extrabold text-foreground">₹1.8 Lakh Cr</div>
          <div className="text-xs text-muted-foreground mt-1">Underserved Indian MSME Credit Gap</div>
        </div>
        <div>
          <div className="font-mono text-2xl font-extrabold text-gain">0.000 FMR</div>
          <div className="text-xs text-muted-foreground mt-1">False Match Rate Across 11,100 Logs</div>
        </div>
        <div>
          <div className="font-mono text-2xl font-extrabold text-primary">₹0.00</div>
          <div className="text-xs text-muted-foreground mt-1">Over-Recovery Under Concurrent Race</div>
        </div>
      </div>
    </section>
  )
}
