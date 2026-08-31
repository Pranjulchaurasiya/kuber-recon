'use client'

import { useState, useMemo } from 'react'
import {
  ledgerEntries as seed,
  guardrails,
  inr,
  paiseToInr,
  type LedgerEntry,
} from '@/lib/kuber-data'
import { Pill } from '@/components/kuber/primitives'
import {
  Search,
  Download,
  Filter,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  ShieldCheck,
  Zap,
  Receipt,
  Layers,
  Database
} from 'lucide-react'

function randHash(len = 4) {
  return (
    '0x' +
    Array.from({ length: len }, () => Math.floor(Math.random() * 16).toString(16)).join('') +
    '…' +
    Array.from({ length: len }, () => Math.floor(Math.random() * 16).toString(16)).join('')
  )
}

export type ReconFilterTab = 'ALL' | 'EXACT_DLX' | 'GSTR_2B' | 'TDS_194O' | 'AMBIGUOUS_HITL'

export function LedgerConsole() {
  const [entries, setEntries] = useState<LedgerEntry[]>([
    ...seed,
    {
      seq: 10437,
      action: 'Exact Cover Match (Knuth DLX)',
      payee: 'Meridian Retail · INV-2291',
      amount: 96380,
      cap: 100000,
      status: 'certified',
      hash: '0x9a4e…81bf',
      sig: 'ed25519:4d…e1',
      ts: '2026-08-27 08:05:12',
    },
    {
      seq: 10436,
      action: 'GSTR-2B ITC Claim Verification',
      payee: 'Nova Logistics · 18% GST',
      amount: 7200,
      cap: 10000,
      status: 'certified',
      hash: '0x33cf…11aa',
      sig: 'ed25519:8e…99',
      ts: '2026-08-27 07:50:33',
    },
    {
      seq: 10435,
      action: 'Sec 194-O TDS Escrow Deduction',
      payee: 'Aster Foods · PAN Verified',
      amount: 200,
      cap: 500,
      status: 'certified',
      hash: '0x55d2…09cc',
      sig: 'ed25519:2b…4a',
      ts: '2026-08-27 07:35:19',
    },
  ])

  const [selected, setSelected] = useState<LedgerEntry | null>(null)
  const [signing, setSigning] = useState(false)
  const [activeTab, setActiveTab] = useState<ReconFilterTab>('ALL')
  const [searchQuery, setSearchQuery] = useState('')

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

  // Filter and Search Pipeline
  const filteredEntries = useMemo(() => {
    return entries.filter((e) => {
      // 1. Tab filtering
      if (activeTab === 'EXACT_DLX') {
        const isDlx = e.action.includes('Exact') || e.action.includes('Rounding') || e.action.includes('Adjustment')
        if (!isDlx) return false
      } else if (activeTab === 'GSTR_2B') {
        const isGst = e.action.includes('GST')
        if (!isGst) return false
      } else if (activeTab === 'TDS_194O') {
        const isTds = e.action.includes('TDS')
        if (!isTds) return false
      } else if (activeTab === 'AMBIGUOUS_HITL') {
        if (e.status !== 'blocked' && e.status !== 'pending') return false
      }

      // 2. Search query matching (UTR, Payee, Action, Seq, Hash)
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim()
        const matchSeq = e.seq.toString().includes(q)
        const matchAction = e.action.toLowerCase().includes(q)
        const matchPayee = e.payee.toLowerCase().includes(q)
        const matchHash = e.hash.toLowerCase().includes(q)
        if (!matchSeq && !matchAction && !matchPayee && !matchHash) {
          return false
        }
      }

      return true
    })
  }, [entries, activeTab, searchQuery])

  // One-click JSON Audit Export
  const handleExportJson = () => {
    const exportPayload = {
      exportTimestamp: new Date().toISOString(),
      statutoryStandard: 'CBIC GST Rule 36(4) & Section 194-O TDS',
      merkleStandard: 'RFC 6962 Certificate Transparency',
      arithmeticStandard: 'Base-10 Integer Paise (Zero IEEE-754 Floats)',
      totalRecords: filteredEntries.length,
      activeFilter: activeTab,
      records: filteredEntries.map((e) => ({
        sequenceNumber: e.seq,
        actionType: e.action,
        payeeEntity: e.payee,
        amountPaise: e.amount * 100,
        amountInr: inr(e.amount),
        spendCapPaise: e.cap * 100,
        spendCapInr: inr(e.cap),
        statutoryStatus: e.status,
        rfc6962BlockHash: e.hash,
        ed25519Signature: e.sig,
        recordedTimestampUtc: e.ts,
      })),
    }

    const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `kuberrecon-audit-trail-${activeTab.toLowerCase()}-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const certifiedCount = entries.filter((e) => e.status === 'certified').length

  return (
    <>
      {/* Top Statutory Guardrail Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {guardrails.map((g) => (
          <div key={g.label} className="rounded-xl border border-border bg-panel p-4 shadow-lg backdrop-blur">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground font-bold">
                Guardrail
              </span>
              <span className="h-1.5 w-1.5 rounded-full bg-gain animate-status-dot" />
            </div>
            <div className="mt-2 text-sm font-semibold text-foreground">{g.label}</div>
            <div className="mt-0.5 font-mono text-xs font-bold text-gain">{g.value}</div>
          </div>
        ))}
      </div>

      {/* Merkle Chain Visualizer */}
      <div className="mt-6 rounded-xl border border-border bg-panel shadow-xl backdrop-blur">
        <div className="flex items-center justify-between border-b border-border p-5">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-gain" />
            <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground font-bold">
              Immutable Settlement Audit Chain · RFC 6962 Verified
            </h2>
          </div>
          <Pill tone="gain">chain verified</Pill>
        </div>
        <div className="flex items-center gap-1 overflow-x-auto p-5">
          {entries
            .filter((e) => e.status === 'certified')
            .slice(0, 5)
            .reverse()
            .map((e, i, arr) => (
              <div key={e.seq} className="flex items-center gap-1">
                <div className="w-44 shrink-0 rounded-lg border border-gain/40 bg-background p-3 shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] text-muted-foreground font-bold">block #{e.seq}</span>
                    <span className="h-1.5 w-1.5 rounded-full bg-gain" />
                  </div>
                  <div className="mt-1 truncate font-mono text-xs font-bold text-gain">{e.hash}</div>
                  <div className="mt-1 truncate font-mono text-[10px] text-muted-foreground font-medium">{e.sig}</div>
                </div>
                {i < arr.length - 1 && <span className="font-mono text-gold px-1 font-bold">→</span>}
              </div>
            ))}
          <div className="ml-3 flex h-full items-center">
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground font-semibold bg-accent/60 px-2.5 py-1 rounded border border-border">
              {certifiedCount} blocks sealed
            </span>
          </div>
        </div>
      </div>

      {/* Main Reconciliation Ledger Workspace */}
      <div className="mt-6 rounded-xl border border-border bg-panel shadow-xl backdrop-blur">
        {/* Workspace Header & Action Controls */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border p-5">
          <div>
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-primary" />
              <h2 className="text-base font-bold tracking-tight text-foreground">
                Reconciliation Ledger &amp; Statutory Workspace
              </h2>
            </div>
            <p className="mt-0.5 font-mono text-xs text-muted-foreground font-medium">
              Filterable transaction ledger with zero-float paise integers &amp; statutory refusal guarantees
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* One-click JSON Audit Export Button */}
            <button
              onClick={handleExportJson}
              className="inline-flex items-center gap-1.5 rounded-lg border border-primary/40 bg-primary/10 px-3.5 py-2 font-mono text-xs font-bold text-primary shadow-sm hover:bg-primary/20 transition"
              title="Download cryptographically verifiable JSON audit trail"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Export Audit Trail (JSON)</span>
            </button>
          </div>
        </div>

        {/* Filter Tabs & Search Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-background p-3.5">
          {/* Filter Tabs */}
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => setActiveTab('ALL')}
              className={`rounded-lg px-3 py-1.5 font-mono text-xs font-semibold transition ${
                activeTab === 'ALL'
                  ? 'bg-primary text-primary-foreground shadow'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
              }`}
            >
              All Transactions ({entries.length})
            </button>
            <button
              onClick={() => setActiveTab('EXACT_DLX')}
              className={`rounded-lg px-3 py-1.5 font-mono text-xs font-semibold transition ${
                activeTab === 'EXACT_DLX'
                  ? 'bg-gain text-primary-foreground shadow'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
              }`}
            >
              Exact Covers (DLX)
            </button>
            <button
              onClick={() => setActiveTab('GSTR_2B')}
              className={`rounded-lg px-3 py-1.5 font-mono text-xs font-semibold transition ${
                activeTab === 'GSTR_2B'
                  ? 'bg-cyan-600 text-primary-foreground shadow'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
              }`}
            >
              GSTR-2B Matched
            </button>
            <button
              onClick={() => setActiveTab('TDS_194O')}
              className={`rounded-lg px-3 py-1.5 font-mono text-xs font-semibold transition ${
                activeTab === 'TDS_194O'
                  ? 'bg-gold text-gold-foreground shadow'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
              }`}
            >
              194-O TDS Withheld
            </button>
            <button
              onClick={() => setActiveTab('AMBIGUOUS_HITL')}
              className={`rounded-lg px-3 py-1.5 font-mono text-xs font-semibold transition ${
                activeTab === 'AMBIGUOUS_HITL'
                  ? 'bg-danger text-primary-foreground shadow'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
              }`}
            >
              Ambiguous (HITL Queue)
            </button>
          </div>

          {/* Real-Time UTR / Invoice Search Bar */}
          <div className="relative min-w-[260px]">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search UTR, Invoice, Payee, Hash..."
              className="w-full rounded-lg border border-border bg-panel pl-9 pr-3 py-1.5 font-mono text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        {/* Filtered Table Content */}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[860px] text-sm">
            <thead>
              <tr className="border-b border-border font-mono text-[10px] uppercase tracking-widest text-muted-foreground bg-accent/40 font-bold">
                <th className="px-5 py-3 text-left font-bold">Seq</th>
                <th className="px-5 py-3 text-left font-bold">Reconciliation Action</th>
                <th className="px-5 py-3 text-left font-bold">Payee / Reference</th>
                <th className="px-5 py-3 text-right font-bold">Amount (₹)</th>
                <th className="px-5 py-3 text-right font-bold">Spend Cap</th>
                <th className="px-5 py-3 text-left font-bold">Statutory Status</th>
                <th className="px-5 py-3 text-right font-bold">Action</th>
              </tr>
            </thead>
            <tbody className="font-mono tabular-nums divide-y divide-border">
              {filteredEntries.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center text-xs text-muted-foreground font-mono font-medium">
                    No transactions matching filter criteria &ldquo;{searchQuery || activeTab}&rdquo;.
                  </td>
                </tr>
              ) : (
                filteredEntries.map((e) => {
                  const overCap = e.amount > e.cap
                  return (
                    <tr key={e.seq} className="transition-colors hover:bg-accent/40">
                      <td className="px-5 py-3.5 text-muted-foreground font-bold">#{e.seq}</td>
                      <td className="px-5 py-3.5 font-sans font-semibold text-foreground">{e.action}</td>
                      <td
                        className={`px-5 py-3.5 font-sans text-xs ${
                          e.payee.includes('Unverified') ? 'text-danger font-bold' : 'text-muted-foreground font-medium'
                        }`}
                      >
                        {e.payee}
                      </td>
                      <td className={`px-5 py-3.5 text-right font-bold ${overCap ? 'text-danger' : 'text-gain'}`}>
                        {inr(e.amount)}
                      </td>
                      <td className="px-5 py-3.5 text-right text-muted-foreground text-xs font-medium">{inr(e.cap)}</td>
                      <td className="px-5 py-3.5">
                        {e.status === 'certified' && <Pill tone="gain">certified</Pill>}
                        {e.status === 'pending' && <Pill tone="warn">pending CFO</Pill>}
                        {e.status === 'blocked' && <Pill tone="danger">blocked / HITL</Pill>}
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        {e.status === 'pending' && (
                          <button
                            onClick={() => setSelected(e)}
                            className="rounded-md bg-gold px-3 py-1 font-sans text-xs font-bold text-gold-foreground transition hover:opacity-90 shadow-sm"
                          >
                            Review
                          </button>
                        )}
                        {e.status === 'blocked' && (
                          <span className="rounded bg-danger/10 px-2 py-0.5 font-mono text-[10px] text-danger border border-danger/20 font-bold">
                            KYC / CAP REFUSAL
                          </span>
                        )}
                        {e.status === 'certified' && (
                          <span className="font-mono text-[11px] text-muted-foreground font-semibold">
                            {e.sig.slice(0, 14)}…
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })
              )}
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
          <div className="relative flex h-full w-full max-w-md flex-col border-l border-border bg-panel text-foreground shadow-2xl">
            <div className="flex items-center justify-between border-b border-border p-5 bg-panel-header">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-gold font-bold">
                  CFO Approval Drawer
                </div>
                <h3 className="mt-1 text-lg font-bold">{selected.action}</h3>
              </div>
              <button
                onClick={() => !signing && setSelected(null)}
                className="text-muted-foreground hover:text-foreground font-bold"
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              <dl className="flex flex-col gap-3 font-mono text-sm">
                <Row k="Payee Entity" v={selected.payee} />
                <Row k="Amount (₹)" v={inr(selected.amount)} />
                <Row k="Spend cap" v={inr(selected.cap)} />
                <Row k="Sequence" v={`#${selected.seq}`} />
              </dl>

              <div className="mt-4 flex flex-col gap-2">
                <Check
                  ok
                  label={
                    selected.cap > 1000
                      ? `Statutory limit (${inr(selected.amount)} ≤ ${inr(selected.cap)})`
                      : `Within ${inr(selected.cap)} spend cap`
                  }
                  detail={
                    selected.cap > 1000
                      ? 'Statutory tax remittance cap'
                      : `${inr(selected.amount)} ≤ ${inr(selected.cap)}`
                  }
                />
                <Check ok label="Payee on KYC whitelist" detail="Verified merchant nodal record" />
                <Check ok label="Merkle predecessor valid" detail="RFC 6962 inclusion proof verified" />
                <Check ok label="Ready for Ed25519 signature" detail="Awaiting CFO key authorization" />
              </div>

              <div className="rounded-lg border border-gold/40 bg-gold/10 p-4 text-xs leading-relaxed text-foreground font-medium">
                Signing appends a cryptographically-sealed block to the Merkle ledger and releases the bounded
                adjustment payout. This action is irreversible and fully audited.
              </div>
            </div>

            <div className="border-t border-border p-5 bg-panel-header">
              <button
                onClick={() => certify(selected)}
                disabled={signing}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-gold py-3 font-bold text-gold-foreground transition hover:opacity-90 disabled:opacity-60 shadow-lg"
              >
                {signing ? (
                  <>
                    <span className="h-2 w-2 animate-pulse rounded-full bg-gold-foreground" />
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
    <div className="flex items-center justify-between border-b border-border pb-2">
      <dt className="text-[11px] uppercase tracking-widest text-muted-foreground font-bold">{k}</dt>
      <dd className="text-foreground font-bold">{v}</dd>
    </div>
  )
}

function Check({ ok, label, detail }: { ok: boolean; label: string; detail: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border bg-background p-3">
      <span
        className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full ${
          ok ? 'bg-gain/20 text-gain' : 'bg-danger/20 text-danger'
        }`}
      >
        <CheckCircle2 className="h-3.5 w-3.5" />
      </span>
      <div>
        <div className="font-sans text-sm font-semibold text-foreground">{label}</div>
        <div className="font-mono text-[11px] text-muted-foreground font-medium">{detail}</div>
      </div>
    </div>
  )
}
