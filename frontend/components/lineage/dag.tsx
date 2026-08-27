'use client'

import { useState } from 'react'
import { lineage, inr, type LineageNode } from '@/lib/kuber-data'

const NODE_W = 168
const NODE_H = 62

const kindColor: Record<LineageNode['kind'], string> = {
  root: 'var(--chart-3)',
  gmv: 'var(--gold)',
  deduction: 'var(--danger)',
  net: 'var(--gain)',
}

export function LineageDag() {
  const [active, setActive] = useState<string>('utr')

  const isEdgeLit = (from: string, to: string) => active === from || active === to
  const nodeById = (id: string) => lineage.nodes.find((n) => n.id === id)!

  return (
    <div className="rounded-lg border border-border bg-panel">
      <div className="flex items-center justify-between border-b border-border p-5">
        <div>
          <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            Money Lineage DAG · Algorithm X
          </h2>
          <div className="mt-1 font-mono text-xs text-muted-foreground">{lineage.utr}</div>
        </div>
        <div className="text-right">
          <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            False Match Rate
          </div>
          <div className="font-mono text-lg font-semibold text-gain">{lineage.fmr.toFixed(3)}</div>
        </div>
      </div>

      <div className="relative overflow-x-auto bg-blueprint">
        <svg viewBox="0 0 780 410" className="h-auto w-full" role="img" aria-label="Money lineage directed acyclic graph">
          {/* edges */}
          {lineage.edges.map((e, i) => {
            const a = nodeById(e.from)
            const b = nodeById(e.to)
            const x1 = a.x + NODE_W
            const y1 = a.y + NODE_H / 2
            const x2 = b.x
            const y2 = b.y + NODE_H / 2
            const midX = (x1 + x2) / 2
            const path = `M${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`
            const lit = isEdgeLit(e.from, e.to)
            return (
              <g key={i}>
                <path d={path} fill="none" stroke={lit ? 'var(--gold)' : 'var(--border)'} strokeWidth={lit ? 2 : 1.25} opacity={lit ? 0.9 : 0.6} />
                {lit && <path d={path} fill="none" stroke="var(--gold)" strokeWidth="2" className="animate-flow" />}
                {e.label && (
                  <text x={midX} y={(y1 + y2) / 2 - 6} textAnchor="middle" fontSize="9" fontFamily="var(--font-mono)" fill={lit ? 'var(--gold)' : 'var(--muted-foreground)'} letterSpacing="1">
                    {e.label}
                  </text>
                )}
              </g>
            )
          })}

          {/* nodes */}
          {lineage.nodes.map((n) => {
            const on = active === n.id
            const color = kindColor[n.kind]
            return (
              <g key={n.id} onClick={() => setActive(n.id)} className="cursor-pointer" role="button" aria-label={n.label}>
                <rect
                  x={n.x}
                  y={n.y}
                  width={NODE_W}
                  height={NODE_H}
                  rx="7"
                  fill={on ? 'color-mix(in oklch, ' + color + ' 14%, var(--panel))' : 'var(--panel)'}
                  stroke={color}
                  strokeWidth={on ? 2 : 1.25}
                  strokeOpacity={on ? 1 : 0.55}
                />
                <rect x={n.x} y={n.y} width="4" height={NODE_H} rx="2" fill={color} />
                <text x={n.x + 16} y={n.y + 22} fontSize="10.5" fontFamily="var(--font-mono)" fill="var(--muted-foreground)" letterSpacing="0.5">
                  {n.label}
                </text>
                <text x={n.x + 16} y={n.y + 42} fontSize="15" fontWeight="600" fontFamily="var(--font-mono)" fill="var(--foreground)">
                  {inr(n.amount)}
                </text>
                <text x={n.x + 16} y={n.y + 55} fontSize="8.5" fontFamily="var(--font-mono)" fill="var(--muted-foreground)">
                  {n.sub}
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      <div className="flex flex-wrap items-center gap-4 border-t border-border p-4">
        <Legend color="var(--chart-3)" label="Bank root" />
        <Legend color="var(--gold)" label="Gross GMV" />
        <Legend color="var(--danger)" label="Statutory deduction" />
        <Legend color="var(--gain)" label="Net settlement" />
        <span className="ml-auto font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          click a node to trace
        </span>
      </div>
    </div>
  )
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="h-2.5 w-2.5 rounded-sm" style={{ background: color }} />
      <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">{label}</span>
    </div>
  )
}
