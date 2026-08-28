'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { Sidebar } from './sidebar'
import { Topbar } from './topbar'
import { ThemeToggle } from './theme-toggle'
import { ArrowRight, Cpu } from 'lucide-react'
import { useEffect, useState } from 'react'
import { getApiUrl } from '@/lib/api-client'

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isLandingPage = pathname === '/'
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

  if (isLandingPage) {
    return (
      <div className="min-h-screen flex flex-col bg-background text-foreground">
        {/* Full-width Landing Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-gold/40 bg-gold/10 font-mono text-sm font-bold text-gold">
                A
              </div>
              <div>
                <span className="text-base font-bold tracking-tight text-foreground">APEX Assurance</span>
                <span className="ml-2 rounded bg-gold/10 px-1.5 py-0.5 font-mono text-[10px] uppercase font-semibold text-gold border border-gold/30">
                  Powered by KuberRecon
                </span>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 font-medium text-sm text-muted-foreground">
            <Link href="/apex" className="transition-colors hover:text-foreground">
              Assurance Console
            </Link>
            <a href="#settlement-gate" className="transition-colors hover:text-foreground">
              Settlement Gate
            </a>
            <a href="#architecture" className="transition-colors hover:text-foreground">
              Architecture
            </a>
            <Link href="/escrow" className="transition-colors hover:text-foreground">
              Verification Rails
            </Link>
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            {gatewayMode === 'test_mode' ? (
              <div className="hidden sm:flex items-center gap-2 rounded-full border border-gain/30 bg-gain/10 px-3 py-1 font-mono text-xs font-semibold text-gain">
                <span className="h-2 w-2 rounded-full bg-gain animate-status-dot" />
                RAZORPAY TEST MODE
              </div>
            ) : (
              <div className="hidden sm:flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 font-mono text-xs font-semibold text-amber-500">
                <span className="h-2 w-2 rounded-full bg-amber-500 animate-status-dot" />
                SANDBOX SIMULATION
              </div>
            )}

            <ThemeToggle />

            <Link
              href="/apex"
              className="hidden sm:inline-flex items-center gap-2 rounded-lg bg-foreground px-4 py-2 text-xs font-semibold text-background shadow transition-all hover:opacity-90"
            >
              Launch Console
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </header>

        {/* Main Landing Canvas */}
        <main className="flex-1">{children}</main>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1">{children}</main>
      </div>
    </div>
  )
}
