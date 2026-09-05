/**
 * KuberRecon domain data.
 *
 * Single source of truth for UI types, baseline constants, and paise-exact formatting helpers.
 */

/**
 * Formats a paise integer (base-10 paisa) as Indian Rupees (₹).
 * E.g., 118000 paise -> ₹1,180.00
 */
export const paiseToInr = (paise: number, opts?: { compact?: boolean }): string => {
  const rupees = paise / 100
  if (opts?.compact) {
    if (Math.abs(rupees) >= 1e7) return `₹${(rupees / 1e7).toFixed(2)}Cr`
    if (Math.abs(rupees) >= 1e5) return `₹${(rupees / 1e5).toFixed(2)}L`
    if (Math.abs(rupees) >= 1e3) return `₹${(rupees / 1e3).toFixed(1)}K`
  }
  return `₹${rupees.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

/**
 * Formats a value already in Rupees.
 */
export const inr = (rupees: number, opts?: { compact?: boolean; paise?: boolean }): string => {
  if (opts?.compact) {
    if (Math.abs(rupees) >= 1e7) return `₹${(rupees / 1e7).toFixed(2)}Cr`
    if (Math.abs(rupees) >= 1e5) return `₹${(rupees / 1e5).toFixed(2)}L`
    if (Math.abs(rupees) >= 1e3) return `₹${(rupees / 1e3).toFixed(1)}K`
  }
  return `₹${rupees.toLocaleString('en-IN', {
    minimumFractionDigits: opts?.paise ? 2 : 0,
    maximumFractionDigits: opts?.paise ? 2 : 0,
  })}`
}

/* ---------------------------------------------------------------- Overview */

export const systemStats = {
  fmr: 0.0, // False Match Rate — measured on synthetic fixture corpus
  protectedToday: 4_28_15_640,
  ordersProcessed: 18_442,
  escrowHeld: 1_92_44_180,
  taxLossPrevented: 6_18_900,
  gstr2bResolveDay: 14,
  merkleRoot: '0x8f3a…d41c',
  uptimeDays: 14,
}

export type Health = { label: string; value: string; status: 'ok' | 'warn' | 'danger' }
export const railHealth: Health[] = [
  { label: 'Gateway Escrow Rail', value: 'ACTIVE', status: 'ok' },
  { label: 'Reconciliation Engine', value: '0 False Matches (Test Corpus)', status: 'ok' },
  { label: 'GSTR-2B Sync', value: 'T-3 days', status: 'warn' },
  { label: 'Vendor GSTR-1 Feed', value: '2 defaults', status: 'danger' },
]

/* ------------------------------------------------ Screen 1: Escrow Rail */

export type EscrowSplit = {
  id: string
  order: string
  merchant: string
  gross: number     // in paise
  principal: number // in paise
  tds: number       // in paise (1%)
  gst: number       // in paise (18%)
  onHold: boolean
  resolvesOn: string
  ts: string
}

export const escrowSplits: EscrowSplit[] = [
  { id: 'e1', order: 'ORD-4471-AX', merchant: 'Meridian Retail', gross: 118000, principal: 99000, tds: 1000, gst: 18000, onHold: true, resolvesOn: 'GSTR-2B · 14th', ts: '09:41:02' },
  { id: 'e2', order: 'ORD-4472-KP', merchant: 'Nova Logistics', gross: 47200, principal: 39600, tds: 400, gst: 7200, onHold: true, resolvesOn: 'GSTR-2B · 14th', ts: '09:41:18' },
  { id: 'e3', order: 'ORD-4473-LM', merchant: 'Aster Foods', gross: 23600, principal: 19800, tds: 200, gst: 3600, onHold: true, resolvesOn: 'GSTR-2B · 14th', ts: '09:41:33' },
  { id: 'e4', order: 'ORD-4474-QR', merchant: 'Vertex Media', gross: 295000, principal: 247500, tds: 2500, gst: 45000, onHold: true, resolvesOn: 'GSTR-2B · 14th', ts: '09:41:51' },
  { id: 'e5', order: 'ORD-4475-ST', merchant: 'Meridian Retail', gross: 59000, principal: 49500, tds: 500, gst: 9000, onHold: false, resolvesOn: 'Released', ts: '09:42:07' },
  { id: 'e6', order: 'ORD-4476-UV', merchant: 'Pallas Traders', gross: 88500, principal: 74250, tds: 750, gst: 13500, onHold: true, resolvesOn: 'GSTR-2B · 14th', ts: '09:42:22' },
]

export const escrowBuckets = [
  { key: 'principal', label: 'Principal (Merchant)', color: 'var(--gain)', pct: 81.7 },
  { key: 'gst', label: 'GST Escrow (18%)', color: 'var(--gold)', pct: 15.3 },
  { key: 'tds', label: 'TDS Escrow (1%)', color: 'var(--chart-3)', pct: 3.0 },
]

/* ---------------------------------------- Screen 2: Money Lineage DAG */

export type LineageNode = {
  id: string
  label: string
  sub: string
  amount: number
  kind: 'root' | 'gmv' | 'deduction' | 'net'
  x: number
  y: number
}

export type LineageEdge = { from: string; to: string; label?: string }

export const lineage = {
  utr: 'UTR-HDFC-0093412771',
  settlement: 1462400,
  fmr: 0.0,
  invoices: 34,
  nodes: [
    { id: 'utr', label: 'Bank Lump-Sum UTR', sub: 'HDFC · 0093412771', amount: 1462400, kind: 'root', x: 40, y: 190 },
    { id: 'gmv', label: 'Gross GMV', sub: '34 invoices · subset-sum', amount: 1800000, kind: 'gmv', x: 300, y: 190 },
    { id: 'mdr', label: 'MDR 1.85%', sub: 'Gateway fee', amount: 33300, kind: 'deduction', x: 570, y: 50 },
    { id: 'gst', label: 'GST 18%', sub: 'on MDR', amount: 5994, kind: 'deduction', x: 570, y: 145 },
    { id: 'tds', label: 'TDS 1%', sub: 'Sec 194-O', amount: 18000, kind: 'deduction', x: 570, y: 240 },
    { id: 'net', label: 'Net Settlement', sub: 'reconciled', amount: 1462400, kind: 'net', x: 570, y: 335 },
  ] as LineageNode[],
  edges: [
    { from: 'utr', to: 'gmv', label: 'Horowitz–Sahni' },
    { from: 'gmv', to: 'mdr' },
    { from: 'gmv', to: 'gst' },
    { from: 'gmv', to: 'tds' },
    { from: 'gmv', to: 'net' },
  ] as LineageEdge[],
}

export const lineageInvoices = [
  { inv: 'INV-2291', amt: 96380, matched: true },
  { inv: 'INV-2292', amt: 240950, matched: true },
  { inv: 'INV-2293', amt: 19276, matched: true },
  { inv: 'INV-2294', amt: 72285, matched: true },
  { inv: 'INV-2295', amt: 38552, matched: true },
  { inv: 'INV-2296', amt: 48190, matched: true },
]

/* ------------------------------------ Screen 3: Causal Digital Twin */

export type Scenario = {
  id: string
  label: string
  desc: string
}
export const scenarios: Scenario[] = [
  { id: 'holiday', label: 'Bank Holiday Freeze', desc: '4-day settlement halt across the rail' },
  { id: 'gstr1', label: 'Vendor GSTR-1 Default', desc: 'Input-credit cascade from defaulting vendors' },
  { id: 'chargeback', label: 'Chargeback Surge', desc: 'Dispute spike against held principal' },
]

export const twinBaseline = {
  liquidity: 1_92_44_180,
  runwayDays: 62,
  exposedCredit: 6_18_900,
}

/* --------------------------------- Screen 4: Self-Healing & Ledger */

export type LedgerEntry = {
  seq: number
  action: string
  payee: string
  amount: number
  cap: number
  status: 'certified' | 'pending' | 'blocked'
  hash: string
  sig: string
  ts: string
}

export const ledgerEntries: LedgerEntry[] = [
  { seq: 10442, action: 'Adjustment Payout', payee: 'Meridian Retail', amount: 184, cap: 200, status: 'certified', hash: '0x8f3a…d41c', sig: 'ed25519:9a…f2', ts: '2026-08-27 09:12:44' },
  { seq: 10441, action: 'GST True-Up', payee: 'GSTN Treasury', amount: 5994, cap: 6000, status: 'certified', hash: '0x71bd…0aa9', sig: 'ed25519:3c…7b', ts: '2026-08-27 08:55:10' },
  { seq: 10440, action: 'Rounding Repair', payee: 'Nova Logistics', amount: 12, cap: 200, status: 'certified', hash: '0x22e1…9f4d', sig: 'ed25519:71…c0', ts: '2026-08-27 08:41:59' },
  { seq: 10439, action: 'Adjustment Payout', payee: 'Unverified KYC', amount: 240, cap: 200, status: 'blocked', hash: '—', sig: '—', ts: '2026-08-27 08:30:02' },
  { seq: 10438, action: 'TDS Remittance', payee: 'CBDT Treasury', amount: 18000, cap: 20000, status: 'pending', hash: '—', sig: 'awaiting CFO', ts: '2026-08-27 08:12:37' },
]

export const guardrails = [
  { label: 'Per-action spend cap', value: '₹200', ok: true },
  { label: 'KYC payee whitelist', value: 'Enforced', ok: true },
  { label: 'Audit hash-chain integrity', value: 'Verified', ok: true },
  { label: 'Ed25519 signatures', value: 'Required', ok: true },
]

/* ----------------------------------------------------------- Navigation */

export const navItems = [
  { href: '/', label: 'Kuber OS Overview', code: 'KBR' },
  { href: '/console', label: 'Assurance Console', code: 'CTL' },
  { href: '/capital', label: 'Kuber Capital', code: 'CAP' },
  { href: '/escrow', label: 'Gateway Escrow', code: 'ESC' },
  { href: '/lineage', label: 'Money Lineage', code: 'DAG' },
  { href: '/twin', label: 'Digital Twin', code: 'SIM' },
  { href: '/ledger', label: 'Ledger & Merkle', code: 'MRK' },
]


