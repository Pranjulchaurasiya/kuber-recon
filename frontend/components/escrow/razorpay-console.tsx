'use client'

import { useEffect, useState } from 'react'
import { getApiUrl } from '@/lib/api-client'
import { paiseToInr } from '@/lib/kuber-data'

// ── Types ─────────────────────────────────────────────────────────────────────

interface IntegrationStatus {
  mode: 'test_mode' | 'sandbox_simulation'
  razorpay_api_live: boolean
  webhook_secret_configured: boolean
  idempotency_backend: string
  fmr: string
}

interface RouteResult {
  transfer_id: string
  entity: string
  account: string
  amount_paise: number
  amount_inr: string
  on_hold: boolean
  status: string
  mode: string
  proof_hash: string
}

interface WebhookResult {
  status: string
  event_id: string
  event: string
  signature_verified: boolean
  idempotency_backend: string
  processed_background: boolean
  proof_hash: string
  latency_ms: number
}

interface ApiError {
  type: 'network' | 'server'
  detail: string
}

// ── Paise-exact parser ────────────────────────────────────────────────────────
/**
 * Convert a rupee string typed by the user into an integer paise value.
 * Uses BigInt for all arithmetic — no float, no Math.round, no parseFloat
 * touches currency at any point.
 *
 * Accepts: "1180", "1180.00", "1180.5"
 * Returns: BigInt paise (e.g. 118000n, 118050n)
 * Throws:  TypeError when input is not a valid rupee string.
 */
function rupeesToPaise(rupeeStr: string): bigint {
  const trimmed = rupeeStr.trim()
  if (!/^\d+(\.\d{0,2})?$/.test(trimmed)) {
    throw new TypeError(`Invalid rupee amount: "${trimmed}"`)
  }
  const [whole, frac = ''] = trimmed.split('.')
  const paise = BigInt(whole) * 100n + BigInt(frac.padEnd(2, '0'))
  return paise
}

function formatPaise(paise: bigint): string {
  return paiseToInr(Number(paise))
}

// ── Component ─────────────────────────────────────────────────────────────────

export function RazorpayRouteConsole() {
  const [status, setStatus] = useState<IntegrationStatus | null>(null)
  const [routeAmount, setRouteAmount] = useState('1180')
  const [paisePreview, setPaisePreview] = useState<bigint | null>(118000n)
  const [paiseError, setPaiseError] = useState<string | null>(null)

  const [routeResult, setRouteResult] = useState<RouteResult | null>(null)
  const [routeError, setRouteError] = useState<ApiError | null>(null)
  const [loadingRoute, setLoadingRoute] = useState(false)

  const [webhookResult, setWebhookResult] = useState<WebhookResult | null>(null)
  const [webhookError, setWebhookError] = useState<ApiError | null>(null)
  const [loadingWebhook, setLoadingWebhook] = useState(false)

  // Fetch integration status on mount to drive mode badge
  useEffect(() => {
    fetch(`${getApiUrl()}/api/integration-status`)
      .then((r) => r.json())
      .then((d: IntegrationStatus) => setStatus(d))
      .catch(() => {/* backend offline — badge stays null */})
  }, [])

  // Update paise preview as user types
  const handleAmountChange = (val: string) => {
    setRouteAmount(val)
    try {
      const p = rupeesToPaise(val)
      setPaisePreview(p)
      setPaiseError(null)
    } catch {
      setPaisePreview(null)
      setPaiseError('Enter a valid rupee amount (e.g. 1180 or 1180.50)')
    }
  }

  // ── Route Transfer ──────────────────────────────────────────────────────────
  const handleCreateRouteTransfer = async () => {
    if (!paisePreview || paisePreview <= 0n) return
    setLoadingRoute(true)
    setRouteResult(null)
    setRouteError(null)

    try {
      const apiUrl = getApiUrl()
      const res = await fetch(`${apiUrl}/api/razorpay/route-transfer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: 'acc_merchant_demo_001',
          amount_paise: Number(paisePreview),   // integer — already BigInt-derived
          notes: { protocol: 'KUBERSOVEREIGN_GSTR2B_ESCROW' },
        }),
      })
      if (res.ok) {
        setRouteResult(await res.json() as RouteResult)
      } else {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        setRouteError({ type: 'server', detail: err.detail ?? res.statusText })
      }
    } catch (e) {
      setRouteError({
        type: 'network',
        detail: 'Cannot reach backend. Start the FastAPI server: python src/kuber_recon/server.py',
      })
    }
    setLoadingRoute(false)
  }

  // ── Webhook — fetch pre-signed fixture, then POST it ───────────────────────
  const handleTestWebhook = async () => {
    setLoadingWebhook(true)
    setWebhookResult(null)
    setWebhookError(null)

    try {
      const apiUrl = getApiUrl()

      // Step 1: fetch a correctly-signed payload from the server
      const fixtureRes = await fetch(`${apiUrl}/api/webhook/test-payload`)
      if (!fixtureRes.ok) {
        const err = await fixtureRes.json().catch(() => ({ detail: fixtureRes.statusText }))
        setWebhookError({ type: 'server', detail: err.detail ?? fixtureRes.statusText })
        setLoadingWebhook(false)
        return
      }
      const fixture = await fixtureRes.json() as {
        raw_body: string
        x_razorpay_signature: string
        x_razorpay_event_id: string
      }

      // Step 2: POST exactly that body + signature — no mutation
      const webhookRes = await fetch(`${apiUrl}/api/webhook/razorpay`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Razorpay-Signature': fixture.x_razorpay_signature,
          'X-Razorpay-Event-Id': fixture.x_razorpay_event_id,
        },
        body: fixture.raw_body,
      })
      const data = await webhookRes.json()
      setWebhookResult(data as WebhookResult)
    } catch (e) {
      setWebhookError({
        type: 'network',
        detail: 'Cannot reach backend. Start the FastAPI server: python src/kuber_recon/server.py',
      })
    }
    setLoadingWebhook(false)
  }

  // ── Mode badge ──────────────────────────────────────────────────────────────
  const isLive = status?.mode === 'test_mode'
  const modeBadge = status === null
    ? { label: 'Checking…', cls: 'border-border text-muted-foreground bg-background' }
    : isLive
      ? { label: '● LIVE TEST MODE', cls: 'border-gain/40 text-gain bg-gain/10' }
      : { label: 'SANDBOX SIMULATION', cls: 'border-gold/40 text-gold bg-gold/10' }

  return (
    <div className="rounded-lg border border-border bg-panel p-5">

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border pb-4">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground font-bold">
            Razorpay Route Transfer & Webhook Proof
          </div>
          <h3 className="mt-1 text-sm font-semibold text-foreground">
            Route Escrow (<code className="text-gold">on_hold: true</code>) · Signed Webhook · SQLite Idempotency
          </h3>
          {status && (
            <p className="mt-1 text-[11px] text-muted-foreground">
              Idempotency: <span className="text-foreground">{status.idempotency_backend}</span>
            </p>
          )}
        </div>
        <span className={`rounded border px-2.5 py-1 font-mono text-[10px] uppercase tracking-widest font-bold ${modeBadge.cls}`}>
          {modeBadge.label}
        </span>
      </div>

      {!isLive && (
        <div className="mt-3 rounded border border-gold/20 bg-gold/5 px-3 py-2 font-mono text-[11px] text-gold">
          To enable Live Test Mode: add <code>RAZORPAY_KEY_ID</code> and <code>RAZORPAY_KEY_SECRET</code> to{' '}
          <code>.env</code>, then restart the server. The /api/webhook/test-payload endpoint is only available in sandbox mode.
        </div>
      )}

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">

        {/* ── Route Transfer ── */}
        <div className="flex flex-col justify-between rounded-md border border-border bg-background p-4">
          <div>
            <div className="font-mono text-xs font-semibold text-foreground">1. Create Route Escrow Transfer</div>
            <p className="mt-1 text-xs text-muted-foreground">
              Calls <code className="text-gold">POST /v1/transfers</code> with{' '}
              <code className="text-gold">on_hold: true</code>. Amount sent as integer paise — no float arithmetic.
            </p>
            <div className="mt-3 flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs text-muted-foreground">₹</span>
              <input
                type="text"
                value={routeAmount}
                onChange={(e) => handleAmountChange(e.target.value)}
                className="w-28 rounded border border-border bg-panel px-2 py-1 font-mono text-xs text-foreground focus:border-gold focus:outline-none"
                placeholder="1180"
              />
              <span className="font-mono text-[10px] text-muted-foreground">
                {paisePreview !== null
                  ? `= ${paisePreview} paise`
                  : '—'}
              </span>
            </div>
            {paiseError && (
              <p className="mt-1 font-mono text-[10px] text-danger">{paiseError}</p>
            )}
          </div>

          <button
            onClick={handleCreateRouteTransfer}
            disabled={loadingRoute || !paisePreview || paisePreview <= 0n}
            className="mt-4 w-full rounded bg-gold py-2 font-mono text-xs font-semibold text-black transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {loadingRoute ? 'Sending to backend…' : 'POST /api/razorpay/route-transfer'}
          </button>

          {routeError && (
            <div className="mt-3 rounded border border-danger/40 bg-danger/5 px-3 py-2 font-mono text-[11px] text-danger">
              <strong>{routeError.type === 'network' ? 'Network error' : 'Server error'}:</strong>{' '}
              {routeError.detail}
            </div>
          )}
          {routeResult && (
            <div className="mt-3 rounded border border-gold/40 bg-gold/5 p-3 font-mono text-xs">
              <div className="flex justify-between text-[10px] font-bold text-gold">
                <span>ROUTE TRANSFER</span>
                <span>{routeResult.mode === 'test_mode' ? '● LIVE' : 'SANDBOX'}</span>
              </div>
              <div className="mt-2 space-y-1 text-[11px]">
                <div>ID: <strong className="text-foreground">{routeResult.transfer_id}</strong></div>
                <div>Amount: <strong className="text-gain">{routeResult.amount_inr}</strong> ({routeResult.amount_paise} paise)</div>
                <div>on_hold: <strong className="text-gold">{String(routeResult.on_hold)}</strong></div>
                <div className="truncate text-muted-foreground">Proof: {routeResult.proof_hash}</div>
              </div>
            </div>
          )}
        </div>

        {/* ── Webhook ── */}
        <div className="flex flex-col justify-between rounded-md border border-border bg-background p-4">
          <div>
            <div className="font-mono text-xs font-semibold text-foreground">2. Test Signed Webhook (HMAC + Idempotency)</div>
            <p className="mt-1 text-xs text-muted-foreground">
              Fetches a correctly-signed fixture from{' '}
              <code className="text-gold">/api/webhook/test-payload</code>, then POSTs it verbatim to{' '}
              <code className="text-gold">/api/webhook/razorpay</code>. The HMAC result is honest — no fabrication.
            </p>
            <div className="mt-3 rounded bg-panel p-2 font-mono text-[10px] text-muted-foreground space-y-0.5">
              <div>1. GET /api/webhook/test-payload → signed body + signature</div>
              <div>2. POST /api/webhook/razorpay with exact headers</div>
              <div>3. Server verifies HMAC, inserts into SQLite, responds</div>
            </div>
          </div>

          <button
            onClick={handleTestWebhook}
            disabled={loadingWebhook || isLive}
            title={isLive ? 'Disabled in Live Test Mode — use real Razorpay webhook' : undefined}
            className="mt-4 w-full rounded border border-gain/40 bg-gain/10 py-2 font-mono text-xs font-semibold text-gain transition-colors hover:bg-gain/20 disabled:opacity-50"
          >
            {loadingWebhook
              ? 'Fetching fixture → verifying HMAC…'
              : isLive
                ? 'Send Real Razorpay Webhook (Live Mode)'
                : 'Run Sandbox HMAC + Idempotency Test'}
          </button>

          {webhookError && (
            <div className="mt-3 rounded border border-danger/40 bg-danger/5 px-3 py-2 font-mono text-[11px] text-danger">
              <strong>{webhookError.type === 'network' ? 'Network error' : 'Server error'}:</strong>{' '}
              {webhookError.detail}
            </div>
          )}
          {webhookResult && (
            <div className={`mt-3 rounded border p-3 font-mono text-xs ${
              webhookResult.status === 'ignored_duplicate'
                ? 'border-gold/40 bg-gold/5'
                : webhookResult.signature_verified
                  ? 'border-gain/40 bg-gain/5'
                  : 'border-border bg-accent/20'
            }`}>
              <div className={`flex justify-between text-[10px] font-bold ${
                webhookResult.status === 'ignored_duplicate' ? 'text-gold' : 'text-gain'
              }`}>
                <span>{webhookResult.status === 'ignored_duplicate' ? 'DUPLICATE BLOCKED' : 'WEBHOOK ACKNOWLEDGED'}</span>
                <span>{webhookResult.signature_verified ? 'HMAC ✓' : 'NO SIG'}</span>
              </div>
              <div className="mt-2 space-y-1 text-[11px]">
                <div>Event ID: <strong className="text-foreground">{webhookResult.event_id}</strong></div>
                <div>Event: <strong className="text-foreground">{webhookResult.event}</strong></div>
                <div>Idempotency: <strong className="text-foreground">{webhookResult.idempotency_backend ?? 'SQLite'}</strong></div>
                <div className="truncate text-muted-foreground">Proof: {webhookResult.proof_hash}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
