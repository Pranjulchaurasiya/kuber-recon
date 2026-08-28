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
          <div className="truncate text-sm font-bold tracking-tight text-foreground">APEX Assurance</div>
          <div className="truncate font-mono text-[11px] uppercase tracking-wider text-gold">
            Powered by KuberRecon
          </div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-3">
        <div className="px-2 pb-2 pt-1 font-mono text-xs uppercase tracking-wider text-muted-foreground">
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
                  ? 'bg-accent text-foreground font-semibold'
                  : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground'
              }`}
            >
              <span
                className={`font-mono text-xs ${
                  active ? 'text-gold font-bold' : 'text-muted-foreground group-hover:text-foreground'
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
        <div className="flex items-center justify-between font-mono text-xs uppercase tracking-wider text-muted-foreground">
          <span>Merkle Root</span>
          <span className="text-gain font-semibold">Verified</span>
        </div>
        <div className="mt-1 truncate font-mono text-xs text-foreground">0x8f3a…d41c</div>
        <div className="mt-3 flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-gain animate-status-dot" />
          <span className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
            Rail Active · 99.99% Sync
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
