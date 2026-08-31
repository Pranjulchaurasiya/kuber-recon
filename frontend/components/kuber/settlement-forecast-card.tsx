'use client'

import { useState } from 'react'
import {
  TrendingUp,
  Calendar,
  Banknote,
  ArrowRight,
  ShieldCheck,
  Clock,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  FileCheck,
  CheckCircle2
} from 'lucide-react'
import { paiseToInr, inr } from '@/lib/kuber-data'

export interface DailyForecastBand {
  dayLabel: string
  dateStr: string
  clearingCycle: 'T+1' | 'T+2' | 'T+0 (Instant)'
  status: 'SETTLED' | 'IN_TRANSIT' | 'SCHEDULED' | 'ESCROW_HELD'
  grossGmvPaise: number
  mdrFeesPaise: number // 1.85%
  gstItcPaise: number // 18% on MDR
  tdsPaise: number // 1.00% Sec 194-O
  netInflowPaise: number
  invoicesCount: number
}

const FORECAST_DAYS: DailyForecastBand[] = [
  {
    dayLabel: 'Today (Mon)',
    dateStr: '31 Aug 2026',
    clearingCycle: 'T+1',
    status: 'IN_TRANSIT',
    grossGmvPaise: 42815640, // ₹4,28,156.40
    mdrFeesPaise: 792089,   // ₹7,920.89 (1.85%)
    gstItcPaise: 142576,    // ₹1,425.76 (18% on MDR)
    tdsPaise: 428156,       // ₹4,281.56 (1% 194-O)
    netInflowPaise: 41452819, // ₹4,14,528.19
    invoicesCount: 142,
  },
  {
    dayLabel: 'Tue',
    dateStr: '01 Sep 2026',
    clearingCycle: 'T+1',
    status: 'SCHEDULED',
    grossGmvPaise: 38450000,
    mdrFeesPaise: 711325,
    gstItcPaise: 128038,
    tdsPaise: 384500,
    netInflowPaise: 37226137,
    invoicesCount: 128,
  },
  {
    dayLabel: 'Wed',
    dateStr: '02 Sep 2026',
    clearingCycle: 'T+1',
    status: 'SCHEDULED',
    grossGmvPaise: 51200000,
    mdrFeesPaise: 947200,
    gstItcPaise: 170496,
    tdsPaise: 512000,
    netInflowPaise: 49570304,
    invoicesCount: 165,
  },
  {
    dayLabel: 'Thu',
    dateStr: '03 Sep 2026',
    clearingCycle: 'T+2',
    status: 'SCHEDULED',
    grossGmvPaise: 46800000,
    mdrFeesPaise: 865800,
    gstItcPaise: 155844,
    tdsPaise: 468000,
    netInflowPaise: 45310356,
    invoicesCount: 150,
  },
  {
    dayLabel: 'Fri',
    dateStr: '04 Sep 2026',
    clearingCycle: 'T+1',
    status: 'SCHEDULED',
    grossGmvPaise: 62400000,
    mdrFeesPaise: 1154400,
    gstItcPaise: 207792,
    tdsPaise: 624000,
    netInflowPaise: 60413808,
    invoicesCount: 204,
  },
  {
    dayLabel: 'Sat',
    dateStr: '05 Sep 2026',
    clearingCycle: 'T+2',
    status: 'ESCROW_HELD',
    grossGmvPaise: 28900000,
    mdrFeesPaise: 534650,
    gstItcPaise: 96237,
    tdsPaise: 289000,
    netInflowPaise: 27980113,
    invoicesCount: 94,
  },
  {
    dayLabel: 'Sun',
    dateStr: '06 Sep 2026',
    clearingCycle: 'T+2',
    status: 'ESCROW_HELD',
    grossGmvPaise: 31500000,
    mdrFeesPaise: 582750,
    gstItcPaise: 104895,
    tdsPaise: 315000,
    netInflowPaise: 30497355,
    invoicesCount: 102,
  },
]

export function SettlementForecastCard() {
  const [selectedDayIndex, setSelectedDayIndex] = useState<number>(0)
  const selectedDay = FORECAST_DAYS[selectedDayIndex]

  const total7DayGmvPaise = FORECAST_DAYS.reduce((sum, d) => sum + d.grossGmvPaise, 0)
  const total7DayNetPaise = FORECAST_DAYS.reduce((sum, d) => sum + d.netInflowPaise, 0)
  const total7DayTdsPaise = FORECAST_DAYS.reduce((sum, d) => sum + d.tdsPaise, 0)
  const total7DayGstPaise = FORECAST_DAYS.reduce((sum, d) => sum + d.gstItcPaise, 0)

  const maxDailyPaise = Math.max(...FORECAST_DAYS.map((d) => d.grossGmvPaise))

  return (
    <div className="rounded-xl border border-border bg-panel p-5 shadow-xl backdrop-blur space-y-6">
      {/* Header with Title & KPI Overview */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold tracking-tight text-foreground flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              7-Day Settlement Forecast &amp; Rail Inflow
            </h2>
            <span className="rounded bg-primary/10 px-2 py-0.5 font-mono text-[10px] font-bold text-primary border border-primary/30">
              RBI T±2 CLEARING
            </span>
          </div>
          <p className="mt-0.5 font-mono text-xs text-muted-foreground font-medium">
            Multi-rail projected payouts with statutory GSTR-2B &amp; 194-O TDS line-item deductions
          </p>
        </div>

        <div className="flex items-center gap-4 font-mono text-xs">
          <div className="text-right">
            <span className="text-[10px] uppercase text-muted-foreground block font-bold">7-Day Projected GMV</span>
            <span className="text-sm font-bold text-foreground tabular-nums">
              {paiseToInr(total7DayGmvPaise)}
            </span>
          </div>
          <div className="h-8 w-px bg-border" />
          <div className="text-right">
            <span className="text-[10px] uppercase text-gain block font-bold">Net Nodal Inflow</span>
            <span className="text-sm font-bold text-gain tabular-nums">
              {paiseToInr(total7DayNetPaise)}
            </span>
          </div>
        </div>
      </div>

      {/* Fund State Transition Pipeline */}
      <div className="rounded-lg border border-border bg-background p-4">
        <div className="mb-2 flex items-center justify-between">
          <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground font-bold flex items-center gap-1.5">
            <Clock className="h-3 w-3 text-gold" />
            Nodal Fund State Transition Flow
          </span>
          <span className="font-mono text-[10px] text-gain font-bold">Zero Paisa Leakage Proof</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 font-mono text-xs">
          {/* Step 1 */}
          <div className="rounded-md border border-primary/30 bg-primary/10 p-3 space-y-1">
            <div className="flex items-center justify-between text-[10px] text-primary uppercase font-bold">
              <span>1. Customer Capture</span>
              <span>T+0</span>
            </div>
            <div className="text-sm font-bold text-foreground">Razorpay Route</div>
            <p className="text-[10px] text-muted-foreground font-medium">Gross funds held in escrow sandbox</p>
          </div>

          {/* Step 2 */}
          <div className="rounded-md border border-gold/30 bg-gold/10 p-3 space-y-1">
            <div className="flex items-center justify-between text-[10px] text-gold uppercase font-bold">
              <span>2. Deductions Lock</span>
              <span>T+0</span>
            </div>
            <div className="text-sm font-bold text-foreground">MDR + GST + TDS</div>
            <p className="text-[10px] text-muted-foreground font-medium">Exact-paise statutory withholding</p>
          </div>

          {/* Step 3 */}
          <div className="rounded-md border border-cyan-500/30 bg-cyan-500/10 p-3 space-y-1">
            <div className="flex items-center justify-between text-[10px] text-cyan-600 dark:text-cyan-400 uppercase font-bold">
              <span>3. Merkle Validation</span>
              <span>T+1</span>
            </div>
            <div className="text-sm font-bold text-foreground">Knuth DLX Check</div>
            <p className="text-[10px] text-muted-foreground font-medium">FMR 0.000 exact cover certification</p>
          </div>

          {/* Step 4 */}
          <div className="rounded-md border border-gain/30 bg-gain/10 p-3 space-y-1">
            <div className="flex items-center justify-between text-[10px] text-gain uppercase font-bold">
              <span>4. Nodal Release</span>
              <span>T+1 / T+2</span>
            </div>
            <div className="text-sm font-bold text-gain">Bank Lump-Sum Payout</div>
            <p className="text-[10px] text-muted-foreground font-medium">Direct NEFT/RTGS to merchant account</p>
          </div>
        </div>
      </div>

      {/* Interactive 7-Day Bar Chart Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground font-bold">
            Daily Settlement Bands (Select Day for Exact Itemization)
          </span>
          <span className="font-mono text-[10px] text-muted-foreground font-medium">
            Selected: <strong className="text-primary">{selectedDay.dayLabel} · {selectedDay.dateStr}</strong>
          </span>
        </div>

        <div className="grid grid-cols-7 gap-2">
          {FORECAST_DAYS.map((day, idx) => {
            const isSelected = selectedDayIndex === idx
            const heightPct = Math.round((day.grossGmvPaise / maxDailyPaise) * 100)

            return (
              <button
                key={day.dayLabel}
                onClick={() => setSelectedDayIndex(idx)}
                className={`group flex flex-col items-center rounded-lg border p-3 text-center transition-all ${
                  isSelected
                    ? 'border-primary bg-primary/10 shadow-lg ring-1 ring-primary'
                    : 'border-border bg-background hover:border-primary/50 hover:bg-accent/60'
                }`}
              >
                <span className="font-mono text-[10px] uppercase text-muted-foreground group-hover:text-foreground font-bold">
                  {day.dayLabel.split(' ')[0]}
                </span>
                <span className="font-mono text-[9px] text-muted-foreground font-medium">
                  {day.clearingCycle}
                </span>

                {/* Visual Bar Indicator */}
                <div className="my-2.5 flex h-24 w-full items-end justify-center rounded bg-accent/40 p-1">
                  <div
                    style={{ height: `${heightPct}%` }}
                    className={`w-full rounded-sm transition-all duration-300 ${
                      isSelected
                        ? 'bg-primary shadow-glow'
                        : 'bg-primary/50 group-hover:bg-primary/70'
                    }`}
                  />
                </div>

                <span className="font-mono text-[11px] font-bold text-foreground tabular-nums">
                  {paiseToInr(day.netInflowPaise, { compact: true })}
                </span>
                <span className="mt-0.5 rounded px-1 py-0.2 font-mono text-[8px] uppercase font-bold text-gain bg-gain/10 border border-gain/20">
                  {day.invoicesCount} txns
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Selected Day Line-Item Breakdown Drawer */}
      <div className="rounded-lg border border-border bg-background p-4 space-y-3 font-mono">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-2">
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 rounded-full bg-gain animate-status-dot" />
            <span className="text-xs font-bold text-foreground">
              {selectedDay.dayLabel} ({selectedDay.dateStr}) Breakdown
            </span>
            <span className="rounded bg-panel px-1.5 py-0.5 text-[10px] text-gold border border-border font-bold">
              {selectedDay.clearingCycle} Settlement
            </span>
          </div>
          <span className="text-xs text-gain font-bold">
            Net Release: {paiseToInr(selectedDay.netInflowPaise)}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
          <div className="rounded border border-border bg-panel p-2.5">
            <span className="text-[9px] uppercase text-muted-foreground block font-bold">Gross GMV</span>
            <span className="font-bold text-foreground tabular-nums text-sm">
              {paiseToInr(selectedDay.grossGmvPaise)}
            </span>
            <span className="text-[9px] text-muted-foreground block mt-0.5 font-medium">{selectedDay.invoicesCount} Invoices</span>
          </div>

          <div className="rounded border border-danger/30 bg-danger/10 p-2.5">
            <span className="text-[9px] uppercase text-danger block font-bold">MDR Fees (1.85%)</span>
            <span className="font-bold text-danger tabular-nums text-sm">
              −{paiseToInr(selectedDay.mdrFeesPaise)}
            </span>
            <span className="text-[9px] text-muted-foreground block mt-0.5 font-medium">Gateway Processing</span>
          </div>

          <div className="rounded border border-gold/30 bg-gold/10 p-2.5">
            <span className="text-[9px] uppercase text-gold block font-bold">GST on MDR (18%)</span>
            <span className="font-bold text-gold tabular-nums text-sm">
              −{paiseToInr(selectedDay.gstItcPaise)}
            </span>
            <span className="text-[9px] text-muted-foreground block mt-0.5 font-medium">GSTR-2B Claimable</span>
          </div>

          <div className="rounded border border-amber-500/30 bg-amber-500/10 p-2.5">
            <span className="text-[9px] uppercase text-amber-600 dark:text-amber-400 block font-bold">TDS (1% 194-O)</span>
            <span className="font-bold text-amber-600 dark:text-amber-400 tabular-nums text-sm">
              −{paiseToInr(selectedDay.tdsPaise)}
            </span>
            <span className="text-[9px] text-muted-foreground block mt-0.5 font-medium">CBDT Nodal Pool</span>
          </div>

          <div className="rounded border border-gain/40 bg-gain/10 p-2.5 col-span-2 sm:col-span-1">
            <span className="text-[9px] uppercase text-gain block font-bold">Net Inflow (₹)</span>
            <span className="font-bold text-gain tabular-nums text-sm">
              {paiseToInr(selectedDay.netInflowPaise)}
            </span>
            <span className="text-[9px] text-gain block mt-0.5 font-semibold">₹0.00 Float Drift</span>
          </div>
        </div>
      </div>
    </div>
  )
}
