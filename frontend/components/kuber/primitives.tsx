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
      className={`rounded-lg border border-border bg-panel ${flush ? '' : 'p-5'} ${className}`}
    >
      {children}
    </section>
  )
}

export function SectionLabel({ children, right }: { children: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between">
      <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
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
    <div className="flex flex-col gap-1.5 rounded-lg border border-border bg-panel p-5">
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
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-widest ${map[tone]}`}
    >
      {children}
    </span>
  )
}
