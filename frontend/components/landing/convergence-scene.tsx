'use client'

import { useState, useEffect } from 'react'
import { Zap, Play } from 'lucide-react'

export function ConvergenceScene() {
  const [activeStep, setActiveStep] = useState<number>(0)
  const [isIgnited, setIsIgnited] = useState<boolean>(true)

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % 4)
    }, 3000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="relative w-full rounded-xl border border-border/70 bg-panel/70 p-4 sm:p-6 shadow-sm backdrop-blur-md overflow-hidden">
      {/* Top Console Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <span className="flex h-2 w-2 rounded-full bg-gain animate-status-dot" />
          <span className="font-mono text-xs font-semibold uppercase tracking-wider text-foreground">
            Settlement Convergence Circuit
          </span>
          <span className="text-muted-foreground/30">•</span>
          <span className="rounded bg-muted/60 px-2 py-0.5 font-mono text-[10px] font-medium text-muted-foreground border border-border/60">
            Route Escrow Sandbox Stream
          </span>
        </div>

        {/* Action Toggle */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsIgnited(!isIgnited)}
            className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-mono font-medium transition-colors ${
              isIgnited
                ? 'bg-primary/10 text-primary border border-primary/20'
                : 'bg-muted/60 text-muted-foreground border border-border/60'
            }`}
          >
            {isIgnited ? <Zap className="h-3 w-3 fill-current" /> : <Play className="h-3 w-3" />}
            {isIgnited ? 'Active Stream' : 'Paused'}
          </button>
        </div>
      </div>

      {/* SVG Canvas & Circuit Topology */}
      <div className="relative w-full overflow-x-auto">
        <div className="min-w-[760px] relative py-1">
          <svg
            viewBox="0 0 920 280"
            className="w-full h-auto select-none"
            aria-label="Kuber 3-Stream Settlement Convergence Diagram"
          >
            <defs>
              {/* Beam Gradients */}
              <linearGradient id="beam-agent" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.2" />
                <stop offset="100%" stopColor="var(--primary)" stopOpacity="0.9" />
              </linearGradient>

              <linearGradient id="beam-tax" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="var(--gold)" stopOpacity="0.2" />
                <stop offset="100%" stopColor="var(--gold)" stopOpacity="0.9" />
              </linearGradient>

              <linearGradient id="beam-solver" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="var(--gain)" stopOpacity="0.2" />
                <stop offset="100%" stopColor="var(--gain)" stopOpacity="0.9" />
              </linearGradient>

              <linearGradient id="beam-output" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="var(--gain)" stopOpacity="0.3" />
                <stop offset="100%" stopColor="var(--gain)" stopOpacity="1" />
              </linearGradient>
            </defs>

            {/* ── FEED 1: Delivery Proof ────────────────────────────────────── */}
            <g className="cursor-pointer transition-opacity hover:opacity-90">
              <rect
                x="20"
                y="16"
                width="240"
                height="64"
                rx="8"
                className="fill-[var(--card)] stroke-[var(--border)]"
                strokeWidth="1"
              />
              <circle cx="38" cy="36" r="3.5" className="fill-[var(--primary)]" />
              <text x="50" y="38" className="fill-[var(--muted-foreground)] text-[9px] font-mono font-bold tracking-wider">
                01 · DELIVERY PROOF
              </text>
              <text x="50" y="54" className="fill-[var(--foreground)] text-xs font-mono font-semibold">
                Ed25519 E-Way Manifest
              </text>
              <text x="50" y="68" className="fill-[var(--primary)] text-[9px] font-mono">
                Triggers on_hold: false
              </text>
            </g>

            {/* ── FEED 2: Statutory Tax Kernel ──────────────────────────────── */}
            <g className="cursor-pointer transition-opacity hover:opacity-90">
              <rect
                x="20"
                y="108"
                width="240"
                height="64"
                rx="8"
                className="fill-[var(--card)] stroke-[var(--border)]"
                strokeWidth="1"
              />
              <circle cx="38" cy="128" r="3.5" className="fill-[var(--gold)]" />
              <text x="50" y="130" className="fill-[var(--muted-foreground)] text-[9px] font-mono font-bold tracking-wider">
                02 · STATUTORY TAX KERNEL
              </text>
              <text x="50" y="146" className="fill-[var(--foreground)] text-xs font-mono font-semibold">
                GSTIN 29ABCDE1234F1Z5
              </text>
              <text x="50" y="160" className="fill-[var(--gold)] text-[9px] font-mono">
                Mod-36 GSTR-2B Verified
              </text>
            </g>

            {/* ── FEED 3: Horowitz-Sahni Solver ─────────────────────────────── */}
            <g className="cursor-pointer transition-opacity hover:opacity-90">
              <rect
                x="20"
                y="200"
                width="240"
                height="64"
                rx="8"
                className="fill-[var(--card)] stroke-[var(--border)]"
                strokeWidth="1"
              />
              <circle cx="38" cy="220" r="3.5" className="fill-[var(--gain)]" />
              <text x="50" y="222" className="fill-[var(--muted-foreground)] text-[9px] font-mono font-bold tracking-wider">
                03 · HOROWITZ–SAHNI SOLVER
              </text>
              <text x="50" y="238" className="fill-[var(--foreground)] text-xs font-mono font-semibold">
                100 Pairs Reconciled (7.34ms)
              </text>
              <text x="50" y="252" className="fill-[var(--gain)] text-[9px] font-mono">
                Paise-Exact (0 Float Drift)
              </text>
            </g>

            {/* ── Connecting Data Tracks to Center ─────────────────────────── */}
            <path
              d="M 260 48 C 340 48, 360 140, 420 140"
              fill="none"
              stroke="var(--border)"
              strokeWidth="1.5"
              strokeDasharray="3 3"
            />
            {isIgnited && (
              <path
                d="M 260 48 C 340 48, 360 140, 420 140"
                fill="none"
                stroke="url(#beam-agent)"
                strokeWidth="2"
                className="animate-beam"
              />
            )}

            <path
              d="M 260 140 H 420"
              fill="none"
              stroke="var(--border)"
              strokeWidth="1.5"
              strokeDasharray="3 3"
            />
            {isIgnited && (
              <path
                d="M 260 140 H 420"
                fill="none"
                stroke="url(#beam-tax)"
                strokeWidth="2"
                className="animate-beam"
              />
            )}

            <path
              d="M 260 232 C 340 232, 360 140, 420 140"
              fill="none"
              stroke="var(--border)"
              strokeWidth="1.5"
              strokeDasharray="3 3"
            />
            {isIgnited && (
              <path
                d="M 260 232 C 340 232, 360 140, 420 140"
                fill="none"
                stroke="url(#beam-solver)"
                strokeWidth="2"
                className="animate-beam"
              />
            )}

            {/* ── CENTRAL NODE: Kuber Recon Solver ─────────────────────────── */}
            <g className="cursor-pointer">
              {/* Subtle outer dashed perimeter */}
              <rect
                x="414"
                y="86"
                width="168"
                height="108"
                rx="14"
                className="fill-none stroke-[var(--primary)]/30"
                strokeWidth="1"
                strokeDasharray="4 4"
              />
              {/* Inner card */}
              <rect
                x="420"
                y="92"
                width="156"
                height="96"
                rx="10"
                className="fill-[var(--card)] stroke-[var(--primary)]/80"
                strokeWidth="1.5"
              />
              <text x="498" y="114" textAnchor="middle" className="fill-[var(--muted-foreground)] text-[9px] font-mono font-bold tracking-wider">
                KUBER RECON SOLVER
              </text>
              <text x="498" y="136" textAnchor="middle" className="fill-[var(--foreground)] text-sm font-mono font-bold">
                SRI: 0.9675
              </text>
              <text x="498" y="152" textAnchor="middle" className="fill-[var(--gain)] text-[10px] font-mono font-semibold">
                TIER A PREMIER
              </text>
              <text x="498" y="170" textAnchor="middle" className="fill-[var(--muted-foreground)] text-[9px] font-mono">
                ₹2,47,089.55 VD-GMV
              </text>
            </g>

            {/* ── Output Connector Track ───────────────────────────────────── */}
            <path
              d="M 582 140 H 660"
              fill="none"
              stroke="var(--border)"
              strokeWidth="1.5"
              strokeDasharray="3 3"
            />
            {isIgnited && (
              <path
                d="M 582 140 H 660"
                fill="none"
                stroke="url(#beam-output)"
                strokeWidth="2"
                className="animate-beam"
              />
            )}

            {/* ── RIGHT OUTPUT CARD: Verified Settlement ───────────────────── */}
            <g className="cursor-pointer transition-opacity hover:opacity-90">
              <rect
                x="660"
                y="74"
                width="240"
                height="132"
                rx="10"
                className="fill-[var(--card)] stroke-[var(--gain)]/60"
                strokeWidth="1.5"
              />
              {/* Clean top bar */}
              <rect
                x="660"
                y="74"
                width="240"
                height="28"
                rx="10"
                className="fill-[var(--gain)]/10"
              />
              <circle cx="676" cy="88" r="3.5" className="fill-[var(--gain)]" />
              <text x="686" y="91" className="fill-[var(--gain)] text-[9px] font-mono font-bold tracking-wider">
                SETTLEMENT RELEASED
              </text>

              <text x="674" y="122" className="fill-[var(--muted-foreground)] text-[9px] font-mono">
                Advance Facility
              </text>
              <text x="674" y="140" className="fill-[var(--gain)] text-sm font-mono font-bold">
                ₹59,764.78 <tspan className="fill-[var(--muted-foreground)] text-[10px] font-normal">(`pout_live_01`)</tspan>
              </text>

              <line x1="674" y1="152" x2="886" y2="152" stroke="var(--border)" strokeWidth="1" strokeOpacity="0.6" />

              <text x="674" y="172" className="fill-[var(--muted-foreground)] text-[9px] font-mono">
                Recovery Protocol
              </text>
              <text x="674" y="188" className="fill-[var(--foreground)] text-[11px] font-mono font-medium">
                12.0% Automated Split-Sweep
              </text>
            </g>
          </svg>
        </div>
      </div>

      {/* Bottom Minimalist Metric Strip */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 border-t border-border/60 pt-4">
        <div className="flex items-center gap-3 py-1 px-2">
          <div className="font-mono text-xs font-bold text-primary">01</div>
          <div>
            <div className="text-[10px] font-mono text-muted-foreground uppercase">Nodal Protection</div>
            <div className="text-xs font-medium text-foreground">Pre-Settlement Route Hold</div>
          </div>
        </div>

        <div className="flex items-center gap-3 py-1 px-2 sm:border-l sm:border-border/60">
          <div className="font-mono text-xs font-bold text-gold">02</div>
          <div>
            <div className="text-[10px] font-mono text-muted-foreground uppercase">Mathematical Underwriting</div>
            <div className="text-xs font-medium text-foreground">Bayesian SRI Prior (N₀=50)</div>
          </div>
        </div>

        <div className="flex items-center gap-3 py-1 px-2 sm:border-l sm:border-border/60">
          <div className="font-mono text-xs font-bold text-gain">03</div>
          <div>
            <div className="text-[10px] font-mono text-muted-foreground uppercase">Nodal Recovery</div>
            <div className="text-xs font-medium text-foreground">Automated 12% Split-Sweep</div>
          </div>
        </div>
      </div>
    </div>
  )
}
