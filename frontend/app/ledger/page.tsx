import { LedgerConsole } from '@/components/ledger/console'
import { Pill } from '@/components/kuber/primitives'

export default function LedgerPage() {
  return (
    <div className="mx-auto max-w-[1400px] px-5 py-8">
      <header className="mb-6">
        <Pill tone="gold">RFC 6962 Audit Ledger · Ed25519 Signed</Pill>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">Self-Healing &amp; Merkle Ledger</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          The system repairs discrepancies within hard bounds — never autonomously beyond them. Every
          adjustment passes a ₹200 spend cap and KYC whitelist, then requires a human CFO signature
          that seals an Ed25519 certificate into an RFC 6962 Merkle chain.
        </p>
      </header>

      <LedgerConsole />
    </div>
  )
}
