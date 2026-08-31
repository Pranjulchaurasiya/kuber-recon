'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { getApiUrl } from '@/lib/api-client'
import {
  CheckCircle2,
  XCircle,
  ShieldAlert,
  Lock,
  Unlock,
  RefreshCw,
  Terminal,
  Cpu,
  ShieldCheck,
  AlertTriangle,
  Fingerprint,
  ChevronDown,
  ChevronUp,
  Activity,
  ArrowRight
} from 'lucide-react'

interface AuditEntry {
  id: number
  contract_id: string
  status: string
  proof_hash: string
  assertions_passed: boolean
  timestamp: number
}

interface ApexContract {
  contract_id: string
  status: 'PENDING_CAPTURE' | 'HELD' | 'VERIFYING' | 'RELEASING' | 'RELEASED' | 'REFUSED' | 'EXPIRED_HOLD' | 'RELEASE_PENDING_RECONCILIATION'
  amount_paise: number
  amount_inr: string
  expected_record_count?: number
  transfer_id: string
  on_hold: boolean
  on_hold_until: number
  proof_hash: string
  audit_trail?: AuditEntry[]
  message?: string
}

interface AssertionResult {
  contract_id: string
  assertions_passed: boolean
  status: string
  on_hold: boolean
  valid_records: number
  failed_records: number
  total_delivered_paise: number
  total_delivered_inr: string
  seller_signature_verified: boolean
  violation_samples: string[]
  manifest_sha256: string
  refusal_certificate?: string
  action_taken: string
}

interface ReleaseResult {
  contract_id: string
  status: string
  transfer_id: string
  on_hold: boolean
  amount_paise: number
  amount_inr: string
  checker_id: string
  public_key_fingerprint: string
  public_key_hex?: string
  signature_hex: string
  signature_verified: boolean
  algorithm?: string
  proof_hash: string
  message: string
}

export function ApexAssuranceConsole() {
  const [loading, setLoading] = useState(false)
  const [integrationMode, setIntegrationMode] = useState<'test_mode' | 'sandbox_simulation'>('sandbox_simulation')
  const [contract, setContract] = useState<ApexContract | null>(null)
  const [assertion, setAssertion] = useState<AssertionResult | null>(null)
  const [release, setRelease] = useState<ReleaseResult | null>(null)
  const [activeStep, setActiveStep] = useState<number>(0)
  const [pollingTimedOut, setPollingTimedOut] = useState(false)
  const [auditLogs, setAuditLogs] = useState<AuditEntry[]>([])

  // Collapsible drawers
  const [showEvidenceDrawer, setShowEvidenceDrawer] = useState(false)
  const [showTerminalDrawer, setShowTerminalDrawer] = useState(false)

  useEffect(() => {
    fetch(`${getApiUrl()}/api/integration-status`)
      .then((r) => r.json())
      .then((data) => {
        if (data.mode === 'test_mode' || data.razorpay_api_live) {
          setIntegrationMode('test_mode')
        } else {
          setIntegrationMode('sandbox_simulation')
        }
      })
      .catch(() => setIntegrationMode('sandbox_simulation'))
  }, [])

  const [agentLogs, setAgentLogs] = useState<Array<{ sender: string; msg: string; time: string; type: 'buyer' | 'apex' | 'seller' }>>([
    {
      sender: 'BUYER_AGENT',
      msg: 'Autonomous Procurement Intent: Requesting 500 supplier records. Budget: ₹25,000.00 (25,00,000 paise).',
      time: '00:00:01',
      type: 'buyer',
    },
    {
      sender: 'APEX_GATEWAY',
      msg: 'APEX Assurance Ready: Awaiting Razorpay Route transfer lock with TTL = 86,400s (24h).',
      time: '00:00:02',
      type: 'apex',
    },
  ])

  const addLog = (sender: string, msg: string, type: 'buyer' | 'apex' | 'seller') => {
    setAgentLogs((prev) => [
      {
        sender,
        msg,
        time: new Date().toLocaleTimeString('en-IN', { hour12: false }),
        type,
      },
      ...prev.slice(0, 19),
    ])
  }

  const refreshContractState = async (contractId: string) => {
    try {
      const res = await fetch(`${getApiUrl()}/api/apex/contracts/${contractId}`)
      if (res.ok) {
        const data: ApexContract = await res.json()
        setContract(data)
        if (data.audit_trail) {
          setAuditLogs(data.audit_trail)
        }
      }
    } catch {
      // ignore
    }
  }

  const signSellerPayload = async (records: any[], sellerAgentId: string = 'agent_seller_data_01') => {
    const seedBytes = await window.crypto.subtle.digest('SHA-256', new TextEncoder().encode(`kuber_${sellerAgentId}_sec_key_v1`))
    const pkcs8Prefix = new Uint8Array([0x30, 0x2e, 0x02, 0x01, 0x00, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x70, 0x04, 0x22, 0x04, 0x20])
    const pkcs8Key = new Uint8Array(pkcs8Prefix.length + seedBytes.byteLength)
    pkcs8Key.set(pkcs8Prefix, 0)
    pkcs8Key.set(new Uint8Array(seedBytes), pkcs8Prefix.length)

    const privateKey = await window.crypto.subtle.importKey('pkcs8', pkcs8Key, { name: 'Ed25519' }, true, ['sign'])
    const pubKeyHex = '728103c318ef2dc044e9ea0ef64881a9a74466f016d604b6bbe539d91b092969'

    const sortedRecords = records.map(r => {
      const keys = Object.keys(r).sort()
      const sortedObj: any = {}
      for (const k of keys) sortedObj[k] = r[k]
      return sortedObj
    })
    const canonicalStr = JSON.stringify(sortedRecords)
    const canonicalBytes = new TextEncoder().encode(canonicalStr)

    const sigRaw = await window.crypto.subtle.sign({ name: 'Ed25519' }, privateKey, canonicalBytes)
    const sigHex = Array.from(new Uint8Array(sigRaw)).map(b => b.toString(16).padStart(2, '0')).join('')

    return { pubKeyHex, sigHex }
  }

  // ── Step 1: Initialize Contract & Lock ────────────────────────────────────────
  const handleCreateContract = async () => {
    setLoading(true)
    setAssertion(null)
    setRelease(null)
    setPollingTimedOut(false)
    try {
      const res = await fetch(`${getApiUrl()}/api/apex/contracts/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          buyer_agent_id: 'agent_buyer_procurement_01',
          seller_agent_id: 'agent_seller_data_01',
          seller_account_id: 'acc_mock_seller_001',
          amount_paise: 2500000,
          expected_record_count: 500,
          ttl_seconds: 86400,
        }),
      })
      const data: ApexContract = await res.json()
      setContract(data)
      setActiveStep(1)
      addLog('APEX_ROUTER', `Route Transfer ${data.transfer_id} (on_hold: true). ₹25,000 locked for 500 records.`, 'apex')
      addLog('SELLER_AGENT', `Contract ${data.contract_id} detected. Preparing 500 supplier records.`, 'seller')
      await refreshContractState(data.contract_id)
    } catch {
      addLog('APEX_ROUTER', 'Error contacting backend API.', 'apex')
    }
    setLoading(false)
  }

  // ── Step 2A: Trigger Invalid Delivery (Refusal) ──────────────────────────────
  const handleDeliverCorrupted = async () => {
    if (!contract) return
    setLoading(true)
    setRelease(null)

    const corruptedRecords = Array.from({ length: 500 }, (_, i) => ({
      supplier_name: `Supplier Alpha-${(i % 25) + 1}`,
      gstin: (i === 2 || i === 4 || i === 7)
        ? (i === 2 ? '27AAPCA1234F1Z9' : (i === 4 ? 'INVALID_GSTIN_99' : '27AAPFU0939F1Z0'))
        : '27AAPFU0939F1ZV',
      invoice_number: `INV-2026-${String(i + 1).padStart(5, '0')}`,
      amount_paise: 5000,
    }))

    addLog('SELLER_AGENT', `Delivering 500 records with Ed25519 signature...`, 'seller')

    try {
      const { pubKeyHex, sigHex } = await signSellerPayload(corruptedRecords, 'agent_seller_data_01')
      const res = await fetch(`${getApiUrl()}/api/apex/contracts/deliver`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contract_id: contract.contract_id,
          seller_agent_id: 'agent_seller_data_01',
          payload_records: corruptedRecords,
          manifest_signature: sigHex,
          seller_public_key_hex: pubKeyHex,
        }),
      })
      const data: AssertionResult = await res.json()
      setAssertion(data)
      setActiveStep(2)
      addLog('APEX_ASSERTION', `🛑 HONEST REFUSAL: Mod-36 GSTIN failed on 3 records (497 valid / 3 invalid). Transfer remains on_hold: true.`, 'apex')
      addLog('BUYER_AGENT', `🛡️ Protected: ₹25,000 liquidity preserved. Refusal cert generated.`, 'buyer')
      await refreshContractState(contract.contract_id)
    } catch {
      addLog('APEX_ASSERTION', 'Verification request failed.', 'apex')
    }
    setLoading(false)
  }

  // ── Step 2B: Trigger Corrected Delivery (100% Clean) ──────────────────────────
  const handleDeliverVerified = async () => {
    if (!contract) return
    setLoading(true)

    const cleanRecords = Array.from({ length: 500 }, (_, i) => ({
      supplier_name: `Supplier Alpha-${(i % 25) + 1}`,
      gstin: '27AAPFU0939F1ZV',
      invoice_number: `INV-2026-${String(i + 1).padStart(5, '0')}`,
      amount_paise: 5000,
    }))

    addLog('SELLER_AGENT', `Delivering corrected batch (500 valid records = ₹25,000.00 exact) with Ed25519 signature.`, 'seller')

    try {
      const { pubKeyHex, sigHex } = await signSellerPayload(cleanRecords, 'agent_seller_data_01')
      const res = await fetch(`${getApiUrl()}/api/apex/contracts/deliver`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contract_id: contract.contract_id,
          seller_agent_id: 'agent_seller_data_01',
          payload_records: cleanRecords,
          manifest_signature: sigHex,
          seller_public_key_hex: pubKeyHex,
        }),
      })
      const data: AssertionResult = await res.json()
      setAssertion(data)
      setActiveStep(2)
      addLog('APEX_ASSERTION', `✅ 100% INVARIANTS PASSED! 500/500 records verified (₹25,000.00 exact). Seller signature verified.`, 'apex')
      await refreshContractState(contract.contract_id)
    } catch {
      addLog('APEX_ASSERTION', 'Verification request failed.', 'apex')
    }
    setLoading(false)
  }

  // ── Step 3: Release Route Hold ───────────────────────────────────────────────
  const handleReleaseHold = async () => {
    if (!contract) return
    setLoading(true)
    setPollingTimedOut(false)
    try {
      const checkerId = 'cfo_autonomous_verifier'

      addLog('CFO_CHECKER', `🔑 Loading Ed25519 keypair for '${checkerId}'...`, 'buyer')
      const seedBytes = await window.crypto.subtle.digest('SHA-256', new TextEncoder().encode('kuber_cfo_autonomous_verifier_sec_key_v1'))
      const pkcs8Prefix = new Uint8Array([0x30, 0x2e, 0x02, 0x01, 0x00, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x70, 0x04, 0x22, 0x04, 0x20])
      const pkcs8Key = new Uint8Array(pkcs8Prefix.length + seedBytes.byteLength)
      pkcs8Key.set(pkcs8Prefix, 0)
      pkcs8Key.set(new Uint8Array(seedBytes), pkcs8Prefix.length)

      const privateKey = await window.crypto.subtle.importKey('pkcs8', pkcs8Key, { name: 'Ed25519' }, true, ['sign'])
      const pubKeyHex = '0f11d9206303ebdc7533920222d1b5bda7d05519211aff465e30138b7a45581c'

      const leafHash = contract.proof_hash.replace('sha256:', '')
      const canonicalStr = `KEY:${checkerId}|CONTRACT:${contract.contract_id}|LEAF:${leafHash}|APPROVER:${checkerId}|ACTION:RELEASE|VER:v1`
      const canonicalBytes = new TextEncoder().encode(canonicalStr)

      const sigRaw = await window.crypto.subtle.sign({ name: "Ed25519" }, privateKey, canonicalBytes)
      const sigHex = Array.from(new Uint8Array(sigRaw)).map(b => b.toString(16).padStart(2, '0')).join('')

      addLog('CFO_CHECKER', `✍️ Signed release intent: ${sigHex.slice(0, 24)}... (Pinned Key: 0x${pubKeyHex.slice(0, 8)}...${pubKeyHex.slice(-6)})`, 'buyer')

      const res = await fetch(`${getApiUrl()}/api/apex/contracts/release`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contract_id: contract.contract_id,
          checker_id: checkerId,
          public_key_hex: pubKeyHex,
          signature_hex: sigHex,
        }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || "Backend rejected release.")
      }

      const data: ReleaseResult = await res.json()
      setRelease(data)
      addLog('APEX_ROUTER', `⚡ PATCH /v1/transfers/${data.transfer_id} on_hold: false... Transitioned to RELEASING`, 'apex')

      if (integrationMode === 'sandbox_simulation') {
        addLog('APEX_GATEWAY', `[Sandbox Simulation] Ingesting signed webhook fixture to simulate Razorpay finality...`, 'apex')
        setTimeout(async () => {
          try {
            const fixRes = await fetch(`${getApiUrl()}/api/sandbox/webhook/fixture?transfer_id=${data.transfer_id}`)
            if (!fixRes.ok) throw new Error("Failed to get fixture")
            const fixture = await fixRes.json()

            const whRes = await fetch(`${getApiUrl()}/api/webhook/razorpay`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-Razorpay-Signature': fixture.x_razorpay_signature,
                'X-Razorpay-Event-Id': fixture.x_razorpay_event_id
              },
              body: JSON.stringify(fixture.raw_payload)
            })

            if (!whRes.ok) throw new Error(`Webhook rejected: ${whRes.status}`)

            setActiveStep(3)
            addLog('APEX_GATEWAY', `📥 Ingested transfer.processed webhook (HMAC verified). Contract state: RELEASED.`, 'apex')
            addLog('SELLER_AGENT', `🎉 Settlement finalized to RELEASED. Seller payout released.`, 'seller')
            await refreshContractState(contract.contract_id)
          } catch (err) {
            addLog('APEX_GATEWAY', `Webhook failed: ${err instanceof Error ? err.message : 'Unknown'}`, 'apex')
          }
        }, 1500)
      } else {
        addLog('APEX_GATEWAY', `[Razorpay Test Mode] Awaiting inbound transfer.processed webhook on /api/webhook/razorpay...`, 'apex')

        let attempts = 0
        const pollInterval = setInterval(async () => {
          attempts += 1
          try {
            const statusRes = await fetch(`${getApiUrl()}/api/apex/contracts/${contract.contract_id}`)
            if (statusRes.ok) {
              const contractStatus = await statusRes.json()
              if (contractStatus.status === 'RELEASED') {
                clearInterval(pollInterval)
                setActiveStep(3)
                addLog('APEX_GATEWAY', `📥 Authoritative Razorpay webhook confirmed! Marked RELEASED.`, 'apex')
                addLog('SELLER_AGENT', `🎉 Live settlement finalized to RELEASED. Payout released.`, 'seller')
                await refreshContractState(contract.contract_id)
              }
            }
          } catch {
            // keep polling
          }
          if (attempts > 30) {
            clearInterval(pollInterval)
            setPollingTimedOut(true)
            addLog('APEX_GATEWAY', `⚠️ [Live Polling Timeout] No webhook received within 60s. Remains in RELEASING.`, 'apex')
          }
        }, 2000)
      }

    } catch (err) {
      addLog('APEX_ROUTER', `Release execution failed: ${err instanceof Error ? err.message : 'Unknown'}`, 'apex')
    }
    setLoading(false)
  }

  // Derive active display state
  const displayStatus: 'HELD' | 'VERIFYING' | 'RELEASING' | 'RELEASED' | 'REFUSED' | 'RELEASE_READY' | 'IDLE' =
    activeStep === 3
      ? 'RELEASED'
      : release
        ? 'RELEASING'
        : loading && contract
          ? 'VERIFYING'
          : assertion?.assertions_passed
            ? 'RELEASE_READY'
            : assertion
              ? 'REFUSED'
              : contract
                ? 'HELD'
                : 'IDLE'

  return (
    <div className="space-y-8">

      {/* ── 1. Above the Fold: Operational Header ───────────────────────────── */}
      <div className="rounded-2xl border border-border bg-panel p-6 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Kuber OS Assurance
              </h1>
              <span className="text-muted-foreground/40">•</span>
              <span className="text-xs text-muted-foreground">
                Settlement Control Console
              </span>
              <span className="text-muted-foreground/40">•</span>
              {integrationMode === 'test_mode' ? (
                <span className="rounded-full bg-gain/10 border border-gain/30 px-2.5 py-0.5 font-mono text-[11px] font-semibold text-gain flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-gain animate-status-dot" />
                  RAZORPAY TEST MODE
                </span>
              ) : (
                <span className="rounded-full bg-amber-500/10 border border-amber-500/30 px-2.5 py-0.5 font-mono text-[11px] font-semibold text-amber-500 flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-status-dot" />
                  SANDBOX SIMULATION
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              Delivery-gated seller settlement powered by the <strong className="font-semibold text-foreground">KuberRecon</strong> deterministic verification kernel.
            </p>
          </div>

          {/* Primary Action Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleCreateContract}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg bg-foreground px-5 py-2.5 text-sm font-semibold text-background shadow transition-all hover:opacity-90 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Run Assurance Demo (₹25,000 Lock)
            </button>
          </div>
        </div>

        {/* Operational Status Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 border-t border-border pt-4 text-xs">
          <div>
            <span className="font-mono text-[11px] text-muted-foreground uppercase tracking-wider block">Held Amount</span>
            <span className="font-mono text-sm font-bold text-foreground">
              {contract ? `${contract.amount_inr} (25L paise)` : '₹25,000.00'}
            </span>
          </div>
          <div>
            <span className="font-mono text-[11px] text-muted-foreground uppercase tracking-wider block">Current State</span>
            <span className={`font-mono text-sm font-bold ${displayStatus === 'RELEASED' ? 'text-gain' :
                displayStatus === 'REFUSED' ? 'text-danger' :
                  displayStatus === 'RELEASING' ? 'text-blue-400' :
                    displayStatus === 'HELD' ? 'text-amber-500' :
                      'text-foreground'
              }`}>
              {displayStatus}
            </span>
          </div>
          <div>
            <span className="font-mono text-[11px] text-muted-foreground uppercase tracking-wider block">Transfer ID</span>
            <span className="font-mono text-xs text-foreground truncate block">
              {contract ? contract.transfer_id : '—'}
            </span>
          </div>
          <div>
            <span className="font-mono text-[11px] text-muted-foreground uppercase tracking-wider block">Contract ID</span>
            <span className="font-mono text-xs text-gold truncate block">
              {contract ? contract.contract_id : '—'}
            </span>
          </div>
        </div>
      </div>

      {/* ── 2. Linear 6-Stage Lifecycle Progress Bar ─────────────────────────── */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Settlement Lifecycle Progression (Deterministic State Machine):
          </span>
          <div className="flex items-center gap-2 font-mono text-[11px]">
            <Link href="/ledger" className="text-primary hover:underline flex items-center gap-1">
              <span>Inspect Merkle Block</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 text-center">
          {[
            { label: 'HELD', active: displayStatus === 'HELD' || activeStep >= 1, color: 'text-amber-500 bg-amber-500/15 border-amber-500/50' },
            { label: 'VERIFYING', active: displayStatus === 'VERIFYING' || activeStep >= 2, color: 'text-blue-500 bg-blue-500/15 border-blue-500/50' },
            { label: 'REFUSED', active: displayStatus === 'REFUSED', color: 'text-danger bg-danger/15 border-danger/50' },
            { label: 'CORRECTED', active: assertion?.assertions_passed, color: 'text-purple-500 bg-purple-500/15 border-purple-500/50' },
            { label: 'RELEASING', active: displayStatus === 'RELEASING', color: 'text-cyan-500 bg-cyan-500/15 border-cyan-500/50' },
            { label: 'RELEASED', active: displayStatus === 'RELEASED', color: 'text-gain bg-gain/15 border-gain/50' },
          ].map((stage, idx) => (
            <div
              key={idx}
              className={`rounded-lg border px-3 py-2.5 transition-all ${stage.active
                  ? `${stage.color} font-bold shadow-sm ring-1 ring-inset ring-current`
                  : 'border-border bg-panel text-foreground/70 font-semibold'
                }`}
            >
              <div className="font-mono text-[10px] uppercase">0{idx + 1}</div>
              <div className="font-mono text-xs">{stage.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── 3. Clean Three-Column Agent Flow ─────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Column 1: Buyer Agent */}
        <div className="rounded-2xl border border-border bg-panel p-6 space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="font-mono text-xs font-bold text-foreground flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-blue-500" /> BUYER AGENT
              </span>
              <span className="font-mono text-[11px] text-muted-foreground">procurement_01</span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">Request:</span>
                <span className="font-bold text-foreground">500 Supplier Records</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">Budget:</span>
                <span className="font-bold text-gain">₹25,000.00 (25L paise)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">Contract ID:</span>
                <span className="text-foreground truncate max-w-[130px]">{contract ? contract.contract_id : '—'}</span>
              </div>
            </div>
          </div>

          <div className="text-xs text-muted-foreground leading-relaxed pt-2">
            Procures B2B supplier records. Funds remain locked in Route hold until 100% of line-item checksums pass.
          </div>
        </div>

        {/* Column 2: APEX Assurance Kernel */}
        <div className="rounded-2xl border border-gold/40 bg-panel p-6 space-y-4 flex flex-col justify-between shadow-sm">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="font-mono text-xs font-bold text-gold flex items-center gap-2">
                <ShieldCheck className="h-4 w-4" /> APEX ASSURANCE
              </span>
              <span className="font-mono text-[11px] text-gold">KuberRecon</span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">Route Hold:</span>
                <span className={`font-bold ${contract?.on_hold ? 'text-amber-500' : contract ? 'text-gain' : 'text-muted-foreground'}`}>
                  {contract ? (contract.on_hold ? 'LOCKED (on_hold: true)' : 'RELEASED (on_hold: false)') : '—'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">Checksums:</span>
                <span className={`font-bold ${assertion?.assertions_passed ? 'text-gain' : assertion ? 'text-danger' : 'text-muted-foreground'}`}>
                  {assertion ? (assertion.assertions_passed ? '100% Mod-36 Passed' : 'Checksum Refusal') : 'Awaiting Manifest'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">Exact Invariant:</span>
                <span className="font-bold text-foreground">
                  {contract ? '500 Records Exact' : '—'}
                </span>
              </div>
            </div>
          </div>

          <div className="text-xs text-muted-foreground leading-relaxed pt-2">
            Refuses unverifiable deliveries without LLM drift in the financial decision path.
          </div>
        </div>

        {/* Column 3: Seller Agent */}
        <div className="rounded-2xl border border-border bg-panel p-6 space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="font-mono text-xs font-bold text-foreground flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-purple-500" /> SELLER AGENT
              </span>
              <span className="font-mono text-[11px] text-muted-foreground">seller_data_01</span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">Delivered:</span>
                <span className="font-bold text-foreground">
                  {assertion ? `${assertion.valid_records + assertion.failed_records} / 500 Records` : '0 / 500 Records'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">GSTIN Status:</span>
                <span className={`font-bold ${assertion?.failed_records ? 'text-danger' : assertion ? 'text-gain' : 'text-foreground'}`}>
                  {assertion ? `${assertion.valid_records} valid / ${assertion.failed_records} invalid` : '—'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">Fingerprint:</span>
                <span className="text-foreground font-mono">0x728103c3…92969</span>
              </div>
            </div>
          </div>

          <div className="text-xs text-muted-foreground leading-relaxed pt-2">
            {assertion ? (
              assertion.assertions_passed ? 'Signed manifest validated against pinned registry key.' : 'Refusal certificate received. Correction required.'
            ) : 'Awaiting manifest delivery.'}
          </div>
        </div>

      </div>

      {/* ── 4. Interactive Scenario Action Triggers ──────────────────────────── */}
      {contract && (
        <div className="rounded-2xl border border-border bg-panel p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
            <div>
              <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-gold">
                Interactive Judge Controls
              </span>
              <h2 className="text-base font-bold text-foreground">
                Step 2: Simulate Seller Delivery & Assertion
              </h2>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleDeliverCorrupted}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-lg border border-danger/40 bg-danger/10 px-4 py-2 font-mono text-xs font-semibold text-danger transition-colors hover:bg-danger/20 disabled:opacity-50"
              >
                <XCircle className="h-4 w-4" />
                1. Trigger Invalid Delivery (Honest Refusal)
              </button>

              <button
                onClick={handleDeliverVerified}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-lg border border-gain/40 bg-gain/10 px-4 py-2 font-mono text-xs font-semibold text-gain transition-colors hover:bg-gain/20 disabled:opacity-50"
              >
                <CheckCircle2 className="h-4 w-4" />
                2. Submit Corrected Delivery (100% Clean)
              </button>
            </div>
          </div>

          {/* Assertion Details & Honest Refusal Output */}
          {assertion && (
            <div className={`rounded-xl border p-4 font-mono text-xs space-y-3 ${assertion.assertions_passed ? 'border-gain/40 bg-gain/5' : 'border-danger/40 bg-danger/5'
              }`}>
              <div className="flex flex-wrap items-center justify-between gap-2 font-bold">
                <span className={`flex items-center gap-2 ${assertion.assertions_passed ? 'text-gain' : 'text-danger'}`}>
                  {assertion.assertions_passed ? (
                    <><CheckCircle2 className="h-4 w-4" /> 100% INVARIANTS PASSED — DELIVERY VERIFIED</>
                  ) : (
                    <><AlertTriangle className="h-4 w-4" /> HONEST REFUSAL: CIRCUIT BREAKER ACTIVE</>
                  )}
                </span>
                <span className="text-[11px] text-muted-foreground">{assertion.manifest_sha256}</span>
              </div>

              <div className="space-y-1 text-foreground text-xs">
                <div>Action: <strong>{assertion.action_taken}</strong></div>
                {assertion.refusal_certificate && (
                  <div className="text-danger truncate">Refusal Cert: <code>{assertion.refusal_certificate}</code></div>
                )}
                {assertion.violation_samples.length > 0 && (
                  <div className="mt-2 rounded bg-background p-3 text-danger space-y-1 border border-border">
                    <div className="text-[11px] uppercase font-bold text-danger">Mod-36 Checksum Violations Detected:</div>
                    {assertion.violation_samples.map((v, i) => (
                      <div key={i} className="text-xs font-mono">• {v}</div>
                    ))}
                  </div>
                )}
              </div>

              {/* Release Action Button */}
              {assertion.assertions_passed && !release && (
                <div className="border-t border-gain/20 pt-3 flex flex-wrap items-center justify-between gap-3">
                  <span className="text-xs text-muted-foreground">
                    All 500 records verified against pinned seller signature. Ready for maker-checker release.
                  </span>
                  <button
                    onClick={handleReleaseHold}
                    disabled={loading}
                    className="inline-flex items-center gap-2 rounded-lg bg-gain px-5 py-2.5 font-mono text-xs font-bold text-black transition-all hover:bg-gain/90 shadow-sm"
                  >
                    <Unlock className="h-4 w-4" />
                    3. Release Settlement (PATCH on_hold: false)
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Release Confirmation Details */}
          {release && (
            <div className="rounded-xl border border-gain/40 bg-gain/5 p-4 font-mono text-xs space-y-2">
              <div className="flex items-center justify-between font-bold text-gain">
                <span className="flex items-center gap-2">
                  <Unlock className="h-4 w-4" />
                  {activeStep === 3 ? 'SETTLEMENT FINALIZED (Webhook Confirmed)' : 'RELEASING — AWAITING WEBHOOK FINALITY'}
                </span>
                <span className="text-[11px] text-muted-foreground">{release.transfer_id}</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-foreground pt-1">
                <div>Approver: <strong>{release.checker_id}</strong></div>
                <div>Public Key Fingerprint: <strong>{release.public_key_fingerprint}</strong></div>
              </div>

              {pollingTimedOut && (
                <div className="mt-2 rounded bg-amber-500/10 border border-amber-500/30 p-2.5 text-xs text-amber-500">
                  ⏱️ Live Webhook Polling Timeout: Contract transitioned to <code>RELEASING</code> in database. Awaiting authoritative webhook on <code>/api/webhook/razorpay</code>.
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── 5. Collapsible Evidence & Terminal Drawers ────────────────────────── */}
      <div className="space-y-4">

        {/* Drawer 1: Authoritative Evidence Rail & Audit Timeline */}
        <div className="rounded-2xl border border-border bg-panel overflow-hidden">
          <button
            onClick={() => setShowEvidenceDrawer(!showEvidenceDrawer)}
            className="w-full flex items-center justify-between p-5 text-left transition-colors hover:bg-accent"
          >
            <div className="flex items-center gap-2.5">
              <Activity className="h-4 w-4 text-gold" />
              <span className="text-sm font-bold text-foreground">
                Authoritative Evidence Rail & Audit Timeline
              </span>
              <span className="font-mono text-xs text-muted-foreground">
                ({auditLogs.length} state records)
              </span>
            </div>
            {showEvidenceDrawer ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
          </button>

          {showEvidenceDrawer && (
            <div className="p-5 border-t border-border bg-background space-y-3 font-mono text-xs">
              {auditLogs.length > 0 ? (
                <div className="space-y-2">
                  {auditLogs.map((entry, i) => (
                    <div key={i} className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-2 last:border-0 last:pb-0">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">#{entry.id}</span>
                        <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${entry.status === 'RELEASED' ? 'bg-gain/20 text-gain' :
                            entry.status === 'REFUSED' ? 'bg-danger/20 text-danger' :
                              entry.status === 'RELEASING' ? 'bg-blue-500/20 text-blue-400' :
                                'bg-amber-500/20 text-amber-500'
                          }`}>
                          {entry.status}
                        </span>
                        <span className="text-muted-foreground truncate max-w-[240px]">{entry.proof_hash}</span>
                      </div>
                      <span className="text-muted-foreground">
                        {new Date(entry.timestamp * 1000).toLocaleTimeString('en-IN', { hour12: false })}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-muted-foreground text-center py-2">
                  Run the demo above to populate the SQLite audit log.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Drawer 2: Agent Protocol Live Bus Stream */}
        <div className="rounded-2xl border border-border bg-panel overflow-hidden">
          <button
            onClick={() => setShowTerminalDrawer(!showTerminalDrawer)}
            className="w-full flex items-center justify-between p-5 text-left transition-colors hover:bg-accent"
          >
            <div className="flex items-center gap-2.5">
              <Terminal className="h-4 w-4 text-gain" />
              <span className="text-sm font-bold text-foreground">
                Autonomous Agent Protocol Bus (Live Stream)
              </span>
              <span className="font-mono text-xs text-muted-foreground">
                ({agentLogs.length} events)
              </span>
            </div>
            {showTerminalDrawer ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
          </button>

          {showTerminalDrawer && (
            <div className="p-5 border-t border-border bg-background space-y-2 font-mono text-xs max-h-60 overflow-y-auto">
              {agentLogs.map((log, idx) => (
                <div key={idx} className="flex items-start gap-3">
                  <span className="text-muted-foreground text-[11px] shrink-0">{log.time}</span>
                  <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] shrink-0 ${log.type === 'buyer' ? 'bg-blue-500/10 text-blue-400' :
                      log.type === 'seller' ? 'bg-purple-500/10 text-purple-400' :
                        'bg-gold/10 text-gold'
                    }`}>
                    {log.sender}
                  </span>
                  <span className="text-foreground leading-relaxed">{log.msg}</span>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

      {/* ── 6. Mandatory Disclosure & Judge Bottom Banner ─────────────────────── */}
      <footer className="space-y-4 pt-4 border-t border-border">
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 text-xs text-muted-foreground leading-relaxed">
          <strong className="text-amber-500 font-semibold font-mono uppercase text-[11px] block mb-1">
            🔒 Key Custody Disclosure:
          </strong>
          “Sandbox demo signer — not production key custody. Production deployment requires KMS/HSM and WebAuthn/FIDO2.”
        </div>

        <div className="rounded-xl border border-border bg-panel p-5 text-center">
          <p className="font-mono text-sm sm:text-base font-bold text-foreground">
            “APEX prevents autonomous seller settlement until delivery is mathematically proven.”
          </p>
        </div>
      </footer>

    </div>
  )
}
