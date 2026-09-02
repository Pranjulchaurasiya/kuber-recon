'use client'

import { Code2, GitCommit, Shield, Cpu, Lock, ArrowDown, CheckCircle2 } from 'lucide-react'

export function HowItWorksSection() {
  const steps = [
    {
      num: '01',
      title: 'Pre-Settlement Interception',
      code: 'POST /v1/transfers on_hold: true',
      desc: 'Buyer agent transactions are captured at the Razorpay Route gateway. Funds are locked in the sovereign nodal account with on_hold: true before reaching the merchant bank account.',
      tag: 'Razorpay Route',
    },
    {
      num: '02',
      title: 'Mod-36 GSTIN & Horowitz–Sahni Subset-Sum',
      code: 'src/kuber_recon/engine.py',
      desc: 'Our Horowitz–Sahni meet-in-the-middle subset-sum solver matches incoming lump-sum UTRs against line-item invoices, subtracting Section 194-O TDS and GST with 0 floating-point operations.',
      tag: 'Horowitz–Sahni Subset-Sum',
    },
    {
      num: '03',
      title: 'Bayesian SRI Underwriting',
      code: 'capital.py:compute_sri',
      desc: 'Merchant reliability is scored using Bayesian shrinkage with an uninformative prior (N₀=50, p₀=0.98), preventing wild swings from low-volume noise.',
      tag: 'Bayesian Prior',
    },
    {
      num: '04',
      title: 'Continuous Pricing & 1-Click Advance',
      code: 'POST /api/capital/drawdown',
      desc: 'Linear interpolation across SRI [0.9300, 0.9700] eliminates cliff-edge jumps. The merchant draws down up to ₹59,764.78 instantly via simulated Razorpay Payouts.',
      tag: 'Zero Cliff-Edge',
    },
    {
      num: '05',
      title: 'Automated Split-Settlement Recovery',
      code: 'POST /api/capital/reconcile-and-sweep',
      desc: 'As new delivery-verified settlements clear, Razorpay Route simulated hooks sweep 12.0% at the nodal source, amortizing the advance down to exactly ₹0.00.',
      tag: 'Split-Settlement Recovery',
    },
    {
      num: '06',
      title: 'Immutable Evidence & CAS Finality',
      code: 'SQLite WAL / PostgreSQL CAS',
      desc: 'Every transition executes Compare-And-Swap (HELD → RELEASING → RELEASED) with signed Ed25519 webhook manifests. 100% auditable under RBI Digital Lending Norms.',
      tag: '5% FLDG Guard',
    },
  ]

  return (
    <section className="space-y-10 py-6" id="how-it-works">
      {/* Section Header */}
      <div className="text-center space-y-3 max-w-3xl mx-auto animate-fade-up">
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-panel px-3 py-1 text-xs font-mono font-semibold text-primary">
          <span className="h-2 w-2 rounded-full bg-primary animate-status-dot" />
          Deterministic Pipeline Trace
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-foreground">
          Deterministic where it must be.<br />
          <span className="text-primary">Autonomous where it scales.</span>
        </h2>
        <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
          No probabilistic LLM decides whether money moves. Every step is bounded by rigorous base-10 mathematics, cryptographic signatures, and Razorpay Route nodal controls.
        </p>
      </div>

      {/* 6-Step Vertical Timeline Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {steps.map((step, idx) => (
          <div
            key={step.num}
            className={`relative flex flex-col justify-between rounded-2xl border border-border bg-panel p-6 shadow-sm hover-glow animate-fade-up stagger-${(idx % 5) + 1}`}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xl font-extrabold text-primary">{step.num}</span>
                <span className="rounded bg-accent px-2 py-0.5 font-mono text-[10px] font-bold text-muted-foreground border border-border">
                  {step.tag}
                </span>
              </div>

              <div>
                <h3 className="text-base font-bold text-foreground">{step.title}</h3>
                <div className="mt-1 inline-block font-mono text-[11px] text-primary/90 bg-primary/10 px-2 py-0.5 rounded border border-primary/20">
                  {step.code}
                </div>
              </div>

              <p className="text-xs text-muted-foreground leading-relaxed pt-1">
                {step.desc}
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-border/60 flex items-center gap-1.5 text-[11px] font-mono text-gain">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Verified Invariant
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
