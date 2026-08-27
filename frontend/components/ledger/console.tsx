'use client'

import { useState } from 'react'
import { ledgerEntries as seed, guardrails, inr, type LedgerEntry } from '@/lib/kuber-data'
import { Pill } from '@/components/kuber/primitives'

function randHash(len = 4) {
  return '0x' + Array.from({ length: len }, () => Math.floor(Math.random() * 16).toString(16)).join('') + '…' + Array.from({ length: len }, () => Math.floor(Math.random() * 16).toString(16)).join('')
}

export function LedgerConsole() {
  const [entries, setEntries] = useState<LedgerEntry[]>(seed)
  const [selected, setSelected] = useState<LedgerEntry | null>(null)
  const [signing, setSigning] = useState(false)

  const certify = (entry: LedgerEntry) => {
    setSigning(true)
    setTimeout(() => {
      setEntries((prev) =>
        prev.map((e) =>
          e.seq === entry.seq
            ? { ...e, status: 'certified', hash: randHash(), sig: 'ed25519:' + randHash(2).replace('0x', '') }
            : e,
        ),
      )
      setSigning(false)
      setSelected(null)
    }, 1100)
  }

  const certifiedCount = entries.filter((e) => e.status === 'certified').length

  return (
    <>
      {/* Guardrails */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {guardrails.map((g) => (
          <div key={g.label} className="rounded-lg border border-border bg-panel p-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                Guardrail
              </span>
              <span className="h-1.5 w-1.5 rounded-full bg-gain" />
            </div>
            <div className="mt-2 text-sm font-medium">{g.label}</div>
            <div className="mt-0.5 font-mono text-xs text-gain">{g.value}</div>
          </div>
        ))}
      </div>

      {/* Merkle chain */}
      <div className="mt-6 rounded-lg border border-border bg-panel">
        <div className="flex items-center justify-between border-b border-border p-5">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            Merkle Ledger · RFC 6962
          </h2>
          <Pill tone="gain">chain verified</Pill>
        </div>
        <div className="flex items-center gap-1 overflow-x-auto p-5">
          {entries
            .filter((e) => e.status === 'certified')
            .slice(0, 5)
            .reverse()
            .map((e, i, arr) => (
              <div key={e.seq} className="flex items-center gap-1">
                <div className="w-40 shrink-0 rounded-md border border-gain/30 bg-gain/5 p-3">
                  <div className="font-mono text-[10px] text-muted-foreground">block #{e.seq}</div>
                  <div className="mt-1 truncate font-mono text-xs text-gain">{e.hash}</div>
                  <div className="mt-1 truncate font-mono text-[10px] text-muted-foreground">{e.sig}</div>
                </div>
                {i < arr.length - 1 && <span className="font-mono text-gold">→</span>}
              </div>
            ))}
          <div className="ml-2 flex h-full items-center">
            <span className="animate-pulse-dot font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              {certifiedCount} certified
            </span>
          </div>
        </div>
      </div>

      {/* Action queue */}
      <div className="mt-6 rounded-lg border border-border bg-panel">
        <div className="flex items-center justify-between border-b border-border p-5">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            Bounded Self-Healing Queue
          </h2>
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            human-in-the-loop
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-sm">
            <thead>
              <tr className="border-b border-border font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                <th className="px-5 py-3 text-left font-medium">Seq</th>
                <th className="px-5 py-3 text-left font-medium">Action</th>
                <th className="px-5 py-3 text-left font-medium">Payee</th>
                <th className="px-5 py-3 text-right font-medium">Amount</th>
                <th className="px-5 py-3 text-right font-medium">Cap</th>
                <th className="px-5 py-3 text-left font-medium">Status</th>
                <th className="px-5 py-3 text-right font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="font-mono tabular-nums">
              {entries.map((e) => {
                const overCap = e.amount > e.cap
                return (
                  <tr key={e.seq} className="border-b border-border/60 last:border-0 transition-colors hover:bg-accent/30">
                    <td className="px-5 py-3 text-muted-foreground">{e.seq}</td>
                    <td className="px-5 py-3 font-sans">{e.action}</td>
                    <td className={`px-5 py-3 font-sans ${e.payee === 'Unverified KYC' ? 'text-danger' : 'text-muted-foreground'}`}>
                      {e.payee}
                    </td>
                    <td className={`px-5 py-3 text-right ${overCap ? 'text-danger' : ''}`}>{inr(e.amount)}</td>
                    <td className="px-5 py-3 text-right text-muted-foreground">{inr(e.cap)}</td>
                    <td className="px-5 py-3">
                      {e.status === 'certified' && <Pill tone="gain">certified</Pill>}
                      {e.status === 'pending' && <Pill tone="warn">pending</Pill>}
                      {e.status === 'blocked' && <Pill tone="danger">blocked</Pill>}
                    </td>
                    <td className="px-5 py-3 text-right">
                      {e.status === 'pending' && (
                        <button
                          onClick={() => setSelected(e)}
                          className="rounded-md bg-gold px-3 py-1.5 font-sans text-xs font-medium text-gold-foreground transition-opacity hover:opacity-90"
                        >
                          Review
                        </button>
                      )}
                      {e.status === 'blocked' && (
                        <span className="font-sans text-xs text-danger">cap / KYC fail</span>
                      )}
                      {e.status === 'certified' && (
                        <span className="font-sans text-xs text-muted-foreground">signed</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* CFO Approval Drawer */}
      {selected && (
        <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-label="CFO approval">
          <button
            className="absolute inset-0 bg-background/70 backdrop-blur-sm"
            onClick={() => !signing && setSelected(null)}
            aria-label="Close drawer"
          />
          <div className="relative flex h-full w-full max-w-md flex-col border-l border-border bg-panel shadow-2xl">
            <div className="flex items-center justify-between border-b border-border p-5">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-gold">CFO Approval Drawer</div>
                <h3 className="mt-1 text-lg font-semibold">{selected.action}</h3>
              </div>
              <button onClick={() => !signing && setSelected(null)} className="text-muted-foreground hover:text-foreground" aria-label="Close">
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              <dl className="flex flex-col gap-4 font-mono text-sm">
                <Row k="Payee" v={selected.payee} />
                <Row k="Amount" v={inr(selected.amount)} />
                <Row k="Spend cap" v={inr(selected.cap)} />
                <Row k="Sequence" v={`#${selected.seq}`} />
              </dl>

              <div className="mt-6 flex flex-col gap-2">
                <Check
                  ok
                  label={selected.cap > 1000 ? `Statutory limit (${inr(selected.amount)} ≤ ${inr(selected.cap)})` : `Within ${inr(selected.cap)} spend cap`}
                  detail={selected.cap > 1000 ? "Statutory tax remittance cap" : `${inr(selected.amount)} ≤ ${inr(selected.cap)}`}
                />
                <Check ok label="Payee on KYC whitelist" detail="Verified merchant" />
                <Check ok label="Merkle predecessor valid" detail="RFC 6962 inclusion proof" />
                <Check ok label="Ready for Ed25519 signature" detail="Awaiting CFO key" />
              </div>

              <div className="mt-6 rounded-md border border-gold/30 bg-gold/5 p-4 text-xs leading-relaxed text-muted-foreground">
                Signing appends a cryptographically-sealed block to the Merkle ledger and releases the
                bounded adjustment payout. This action is irreversible and fully audited.
              </div>
            </div>

            <div className="border-t border-border p-5">
              <button
                onClick={() => certify(selected)}
                disabled={signing}
                className="flex w-full items-center justify-center gap-2 rounded-md bg-gold py-3 font-medium text-gold-foreground transition-opacity hover:opacity-90 disabled:opacity-60"
              >
                {signing ? (
                  <>
                    <span className="h-2 w-2 animate-pulse-dot rounded-full bg-gold-foreground" />
                    Signing with Ed25519…
                  </>
                ) : (
                  'Sign & Certify Payout'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 pb-2">
      <dt className="text-[11px] uppercase tracking-widest text-muted-foreground">{k}</dt>
      <dd className="text-foreground">{v}</dd>
    </div>
  )
}

function Check({ ok, label, detail }: { ok: boolean; label: string; detail: string }) {
  return (
    <div className="flex items-start gap-3 rounded-md border border-border bg-background p-3">
      <span className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full ${ok ? 'bg-gain/15 text-gain' : 'bg-danger/15 text-danger'}`}>
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none" aria-hidden="true">
          <path d="M2.5 6.5l2.5 2.5 4.5-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      <div>
        <div className="font-sans text-sm">{label}</div>
        <div className="font-mono text-[11px] text-muted-foreground">{detail}</div>
      </div>
    </div>
  )
}
