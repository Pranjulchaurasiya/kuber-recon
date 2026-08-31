/**
 * API client module for KuberRecon FastAPI Backend.
 *
 * Reads NEXT_PUBLIC_API_URL environment variable with fallback to http://localhost:8000.
 */

export function getApiUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  return url.replace(/\/$/, '')
}

export interface BackendHealth {
  status: string
  service: string
  engine: string
  fmr: string
  timestamp: number
}

export async function checkBackendHealth(): Promise<{ online: boolean; data?: BackendHealth }> {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 2000)
    const res = await fetch(`${getApiUrl()}/api/health`, {
      method: 'GET',
      signal: controller.signal,
      cache: 'no-store',
    })
    clearTimeout(timeoutId)
    if (res.ok) {
      const data: BackendHealth = await res.json()
      return { online: true, data }
    }
  } catch {
    // Backend unreachable
  }
  return { online: false }
}

export interface CapitalOfferResponse {
  merchant_id: string
  reconciled_gmv_paise: number
  reconciled_gmv_inr: string
  reliability_score: number
  reliability_tier: string
  offered_principal_paise: number
  offered_principal_inr: string
  factor_fee_paise: number
  factor_fee_inr: string
  total_repayment_paise: number
  total_repayment_inr: string
  sweep_rate_pct: string
  explanation: string
}

export interface CapitalDrawdownResponse {
  status: string
  facility_id: string
  merchant_id: string
  principal_paise: number
  principal_inr: string
  total_repayment_paise: number
  remaining_balance_paise: number
  remaining_balance_inr: string
  sweep_rate_pct: string
  payout_transfer_id: string
  disbursed_at: string
}

export interface CapitalSweepResponse {
  status: string
  facility_status: string
  settlement_utr: string
  gross_settlement_inr: string
  sweep_deduction_inr: string
  net_merchant_payout_inr: string
  remaining_balance_inr: string
  is_fully_repaid: boolean
}

export async function fetchCapitalOffer(merchantId = 'merch_delhi_hyperlocal_01'): Promise<CapitalOfferResponse> {
  const res = await fetch(`${getApiUrl()}/api/capital/offer?merchant_id=${merchantId}`, {
    method: 'GET',
    cache: 'no-store',
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch capital offer: ${res.statusText}`)
  }
  return res.json()
}

export async function executeCapitalDrawdown(merchantId = 'merch_delhi_hyperlocal_01', requestedAmountPaise = 5976478): Promise<{ ok: boolean; data?: CapitalDrawdownResponse; error?: string; status?: number }> {
  try {
    const res = await fetch(`${getApiUrl()}/api/capital/drawdown`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        merchant_id: merchantId,
        requested_amount_paise: requestedAmountPaise,
      }),
    })
    const body = await res.json()
    if (!res.ok) {
      return { ok: false, error: body.detail || res.statusText, status: res.status }
    }
    return { ok: true, data: body, status: res.status }
  } catch (err: any) {
    return { ok: false, error: err.message || 'Network error connecting to APEX Kernel' }
  }
}

export async function executeCapitalSweep(facilityId: string, numRecords = 20): Promise<{ ok: boolean; data?: CapitalSweepResponse; error?: string }> {
  try {
    const res = await fetch(`${getApiUrl()}/api/capital/reconcile-and-sweep`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        facility_id: facilityId,
        num_records: numRecords,
      }),
    })
    const body = await res.json()
    if (!res.ok) {
      return { ok: false, error: body.detail || res.statusText }
    }
    return { ok: true, data: body }
  } catch (err: any) {
    return { ok: false, error: err.message || 'Network error executing sweep' }
  }
}

export async function resetCapitalFacilities(): Promise<boolean> {
  try {
    const res = await fetch(`${getApiUrl()}/api/capital/reset`, { method: 'POST' })
    return res.ok
  } catch {
    return false
  }
}
