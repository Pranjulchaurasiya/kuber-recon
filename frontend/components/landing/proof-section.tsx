'use client'

import { CheckCircle2, XCircle, AlertTriangle, ShieldCheck, Zap, Database, ArrowUpRight } from 'lucide-react'

export function ProofSection() {
  return (
    <section className="space-y-10 py-6" id="the-proof">
      {/* Section Header */}
      <div className="text-center space-y-3 max-w-3xl mx-auto animate-fade-up">
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-panel px-3 py-1 text-xs font-mono font-semibold text-gain">
          <span className="h-2 w-2 rounded-full bg-gain animate-status-dot" />
          Empirical Invariant Benchmarks
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-foreground">
          Measured against the methods it replaces.
        </h2>
        <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
          Every assertion in Kuber OS is backed by automated property-based fuzzing and static AST verification. We do not use probabilistic LLM guesses for money reconciliation.
        </p>
      </div>

      {/* 3 Benchmark Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Card 1: Traditional Credit Bureau */}
        <div className="flex flex-col justify-between rounded-2xl border border-border bg-panel p-6 shadow-sm hover-glow animate-fade-up stagger-1">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="font-mono text-xs font-bold text-muted-foreground uppercase">Baseline 01</span>
              <span className="rounded-full bg-muted px-2.5 py-0.5 font-mono text-[10px] font-semibold text-muted-foreground">
                Historical Bank Model
              </span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground">Bureau & Bank Statements</h3>
              <p className="text-xs text-muted-foreground mt-1">Self-reported PDFs and quarterly CIBIL pull.</p>
            </div>

            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Default Rate (MSME)</span>
                <span className="font-mono font-bold text-rose-500">12.4%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                <div className="bg-rose-500 h-full rounded-full" style={{ width: '45%' }} />
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Underwriting Latency</span>
                <span className="font-mono font-semibold text-foreground">3 – 5 Days</span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Line-Item Delivery Proof</span>
                <span className="font-mono font-semibold text-rose-500">0.0% (None)</span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Recovery Enforcement</span>
                <span className="font-mono font-semibold text-muted-foreground">NACH Debit (Bouncable)</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-border/80 text-[11px] text-muted-foreground flex items-center gap-1.5">
            <XCircle className="h-3.5 w-3.5 text-rose-500 shrink-0" />
            Unsecured, lagging, high default exposure.
          </div>
        </div>

        {/* Card 2: Probabilistic LLM Parser */}
        <div className="flex flex-col justify-between rounded-2xl border border-border bg-panel p-6 shadow-sm hover-glow animate-fade-up stagger-2">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="font-mono text-xs font-bold text-muted-foreground uppercase">Baseline 02</span>
              <span className="rounded-full bg-amber-500/10 px-2.5 py-0.5 font-mono text-[10px] font-semibold text-amber-500 border border-amber-500/20">
                LLM Wrapper Pattern
              </span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground">Probabilistic LLM Recon</h3>
              <p className="text-xs text-muted-foreground mt-1">Prompted GPT/Claude ledger text parsing.</p>
            </div>

            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">False Match Rate (FMR)</span>
                <span className="font-mono font-bold text-amber-500">0.041 (4.1% Error)</span>
              </div>
              <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                <div className="bg-amber-500 h-full rounded-full" style={{ width: '28%' }} />
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Hallucination Risk</span>
                <span className="font-mono font-semibold text-amber-500">&gt; 3.5% on Edge Cases</span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Arithmetic Precision</span>
                <span className="font-mono font-semibold text-rose-500">IEEE-754 Floats (Unsafe)</span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Audit Defensibility</span>
                <span className="font-mono font-semibold text-muted-foreground">Non-Deterministic</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-border/80 text-[11px] text-muted-foreground flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0" />
            Unacceptable for RBI regulatory compliance.
          </div>
        </div>

        {/* Card 3: APEX Neurosymbolic Kernel (Ours) */}
        <div className="relative flex flex-col justify-between rounded-2xl border-2 border-gain bg-panel p-6 shadow-xl ring-4 ring-gain/10 hover-glow animate-fade-up stagger-3">
          {/* Top Tag */}
          <div className="absolute -top-3 right-6 rounded-full bg-gain px-3 py-0.5 font-mono text-[10px] font-bold text-white uppercase shadow">
            APEX KERNEL (OURS)
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="font-mono text-xs font-bold text-gain uppercase">Determinism Standard</span>
              <span className="rounded-full bg-gain/10 px-2.5 py-0.5 font-mono text-[10px] font-semibold text-gain border border-gain/30">
                81/81 Tests Passing
              </span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground">APEX Knuth + Bayesian SRI</h3>
              <p className="text-xs text-muted-foreground mt-1">Paise-exact combinatorial subset solver & Route sweeps.</p>
            </div>

            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">False Match Rate (FMR)</span>
                <span className="font-mono font-extrabold text-gain">0.000 (Exact 0/11,100)</span>
              </div>
              <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                <div className="bg-gain h-full rounded-full" style={{ width: '100%' }} />
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Solver Latency</span>
                <span className="font-mono font-bold text-primary">7.34 ms (Sub-10ms)</span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Floating-Point Policy</span>
                <span className="font-mono font-bold text-gain">0 Floats (100% Base-10 AST)</span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Over-Recovery Guarantee</span>
                <span className="font-mono font-bold text-gain">Strictly ₹0.00 Underflow</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-border/80 text-[11px] font-medium text-gain flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-gain shrink-0" />
            100% mathematically bounded and auditor-ready.
          </div>
        </div>

      </div>
    </section>
  )
}
