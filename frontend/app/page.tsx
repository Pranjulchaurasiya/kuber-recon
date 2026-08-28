'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  ShieldCheck,
  ArrowRight,
  Lock,
  Unlock,
  FileCheck,
  ExternalLink,
  Cpu,
  Fingerprint,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Activity,
  Layers
} from 'lucide-react'

export default function RootLandingPage() {
  const [simulatedGateState, setSimulatedGateState] = useState<'refused' | 'verified'>('refused')

  return (
    <div className="mx-auto max-w-[1200px] px-5 py-10 sm:px-8 sm:py-14 space-y-16">

      {/* ── 1. Dominant Hero Section (Above the Fold) ──────────────────────── */}
      <section className="text-center space-y-7">

        {/* Track Badge */}
        <div className="inline-flex flex-wrap items-center justify-center gap-2 rounded-full border border-border bg-panel px-4 py-1.5 shadow-sm">
          <span className="flex items-center gap-1.5 font-mono text-xs font-semibold text-gold">
            <Cpu className="h-3.5 w-3.5" /> Razorpay AI Buildathon · Track 01
          </span>
          <span className="text-muted-foreground/40">•</span>
          <span className="text-xs text-muted-foreground">
            Powered by <strong className="font-semibold text-foreground">KuberRecon</strong>
          </span>
        </div>

        {/* Hero Headline */}
        <div className="space-y-3 max-w-4xl mx-auto">
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight text-foreground leading-[1.08]">
            AI agents can transact.<br />
            <span className="text-gold">They should not settle blindly.</span>
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-muted-foreground leading-relaxed max-w-2xl mx-auto pt-1">
            APEX Assurance gates Razorpay Route settlement behind deterministic delivery verification, cryptographic agent identity, and authoritative webhook finality.
          </p>
        </div>

        {/* Primary & Secondary CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-1">
          <Link
            href="/apex"
            className="inline-flex items-center gap-2.5 rounded-lg bg-foreground px-7 py-3.5 font-semibold text-sm text-background shadow-md transition-all hover:opacity-90 hover:shadow-lg"
          >
            Launch Assurance Console
            <ArrowRight className="h-4 w-4" />
          </Link>
          <a
            href="#settlement-gate"
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-panel px-6 py-3.5 text-sm font-semibold text-foreground transition-colors hover:bg-accent"
          >
            Interactive Settlement Gate
          </a>
        </div>

        {/* ── 2. Interactive Settlement Gate Visualizer (Hero Moat Moment) ──── */}
        <div id="settlement-gate" className="pt-4 scroll-mt-24">
          <div className="rounded-2xl border border-border bg-panel p-6 sm:p-8 shadow-md space-y-6">

            {/* Header & Simulator Toggle */}
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
              <div className="text-left">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-gold" />
                  <span className="font-mono text-xs font-bold uppercase tracking-wider text-foreground">
                    APEX Settlement Gate Simulator
                  </span>
                  <span className="rounded bg-accent px-2 py-0.5 font-mono text-[10px] uppercase font-semibold text-muted-foreground border border-border">
                    Interactive concept preview
                  </span>
                </div>
                <div className="font-mono text-xs text-muted-foreground mt-0.5">
                  Route Contract: ₹25,000.00 (500 Records: 497 Valid / 3 Invalid Canonical Scenario)
                </div>
              </div>

              {/* Interactive Demo Toggles */}
              <div className="flex items-center gap-2 bg-background p-1 rounded-lg border border-border">
                <button
                  onClick={() => setSimulatedGateState('refused')}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md font-mono text-xs font-semibold transition-all ${
                    simulatedGateState === 'refused'
                      ? 'bg-danger/20 text-danger border border-danger/40 shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <XCircle className="h-3.5 w-3.5" />
                  1. Delivery Corrupted (Refusal)
                </button>
                <button
                  onClick={() => setSimulatedGateState('verified')}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md font-mono text-xs font-semibold transition-all ${
                    simulatedGateState === 'verified'
                      ? 'bg-gain/20 text-gain border border-gain/40 shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  2. Delivery 100% Valid (Release)
                </button>
              </div>
            </div>

            {/* Interactive Visual Gate Flow */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-left items-center">

              {/* Node 1: Buyer Agent */}
              <div className="rounded-xl border border-border bg-background p-4 space-y-1">
                <div className="font-mono text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                  01. Buyer Agent
                </div>
                <div className="text-sm font-bold text-foreground">Procurement Intent</div>
                <div className="font-mono text-xs text-gain font-semibold">Allocates ₹25,000.00</div>
              </div>

              {/* Node 2: Razorpay Route Hold */}
              <div className="rounded-xl border border-amber-500/40 bg-amber-500/5 p-4 space-y-1">
                <div className="font-mono text-[11px] font-semibold text-amber-500 uppercase tracking-wider flex items-center gap-1.5">
                  <Lock className="h-3 w-3" /> 02. Gateway Lock
                </div>
                <div className="text-sm font-bold text-foreground">Razorpay Route</div>
                <div className="font-mono text-xs text-amber-500 font-bold">on_hold: true</div>
              </div>

              {/* Node 3: The APEX Settlement Gate (Central Dynamic Moat) */}
              <div className={`rounded-xl border p-4 space-y-1.5 transition-all shadow-md ${
                simulatedGateState === 'refused'
                  ? 'border-danger/50 bg-danger/10 shadow-danger/5'
                  : 'border-gain/50 bg-gain/10 shadow-gain/5'
              }`}>
                <div className="flex items-center justify-between font-mono text-[11px] font-bold uppercase tracking-wider">
                  <span className={simulatedGateState === 'refused' ? 'text-danger' : 'text-gain'}>
                    03. APEX GATE
                  </span>
                  {simulatedGateState === 'refused' ? (
                    <span className="flex items-center gap-1 text-danger font-bold">
                      <Lock className="h-3 w-3" /> BLOCKED
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-gain font-bold">
                      <Unlock className="h-3 w-3" /> OPEN
                    </span>
                  )}
                </div>
                <div className="text-sm font-bold text-foreground">
                  {simulatedGateState === 'refused' ? 'Honest Refusal' : '100% Invariants OK'}
                </div>
                <div className="font-mono text-xs text-muted-foreground">
                  {simulatedGateState === 'refused' ? 'Mod-36 Checksum Fail' : '500/500 Verified'}
                </div>
              </div>

              {/* Node 4: Seller Agent */}
              <div className="rounded-xl border border-border bg-background p-4 space-y-1">
                <div className="font-mono text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                  04. Seller Agent
                </div>
                <div className="text-sm font-bold text-foreground">
                  {simulatedGateState === 'refused' ? 'Correction Req.' : 'Ed25519 Signed'}
                </div>
                <div className="font-mono text-xs text-muted-foreground truncate">
                  {simulatedGateState === 'refused' ? 'Refusal cert issued' : '0x728103c3…92969'}
                </div>
              </div>

              {/* Node 5: Settlement State */}
              <div className={`rounded-xl border p-4 space-y-1 transition-all ${
                simulatedGateState === 'refused'
                  ? 'border-border bg-background/50'
                  : 'border-gain/40 bg-gain/5'
              }`}>
                <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  05. Settlement Finality
                </div>
                <div className="text-sm font-bold text-foreground">
                  {simulatedGateState === 'refused' ? 'Liquidity Protected' : 'Verified Payout'}
                </div>
                <div className={`font-mono text-xs font-bold ${
                  simulatedGateState === 'refused' ? 'text-amber-500' : 'text-gain'
                }`}>
                  {simulatedGateState === 'refused' ? 'Hold Preserved' : 'RELEASED (Webhook)'}
                </div>
              </div>

            </div>

            {/* Dynamic Status Explanation */}
            <div className={`rounded-xl border p-4 text-xs leading-relaxed flex items-center justify-between gap-4 ${
              simulatedGateState === 'refused'
                ? 'border-danger/30 bg-danger/5 text-danger'
                : 'border-gain/30 bg-gain/5 text-gain'
            }`}>
              <div className="flex items-center gap-2">
                {simulatedGateState === 'refused' ? (
                  <AlertTriangle className="h-4 w-4 shrink-0 text-danger" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-gain" />
                )}
                <span className="font-sans text-xs">
                  {simulatedGateState === 'refused' ? (
                    <><strong>Honest Refusal:</strong> Mod-36 checksum mismatch detected on supplier records. APEX refuses unverifiable delivery while preserving the Razorpay Route hold (<code className="font-mono font-bold">on_hold: true</code>).</>
                  ) : (
                    <><strong>Verified Release:</strong> All 500 records verified mathematically against pinned seller signature. CFO maker-checker authorizes settlement (<code className="font-mono font-bold">PATCH on_hold: false</code>), finalized by Razorpay webhook.</>
                  )}
                </span>
              </div>
              <Link
                href="/apex"
                className="shrink-0 font-mono text-xs font-bold underline flex items-center gap-1 hover:opacity-80"
              >
                Run Live in Console <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

          </div>
        </div>

      </section>

      {/* ── 3. Three Compact Proof Cards ────────────────────────────────────── */}
      <section className="space-y-5 pt-2">
        <div className="text-center space-y-1">
          <span className="font-mono text-xs font-semibold uppercase tracking-wider text-gold">
            Deterministic Kernel
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
            Three Core Invariants
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

          <div className="rounded-2xl border border-border bg-panel p-6 space-y-3 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-background text-gold">
                <FileCheck className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-foreground">
                1. Deterministic Assertions
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Evaluates structured delivery manifests against Mod-36 GSTIN checksums and schema bounds. The deterministic kernel does not use an LLM in the financial decision path and refuses unverifiable deliveries.
              </p>
            </div>
            <div className="font-mono text-xs text-gold border-t border-border pt-3">
              Test Corpus FMR = 0.000
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-panel p-6 space-y-3 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-background text-gain">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-foreground">
                2. Paise-Exact Accounting
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Enforces strict base-10 integer arithmetic on all amounts and statutory tax withholdings (TDS under Section 194-O, GST on MDR). Completely eliminates floating-point rounding leakage.
              </p>
            </div>
            <div className="font-mono text-xs text-gain border-t border-border pt-3">
              Delta = ₹0.0000 · Zero Rounding Drift
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-panel p-6 space-y-3 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-background text-foreground">
                <Fingerprint className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-foreground">
                3. Cryptographic Authorization
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Dual-party RFC 8032 Ed25519 signatures (Seller manifest + CFO checker authorization). Settlement state transitions to RELEASED exclusively upon authoritative Razorpay webhook confirmation.
              </p>
            </div>
            <div className="font-mono text-xs text-muted-foreground border-t border-border pt-3">
              Single-Source Webhook Finality
            </div>
          </div>

        </div>
      </section>

      {/* ── 4. Subsystem Topology Section ───────────────────────────────────── */}
      <section id="architecture" className="space-y-5 pt-2 scroll-mt-24">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-gold">
              Subsystem Topology
            </span>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
              Verification & Evidence Rails
            </h2>
          </div>
          <span className="font-mono text-xs text-muted-foreground">
            Supporting Infrastructure Modules
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              href: '/escrow',
              label: 'Gateway Escrow',
              code: 'ESC',
              desc: 'T=0 statutory split & Section 194-O TDS pre-settlement withholding.',
            },
            {
              href: '/lineage',
              label: 'Money Lineage',
              code: 'DAG',
              desc: 'Donald Knuth exact-cover solver matching lump-sum UTRs to gross GMV.',
            },
            {
              href: '/twin',
              label: 'Digital Twin',
              code: 'SIM',
              desc: 'Stress-test merchant liquidity against bank holiday freezes & defaults.',
            },
            {
              href: '/ledger',
              label: 'Ledger & Merkle',
              code: 'MRK',
              desc: 'One-click CFO approvals with Ed25519-signed Merkle audit certificates.',
            },
          ].map((rail, idx) => (
            <Link
              key={idx}
              href={rail.href}
              className="group rounded-xl border border-border bg-panel p-5 space-y-3 transition-all hover:border-gold/50 hover:bg-accent"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-gold">{rail.code}</span>
                <ExternalLink className="h-4 w-4 text-muted-foreground/60 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-gold" />
              </div>
              <div>
                <div className="text-sm font-bold text-foreground group-hover:text-gold transition-colors">
                  {rail.label}
                </div>
                <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                  {rail.desc}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ── 5. Disclosure & Bottom Banner ───────────────────────────────────── */}
      <footer className="space-y-4 pt-4 border-t border-border">
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 text-xs text-muted-foreground leading-relaxed">
          <strong className="text-amber-500 font-semibold font-mono uppercase text-[11px] block mb-1">
            🔒 Key Custody & Security Disclosure:
          </strong>
          “Buildathon prototype. Browser signing keys are sandbox credentials; production custody requires KMS/HSM and WebAuthn/FIDO2.”
        </div>

        <div className="rounded-xl border border-border bg-panel p-5 text-center">
          <p className="font-mono text-sm sm:text-base font-bold text-foreground">
            “APEX prevents autonomous seller settlement until delivery is mathematically proven.”
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Razorpay AI Buildathon · Track 01: Agentic Commerce
          </p>
        </div>
      </footer>

    </div>
  )
}
