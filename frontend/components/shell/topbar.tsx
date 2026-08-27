'use client'

import { usePathname } from 'next/navigation'
import { navItems } from '@/lib/kuber-data'
import { ThemeToggle } from './theme-toggle'

export function Topbar() {
  const pathname = usePathname()
  const current = navItems.find((n) => n.href === pathname) ?? navItems[0]

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-4 border-b border-border bg-background/90 px-5 backdrop-blur-md">
      {/* Mobile brand mark */}
      <div className="flex items-center gap-2 md:hidden">
        <span className="font-mono text-xs font-semibold text-gold">KR</span>
      </div>

      {/* Breadcrumb */}
      <div className="flex min-w-0 items-center gap-2">
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
          {current.code}
        </span>
        <span className="text-muted-foreground/40">/</span>
        <h1 className="truncate text-sm font-medium text-foreground">{current.label}</h1>
      </div>

      {/* Right controls */}
      <div className="ml-auto flex items-center gap-3">
        {/* Live rail status */}
        <div className="hidden items-center gap-2 rounded-full border border-border bg-panel px-3 py-1.5 sm:flex">
          <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-gain" />
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Live · Razorpay Rail
          </span>
        </div>

        {/* FMR display */}
        <div className="hidden text-right md:block">
          <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            FMR
          </div>
          <div className="font-mono text-sm font-semibold text-gain">0.000</div>
        </div>

        {/* Theme toggle */}
        <ThemeToggle />

        {/* CFO badge */}
        <div className="flex h-8 w-8 items-center justify-center rounded-full border border-gold/40 bg-gold/10 font-mono text-[11px] font-semibold text-gold">
          CFO
        </div>
      </div>
    </header>
  )
}
