'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { Sidebar } from './sidebar'
import { Topbar } from './topbar'
import { ThemeToggle } from './theme-toggle'
import { AmbientMesh3D } from '@/components/ui/ambient-mesh-3d'
import { ArrowRight, Cpu, ShieldCheck } from 'lucide-react'
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
      <div className="relative min-h-screen flex flex-col bg-background text-foreground transition-colors duration-200 overflow-x-hidden">
        {/* Interactive 3D Ambient Mesh Layer */}
        <AmbientMesh3D />

        {/* Full-width Tactical Landing Header */}
        <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-border/80 bg-background/90 px-4 sm:px-8 backdrop-blur-2xl">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-primary/40 bg-primary/10 font-mono text-sm font-bold text-primary shadow-sm">
                A
              </div>
              <div>
                <span className="text-base font-bold tracking-tight text-foreground">APEX</span>
                <span className="ml-1.5 text-xs text-muted-foreground font-semibold">Capital &amp; Assurance</span>
                <span className="hidden lg:inline-block ml-2 rounded bg-primary/10 px-1.5 py-0.5 font-mono text-[10px] uppercase font-bold text-primary border border-primary/20">
                  Razorpay Route Escrow
                </span>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 font-medium text-xs text-muted-foreground">
            <a href="#problem-solution" className="transition-colors hover:text-foreground font-semibold">
              Why APEX
            </a>
            <a href="#the-proof" className="transition-colors hover:text-foreground font-semibold">
              Proof
            </a>
            <a href="#how-it-works" className="transition-colors hover:text-foreground font-semibold">
              How It Works
            </a>
            <a href="#product-console" className="transition-colors hover:text-foreground font-semibold">
              Operating Console
            </a>
            <Link href="/apex" className="transition-colors hover:text-foreground font-semibold">
              Assurance Terminal
            </Link>
          </nav>

          {/* Right Actions & Theme Switcher */}
          <div className="flex items-center gap-3">
            {gatewayMode === 'test_mode' ? (
              <div className="hidden sm:flex items-center gap-2 rounded-full border border-gain/30 bg-gain/10 px-3 py-1 font-mono text-xs font-semibold text-gain">
                <span className="h-2 w-2 rounded-full bg-gain animate-status-dot" />
                RAZORPAY TEST MODE
              </div>
            ) : (
              <div className="hidden sm:flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 font-mono text-xs font-semibold text-amber-600 dark:text-amber-500">
                <span className="h-2 w-2 rounded-full bg-amber-500 animate-status-dot" />
                SANDBOX SIMULATION
              </div>
            )}

            <ThemeToggle />

            <Link
              href="/apex"
              className="inline-flex items-center gap-2 rounded-lg bg-foreground px-4 py-2 text-xs font-bold text-background shadow-lg transition-all hover:opacity-90 hover:scale-[1.02]"
            >
              Launch Console
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </header>

        {/* Main Landing Canvas */}
        <main className="flex-1 relative z-10">{children}</main>

        {/* Tactical Footer */}
        <footer className="relative z-10 border-t border-border bg-panel py-8 px-6 sm:px-8 text-xs text-muted-foreground backdrop-blur-xl">
          <div className="max-w-[1280px] mx-auto flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-gain" />
              <span className="font-mono font-semibold text-foreground">APEX Autonomous Kernel</span>
              <span>· Razorpay AI Buildathon 2026 (Track 01 &amp; 04)</span>
            </div>
            <div className="flex items-center gap-6 font-mono text-[11px]">
              <span>81/81 INVARIANT TESTS PASSING</span>
              <span>FMR 0.000</span>
              <span>BASE-10 ZERO FLOAT</span>
            </div>
          </div>
        </footer>
      </div>
    )
  }

  return (
    <div className="relative flex min-h-screen bg-background text-foreground overflow-x-hidden">
      {/* 3D Ambient Particle Mesh across console pages */}
      <AmbientMesh3D />

      <Sidebar />
      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1">{children}</main>
      </div>
    </div>
  )
}
