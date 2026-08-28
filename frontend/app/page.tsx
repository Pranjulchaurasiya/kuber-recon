import Link from 'next/link'
import {
  ShieldCheck,
  ArrowRight,
  Lock,
  FileCheck,
  ExternalLink,
  Cpu,
  Fingerprint,
  Layers,
  Database,
  GitBranch,
  Sliders,
  CheckCircle2,
  AlertCircle
} from 'lucide-react'

export default function RootLandingPage() {
  return (
    <div className="mx-auto max-w-[1200px] px-5 py-12 sm:px-8 sm:py-16 md:py-24 space-y-20">

      {/* ── 1. Dominant Hero Section (Above the Fold) ──────────────────────── */}
      <section className="text-center space-y-8">

        {/* Track Badge & Subtitle */}
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
        <div className="space-y-4 max-w-4xl mx-auto">
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight text-foreground leading-[1.08]">
            AI agents can transact.<br />
            <span className="text-gold">They should not settle blindly.</span>
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-muted-foreground leading-relaxed max-w-2xl mx-auto pt-2">
            APEX Assurance gates Razorpay Route settlement behind deterministic delivery verification, cryptographic agent identity, and authoritative webhook finality.
          </p>
        </div>

        {/* Primary & Secondary CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <Link
            href="/apex"
            className="inline-flex items-center gap-2.5 rounded-lg bg-foreground px-7 py-3.5 font-semibold text-sm text-background shadow-md transition-all hover:opacity-90 hover:shadow-lg"
          >
            Launch Assurance Console
            <ArrowRight className="h-4 w-4" />
          </Link>
          <a
            href="#architecture"
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-panel px-6 py-3.5 text-sm font-semibold text-foreground transition-colors hover:bg-accent"
          >
            View Architecture
          </a>
        </div>

        {/* Hero Visual: Settlement-Flow Pipeline */}
        <div className="pt-8">
          <div className="rounded-2xl border border-border bg-panel p-6 sm:p-8 shadow-md space-y-6">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Autonomous Settlement Flow
              </span>
              <span className="font-mono text-xs text-gold">
                Contract Invariant: 500 Records (₹25,000.00)
              </span>
            </div>

            {/* Visual 5-Stage Pipeline */}
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 text-left">

              <div className="rounded-xl border border-border bg-background p-4 space-y-1.5">
                <div className="font-mono text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                  01. Initiator
                </div>
                <div className="text-sm font-bold text-foreground">Buyer Agent</div>
                <div className="font-mono text-xs text-muted-foreground">₹25,000 budget</div>
              </div>

              <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 space-y-1.5">
                <div className="font-mono text-[11px] font-semibold text-amber-500 uppercase tracking-wider">
                  02. Gateway Lock
                </div>
                <div className="text-sm font-bold text-foreground">Razorpay Route</div>
                <div className="font-mono text-xs text-amber-500">on_hold: true</div>
              </div>

              <div className="rounded-xl border border-gold/40 bg-gold/5 p-4 space-y-1.5">
                <div className="font-mono text-[11px] font-semibold text-gold uppercase tracking-wider">
                  03. Verification
                </div>
                <div className="text-sm font-bold text-foreground">APEX Assurance</div>
                <div className="font-mono text-xs text-foreground">500 records check</div>
              </div>

              <div className="rounded-xl border border-border bg-background p-4 space-y-1.5">
                <div className="font-mono text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                  04. Delivery
                </div>
                <div className="text-sm font-bold text-foreground">Seller Agent</div>
                <div className="font-mono text-xs text-muted-foreground">Ed25519 Signed</div>
              </div>

              <div className="rounded-xl border border-gain/30 bg-gain/5 p-4 space-y-1.5">
                <div className="font-mono text-[11px] font-semibold text-gain uppercase tracking-wider">
                  05. Finality
                </div>
                <div className="text-sm font-bold text-foreground">Verified Webhook</div>
                <div className="font-mono text-xs text-gain">RELEASED only</div>
              </div>

            </div>

            <div className="text-xs text-muted-foreground flex items-center justify-between border-t border-border pt-3">
              <span>Razorpay Route authorizes the seller settlement; APEX releases it only after deterministic verification.</span>
              <span className="font-mono text-[11px] font-semibold text-gold">on_hold: true ➔ false</span>
            </div>
          </div>
        </div>

      </section>

      {/* ── 2. Three Compact Proof Cards ────────────────────────────────────── */}
      <section className="space-y-6 pt-4">
        <div className="text-center space-y-1">
          <span className="font-mono text-xs font-semibold uppercase tracking-wider text-gold">
            Deterministic Engine
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
                Evaluates structured delivery manifests against Mod-36 GSTIN checksums and schema bounds. The deterministic kernel refuses unverifiable deliveries without LLM drift in the financial decision path.
              </p>
            </div>
            <div className="font-mono text-xs text-gold border-t border-border pt-3">
              FMR = 0.000 on Adversarial Corpus
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
                Enforces strict base-10 integer arithmetic on all amounts and statutory tax withholdings (TDS under Section 194-O, GST on MDR). Eliminates floating-point rounding errors across the entire ledger.
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
                Enforces RFC 8032 Ed25519 dual-party signatures (Seller manifest + CFO checker authorization). Settlement state transitions to RELEASED exclusively upon authoritative Razorpay webhook confirmation.
              </p>
            </div>
            <div className="font-mono text-xs text-muted-foreground border-t border-border pt-3">
              Single-Source Webhook Finality
            </div>
          </div>

        </div>
      </section>

      {/* ── 3. Architecture Deep-Dive Section ─────────────────────────────────── */}
      <section id="architecture" className="space-y-6 pt-4 scroll-mt-20">
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
            Deep-Dive Modules
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              href: '/escrow',
              label: 'Gateway Escrow Rail',
              code: 'ESC',
              desc: 'T=0 statutory split & Section 194-O TDS pre-settlement withholding.',
            },
            {
              href: '/lineage',
              label: 'Money Lineage Engine',
              code: 'DAG',
              desc: 'Donald Knuth exact-cover solver matching lump-sum UTRs to gross GMV.',
            },
            {
              href: '/twin',
              label: 'Causal Digital Twin',
              code: 'SIM',
              desc: 'Stress-test merchant liquidity against bank holiday freezes & defaults.',
            },
            {
              href: '/ledger',
              label: 'Self-Healing Ledger',
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

      {/* ── 4. Disclosure & Final Judge Banner ───────────────────────────────── */}
      <footer className="space-y-4 pt-6 border-t border-border">
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
