'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  Banknote,
  ShieldCheck,
  Layers,
  ArrowRight,
  Sparkles,
  TrendingUp,
  Cpu,
  Lock,
  Unlock,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
} from 'lucide-react'
import { CapitalHub } from '@/components/capital/capital-hub'

export function ProductConsoleSection() {
  const [activeTab, setActiveTab] = useState<'capital' | 'recon'>('capital')

  return (
    <section className="space-y-8 py-6" id="product-console">
      {/* Section Header */}
      <div className="text-center space-y-3 max-w-3xl mx-auto animate-fade-up">
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-panel px-3 py-1 text-xs font-mono font-semibold text-gold">
          <span className="h-2 w-2 rounded-full bg-gold animate-status-dot" />
          The Dual-Surface Operating System
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-foreground">
          Two surfaces. One sovereign settlement rail.
        </h2>
        <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
          The merchant accesses instant working capital underwritten by verified delivery. The CFO and risk team inspect real-time mathematical reconciliation and cryptographic audit trails.
        </p>
      </div>

      {/* Surface Selector Tabs */}
      <div className="flex justify-center animate-fade-up stagger-1">
        <div className="inline-flex rounded-xl border border-border bg-panel p-1.5 shadow-sm">
          <button
            onClick={() => setActiveTab('capital')}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-bold transition-all ${
              activeTab === 'capital'
                ? 'bg-foreground text-background shadow-md'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Banknote className="h-4 w-4" />
            Merchant Working Capital Hub
          </button>
          <button
            onClick={() => setActiveTab('recon')}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-bold transition-all ${
              activeTab === 'recon'
                ? 'bg-foreground text-background shadow-md'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <ShieldCheck className="h-4 w-4" />
            CFO Pre-Settlement Escrow Radar
          </button>
        </div>
      </div>

      {/* Surface Display Frame */}
      <div className="rounded-2xl border border-border bg-panel p-4 sm:p-8 shadow-2xl space-y-6 hover-glow animate-fade-up stagger-2">
        {activeTab === 'capital' ? (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
              <div>
                <h3 className="text-lg font-bold text-foreground">APEX Capital Merchant Terminal</h3>
                <p className="text-xs text-muted-foreground">
                  Live underwritten facility for Delhi Hyperlocal Logistics (<code className="font-mono">merch_delhi_hyperlocal_01</code>)
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded-full bg-gain/10 border border-gain/30 px-3 py-1 font-mono text-xs font-semibold text-gain flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-gain animate-status-dot" />
                  Live Underwriting Active
                </span>
              </div>
            </div>

            {/* Embedded Capital Hub Component */}
            <CapitalHub />
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
              <div>
                <h3 className="text-lg font-bold text-foreground">APEX Pre-Settlement Escrow Console</h3>
                <p className="text-xs text-muted-foreground">
                  Cryptographic delivery gating & Knuth exact-cover settlement matching
                </p>
              </div>
              <Link
                href="/apex"
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-1.5 text-xs font-bold text-primary-foreground shadow transition-opacity hover:opacity-90"
              >
                Open Full Screen Radar
                <ExternalLink className="h-3.5 w-3.5" />
              </Link>
            </div>

            {/* Escrow Radar Summary Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="rounded-xl border border-border bg-background p-4 space-y-2">
                <div className="text-xs text-muted-foreground font-mono">Total Pre-Settlement Escrow</div>
                <div className="text-2xl font-bold font-mono text-foreground">₹2,47,089.55</div>
                <div className="text-[11px] text-gain font-semibold flex items-center gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5" /> 100% Locked with on_hold: true
                </div>
              </div>

              <div className="rounded-xl border border-border bg-background p-4 space-y-2">
                <div className="text-xs text-muted-foreground font-mono">Knuth Exact-Cover Invariant</div>
                <div className="text-2xl font-bold font-mono text-gain">0.000 FMR</div>
                <div className="text-[11px] text-muted-foreground">Sub-10ms DLX branch & bound</div>
              </div>

              <div className="rounded-xl border border-border bg-background p-4 space-y-2">
                <div className="text-xs text-muted-foreground font-mono">Statutory Section 194-O TDS</div>
                <div className="text-2xl font-bold font-mono text-gold">0.10% Withheld</div>
                <div className="text-[11px] text-muted-foreground">Paise-exact base-10 deduction</div>
              </div>
            </div>

            {/* Simulated Live Event Stream */}
            <div className="rounded-xl border border-border bg-background/80 p-4 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between text-muted-foreground text-[10px] uppercase tracking-wider border-b border-border pb-2">
                <span>Timestamp / Event Type</span>
                <span>Payload / Status</span>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-foreground">
                  <span className="text-primary font-semibold">T-00:00:02 · webhook.payment_authorized</span>
                  <span className="text-gain">`on_hold: true` (₹25,000.00 locked in Route)</span>
                </div>
                <div className="flex items-center justify-between text-foreground">
                  <span className="text-gold font-semibold">T-00:00:01 · gst.mod36_validation</span>
                  <span className="text-gain">GSTIN 29ABCDE1234F1Z5 MATCHED GSTR-2B</span>
                </div>
                <div className="flex items-center justify-between text-foreground">
                  <span className="text-gain font-semibold">T-00:00:00 · settlement.release_executed</span>
                  <span className="text-gain">CAS State: RELEASED (12% swept to Capital Fund)</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
