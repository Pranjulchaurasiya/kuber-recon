'use client'

import Link from 'next/link'
import {
  ArrowRight,
  Cpu,
  ShieldCheck,
  Zap,
  Banknote,
  FileCheck,
  Layers,
  Sparkles,
  ExternalLink,
} from 'lucide-react'
import { ConvergenceScene } from '@/components/landing/convergence-scene'
import { ProblemSolutionSection } from '@/components/landing/problem-solution-section'
import { GapSection } from '@/components/landing/gap-section'
import { ProofSection } from '@/components/landing/proof-section'
import { HowItWorksSection } from '@/components/landing/how-it-works-section'
import { ProductConsoleSection } from '@/components/landing/product-console-section'
import { VoiceBriefingPlayer } from '@/components/landing/voice-briefing-player'

export default function RootLandingPage() {
  return (
    <div className="relative overflow-hidden">
      {/* ── Atmospheric Hero Backdrop ─────────────────────────────────────── */}
      <div className="aurora-backdrop" aria-hidden="true">
        <div className="aurora-glow" />
      </div>

      <div className="relative z-10 mx-auto max-w-[1280px] px-4 py-8 sm:px-8 sm:py-12 space-y-20">

        {/* ── 1. Hero Section ──────────────────────────────────────────────── */}
        <section className="space-y-8 pt-4">
          <div className="text-center space-y-5 max-w-4xl mx-auto">
            {/* Buildathon Eyebrow */}
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-panel/90 px-3.5 py-1.5 shadow-sm backdrop-blur">
              <span className="flex h-2 w-2 rounded-full bg-primary animate-status-dot" />
              <span className="font-mono text-xs font-bold text-primary">
                Razorpay AI Buildathon 2026 · Track 04
              </span>
              <span className="text-muted-foreground/40">•</span>
              <span className="text-xs text-muted-foreground">
                AI Finance Controller &amp; Settlement OS
              </span>
            </div>

            {/* High-Impact Split Headline */}
            <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-foreground leading-[1.08]">
              AI transactions move fast.<br />
              <span>
                Settlement must never be{' '}
                <span className="text-primary drop-shadow-sm underline decoration-primary/40 underline-offset-8">
                  blind
                </span>
                .
              </span>
            </h1>

            {/* Pitch Lede */}
            <p className="text-base sm:text-lg md:text-xl text-muted-foreground leading-relaxed max-w-2xl mx-auto">
              Kuber OS gates Razorpay Route pre-settlement behind line-item delivery proofs, turns verified revenue into instant working capital, and sweeps repayments at the nodal source.
            </p>

            {/* CTAs & 60s Voice Briefing */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Link
                href="/apex"
                className="inline-flex items-center gap-2 rounded-xl bg-foreground px-6 py-3 text-sm font-bold text-background shadow-lg transition-all hover:opacity-90 hover:scale-[1.02]"
              >
                Launch Assurance Radar
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="#product-console"
                className="inline-flex items-center gap-2 rounded-xl border border-border bg-panel/80 px-6 py-3 text-sm font-bold text-foreground shadow-sm transition-all hover:bg-accent hover:border-primary/40"
              >
                <Banknote className="h-4 w-4 text-primary" />
                Working Capital Terminal
              </a>
            </div>

            {/* 🎙️ Sarvam AI 60s Executive Audio Briefing Player */}
            <div className="pt-2">
              <VoiceBriefingPlayer />
            </div>
          </div>

          {/* ── Signature Hero Convergence Circuit ─────────────────────────── */}
          <div className="pt-2">
            <ConvergenceScene />
          </div>
        </section>

        {/* ── 2. Problem vs Solution: The Dilemma & The Moat ──────────────── */}
        <ProblemSolutionSection />

        {/* ── 3. The Gap Section: Institutional Ownership Moat ─────────────── */}
        <GapSection />

        {/* ── 3. The Proof Section: Empirical Invariant Benchmarks ──────────── */}
        <ProofSection />

        {/* ── 4. How It Works Section: 6-Stage Deterministic Trace ──────────── */}
        <HowItWorksSection />

        {/* ── 5. The Product Section: Dual-Surface Operating Mockup ─────────── */}
        <ProductConsoleSection />

      </div>
    </div>
  )
}
