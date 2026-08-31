'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { navItems } from '@/lib/kuber-data'
import { CfoCopilotDrawer } from '@/components/kuber/cfo-copilot-drawer'
import { Sparkles, ShieldCheck, Database, Github, BookOpen, ExternalLink } from 'lucide-react'
import { getApiUrl } from '@/lib/api-client'

export function Sidebar() {
  const pathname = usePathname()
  const [copilotOpen, setCopilotOpen] = useState(false)

  return (
    <>
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-border bg-panel md:flex">
        {/* Brand Header */}
        <div className="flex items-center gap-3 border-b border-border px-5 py-4 bg-background/50">
          <KuberMark />
          <div className="min-w-0">
            <div className="truncate text-sm font-bold tracking-tight text-foreground">APEX Assurance</div>
            <div className="truncate font-mono text-[11px] uppercase tracking-wider text-gold font-bold">
              Powered by KuberRecon
            </div>
          </div>
        </div>

        {/* CFO AI Copilot Quick Trigger Card */}
        <div className="p-3">
          <button
            onClick={() => setCopilotOpen(true)}
            className="group relative flex w-full items-center gap-3 overflow-hidden rounded-xl border border-primary/40 bg-primary/10 p-3 text-left shadow-lg transition-all hover:border-primary hover:shadow-primary/20 hover:scale-[1.01]"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-primary/40 bg-primary/20 text-primary shadow-sm group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
              <Sparkles className="h-4 w-4 animate-pulse" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-foreground group-hover:text-primary transition-colors">
                  CFO AI Copilot
                </span>
                <span className="rounded bg-primary/20 px-1 py-0.2 font-mono text-[8px] font-bold text-primary uppercase">
                  Zero Hallucination
                </span>
              </div>
              <p className="truncate font-mono text-[10px] text-muted-foreground mt-0.5 font-medium">
                Settlement Q&amp;A · TDS · GST
              </p>
            </div>
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex flex-1 flex-col gap-1 p-3 pt-1">
          <div className="px-2 pb-2 pt-1 font-mono text-xs uppercase tracking-wider text-muted-foreground font-bold">
            Verification Rails
          </div>
          {navItems.map((item) => {
            const active = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  active
                    ? 'bg-accent text-accent-foreground font-semibold border border-border shadow-sm'
                    : 'text-muted-foreground hover:bg-accent/60 hover:text-foreground font-medium'
                }`}
              >
                <span
                  className={`font-mono text-xs ${
                    active ? 'text-primary font-bold' : 'text-muted-foreground group-hover:text-foreground'
                  }`}
                >
                  {item.code}
                </span>
                <span className="truncate leading-tight">{item.label}</span>
                {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />}
              </Link>
            )
          })}
        </nav>

        {/* Developer & Documentation Links */}
        <div className="px-3 pb-2 flex items-center gap-2">
          <a
            href="https://github.com/Pranjulchaurasiya/kuber-recon"
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-1.5 rounded-lg border border-border bg-background/60 py-1.5 font-mono text-[11px] font-semibold text-muted-foreground hover:border-primary/40 hover:text-foreground transition"
          >
            <Github className="h-3.5 w-3.5" />
            <span>GitHub</span>
          </a>
          <a
            href={`${getApiUrl()}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-1.5 rounded-lg border border-border bg-background/60 py-1.5 font-mono text-[11px] font-semibold text-muted-foreground hover:border-primary/40 hover:text-foreground transition"
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span>API Docs</span>
          </a>
        </div>

        {/* Bottom Merkle Root Verification Box */}
        <div className="border-t border-border p-4 space-y-2 bg-background/50">
          <div className="flex items-center justify-between font-mono text-xs uppercase tracking-wider text-muted-foreground font-bold">
            <span>RFC 6962 Root</span>
            <span className="text-gain font-bold flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-gain animate-status-dot" />
              Verified
            </span>
          </div>
          <div className="truncate font-mono text-xs text-foreground font-bold">0x8f3a…d41c</div>
          <div className="flex items-center justify-between font-mono text-[11px] text-muted-foreground pt-1 border-t border-border/60">
            <span className="font-medium">Assertions: 6/6</span>
            <span className="text-gain font-bold">FMR: 0.000</span>
          </div>
        </div>
      </aside>

      {/* CFO Copilot Slide-Over Drawer Component */}
      <CfoCopilotDrawer isOpen={copilotOpen} onClose={() => setCopilotOpen(false)} />
    </>
  )
}

function KuberMark() {
  return (
    <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-primary/40 bg-primary/10">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M12 2 L21 7 V17 L12 22 L3 17 V7 Z"
          stroke="var(--primary)"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <path d="M12 7 V17 M8 12 L12 9 L16 12" stroke="var(--primary)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  )
}
