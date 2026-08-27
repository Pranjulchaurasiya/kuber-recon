import type { ReactNode } from 'react'

export function Panel({
  children,
  className = '',
  flush = false,
}: {
  children: ReactNode
  className?: string
  flush?: boolean
}) {
  return (
    <section
      className={`kuber-panel border border-border bg-panel ${flush ? '' : 'p-5'} ${className}`}
    >
      {children}
    </section>
  )
}

export function SectionLabel({ children, right }: { children: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h2 className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
        <span className="h-1.5 w-1.5 bg-gold shadow-[0_0_12px_var(--gold)]" />
        {children}
      </h2>
      {right}
    </div>
  )
}

export function StatusDot({ status }: { status: 'ok' | 'warn' | 'danger' }) {
  const color =
    status === 'ok' ? 'bg-gain' : status === 'warn' ? 'bg-warn' : 'bg-danger'
  return <span className={`inline-block h-1.5 w-1.5 rounded-full ${color}`} />
}

export function StatTile({
  label,
  value,
  hint,
  accent = 'default',
}: {
  label: string
  value: ReactNode
  hint?: ReactNode
  accent?: 'default' | 'gold' | 'gain' | 'warn' | 'danger'
}) {
  const valueColor =
    accent === 'gold'
      ? 'text-gold'
      : accent === 'gain'
        ? 'text-gain'
        : accent === 'warn'
          ? 'text-warn'
          : accent === 'danger'
            ? 'text-danger'
            : 'text-foreground'
  return (
    <div className="kuber-stat group relative flex flex-col gap-1.5 overflow-hidden border border-border bg-panel p-5">
      <span className={`absolute inset-x-0 top-0 h-px ${accent === 'gold' ? 'bg-gold' : accent === 'gain' ? 'bg-gain' : accent === 'warn' ? 'bg-warn' : accent === 'danger' ? 'bg-danger' : 'bg-border'}`} />
      <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </span>
      <span className={`font-mono text-2xl font-semibold tabular-nums tracking-tight ${valueColor}`}>
        {value}
      </span>
      {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
    </div>
  )
}

export function Pill({
  children,
  tone = 'muted',
}: {
  children: ReactNode
  tone?: 'muted' | 'gold' | 'gain' | 'warn' | 'danger'
}) {
  const map: Record<string, string> = {
    muted: 'border-border text-muted-foreground',
    gold: 'border-gold/40 text-gold bg-gold/10',
    gain: 'border-gain/40 text-gain bg-gain/10',
    warn: 'border-warn/40 text-warn bg-warn/10',
    danger: 'border-danger/40 text-danger bg-danger/10',
  }
  return (
    <span
      className={`inline-flex items-center gap-1.5 border px-2.5 py-1 font-mono text-[10px] uppercase tracking-widest ${map[tone]}`}
    >
      {children}
    </span>
  )
}
