import { AlertTriangle, CheckCircle2, ShieldAlert, Sparkles, XCircle, ArrowRight, Lock, Zap, ShieldCheck } from 'lucide-react'

export function ProblemSolutionSection() {
  return (
    <section className="space-y-8" id="problem-solution">
      <div className="text-center space-y-3 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-panel/80 px-3 py-1 font-mono text-xs font-semibold text-foreground">
          <Sparkles className="h-3.5 w-3.5 text-primary" /> The Core Problem &amp; The Architecture
        </div>
        <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-foreground">
          Why Blind Settlement Breaks —{' '}<span className="text-primary">And How Kuber OS Solves It</span>
        </h2>
        <p className="text-muted-foreground text-sm sm:text-base leading-relaxed">
          Autonomous AI agents execute transactions in milliseconds, but traditional payment gateways settle blindly. Kuber OS bridges the gap with deterministic verification.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
        {/* ── 🔴 THE PROBLEM CARD ────────────────────────────────────────── */}
        <div className="rounded-xl border border-border/70 bg-panel/70 p-6 sm:p-8 space-y-6 shadow-sm flex flex-col justify-between">
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-border/60 pb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-danger/10 text-danger border border-danger/20 font-bold">
                  <ShieldAlert className="h-4 w-4" />
                </div>
                <div>
                  <span className="font-mono text-[10px] font-bold text-danger uppercase tracking-wider">Traditional Rails</span>
                  <h3 className="text-base sm:text-lg font-bold text-foreground">The Crisis in Agentic Commerce</h3>
                </div>
              </div>
              <span className="rounded-full bg-danger/10 text-danger border border-danger/20 px-2.5 py-0.5 font-mono text-[10px] font-semibold">
                Unverified Disbursal
              </span>
            </div>

            {/* Flat List (No nested sub-boxes) */}
            <div className="space-y-5">
              <div className="flex items-start gap-3">
                <XCircle className="h-4 w-4 text-danger shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-xs sm:text-sm font-semibold text-foreground">1. Blind Pre-Settlement Disbursals</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Buyer agents execute orders instantly, but gateways disburse funds immediately to the seller <span className="text-danger font-medium">before verifying if delivery occurred</span> or if the seller is legitimate.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <XCircle className="h-4 w-4 text-danger shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-xs sm:text-sm font-semibold text-foreground">2. The LLM Hallucination &amp; Float Drift Trap</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Using an LLM for invoice reconciliation introduces phantom line items and IEEE-754 floating-point drift where <span className="font-mono text-danger font-medium">0.1 + 0.2 ≠ 0.3</span>.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <XCircle className="h-4 w-4 text-danger shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-xs sm:text-sm font-semibold text-foreground">3. Merchant Working Capital Crushes</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Sellers supplying buyer platforms face severe 30-to-45 day cash crunches waiting for bank clearance, creating cashflow bottlenecks.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-border/60 text-xs text-muted-foreground flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-danger shrink-0" />
            <span>High default exposure, permanent capital loss, and delayed merchant growth.</span>
          </div>
        </div>

        {/* ── 🟢 THE SOLUTION CARD ────────────────────────────────────────── */}
        <div className="rounded-xl border border-border/70 bg-panel/70 p-6 sm:p-8 space-y-6 shadow-sm flex flex-col justify-between">
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-border/60 pb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gain/10 text-gain border border-gain/20 font-bold">
                  <ShieldCheck className="h-4 w-4" />
                </div>
                <div>
                  <span className="font-mono text-[10px] font-bold text-gain uppercase tracking-wider">Kuber Architecture</span>
                  <h3 className="text-base sm:text-lg font-bold text-foreground">The Kuber Settlement OS</h3>
                </div>
              </div>
              <span className="rounded-full bg-gain/10 text-gain border border-gain/20 px-2.5 py-0.5 font-mono text-[10px] font-semibold">
                Verified Pre-Settlement
              </span>
            </div>

            {/* Flat List (No nested sub-boxes) */}
            <div className="space-y-5">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-4 w-4 text-gain shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-xs sm:text-sm font-semibold text-foreground">1. Deterministic Escrow (Razorpay Route)</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Funds are automatically placed on hold (<span className="font-mono text-primary font-medium">on_hold: true</span>). Settlement only releases when cryptographic proof of delivery passes all checks.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-4 w-4 text-gain shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-xs sm:text-sm font-semibold text-foreground">2. Dual-Layer: AI Agent + Zero-Float Kernel</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    AI orchestrates order context, while financial clearing is locked to the <span className="text-foreground font-medium">Horowitz–Sahni Subset-Sum solver</span> and <span className="text-foreground font-medium">GSTIN Mod-36 checksums</span> in exact base-10 paise.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-4 w-4 text-gain shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-xs sm:text-sm font-semibold text-foreground">3. Instant Capital with 12% Nodal Recovery</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Verified delivery revenue converts into instant working capital advances, automatically recovered through an automated <span className="text-foreground font-medium">12% Split-Settlement Nodal Sweep</span> from daily sales.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-border/60 text-xs text-muted-foreground flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-gain shrink-0" />
            <span>Mathematical safety for buyers with instant working capital for sellers.</span>
          </div>
        </div>
      </div>
    </section>
  )
}
