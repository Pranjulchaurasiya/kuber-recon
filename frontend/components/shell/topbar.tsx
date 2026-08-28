'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { navItems } from '@/lib/kuber-data'
import { ThemeToggle } from './theme-toggle'
import { getApiUrl } from '@/lib/api-client'

export function Topbar() {
  const pathname = usePathname()
  const current = navItems.find((n) => n.href === pathname) ?? navItems[0]
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [gatewayMode, setGatewayMode] = useState<'test_mode' | 'sandbox_simulation'>('sandbox_simulation')

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
          <span className="font-mono text-xs font-bold text-gold">APEX</span>
        </div>

        {/* Breadcrumb */}
        <div className="flex min-w-0 items-center gap-2">
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-gold">
            {current.code}
          </span>
          <span className="text-muted-foreground/40">/</span>
          <h1 className="truncate text-sm font-semibold text-foreground">{current.label}</h1>
        </div>

        {/* Right controls */}
        <div className="ml-auto flex items-center gap-3">
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

          {/* Theme toggle */}
          <ThemeToggle />

          {/* CFO badge */}
          <div className="flex h-8 w-8 items-center justify-center rounded-full border border-gold/40 bg-gold/10 font-mono text-xs font-bold text-gold">
            CFO
          </div>
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
                  <span className={`font-mono text-[10px] ${active ? 'text-gold' : 'text-muted-foreground'}`}>{item.code}</span>
                  <span>{item.label}</span>
                </div>
                {active && <span className="h-1.5 w-1.5 rounded-full bg-gold" />}
              </Link>
            )
          })}
        </nav>
      )}
    </header>
  )
}
