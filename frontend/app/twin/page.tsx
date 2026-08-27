import { Simulator } from '@/components/twin/simulator'
import { Pill } from '@/components/kuber/primitives'
import { scenarios } from '@/lib/kuber-data'

export default function TwinPage() {
  return (
    <div className="mx-auto max-w-[1400px] px-5 py-8">
      <header className="mb-6">
        <Pill tone="gold">Causal Digital Twin · Screen 03</Pill>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight">Causal Digital Twin</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          Move from reporting the past to stress-testing the future. The twin models causal shocks —
          bank-holiday freezes, vendor GSTR-1 defaults, chargeback surges — and projects their impact
          on liquidity before they ever hit the books.
        </p>
      </header>

      <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
        {scenarios.map((s) => (
          <div key={s.id} className="rounded-lg border border-border bg-panel p-4">
            <div className="font-mono text-[10px] uppercase tracking-widest text-warn">Scenario</div>
            <div className="mt-1 text-sm font-medium">{s.label}</div>
            <div className="mt-1 text-xs leading-relaxed text-muted-foreground">{s.desc}</div>
          </div>
        ))}
      </div>

      <Simulator />
    </div>
  )
}
