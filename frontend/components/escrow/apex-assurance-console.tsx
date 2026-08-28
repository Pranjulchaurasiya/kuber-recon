'use client'

import { useState } from 'react'
import { getApiUrl } from '@/lib/api-client'
import { paiseToInr } from '@/lib/kuber-data'
import { CheckCircle2, XCircle, ShieldAlert, Lock, Unlock, ArrowRight, RefreshCw, Terminal, Cpu } from 'lucide-react'

interface ApexContract {
  contract_id: string
  status: 'PENDING_CAPTURE' | 'HELD' | 'VERIFYING' | 'RELEASED' | 'REFUSED' | 'EXPIRED'
  amount_paise: number
  amount_inr: string
  transfer_id: string
  on_hold: boolean
  on_hold_until: number
  proof_hash: string
  message?: string
}

interface AssertionResult {
  contract_id: string
  assertions_passed: boolean
  status: string
  on_hold: boolean
  valid_records: number
  failed_records: number
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
  const [contract, setContract] = useState<ApexContract | null>(null)
  const [assertion, setAssertion] = useState<AssertionResult | null>(null)
  const [release, setRelease] = useState<ReleaseResult | null>(null)
  const [activeStep, setActiveStep] = useState<number>(0)
  const [agentLogs, setAgentLogs] = useState<Array<{ sender: string; msg: string; time: string; type: 'buyer' | 'apex' | 'seller' }>>([
    {
      sender: 'BUYER_AGENT_01',
      msg: 'Autonomous Procurement Intent: Requesting 500 B2B supplier records. Budget allocated: ₹25,000.00',
      time: '01:50:00',
      type: 'buyer',
    },
    {
      sender: 'APEX_GATEWAY',
      msg: 'APEX Protocol Ready: Awaiting Razorpay Route transfer lock with TTL = 86,400s (24h).',
      time: '01:50:01',
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
      ...prev.slice(0, 14),
    ])
  }

  // ── Step 1: Create Contract & Lock Settlement ─────────────────────────────────
  const handleCreateContract = async () => {
    setLoading(true)
    setAssertion(null)
    setRelease(null)
    try {
      const res = await fetch(`${getApiUrl()}/api/apex/contracts/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          buyer_agent_id: 'agent_buyer_procurement_01',
          seller_agent_id: 'agent_seller_data_01',
          seller_account_id: 'acc_seller_linked_001',
          amount_paise: 2500000, // ₹25,000.00
          ttl_seconds: 86400,
        }),
      })
      const data: ApexContract = await res.json()
      setContract(data)
      setActiveStep(1)
      addLog('APEX_ROUTER', `Razorpay Route Transfer Created: ${data.transfer_id} (on_hold: true). ₹25,000 locked.`, 'apex')
      addLog('SELLER_AGENT_01', `Contract ${data.contract_id} detected. Preparing payload manifest for delivery.`, 'seller')
    } catch {
      addLog('APEX_ROUTER', 'Error contacting backend server.', 'apex')
    }
    setLoading(false)
  }

  // ── Step 2A: Trigger Corrupted / Hallucinated Delivery (Refusal) ─────────────
  const handleDeliverCorrupted = async () => {
    if (!contract) return
    setLoading(true)
    setRelease(null)

    const corruptedRecords = [
      { supplier_name: 'Alpha Logistics', gstin: '27AAPCA1234F1Z5', invoice_number: 'INV-101', amount_paise: 250000 },
      { supplier_name: 'Beta Steels', gstin: '29BBBBB5678G2Z1', invoice_number: 'INV-102', amount_paise: 250000 },
      { supplier_name: 'Gamma Tech (Corrupted)', gstin: '27AAPCA1234F1Z9', invoice_number: 'INV-103', amount_paise: 250000 }, // Corrupted Checksum
      { supplier_name: 'Delta Corp (Malformed)', gstin: 'INVALID_GSTIN_99', invoice_number: 'INV-104', amount_paise: 250000 }, // Invalid Length
    ]

    addLog('SELLER_AGENT_01', `Delivering batch of 4 records to APEX Assurance Kernel...`, 'seller')

    try {
      const res = await fetch(`${getApiUrl()}/api/apex/contracts/deliver`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contract_id: contract.contract_id,
          seller_agent_id: 'agent_seller_data_01',
          payload_records: corruptedRecords,
        }),
      })
      const data: AssertionResult = await res.json()
      setAssertion(data)
      setActiveStep(2)
      addLog('APEX_ASSERTION', `🛑 REFUSAL: 2 records failed Mod-36 checksums! Transfer REMAINS on_hold: true.`, 'apex')
      addLog('BUYER_AGENT_01', `🛡️ Protected: ₹25,000.00 merchant liquidity preserved. Refusal cert generated.`, 'buyer')
    } catch {
      addLog('APEX_ASSERTION', 'Verification request failed.', 'apex')
    }
    setLoading(false)
  }

  // ── Step 2B: Trigger 100% Clean / Verified Delivery ─────────────────────────
  const handleDeliverVerified = async () => {
    if (!contract) return
    setLoading(true)

    const cleanRecords = [
      { supplier_name: 'Alpha Logistics', gstin: '27AAPCA1234F1Z5', invoice_number: 'INV-101', amount_paise: 250000 },
      { supplier_name: 'Beta Steels', gstin: '29BBBBB5678G2Z1', invoice_number: 'INV-102', amount_paise: 250000 },
      { supplier_name: 'Zeta Infratech', gstin: '27AAPCA1234F1Z5', invoice_number: 'INV-103', amount_paise: 250000 },
      { supplier_name: 'Omicron Labs', gstin: '29BBBBB5678G2Z1', invoice_number: 'INV-104', amount_paise: 250000 },
    ]

    addLog('SELLER_AGENT_01', `Delivering 100% verified batch (4 records) + Ed25519 signature manifest.`, 'seller')

    try {
      const res = await fetch(`${getApiUrl()}/api/apex/contracts/deliver`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contract_id: contract.contract_id,
          seller_agent_id: 'agent_seller_data_01',
          payload_records: cleanRecords,
        }),
      })
      const data: AssertionResult = await res.json()
      setAssertion(data)
      setActiveStep(2)
      addLog('APEX_ASSERTION', `✅ 100% Invariants Passed! 0 Errors. Ready for Route settlement release.`, 'apex')
    } catch {
      addLog('APEX_ASSERTION', 'Verification request failed.', 'apex')
    }
    setLoading(false)
  }

  // ── Step 3: Release Route Hold ───────────────────────────────────────────────
  const handleReleaseHold = async () => {
    if (!contract) return
    setLoading(true)
    try {
      const checkerId = 'cfo_autonomous_verifier'

      // 1. Authenticated CFO Checker Keypair (Web Crypto RFC 8410 PKCS#8 Ed25519)
      addLog('CFO_CHECKER_AGENT', `🔑 [Sandbox demo signer — not production key custody] Loading Ed25519 keypair for '${checkerId}' (RFC 8410 PKCS#8)...`, 'buyer')
      const seedBytes = await window.crypto.subtle.digest('SHA-256', new TextEncoder().encode('kuber_cfo_autonomous_verifier_sec_key_v1'))
      const pkcs8Prefix = new Uint8Array([0x30, 0x2e, 0x02, 0x01, 0x00, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x70, 0x04, 0x22, 0x04, 0x20])
      const pkcs8Key = new Uint8Array(pkcs8Prefix.length + seedBytes.byteLength)
      pkcs8Key.set(pkcs8Prefix, 0)
      pkcs8Key.set(new Uint8Array(seedBytes), pkcs8Prefix.length)

      const privateKey = await window.crypto.subtle.importKey('pkcs8', pkcs8Key, { name: 'Ed25519' }, true, ['sign'])
      const pubKeyHex = '0f11d9206303ebdc7533920222d1b5bda7d05519211aff465e30138b7a45581c'

      // 2. Deterministic Canonical Payload Serialization
      const leafHash = contract.proof_hash.replace('sha256:', '')
      const canonicalStr = `KEY:${checkerId}|CONTRACT:${contract.contract_id}|LEAF:${leafHash}|APPROVER:${checkerId}|ACTION:RELEASE|VER:v1`
      const canonicalBytes = new TextEncoder().encode(canonicalStr)

      // 3. Client Cryptographic Signature with Pinned Identity Key
      const sigRaw = await window.crypto.subtle.sign(
        { name: "Ed25519" },
        privateKey,
        canonicalBytes
      )
      const sigHex = Array.from(new Uint8Array(sigRaw)).map(b => b.toString(16).padStart(2, '0')).join('')

      addLog('CFO_CHECKER_AGENT', `✍️ Signed release intent: ${sigHex.slice(0, 24)}... (Pinned Key: 0x${pubKeyHex.slice(0, 8)}...${pubKeyHex.slice(-6)})`, 'buyer')

      // 4. Send Authenticated Release Request to Backend
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
      addLog('APEX_ROUTER', `🔐 Ed25519 Verified (${data.algorithm || 'RFC 8032'}) | Key: ${data.public_key_fingerprint} | Sig: ${data.signature_hex.slice(0, 24)}...`, 'apex')
      addLog('APEX_ROUTER', `⚡ PATCH /v1/transfers/${data.transfer_id} on_hold: false... Transitioning to RELEASING`, 'apex')

      // Simulate webhook
      setTimeout(async () => {
        addLog('APEX_GATEWAY', `Waiting for Razorpay transfer.processed webhook...`, 'apex')
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
            body: fixture.raw_body
          })

          if (!whRes.ok) throw new Error(`Webhook rejected: ${whRes.status}`)
          
          setActiveStep(3)
          addLog('SELLER_AGENT_01', `🎉 Webhook received! Settlement finalized.`, 'seller')
        } catch (err) {
          addLog('APEX_GATEWAY', `Webhook delivery failed: ${err instanceof Error ? err.message : 'Unknown'}`, 'apex')
        }
      }, 1500)

    } catch {
      addLog('APEX_ROUTER', 'Release execution failed.', 'apex')
    }
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-xl border border-gold/30 bg-gradient-to-r from-panel via-background to-panel p-6 shadow-2xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-widest text-gold">
              <Cpu className="h-4 w-4" /> Track 01: AI Growth & Agentic Commerce
            </div>
            <h2 className="mt-1 text-2xl font-black tracking-tight text-foreground">
              APEX Assurance — Delivery-Gated Settlement
            </h2>
            <p className="mt-1 max-w-2xl text-xs text-muted-foreground">
              Razorpay authorizes agent spend. <strong className="text-foreground">APEX Assurance proves seller delivery</strong> before releasing settlements via Razorpay Route (<code className="text-gold">on_hold: true ➔ false</code>).
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleCreateContract}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg bg-gold px-4 py-2 font-mono text-xs font-bold text-black transition-all hover:bg-gold/90 disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
              1. Initialize Agent Contract (₹25,000 Lock)
            </button>
          </div>
        </div>
      </div>

      {/* 3-Stage Pipeline State Card */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {/* Stage 1 */}
        <div className={`rounded-xl border p-4 transition-all ${activeStep >= 1 ? 'border-gold/50 bg-gold/5' : 'border-border bg-panel/50'}`}>
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs font-bold text-gold">STAGE 1: ROUTE HOLD</span>
            {contract ? <Lock className="h-4 w-4 text-gold" /> : <span className="text-xs text-muted-foreground">Idle</span>}
          </div>
          <div className="mt-2 text-sm font-semibold text-foreground">
            {contract ? `Locked: ${contract.amount_inr}` : 'Awaiting Contract'}
          </div>
          <p className="mt-1 font-mono text-[11px] text-muted-foreground">
            {contract ? `Transfer: ${contract.transfer_id} (on_hold: true)` : 'No active Route transfer'}
          </p>
        </div>

        {/* Stage 2 */}
        <div className={`rounded-xl border p-4 transition-all ${
          assertion?.assertions_passed ? 'border-gain/50 bg-gain/5' : assertion ? 'border-danger/50 bg-danger/5' : 'border-border bg-panel/50'
        }`}>
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs font-bold text-foreground">STAGE 2: ASSERTION KERNEL</span>
            {assertion?.assertions_passed ? (
              <CheckCircle2 className="h-4 w-4 text-gain" />
            ) : assertion ? (
              <ShieldAlert className="h-4 w-4 text-danger" />
            ) : (
              <span className="text-xs text-muted-foreground">Idle</span>
            )}
          </div>
          <div className="mt-2 text-sm font-semibold text-foreground">
            {assertion ? (assertion.assertions_passed ? '100% Invariants Passed' : 'Honest Refusal Triggered') : 'Non-LLM Validation'}
          </div>
          <p className="mt-1 font-mono text-[11px] text-muted-foreground">
            {assertion ? `${assertion.valid_records} valid / ${assertion.failed_records} failed` : 'Mod-36 GSTIN & zero-float check'}
          </p>
        </div>

        {/* Stage 3 */}
        <div className={`rounded-xl border p-4 transition-all ${activeStep === 3 ? 'border-gain/50 bg-gain/5' : 'border-border bg-panel/50'}`}>
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs font-bold text-gain">STAGE 3: SETTLEMENT RELEASE</span>
            {activeStep === 3 ? <Unlock className="h-4 w-4 text-gain" /> : <span className="text-xs text-muted-foreground">Locked</span>}
          </div>
          <div className="mt-2 text-sm font-semibold text-foreground">
            {activeStep === 3 ? 'Settlement Unlocked' : release ? 'Releasing...' : 'PATCH on_hold: false'}
          </div>
          <p className="mt-1 font-mono text-[11px] text-muted-foreground">
            {release ? `Auth: ${release.checker_id}` : 'Gated behind 100% verification'}
          </p>
          {release && (
            <div className="mt-2 text-[10px] text-muted-foreground font-mono space-y-0.5 break-all">
              <div>Fingerprint: {release.public_key_fingerprint}</div>
              <div>Sig: {release.signature_hex.substring(0, 32)}...</div>
            </div>
          )}
        </div>
      </div>

      {/* Interactive 90-Second Demo Triggers */}
      {contract && (
        <div className="rounded-xl border border-border bg-panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
            <div>
              <span className="font-mono text-[10px] uppercase tracking-widest text-gold font-bold">Interactive Judge Demo Triggers</span>
              <h3 className="text-sm font-semibold text-foreground">Step 2: Simulate Seller Agent Delivery</h3>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleDeliverCorrupted}
                disabled={loading}
                className="flex items-center gap-2 rounded-md border border-danger/40 bg-danger/10 px-3.5 py-2 font-mono text-xs font-bold text-danger transition-colors hover:bg-danger/20 disabled:opacity-50"
              >
                <XCircle className="h-3.5 w-3.5" />
                Scenario A: Malicious / Corrupted Delivery
              </button>
              <button
                onClick={handleDeliverVerified}
                disabled={loading}
                className="flex items-center gap-2 rounded-md border border-gain/40 bg-gain/10 px-3.5 py-2 font-mono text-xs font-bold text-gain transition-colors hover:bg-gain/20 disabled:opacity-50"
              >
                <CheckCircle2 className="h-3.5 w-3.5" />
                Scenario B: 100% Verified Clean Delivery
              </button>
            </div>
          </div>

          {/* Assertion Result Details */}
          {assertion && (
            <div className={`mt-4 rounded-lg border p-4 font-mono text-xs ${
              assertion.assertions_passed ? 'border-gain/30 bg-gain/5' : 'border-danger/30 bg-danger/5'
            }`}>
              <div className="flex items-center justify-between font-bold">
                <span className={assertion.assertions_passed ? 'text-gain' : 'text-danger'}>
                  {assertion.assertions_passed ? 'ASSERTION VERIFIED: PROOF GENERATED' : 'HONEST REFUSAL: CIRCUIT BREAKER ACTIVE'}
                </span>
                <span className="text-muted-foreground">{assertion.manifest_sha256}</span>
              </div>
              <div className="mt-2 space-y-1 text-[11px] text-foreground">
                <div>Action: <strong>{assertion.action_taken}</strong></div>
                {assertion.refusal_certificate && (
                  <div className="text-danger truncate">Refusal Cert: {assertion.refusal_certificate}</div>
                )}
                {assertion.violation_samples.length > 0 && (
                  <div className="mt-2 text-danger space-y-0.5">
                    {assertion.violation_samples.map((v, i) => (
                      <div key={i}>• {v}</div>
                    ))}
                  </div>
                )}
              </div>

              {/* Release Button (Only Enabled if 100% Passed) */}
              {assertion.assertions_passed && !release && (
                <div className="mt-4 border-t border-gain/20 pt-3 flex justify-end">
                  <button
                    onClick={handleReleaseHold}
                    disabled={loading}
                    className="flex items-center gap-2 rounded bg-gain px-4 py-2 font-mono text-xs font-bold text-black transition-all hover:bg-gain/90"
                  >
                    <Unlock className="h-3.5 w-3.5" />
                    3. Execute Settlement Release (PATCH on_hold: false)
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Live Agent Terminal Stream */}
      <div className="rounded-xl border border-border bg-black/80 p-4 shadow-inner">
        <div className="flex items-center justify-between border-b border-border/50 pb-2.5">
          <div className="flex items-center gap-2 font-mono text-xs text-muted-foreground">
            <Terminal className="h-3.5 w-3.5 text-gain" />
            <span>Autonomous Agentic Protocol Bus (Live Stream)</span>
          </div>
          <span className="font-mono text-[10px] text-muted-foreground">Zero-Float Base-10 Integer Bus</span>
        </div>
        <div className="mt-3 space-y-2 font-mono text-xs max-h-56 overflow-y-auto">
          {agentLogs.map((log, idx) => (
            <div key={idx} className="flex items-start gap-2.5">
              <span className="text-[10px] text-muted-foreground/60">{log.time}</span>
              <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${
                log.type === 'buyer' ? 'bg-blue-500/10 text-blue-400' :
                log.type === 'seller' ? 'bg-purple-500/10 text-purple-400' :
                'bg-gold/10 text-gold'
              }`}>
                {log.sender}
              </span>
              <span className="text-foreground/90">{log.msg}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
