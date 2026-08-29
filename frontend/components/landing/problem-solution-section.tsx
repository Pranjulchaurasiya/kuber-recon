import { AlertTriangle, CheckCircle2, ShieldAlert, Sparkles, XCircle, ArrowRight, Lock, Zap } from 'lucide-react'
import Link from 'next/link'

export function ProblemSolutionSection() {
  return (
    <section className="space-y-8" id="problem-solution">
      <div className="text-center space-y-3 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 font-mono text-xs font-bold text-primary">
          <Sparkles className="h-3.5 w-3.5" /> The Core Problem
        </div>
        <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-foreground">
          Why AI Commerce Breaks —{' '}<span className="text-primary">And How APEX Fixes It</span>
        </h2>
        <p className="text-muted-foreground text-sm sm:text-base">
          Autonomous agents execute purchases in milliseconds. Traditional payment rails settle funds blindly. That gap costs real money.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
        {/* ── 🔴 THE PROBLEM CARD ────────────────────────────────────────── */}
        <div className="rounded-2xl border-2 border-danger/40 bg-panel/90 p-6 sm:p-8 space-y-6 shadow-xl backdrop-blur relative overflow-hidden">
          <div className="absolute top-0 right-0 h-32 w-32 bg-danger/10 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none" />
          
          <div className="flex items-center gap-3 border-b border-border pb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-danger/20 text-danger border border-danger/30 font-bold">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div>
              <span className="font-mono text-xs font-bold text-danger uppercase tracking-wider">The Crisis</span>
              <h3 className="text-xl font-extrabold text-foreground">The Problem in Agentic Commerce</h3>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-start gap-3 rounded-xl border border-danger/20 bg-danger/5 p-3.5">
              <XCircle className="h-5 w-5 text-danger shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-foreground">1. Blind Pre-Settlement Disbursals</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Autonomous AI buyer agents execute orders instantly. But traditional payment gateways disburse funds immediately to the seller <span className="text-danger font-semibold">before verifying if delivery occurred</span> or if the seller is legitimate.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-xl border border-danger/20 bg-danger/5 p-3.5">
              <XCircle className="h-5 w-5 text-danger shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-foreground">2. The AI Hallucination & Math Trap</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Using an LLM to verify invoices causes dangerous hallucinations, phantom line items, and IEEE-754 float rounding drift where <span className="font-mono text-danger font-semibold">0.1 + 0.2 != 0.3</span>.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-xl border border-danger/20 bg-danger/5 p-3.5">
              <XCircle className="h-5 w-5 text-danger shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-foreground">3. Merchant Working Capital Crushes</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Small sellers supplying AI buyer platforms face severe 30-to-45 day cash crunches while funds wait for bank clearing, killing business growth.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-danger/30 bg-danger/10 p-3 text-xs font-mono text-danger font-semibold text-center">
            Result: High fraud, permanent capital loss, and stalled agentic commerce.
          </div>
        </div>

        {/* ── 🟢 THE SOLUTION CARD ────────────────────────────────────────── */}
        <div className="rounded-2xl border-2 border-primary/40 bg-panel/90 p-6 sm:p-8 space-y-6 shadow-xl backdrop-blur relative overflow-hidden">
          <div className="absolute top-0 right-0 h-32 w-32 bg-primary/10 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none" />
          
          <div className="flex items-center gap-3 border-b border-border pb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/20 text-primary border border-primary/30 font-bold">
              <CheckCircle2 className="h-5 w-5" />
            </div>
            <div>
              <span className="font-mono text-xs font-bold text-primary uppercase tracking-wider">The Solution</span>
              <h3 className="text-xl font-extrabold text-foreground">The APEX Autonomous Operating System</h3>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-start gap-3 rounded-xl border border-primary/20 bg-primary/5 p-3.5 border-l-4 border-l-primary">
              <Lock className="h-5 w-5 text-primary shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-foreground">1. Deterministic Escrow (Razorpay Route)</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Funds are automatically placed on strict hold (<span className="font-mono text-primary font-semibold">on_hold: true</span>). Money only releases when cryptographic proof of delivery is verified.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-xl border border-primary/20 bg-primary/5 p-3.5 border-l-4 border-l-primary">
              <Zap className="h-5 w-5 text-primary shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-foreground">2. Zero-LLM Deterministic Math Kernel</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Replaces fallible AI parsing with <span className="text-foreground font-semibold">Donald Knuth&apos;s Exact-Cover algorithm</span> and <span className="text-foreground font-semibold">Indian GSTIN Mod-36 checksums</span> in exact base-10 paise. Zero false matches.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-xl border border-primary/20 bg-primary/5 p-3.5 border-l-4 border-l-primary">
              <Sparkles className="h-5 w-5 text-primary shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-foreground">3. 1-Click Capital with 12% Nodal Recovery</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Converts verified delivery revenue into instant working capital advances, automatically recovered through a <span className="text-primary font-semibold">12% First-Lien Nodal Sweep</span> from future daily sales.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-primary/30 bg-primary/10 p-3 text-xs font-mono text-primary font-semibold text-center">
            Result: 100% mathematical safety for buyers + instant working capital for sellers.
          </div>
        </div>
      </div>
    </section>
  )
}
