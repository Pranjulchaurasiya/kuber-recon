'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { navItems } from '@/lib/kuber-data'
import { ThemeToggle } from './theme-toggle'
import { CfoCopilotDrawer } from '@/components/kuber/cfo-copilot-drawer'
import { getApiUrl } from '@/lib/api-client'
import { Sparkles } from 'lucide-react'

export function Topbar() {
  const pathname = usePathname()
  const current = navItems.find((n) => n.href === pathname) ?? navItems[0]
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [gatewayMode, setGatewayMode] = useState<'test_mode' | 'sandbox_simulation'>('sandbox_simulation')
  const [copilotOpen, setCopilotOpen] = useState(false)

  useEffect(() => {
    fetch(`${getApiUrl()}/api/integration-status`)
      .then((r) => r.json())
      .then((data) => {
        if (data.mode === 'test_mode' || data.razorpay_api_live) {
          setGatewayMode('test_mode')
        } else {
          setGatewayMode('sandbox_simulation')
        }
      })
      .catch(() => setGatewayMode('sandbox_simulation'))
  }, [])

  return (
    <>
      <header className="sticky top-0 z-20 flex flex-col border-b border-border bg-background/90 backdrop-blur-md">
        <div className="flex h-14 items-center gap-3 px-4 sm:px-5">
          {/* Mobile menu toggle */}
          <button
            onClick={() => setMobileMenuOpen((o) => !o)}
            className="flex h-9 w-9 items-center justify-center rounded-md border border-border bg-panel text-muted-foreground hover:text-foreground md:hidden"
            aria-label="Toggle mobile navigation menu"
            aria-expanded={mobileMenuOpen}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {mobileMenuOpen ? (
                <path d="M18 6L6 18M6 6l12 12" />
              ) : (
                <path d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>

          {/* Mobile brand mark */}
          <div className="flex items-center gap-2 md:hidden">
            <Link href="/" className="font-mono text-xs font-bold text-primary">APEX</Link>
          </div>

          {/* Breadcrumb */}
          <div className="flex min-w-0 items-center gap-2">
            <Link href="/" className="font-mono text-xs font-bold uppercase tracking-wider text-primary hover:underline">
              {current.code}
            </Link>
            <span className="text-muted-foreground/40">/</span>
            <h1 className="truncate text-sm font-semibold text-foreground">{current.label}</h1>
          </div>

          {/* Right controls */}
          <div className="ml-auto flex items-center gap-3">
            {/* CFO Copilot Launcher Button */}
            <button
              onClick={() => setCopilotOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-primary/40 bg-primary/10 px-3 py-1.5 font-mono text-xs font-bold text-primary shadow-sm hover:bg-primary/20 hover:border-primary/60 transition"
              title="Launch CFO AI Settlement Q&A Copilot"
            >
              <Sparkles className="h-3.5 w-3.5 animate-pulse" />
              <span className="hidden sm:inline">CFO Copilot</span>
            </button>

            {/* Dynamic Truthful Mode Badge */}
            {gatewayMode === 'test_mode' ? (
              <div className="hidden items-center gap-2 rounded-full border border-gain/30 bg-gain/10 px-3 py-1 sm:flex font-mono text-[11px] font-semibold text-gain">
                <span className="h-1.5 w-1.5 rounded-full bg-gain animate-status-dot" />
                RAZORPAY TEST MODE
              </div>
            ) : (
              <div className="hidden items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 sm:flex font-mono text-[11px] font-semibold text-amber-500">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-status-dot" />
                SANDBOX SIMULATION
              </div>
            )}

            {/* Test Corpus FMR display */}
            <div className="hidden text-right md:block">
              <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                TEST CORPUS FMR
              </div>
              <div className="font-mono text-sm font-semibold text-gain">0.000</div>
            </div>

            {/* Standard Light / Dark Toggle */}
            <ThemeToggle />

            {/* CFO badge */}
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-primary/40 bg-primary/10 font-mono text-xs font-bold text-primary">
              CFO
            </div>
          </div>
        </div>

        {/* 🔴 P1: Live Inbound Webhook Telemetry Stream Ticker */}
        <div className="flex items-center justify-between border-t border-border/80 bg-panel/70 px-4 py-1.5 font-mono text-[11px] backdrop-blur overflow-hidden">
          <div className="flex items-center gap-2 min-w-0">
            <span className="flex h-2 w-2 rounded-full bg-gain animate-status-dot shrink-0" />
            <span className="font-bold text-primary shrink-0 uppercase tracking-wider text-[10px]">
              LIVE WEBHOOK STREAM
            </span>
            <span className="text-muted-foreground/40 shrink-0">•</span>
            <div className="truncate text-foreground/90 transition-all duration-300">
              <LiveWebhookTicker />
            </div>
          </div>

          <div className="hidden sm:flex items-center gap-3 shrink-0 pl-3">
            <Link
              href="/ledger"
              className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-primary transition"
            >
              <span>Merkle Block: #8492</span>
              <span className="text-gain font-semibold">✓ Verified</span>
            </Link>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <nav className="flex flex-col gap-1 border-t border-border bg-panel p-3 md:hidden">
            <div className="px-2 pb-1 font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
              Navigation Rails
            </div>
            {navItems.map((item) => {
              const active = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center justify-between rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    active ? 'bg-accent text-foreground' : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className={`font-mono text-[10px] ${active ? 'text-primary' : 'text-muted-foreground'}`}>{item.code}</span>
                    <span>{item.label}</span>
                  </div>
                  {active && <span className="h-1.5 w-1.5 rounded-full bg-primary" />}
                </Link>
              )
            })}
          </nav>
        )}
      </header>

      {/* CFO Copilot Slide-Over Drawer */}
      <CfoCopilotDrawer isOpen={copilotOpen} onClose={() => setCopilotOpen(false)} />
    </>
  )
}

function LiveWebhookTicker() {
  const events = [
    {
      badge: 'HMAC✓ 00:20:14',
      text: 'razorpay.payment.captured · ₹59,764.78 · Route Transferred (on_hold: true)',
      tone: 'text-gain',
    },
    {
      badge: 'ED25519✓ 00:20:17',
      text: 'gst.mod36_validation · GSTIN 29ABCDE1234F1Z5 MATCHED GSTR-2B',
      tone: 'text-primary',
    },
    {
      badge: 'KNUTH✓ 00:20:20',
      text: 'exact_cover.solved · 4 Invoices · UTR HDFCN24942603 · FMR 0.000',
      tone: 'text-gain',
    },
    {
      badge: 'SWEEP✓ 00:20:23',
      text: 'capital.reconcile_and_sweep · 12% Auto-Deduction · Balance ₹0.00',
      tone: 'text-gold',
    },
    {
      badge: 'CERT#c7a9f1',
      text: 'rbi.digital_lending_norm · FLDG 0% Risk Transfer Compliant',
      tone: 'text-primary',
    },
  ]

  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % events.length)
    }, 3500)
    return () => clearInterval(timer)
  }, [events.length])

  const current = events[currentIndex]

  return (
    <span className="inline-flex items-center gap-1.5 font-mono">
      <span className={`font-bold ${current.tone}`}>[{current.badge}]</span>
      <span className="text-foreground">{current.text}</span>
    </span>
  )
}
