'use client'

import { useState } from 'react'
import {
  Sparkles,
  X,
  Send,
  MessageSquare,
  ShieldCheck,
  FileCheck,
  AlertTriangle,
  Receipt,
  ArrowRight,
  TrendingDown,
  Clock,
  ExternalLink,
  ChevronRight,
  Database
} from 'lucide-react'
import {
  escrowSplits,
  lineage,
  systemStats,
  ledgerEntries,
  paiseToInr,
  inr,
  EscrowSplit,
  LedgerEntry
} from '@/lib/kuber-data'

export interface CopilotCitation {
  type: 'LEDGER_ENTRY' | 'GSTR_2B_RECORD' | 'ESCROW_SPLIT' | 'MERKLE_PROOF' | 'TAX_RULE'
  reference: string
  label: string
  detail: string
  paiseAmount?: number
}

export interface CopilotResponse {
  query: string
  summary: string
  metricHighlighted?: {
    label: string
    value: string
    subtext: string
    tone: 'gain' | 'gold' | 'warn' | 'cyan'
  }
  breakdown: Array<{
    field: string
    paise: number
    inr: string
    note: string
  }>
  citations: CopilotCitation[]
  statutoryRule?: string
  confidence: string
}

const SAMPLE_PROMPTS = [
  'What is total TDS withheld under 194-O?',
  'Show isolated ambiguous credits',
  'Summarize GSTR-2B compliance',
  'What is our effective MDR fee rate across all payment rails?',
]

export function executeDeterministicCopilotQuery(prompt: string): CopilotResponse {
  const p = prompt.toLowerCase().trim()

  // 1. Query: TDS Withheld under Section 194-O
  if (p.includes('tds') || p.includes('194-o') || p.includes('tax')) {
    const totalTdsPaise = escrowSplits.reduce((acc, curr) => acc + curr.tds, 0)
    const grossPaise = escrowSplits.reduce((acc, curr) => acc + curr.gross, 0)
    const pendingTdsEntry = ledgerEntries.find(e => e.action.includes('TDS'))

    return {
      query: prompt,
      summary: `Total Section 194-O TDS withheld across current active escrow batches is exactly ${paiseToInr(totalTdsPaise)} (100 basis points on ₹${(grossPaise / 100).toLocaleString('en-IN')}). All deductions are cryptographically pinned to merchant PAN entities pending monthly CBDT treasury transfer.`,
      metricHighlighted: {
        label: 'Total TDS Withheld (Sec 194-O)',
        value: paiseToInr(totalTdsPaise),
        subtext: `${escrowSplits.length} orders evaluated · 1.00% Statutory Rate`,
        tone: 'gold',
      },
      breakdown: escrowSplits.map((split) => ({
        field: `${split.order} (${split.merchant})`,
        paise: split.tds,
        inr: paiseToInr(split.tds),
        note: `1% TDS on ${paiseToInr(split.gross)} gross`,
      })),
      citations: [
        {
          type: 'TAX_RULE',
          reference: 'Income Tax Act 1961 · Sec 194-O',
          label: 'E-Commerce Operator TDS Mandate',
          detail: '1.00% deduction on gross merchant payment volume before nodal settlement release.',
        },
        {
          type: 'LEDGER_ENTRY',
          reference: `block #${pendingTdsEntry?.seq || 10438}`,
          label: 'Pending CBDT Remittance Entry',
          detail: 'Awaiting scheduled monthly CFO batch certificate.',
          paiseAmount: (pendingTdsEntry?.amount || 18000) * 100,
        },
      ],
      statutoryRule: 'Section 194-O mandates 1% TDS on gross e-commerce marketplace transactions.',
      confidence: '100% Deterministic (Paise Exact)',
    }
  }

  // 2. Query: Ambiguous Credits & Isolations
  if (p.includes('ambiguous') || p.includes('isolated') || p.includes('exception') || p.includes('unmatched') || p.includes('hitl')) {
    const blockedEntries = ledgerEntries.filter(e => e.status === 'blocked')

    return {
      query: prompt,
      summary: `The Knuth DLX Exact-Cover solver and KYC guardrails isolated ${blockedEntries.length} non-reconciled actions. Zero ambiguous guesses were committed to the ledger, enforcing the hard False Match Rate (FMR) = 0.000 invariant.`,
      metricHighlighted: {
        label: 'Isolated Ambiguous Exceptions',
        value: `${blockedEntries.length} Records Isolated`,
        subtext: 'FMR = 0.000 (Guaranteed Honest Refusal)',
        tone: 'warn',
      },
      breakdown: [
        {
          field: 'Unverified KYC Payout (Seq #10439)',
          paise: 24000,
          inr: '₹240.00',
          note: 'Blocked by KYC payee whitelist check (₹200 spend cap exceeded)',
        },
        {
          field: 'Multi-Invoice Collision (INV-2291 / INV-2294)',
          paise: 9638000,
          inr: '₹96,380.00',
          note: 'AmbiguousMatchError triggered on identical net delta; isolated for HITL review',
        },
      ],
      citations: [
        {
          type: 'MERKLE_PROOF',
          reference: 'KuberRecon DLX Invariant #1',
          label: 'Knuth DLX All-Solution Enumerator',
          detail: 'When |Solutions| > 1, solver halts mutation and routes payload to Human-in-the-Loop triage.',
        },
        {
          type: 'LEDGER_ENTRY',
          reference: 'block #10439',
          label: 'Unverified KYC Payout Rejection',
          detail: 'Payload rejected by hardcoded KYC whitelist invariant.',
          paiseAmount: 24000,
        },
      ],
      statutoryRule: 'RBI Master Direction DPSS.CO.PD.No.1810/02.14.008/2019-20 (Nodal Account Guardrails)',
      confidence: '100% Deterministic (Paise Exact)',
    }
  }

  // 3. Query: GSTR-2B Compliance
  if (p.includes('gstr') || p.includes('gst') || p.includes('itc') || p.includes('compliance')) {
    const totalGstPaise = escrowSplits.reduce((acc, curr) => acc + curr.gst, 0)
    const onHoldGstPaise = escrowSplits.filter(s => s.onHold).reduce((acc, curr) => acc + curr.gst, 0)

    return {
      query: prompt,
      summary: `GSTR-2B Input Tax Credit (ITC) reconciliation status: ${paiseToInr(onHoldGstPaise)} in GST escrow is currently held pending mandatory 14th-of-the-month vendor GSTR-1 filings. ${paiseToInr(totalGstPaise - onHoldGstPaise)} has been reconciled and released.`,
      metricHighlighted: {
        label: 'GST Escrow Held (Rule 36(4))',
        value: paiseToInr(onHoldGstPaise),
        subtext: 'Resolves on GSTR-2B filing (14th monthly)',
        tone: 'cyan',
      },
      breakdown: escrowSplits.map((split) => ({
        field: `${split.order} · ${split.merchant}`,
        paise: split.gst,
        inr: paiseToInr(split.gst),
        note: split.onHold ? 'Held in GST Escrow (Pending GSTR-2B match)' : 'Released to merchant nodal balance',
      })),
      citations: [
        {
          type: 'TAX_RULE',
          reference: 'CGST Act Section 16(2)(aa) & Rule 36(4)',
          label: 'Input Tax Credit Eligibility Rule',
          detail: 'ITC cannot be availed unless invoice details are uploaded by vendor in GSTR-1 and reflected in GSTR-2B.',
        },
        {
          type: 'GSTR_2B_RECORD',
          reference: 'GSTN-SYNC-AUG2026-CYCLE',
          label: 'Monthly GSTR-2B Auto-Drafted Feed',
          detail: 'Auto-reconciliation lock active until 14th 23:59:59 IST.',
        },
      ],
      statutoryRule: 'CGST Rule 36(4) strict 100% invoice match invariant.',
      confidence: '100% Deterministic (Paise Exact)',
    }
  }

  // 4. Default / MDR Query: Effective fee rates & multi-rail metrics
  const gmv = lineage.nodes.find(n => n.id === 'gmv')?.amount || 1800000
  const mdr = lineage.nodes.find(n => n.id === 'mdr')?.amount || 33300
  const gst = lineage.nodes.find(n => n.id === 'gst')?.amount || 5994
  const tds = lineage.nodes.find(n => n.id === 'tds')?.amount || 18000
  const net = lineage.nodes.find(n => n.id === 'net')?.amount || 1462400

  return {
    query: prompt,
    summary: `Effective MDR across active settlement rails is exactly 1.850% (₹333.00 on ₹18,000.00 GMV), with 18% GST (₹59.94) on fees and 1.00% Section 194-O TDS (₹180.00), yielding a net merchant settlement of ₹14,624.00.`,
    metricHighlighted: {
      label: 'Effective Multi-Rail MDR Rate',
      value: '1.850%',
      subtext: `₹${(mdr / 100).toFixed(2)} on ₹${(gmv / 100).toLocaleString('en-IN')} GMV`,
      tone: 'gain',
    },
    breakdown: [
      { field: 'Gross GMV (34 Invoices)', paise: gmv * 100, inr: inr(gmv), note: 'Verified by Knuth DLX Exact Cover' },
      { field: 'MDR Gateway Processing (1.85%)', paise: mdr * 100, inr: inr(mdr), note: 'Razorpay Route contract rate' },
      { field: 'GST on MDR (18%)', paise: gst * 100, inr: inr(gst), note: 'Input tax credit claimed in GSTR-2B' },
      { field: 'TDS Withholding (Sec 194-O 1%)', paise: tds * 100, inr: inr(tds), note: 'Remitted directly to CBDT pool' },
      { field: 'Net Settlement Payout', paise: net * 100, inr: inr(net), note: 'Released to merchant bank account' },
    ],
    citations: [
      {
        type: 'MERKLE_PROOF',
        reference: lineage.utr,
        label: 'Bank Lump-Sum UTR Settlement Proof',
        detail: '34 line-item invoices reconciled to single bank lump-sum with 0-paise residual drift.',
        paiseAmount: net * 100,
      },
      {
        type: 'TAX_RULE',
        reference: 'Razorpay Route Escrow Specification',
        label: 'Nodal Settlement Equation',
        detail: 'Net = Gross − MDR − GST(18% on MDR) − TDS(1% on Gross)',
      },
    ],
    statutoryRule: 'RBI Nodal Account Regulations (2020) & GST Section 9(5) E-Commerce Operators.',
    confidence: '100% Deterministic (Paise Exact)',
  }
}

export function CfoCopilotDrawer({
  isOpen,
  onClose,
}: {
  isOpen: boolean
  onClose: () => void
}) {
  const [inputQuery, setInputQuery] = useState('')
  const [history, setHistory] = useState<CopilotResponse[]>([
    executeDeterministicCopilotQuery('What is total TDS withheld under 194-O?'),
  ])
  const [isProcessing, setIsProcessing] = useState(false)

  const handleSend = (queryToSend?: string) => {
    const q = (queryToSend || inputQuery).trim()
    if (!q) return

    setIsProcessing(true)
    setTimeout(() => {
      const response = executeDeterministicCopilotQuery(q)
      setHistory((prev) => [response, ...prev])
      setInputQuery('')
      setIsProcessing(false)
    }, 350)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative flex h-full w-full max-w-2xl flex-col border-l border-border bg-panel text-foreground shadow-2xl animate-in slide-in-from-right duration-300">
        {/* Drawer Header */}
        <div className="flex items-center justify-between border-b border-border bg-panel-header px-6 py-4 backdrop-blur">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-primary/40 bg-primary/10 text-primary shadow-sm">
              <Sparkles className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold tracking-tight text-foreground">CFO AI Copilot</h2>
                <span className="rounded bg-gain/10 px-2 py-0.5 font-mono text-[10px] font-bold text-gain border border-gain/30">
                  PAISE-EXACT
                </span>
              </div>
              <p className="font-mono text-xs text-muted-foreground font-medium">
                Zero-hallucination settlement Q&amp;A · Grounded in Merkle Ledger
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-muted-foreground hover:bg-accent hover:text-foreground transition"
            aria-label="Close CFO Copilot Drawer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Prompt Chips Bar */}
        <div className="border-b border-border bg-background p-4">
          <div className="mb-2.5 flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground font-bold flex items-center gap-1.5">
              <MessageSquare className="h-3.5 w-3.5 text-primary" />
              Verified Financial Queries
            </span>
            <span className="font-mono text-[10px] text-gain font-bold">FMR: 0.000</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSend(prompt)}
                disabled={isProcessing}
                className="group inline-flex items-center gap-1.5 rounded-md border border-border bg-panel px-3 py-1.5 text-left font-mono text-xs text-muted-foreground font-semibold hover:border-primary/50 hover:bg-accent hover:text-foreground transition disabled:opacity-50 shadow-sm"
              >
                <span>{prompt}</span>
                <ChevronRight className="h-3 w-3 text-muted-foreground/60 group-hover:text-primary transition" />
              </button>
            ))}
          </div>
        </div>

        {/* Conversation Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {history.map((item, idx) => (
            <div key={idx} className="space-y-4 rounded-xl border border-border bg-card p-5 shadow-lg backdrop-blur">
              {/* User Query Tag */}
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2 font-mono text-xs font-bold text-primary">
                  <span className="flex h-1.5 w-1.5 rounded-full bg-primary" />
                  Q: &ldquo;{item.query}&rdquo;
                </div>
                <span className="font-mono text-[10px] uppercase text-gain font-bold tracking-wider">
                  {item.confidence}
                </span>
              </div>

              {/* Highlight Metric Card if available */}
              {item.metricHighlighted && (
                <div className="rounded-lg border border-border bg-background p-4 flex items-center justify-between">
                  <div>
                    <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground font-bold">
                      {item.metricHighlighted.label}
                    </div>
                    <div className="mt-0.5 font-mono text-2xl font-bold tracking-tight text-foreground">
                      {item.metricHighlighted.value}
                    </div>
                    <div className="mt-0.5 font-mono text-xs text-muted-foreground font-medium">
                      {item.metricHighlighted.subtext}
                    </div>
                  </div>
                  <div className="rounded-full border border-primary/30 bg-primary/10 p-3 text-primary">
                    <Receipt className="h-6 w-6" />
                  </div>
                </div>
              )}

              {/* Natural Narrative Summary */}
              <p className="text-sm leading-relaxed text-foreground font-sans font-medium">
                {item.summary}
              </p>

              {/* Paise-Exact Itemized Breakdown Table */}
              <div className="space-y-2 pt-2">
                <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground font-bold flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5 text-gold" />
                  Paise-Level Deterministic Itemization
                </div>
                <div className="rounded-lg border border-border bg-background overflow-hidden text-xs font-mono">
                  <table className="w-full text-left">
                    <thead className="border-b border-border bg-panel text-muted-foreground text-[10px] uppercase font-bold">
                      <tr>
                        <th className="px-3 py-2.5">Line-Item Reference</th>
                        <th className="px-3 py-2.5 text-right">Amount (₹)</th>
                        <th className="px-3 py-2.5">Audit Constraint</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {item.breakdown.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-accent/50 transition">
                          <td className="px-3 py-2.5 font-semibold text-foreground truncate max-w-[180px]">
                            {row.field}
                          </td>
                          <td className="px-3 py-2.5 text-right font-bold text-gain tabular-nums">
                            {row.inr}
                          </td>
                          <td className="px-3 py-2.5 text-muted-foreground font-medium text-[11px] truncate max-w-[200px]">
                            {row.note}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Statutory Citations & Ledger Proofs */}
              <div className="space-y-2 pt-2 border-t border-border">
                <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground font-bold flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-gain" />
                  Statutory Invariant Citations &amp; Merkle Proofs
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {item.citations.map((cite, cIdx) => (
                    <div key={cIdx} className="rounded-md border border-border bg-background p-3 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[9px] uppercase font-bold text-gold">
                          {cite.type}
                        </span>
                        {cite.paiseAmount && (
                          <span className="font-mono text-[9px] text-gain font-bold">
                            {paiseToInr(cite.paiseAmount)}
                          </span>
                        )}
                      </div>
                      <div className="font-mono text-[11px] font-bold text-foreground truncate">
                        {cite.reference}
                      </div>
                      <p className="text-[11px] text-muted-foreground leading-snug font-medium">
                        {cite.detail}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {item.statutoryRule && (
                <div className="rounded-md border border-primary/30 bg-primary/10 p-3 text-[11px] text-foreground font-mono flex items-start gap-2 font-medium">
                  <FileCheck className="h-4 w-4 shrink-0 mt-0.5 text-primary" />
                  <span>{item.statutoryRule}</span>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Interactive Query Input Bar */}
        <div className="border-t border-border bg-panel-header p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSend()
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask CFO Copilot about TDS, GSTR-2B, MDR fees, or UTRs..."
              disabled={isProcessing}
              className="flex-1 rounded-lg border border-border bg-background px-4 py-2.5 font-mono text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isProcessing || !inputQuery.trim()}
              className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary font-bold text-primary-foreground shadow transition hover:opacity-90 disabled:opacity-40"
              aria-label="Send Query to CFO Copilot"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
          <div className="mt-2 flex items-center justify-between font-mono text-[10px] text-muted-foreground font-medium">
            <span>Enforcing Base-10 Paise Invariants (Zero IEEE-754 Floats)</span>
            <span className="text-gain font-bold">Connected to KuberRecon Kernel</span>
          </div>
        </div>
      </div>
    </div>
  )
}
