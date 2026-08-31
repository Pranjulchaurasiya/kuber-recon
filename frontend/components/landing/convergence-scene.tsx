'use client'

import { useState, useEffect } from 'react'
import { ShieldCheck, Zap, Cpu, Sparkles, CheckCircle2, ArrowRight, Play, RotateCcw } from 'lucide-react'

export function ConvergenceScene() {
  const [activeStep, setActiveStep] = useState<number>(0)
  const [isIgnited, setIsIgnited] = useState<boolean>(true)
  const [activeFeed, setActiveFeed] = useState<number>(3) // 1, 2, 3 or all

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % 4)
    }, 3000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="relative w-full rounded-2xl border border-border bg-panel/90 p-4 sm:p-6 shadow-2xl backdrop-blur-xl overflow-hidden">
      {/* Top Console Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/80 pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <span className="flex h-2.5 w-2.5 rounded-full bg-gain animate-status-dot" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-foreground">
            APEX Autonomous Convergence Circuit
          </span>
          <span className="rounded bg-accent px-2 py-0.5 font-mono text-[10px] uppercase font-semibold text-primary border border-border">
            Live Route Escrow Stream
          </span>
        </div>

        {/* Action Toggle */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsIgnited(!isIgnited)}
            className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-mono font-semibold transition-all ${
              isIgnited
                ? 'bg-primary/10 text-primary border border-primary/30'
                : 'bg-muted text-muted-foreground border border-border'
            }`}
          >
            {isIgnited ? <Zap className="h-3.5 w-3.5 fill-current" /> : <Play className="h-3.5 w-3.5" />}
            {isIgnited ? 'Reactor Ignited' : 'Standby'}
          </button>
        </div>
      </div>

      {/* SVG Canvas & Circuit Topology */}
      <div className="relative w-full overflow-x-auto">
        <div className="min-w-[760px] relative py-2">
          <svg
            viewBox="0 0 920 340"
            className="w-full h-auto drop-shadow-sm select-none"
            aria-label="APEX 3-Stream Convergence Diagram"
          >
            <defs>
              {/* Glow Filter */}
              <filter id="apex-glow" x="-40%" y="-40%" width="180%" height="180%">
                <feGaussianBlur stdDeviation="8" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>

              {/* Beam Gradients */}
              <linearGradient id="beam-agent" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.2" />
                <stop offset="100%" stopColor="var(--primary)" stopOpacity="1" />
              </linearGradient>

              <linearGradient id="beam-tax" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="var(--gold)" stopOpacity="0.2" />
                <stop offset="100%" stopColor="var(--gold)" stopOpacity="1" />
              </linearGradient>

              <linearGradient id="beam-knuth" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="var(--gain)" stopOpacity="0.2" />
                <stop offset="100%" stopColor="var(--gain)" stopOpacity="1" />
              </linearGradient>

              <linearGradient id="beam-output" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="var(--gain)" stopOpacity="0.4" />
                <stop offset="100%" stopColor="var(--gain)" stopOpacity="1" />
              </linearGradient>
            </defs>

            {/* ── 1. Left Input Feeds (3 Stations) ────────────────────────── */}

            {/* Feed 1: Agentic Commerce PO */}
            <g className="cursor-pointer transition-transform hover:scale-[1.01]">
              <rect
                x="20"
                y="20"
                width="248"
                height="76"
                rx="10"
                className="fill-[var(--card)] stroke-[var(--border)]"
                strokeWidth="1.5"
              />
              <circle cx="42" cy="42" r="5" className="fill-[var(--primary)]" />
              <text x="56" y="44" className="fill-[var(--muted-foreground)] text-[10px] font-mono font-bold tracking-wider">
                01 · AGENTIC COMMERCE
              </text>
              <text x="56" y="62" className="fill-[var(--foreground)] text-xs font-mono font-bold">
                PO #9482 · Autonomous PO
              </text>
              <text x="56" y="78" className="fill-[var(--primary)] text-[10px] font-mono font-semibold">
                Captured via Route on_hold: true
              </text>
            </g>

            {/* Feed 2: Statutory Tax Kernel */}
            <g className="cursor-pointer transition-transform hover:scale-[1.01]">
              <rect
                x="20"
                y="132"
                width="248"
                height="76"
                rx="10"
                className="fill-[var(--card)] stroke-[var(--border)]"
                strokeWidth="1.5"
              />
              <circle cx="42" cy="154" r="5" className="fill-[var(--gold)]" />
              <text x="56" y="156" className="fill-[var(--muted-foreground)] text-[10px] font-mono font-bold tracking-wider">
                02 · STATUTORY TAX KERNEL
              </text>
              <text x="56" y="174" className="fill-[var(--foreground)] text-xs font-mono font-bold">
                GSTIN 29ABCDE1234F1Z5
              </text>
              <text x="56" y="190" className="fill-[var(--gold)] text-[10px] font-mono font-semibold">
                Mod-36 Verified GSTR-2B Match
              </text>
            </g>

            {/* Feed 3: Knuth Exact-Cover Solver */}
            <g className="cursor-pointer transition-transform hover:scale-[1.01]">
              <rect
                x="20"
                y="244"
                width="248"
                height="76"
                rx="10"
                className="fill-[var(--card)] stroke-[var(--border)]"
                strokeWidth="1.5"
              />
              <circle cx="42" cy="266" r="5" className="fill-[var(--gain)]" />
              <text x="56" y="268" className="fill-[var(--muted-foreground)] text-[10px] font-mono font-bold tracking-wider">
                03 · KNUTH EXACT-COVER
              </text>
              <text x="56" y="286" className="fill-[var(--foreground)] text-xs font-mono font-bold">
                100 Items Reconciled (7.34ms)
              </text>
              <text x="56" y="302" className="fill-[var(--gain)] text-[10px] font-mono font-semibold">
                Paise-Exact FMR 0.000 (0 Floats)
              </text>
            </g>

            {/* ── 2. Animated Energy Beam Tracks to Center ─────────────────── */}

            {/* Beam 1 Track & Flow */}
            <path
              d="M 268 58 C 340 58, 360 170, 428 170"
              fill="none"
              stroke="var(--border)"
              strokeWidth="2"
              strokeDasharray="4 4"
            />
            {isIgnited && (
              <path
                d="M 268 58 C 340 58, 360 170, 428 170"
                fill="none"
                stroke="url(#beam-agent)"
                strokeWidth="3.5"
                className="animate-beam"
              />
            )}

            {/* Beam 2 Track & Flow */}
            <path
              d="M 268 170 H 428"
              fill="none"
              stroke="var(--border)"
              strokeWidth="2"
              strokeDasharray="4 4"
            />
            {isIgnited && (
              <path
                d="M 268 170 H 428"
                fill="none"
                stroke="url(#beam-tax)"
                strokeWidth="3.5"
                className="animate-beam"
              />
            )}

            {/* Beam 3 Track & Flow */}
            <path
              d="M 268 282 C 340 282, 360 170, 428 170"
              fill="none"
              stroke="var(--border)"
              strokeWidth="2"
              strokeDasharray="4 4"
            />
            {isIgnited && (
              <path
                d="M 268 282 C 340 282, 360 170, 428 170"
                fill="none"
                stroke="url(#beam-knuth)"
                strokeWidth="3.5"
                className="animate-beam"
              />
            )}

            {/* ── 3. Central Glowing Reactor: APEX Underwriter ────────────── */}
            <g className="cursor-pointer">
              {/* Outer Halo */}
              {isIgnited && (
                <circle
                  cx="490"
                  cy="170"
                  r="72"
                  className="fill-none stroke-[var(--primary)]/30"
                  strokeWidth="6"
                  filter="url(#apex-glow)"
                />
              )}
              {/* Reactor Core */}
              <circle
                cx="490"
                cy="170"
                r="62"
                className="fill-[var(--card)] stroke-[var(--primary)]"
                strokeWidth="2.5"
              />
              <text x="490" y="142" textAnchor="middle" className="fill-[var(--muted-foreground)] text-[9px] font-mono font-bold tracking-wider">
                APEX UNDERWRITER
              </text>
              <text x="490" y="164" textAnchor="middle" className="fill-[var(--foreground)] text-sm font-mono font-extrabold">
                SRI: 0.9675
              </text>
              <text x="490" y="180" textAnchor="middle" className="fill-[var(--gain)] text-[10px] font-mono font-bold">
                TIER A PREMIER
              </text>
              <text x="490" y="196" textAnchor="middle" className="fill-[var(--muted-foreground)] text-[9px] font-mono font-semibold">
                ₹2,47,089.55 VD-GMV
              </text>
            </g>

            {/* ── 4. Output Beam to Dual-Action Verdict ────────────────────── */}
            <path
              d="M 546 170 H 640"
              fill="none"
              stroke="var(--border)"
              strokeWidth="2"
              strokeDasharray="4 4"
            />
            {isIgnited && (
              <path
                d="M 546 170 H 640"
                fill="none"
                stroke="url(#beam-output)"
                strokeWidth="4"
                className="animate-beam"
              />
            )}

            {/* ── 5. Right Output Box: Instant Capital & Route Split-Sweep ──── */}
            <g className="cursor-pointer transition-transform hover:scale-[1.01]">
              <rect
                x="640"
                y="90"
                width="260"
                height="160"
                rx="12"
                className="fill-[var(--card)] stroke-[var(--gain)]/60"
                strokeWidth="2"
              />
              <rect
                x="640"
                y="90"
                width="260"
                height="32"
                rx="12"
                className="fill-[var(--gain)]/15"
              />
              <circle cx="658" cy="106" r="4" className="fill-[var(--gain)]" />
              <text x="670" y="110" className="fill-[var(--gain)] text-[10px] font-mono font-extrabold tracking-wider">
                1-CLICK CAPITAL DISBURSED
              </text>

              <text x="656" y="142" className="fill-[var(--muted-foreground)] text-[10px] font-mono">
                Advance Facility
              </text>
              <text x="656" y="162" className="fill-[var(--foreground)] text-base font-mono font-bold text-gain">
                ₹59,764.78 <tspan className="fill-[var(--muted-foreground)] text-xs font-normal">(`pout_live_01`)</tspan>
              </text>

              <line x1="656" y1="174" x2="884" y2="174" stroke="var(--border)" strokeWidth="1" />

              <text x="656" y="196" className="fill-[var(--muted-foreground)] text-[10px] font-mono">
                Recovery Protocol
              </text>
              <text x="656" y="214" className="fill-[var(--foreground)] text-xs font-mono font-semibold">
                12.0% Automated Split-Sweep
              </text>
              <text x="656" y="232" className="fill-[var(--gain)] text-[10px] font-mono font-semibold">
                Locked to Nodal Settlement Inflow
              </text>
            </g>
          </svg>
        </div>
      </div>

      {/* Bottom Live Metric Strip */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 border-t border-border/80 pt-4">
        <div className="flex items-center gap-2 rounded-lg bg-background/50 p-2.5 border border-border/60">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-primary/10 text-primary font-mono text-xs font-bold">
            01
          </div>
          <div>
            <div className="text-[10px] font-mono text-muted-foreground uppercase">Nodal Protection</div>
            <div className="text-xs font-semibold text-foreground">Pre-Settlement Route Hold</div>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-lg bg-background/50 p-2.5 border border-border/60">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-gold/10 text-gold font-mono text-xs font-bold">
            02
          </div>
          <div>
            <div className="text-[10px] font-mono text-muted-foreground uppercase">Mathematical Underwriting</div>
            <div className="text-xs font-semibold text-foreground">Bayesian SRI Prior (N₀=50)</div>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-lg bg-background/50 p-2.5 border border-border/60">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-gain/10 text-gain font-mono text-xs font-bold">
            03
          </div>
          <div>
            <div className="text-[10px] font-mono text-muted-foreground uppercase">First-Lien Recovery</div>
            <div className="text-xs font-semibold text-foreground">Automated 12% Split-Sweep</div>
          </div>
        </div>
      </div>
    </div>
  )
}
