'use client'

import Link from 'next/link'
import { useState } from 'react'
import type { ReactNode } from 'react'

type Stage = 'incoming' | 'refused' | 'review'

const covers = [
  { label: 'Candidate cover A', invoices: ['INV-841 · ₹60,000', 'INV-842 · ₹40,000'] },
  { label: 'Candidate cover B', invoices: ['INV-903 · ₹70,000', 'INV-904 · ₹30,000'] },
]

export function SettlementIntervention() {
  const [stage, setStage] = useState<Stage>('incoming')

  const refused = stage !== 'incoming'
  const reviewOpen = stage === 'review'

  return (
    <section className="kuber-hero relative overflow-hidden border border-danger/35 bg-panel px-5 py-6 md:px-8 md:py-8">
      <div className="absolute inset-x-0 top-0 h-px bg-danger shadow-[0_0_24px_var(--danger)]" />
      <div className="relative">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.22em] text-danger">
              <span className="h-2 w-2 animate-pulse rounded-full bg-danger" />
              Live intervention scenario / sandbox
            </div>
            <h1 className="mt-3 max-w-3xl text-balance text-3xl font-semibold leading-[1.02] tracking-[-0.04em] md:text-5xl">
              A payout is waiting for a <span className="text-danger">proof</span>, not a prediction.
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground md:text-base">
              One bank credit maps to two equally valid invoice covers. KuberRecon halts the settlement
              instead of guessing who should receive the money.
            </p>
          </div>
          <div className="border border-danger/40 bg-danger/10 px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-danger">
            {refused ? 'release blocked' : 'decision pending'}
          </div>
        </div>

        <div className="mt-7 grid gap-3 lg:grid-cols-[0.85fr_1.3fr_0.85fr]">
          <IncidentCard title="01 / Bank credit" accent="gold">
            <div className="font-mono text-3xl font-semibold tracking-tight text-foreground">₹1,00,000.00</div>
            <div className="mt-2 font-mono text-xs text-muted-foreground">UTR HDFC-CRD-9912 · 10,000,000 paise</div>
            <div className="mt-5 border-t border-border pt-4 text-xs leading-relaxed text-muted-foreground">
              Captured payment batch received. The reconciliation rail must prove one non-overlapping invoice cover before release.
            </div>
          </IncidentCard>

          <div className={`border p-5 transition-colors ${refused ? 'border-danger/50 bg-danger/[0.06]' : 'border-gold/35 bg-background/45'}`}>
            <div className="flex items-center justify-between gap-3">
              <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">02 / Exact-cover evidence</span>
              <span className={`font-mono text-[10px] uppercase tracking-widest ${refused ? 'text-danger' : 'text-gold'}`}>
                {refused ? '2 covers found' : 'awaiting solve'}
              </span>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {covers.map((cover) => (
                <div key={cover.label} className={`border p-3 ${refused ? 'border-danger/35 bg-panel' : 'border-border bg-panel/70'}`}>
                  <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">{cover.label}</div>
                  <div className="mt-3 space-y-2 font-mono text-xs text-foreground">
                    {cover.invoices.map((invoice) => <div key={invoice}>{invoice}</div>)}
                  </div>
                  <div className="mt-4 border-t border-border pt-2 font-mono text-[10px] uppercase tracking-widest text-gain">exact sum ₹1,00,000</div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
              <span className="text-xs text-muted-foreground">Knuth DLX will accept only one provable cover.</span>
              <button
                onClick={() => setStage('refused')}
                className="border border-danger/50 bg-danger/10 px-4 py-2 font-mono text-[11px] font-semibold uppercase tracking-widest text-danger transition-colors hover:bg-danger/20"
              >
                {refused ? 'Ambiguity confirmed' : 'Run proof check'}
              </button>
            </div>
          </div>

          <IncidentCard title="03 / Rail decision" accent={refused ? 'danger' : 'muted'}>
            <div className={`font-mono text-xl font-semibold ${refused ? 'text-danger' : 'text-muted-foreground'}`}>
              {refused ? 'DO NOT RELEASE' : 'ROUTE ON HOLD'}
            </div>
            <div className="mt-2 font-mono text-xs text-muted-foreground">Route transfer · on_hold: true</div>
            <div className="mt-5 border-t border-border pt-4 text-xs leading-relaxed text-muted-foreground">
              {refused
                ? 'No payout instruction is created. The case is routed to a CFO maker-checker review with both candidate covers attached.'
                : 'Funds remain held until the control plane receives a unique settlement proof.'}
            </div>
            <button
              onClick={() => setStage('review')}
              disabled={!refused}
              className="mt-4 w-full border border-border bg-background px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-foreground transition-colors enabled:hover:border-gold enabled:hover:text-gold disabled:cursor-not-allowed disabled:opacity-40"
            >
              Open CFO review
            </button>
          </IncidentCard>
        </div>

        {refused && (
          <div className="mt-3 grid gap-3 border border-danger/40 bg-danger/10 p-4 md:grid-cols-[1fr_auto] md:items-center">
            <div>
              <div className="font-mono text-xs font-semibold uppercase tracking-widest text-danger">AmbiguousMatchError · honest refusal enforced</div>
              <p className="mt-1 text-sm text-foreground">Two exact covers are valid. Guessing would create a false match; the release is blocked at ₹0 residual.</p>
            </div>
            <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">proof sha256:9c7a…e21b</div>
          </div>
        )}

        {reviewOpen && (
          <div className="mt-3 border border-gold/40 bg-gold/5 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-gold">CFO review case / CRD-BANK-HDFC-9912</div>
                <div className="mt-1 text-sm text-foreground">Approval is unavailable until a human establishes which invoice cover is real.</div>
              </div>
              <span className="border border-gold/40 px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-gold">maker-checker required</span>
            </div>
          </div>
        )}

        <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-border pt-5">
          <Link href="/lineage" className="bg-gold px-4 py-2 text-sm font-medium text-gold-foreground transition-opacity hover:opacity-90">
            Inspect the proof engine
          </Link>
          <Link href="/escrow" className="border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:border-gold hover:text-gold">
            Inspect Route hold controls
          </Link>
          <span className="ml-auto font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Scenario data · deliberate ambiguity test</span>
        </div>
      </div>
    </section>
  )
}

function IncidentCard({ title, accent, children }: { title: string; accent: 'gold' | 'danger' | 'muted'; children: ReactNode }) {
  const color = accent === 'danger' ? 'border-danger/45' : accent === 'gold' ? 'border-gold/35' : 'border-border'
  return (
    <div className={`border bg-background/45 p-5 ${color}`}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{title}</div>
      <div className="mt-5">{children}</div>
    </div>
  )
}
