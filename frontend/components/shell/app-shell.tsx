'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { Sidebar } from './sidebar'
import { Topbar } from './topbar'
import { ThemeToggle } from './theme-toggle'
import { AmbientMesh3D } from '@/components/ui/ambient-mesh-3d'
import { ArrowRight, Cpu, ShieldCheck, BookOpen, ExternalLink } from 'lucide-react'
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
          {/* Left Brand Identity */}
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-primary/40 bg-primary/10 font-mono text-sm font-bold text-primary shadow-sm group-hover:border-primary transition-colors">
                A
              </div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-base font-bold tracking-tight text-foreground">APEX</span>
                <span className="text-xs text-muted-foreground font-semibold">Assurance</span>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center gap-7 font-medium text-xs text-muted-foreground">
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
              Console
            </a>
            <a
              href={`${getApiUrl()}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-foreground font-semibold flex items-center gap-1"
            >
              Docs <ExternalLink className="h-3 w-3 opacity-60" />
            </a>
          </nav>

          {/* Right Sleek Actions */}
          <div className="flex items-center gap-2.5">
            {/* Live Gateway Mode Indicator */}
            {gatewayMode === 'test_mode' ? (
              <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-gain/30 bg-gain/10 px-2.5 py-1 font-mono text-[11px] font-semibold text-gain">
                <span className="h-1.5 w-1.5 rounded-full bg-gain animate-status-dot" />
                TEST MODE
              </div>
            ) : (
              <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 font-mono text-[11px] font-semibold text-amber-600 dark:text-amber-500">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-status-dot" />
                SANDBOX
              </div>
            )}

            {/* GitHub Repository Icon Link */}
            <a
              href="https://github.com/Pranjulchaurasiya/kuber-recon"
              target="_blank"
              rel="noopener noreferrer"
              className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/60 transition"
              title="View Source on GitHub"
              aria-label="View Source on GitHub"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
            </a>

            {/* Theme Toggle */}
            <ThemeToggle />

            {/* Primary Action Button */}
            <Link
              href="/apex"
              className="inline-flex items-center gap-1.5 rounded-lg bg-foreground px-3.5 py-2 text-xs font-bold text-background shadow-md transition-all hover:opacity-90 hover:scale-[1.02]"
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
              <a
                href="https://github.com/Pranjulchaurasiya/kuber-recon"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-primary transition flex items-center gap-1.5"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
                <span>GitHub Repo</span>
              </a>
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
