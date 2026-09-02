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
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('judge')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              activeTab === 'judge'
                ? 'bg-gold text-black shadow'
                : 'bg-panel border border-border text-muted-foreground hover:text-foreground hover:border-gold/50'
            }`}
          >
            <Cpu className="h-4 w-4" />
            Judge Control Panel (5 Invariants)
          </button>
          <button
            onClick={() => setActiveTab('assurance')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              activeTab === 'assurance'
                ? 'bg-foreground text-background shadow'
                : 'bg-panel border border-border text-muted-foreground hover:text-foreground hover:border-gold/50'
            }`}
          >
            <ShieldCheck className="h-4 w-4" />
            Assurance Lifecycle (3-Stage Demo)
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              activeTab === 'security'
                ? 'bg-foreground text-background shadow'
                : 'bg-panel border border-border text-muted-foreground hover:text-foreground hover:border-gold/50'
            }`}
          >
            <ShieldAlert className="h-4 w-4" />
            Security Proof & Attack Matrix (9 Vectors)
          </button>
        </div>

        <div className="font-mono text-[11px] text-muted-foreground flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-gain animate-status-dot" />
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
