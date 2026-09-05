'use client'

import { useState } from 'react'
import { ApexAssuranceConsole } from '@/components/escrow/apex-assurance-console'
import { SecurityProofMatrix } from '@/components/security/security-proof-matrix'
import { DemoControlPanel } from '@/components/kuber/demo-control-panel'
import { ShieldCheck, ShieldAlert, Cpu, Terminal } from 'lucide-react'

export default function ConsolePage() {
  const [activeTab, setActiveTab] = useState<'judge' | 'assurance' | 'security'>('judge')

  return (
    <div className="mx-auto max-w-[1480px] px-5 py-6 md:px-8 md:py-8 space-y-6">
      {/* Console Tab Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-4">
        <div className="inline-flex rounded-xl border border-border/70 bg-panel/70 p-1 shadow-sm">
          <button
            onClick={() => setActiveTab('judge')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-mono text-xs transition-all ${
              activeTab === 'judge'
                ? 'bg-foreground text-background shadow-sm font-bold'
                : 'text-muted-foreground hover:text-foreground font-medium'
            }`}
          >
            <Cpu className="h-3.5 w-3.5" />
            Judge Control Panel (5 Invariants)
          </button>
          <button
            onClick={() => setActiveTab('assurance')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-mono text-xs transition-all ${
              activeTab === 'assurance'
                ? 'bg-foreground text-background shadow-sm font-bold'
                : 'text-muted-foreground hover:text-foreground font-medium'
            }`}
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            Assurance Lifecycle (3-Stage Demo)
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-mono text-xs transition-all ${
              activeTab === 'security'
                ? 'bg-foreground text-background shadow-sm font-bold'
                : 'text-muted-foreground hover:text-foreground font-medium'
            }`}
          >
            <ShieldAlert className="h-3.5 w-3.5" />
            Security Proof &amp; Attack Matrix (9 Vectors)
          </button>
        </div>

        <div className="font-mono text-[11px] text-muted-foreground flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border/60 bg-panel/60">
          <span className="h-1.5 w-1.5 rounded-full bg-gain animate-status-dot" />
          <span>Tenant Scope: <strong className="text-foreground">merchant_rzp_primary</strong></span>
        </div>
      </div>

      {/* Tab View */}
      {activeTab === 'judge' ? (
        <DemoControlPanel />
      ) : activeTab === 'assurance' ? (
        <ApexAssuranceConsole />
      ) : (
        <SecurityProofMatrix />
      )}
    </div>
  )
}
