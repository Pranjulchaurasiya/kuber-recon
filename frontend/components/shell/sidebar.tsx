'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { navItems } from '@/lib/kuber-data'

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-border bg-panel md:flex">
      <div className="flex items-center gap-3 border-b border-border px-5 py-4">
        <KuberMark />
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold tracking-tight">KuberRecon</div>
          <div className="truncate font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Integrity OS
          </div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 p-3">
        <div className="px-2 pb-2 pt-1 font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
          Rails
        </div>
        {navItems.map((item) => {
          const active = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors ${
                active
                  ? 'bg-accent text-foreground'
                  : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground'
              }`}
            >
              <span
                className={`font-mono text-[10px] tracking-wider ${
                  active ? 'text-gold' : 'text-muted-foreground/70 group-hover:text-foreground/70'
                }`}
              >
                {item.code}
              </span>
              <span className="truncate leading-tight">{item.label}</span>
              {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-gold" />}
            </Link>
          )
        })}
      </nav>

      <div className="border-t border-border p-4">
        <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          <span>Merkle root</span>
          <span className="text-gain">verified</span>
        </div>
        <div className="mt-1 truncate font-mono text-xs text-foreground/80">0x8f3a…d41c</div>
        <div className="mt-3 flex items-center gap-2">
          <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-gain" />
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Rail active · 99.99% sync
          </span>
        </div>
      </div>
    </aside>
  )
}

function KuberMark() {
  return (
    <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-gold/40 bg-gold/10">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M12 2 L21 7 V17 L12 22 L3 17 V7 Z"
          stroke="var(--gold)"
          strokeWidth="1.4"
          strokeLinejoin="round"
        />
        <path d="M12 7 V17 M8 12 L12 9 L16 12" stroke="var(--gold)" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  )
}
