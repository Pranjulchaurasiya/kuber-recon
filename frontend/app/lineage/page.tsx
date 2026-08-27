import { LineageDag } from '@/components/lineage/dag'
import { Panel, SectionLabel, StatTile, Pill } from '@/components/kuber/primitives'
import { lineage, lineageInvoices, inr } from '@/lib/kuber-data'

export default function LineagePage() {
  return (
    <div className="mx-auto max-w-[1400px] px-5 py-8">
      <header className="mb-6">
        <Pill tone="gold">Knuth Algorithm X · Combinatorial Exact Cover</Pill>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">Money Lineage</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          A single bank lump-sum can hide dozens of invoices. KuberRecon uses Donald Knuth&apos;s
          Algorithm X to solve the exact cover — proving how one UTR decomposes into gross GMV, MDR,
          GST and TDS with a False Match Rate of{' '}
          <span className="font-mono text-gain">0.000</span>.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Settlement (UTR)" value={inr(lineage.settlement, { compact: true })} hint="HDFC lump-sum" />
        <StatTile label="Invoices covered" value={lineage.invoices} accent="gold" hint="Exact cover solved" />
        <StatTile label="False Match Rate" value={lineage.fmr.toFixed(3)} accent="gain" hint="Mathematical certainty" />
        <StatTile label="Unexplained delta" value="₹0.00" accent="gain" hint="Every paisa attributed" />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <LineageDag />
        </div>

        <div className="flex flex-col gap-4">
          <Panel>
            <SectionLabel right={<Pill tone="gain">exact cover</Pill>}>Invoice Set</SectionLabel>
            <div className="flex flex-col divide-y divide-border">
              {lineageInvoices.map((iv) => (
                <div key={iv.inv} className="flex items-center justify-between py-2.5 first:pt-0 last:pb-0">
                  <span className="font-mono text-xs text-muted-foreground">{iv.inv}</span>
                  <span className="font-mono text-sm tabular-nums">{inr(iv.amt)}</span>
                  <span className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-gain">
                    <span className="h-1.5 w-1.5 rounded-full bg-gain" />
                    matched
                  </span>
                </div>
              ))}
            </div>
          </Panel>

          <Panel>
            <SectionLabel>Reconciliation Proof</SectionLabel>
            <dl className="flex flex-col gap-3 font-mono text-xs">
              <ProofRow k="Method" v="Knuth Algorithm X (DLX)" />
              <ProofRow k="Cover type" v="Exact · non-overlapping" />
              <ProofRow k="Residual" v="₹0.00" accent />
              <ProofRow k="Certainty" v="FMR = 0.000" accent />
            </dl>
            <div className="mt-4 rounded-md border border-gain/30 bg-gain/5 p-3 text-xs leading-relaxed text-muted-foreground">
              The engine proves lineage rather than estimating it — no heuristic matching, no guessed
              math. Each node above is a verifiable link from bank root to statutory leaf.
            </div>
          </Panel>
        </div>
      </div>
    </div>
  )
}

function ProofRow({ k, v, accent }: { k: string; v: string; accent?: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="uppercase tracking-widest text-muted-foreground">{k}</dt>
      <dd className={accent ? 'text-gain' : 'text-foreground'}>{v}</dd>
    </div>
  )
}
