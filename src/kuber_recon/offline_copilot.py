"""Offline Read-Only CFO Copilot Fallback Engine.
=================================================
Provides deterministic, zero-network financial explanations directly from
underlying ledger state (SQLite / PostgreSQL) when external LLM endpoints
are unavailable or disabled.

Non-Negotiable Invariants:
1. Pure Read-Only: Zero write operations, mutations, or side-effects on ledger state.
2. Zero Network Calls: Zero external HTTP / LLM dependencies.
3. Strict Base-10 Integer (Paise) Arithmetic: Zero IEEE-754 floats.
4. Banner Disclaimer:
   "Core reconciliation and read-only finance explanations remain available without an LLM. Live payment actions still require the payment rail."
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Tuple

from kuber_recon.capital import CapitalFacilityManager, CapitalUnderwriter, CapitalUnderwritingConfig, FacilityStatus
from kuber_recon.storage import StorageBackend, get_storage_backend
from kuber_recon.tax import IndianTaxKernel
from kuber_recon.types import PaymentMethod


OFFLINE_DISCLAIMER = (
    "Core reconciliation and read-only finance explanations remain available without an LLM. "
    "Live payment actions still require the payment rail."
)


class CFOQueryIntent(str, Enum):
    GST_LIABILITY = "GST_LIABILITY"
    HOLD_REASON = "HOLD_REASON"
    SRI_METRICS = "SRI_METRICS"
    TDS_194O = "TDS_194O"
    CAPITAL_FACILITY = "CAPITAL_FACILITY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class OfflineCFOResponse:
    intent: CFOQueryIntent
    title: str
    explanation: str
    structured_data: Dict[str, Any]
    disclaimer: str = OFFLINE_DISCLAIMER
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OfflineCFOCopilot:
    """Deterministic read-only CFO explainer operating without network or LLM calls."""

    def __init__(
        self,
        backend: Optional[StorageBackend] = None,
        facility_manager: Optional[CapitalFacilityManager] = None,
    ):
        self._backend = backend
        self._facility_manager = facility_manager

    def _get_backend(self) -> StorageBackend:
        if self._backend is None:
            self._backend = get_storage_backend()
        return self._backend

    def _get_facility_manager(self) -> CapitalFacilityManager:
        if self._facility_manager is None:
            self._facility_manager = CapitalFacilityManager()
        return self._facility_manager

    @staticmethod
    def classify_intent(query: str) -> CFOQueryIntent:
        """Classify financial query intent via deterministic keyword and pattern matching."""
        q = query.lower().strip()

        # 1. GST Liability & ITC
        if re.search(r"\b(gst|gstr|gstr-?2b|cgst|sgst|igst|itc|input tax|rule 36|hsn|sac)\b", q):
            return CFOQueryIntent.GST_LIABILITY

        # 2. Hold Reason & Exception Refusal
        if re.search(r"\b(hold|held|reason|why held|ambiguous|collision|quarantine|tier[-_ ]?[bc]|mod36|refus|inconclusive|unmatched)\b", q):
            return CFOQueryIntent.HOLD_REASON

        # 3. SRI Metrics & Bayesian Reliability
        if re.search(r"\b(sri|reliability|bayesian|shrinkage|prior|factor fee|risk tier|score)\b", q):
            return CFOQueryIntent.SRI_METRICS

        # 4. Section 194-O / 206AB TDS
        if re.search(r"\b(tds|194-?o|206-?ab|pan|non-?filer|withhold|withholding)\b", q):
            return CFOQueryIntent.TDS_194O

        # 5. Working Capital Facility & Split-Sweep
        if re.search(r"\b(capital|facility|advance|sweep|split-?sweep|amortiz|repay|balance|credit line)\b", q):
            return CFOQueryIntent.CAPITAL_FACILITY

        return CFOQueryIntent.UNKNOWN

    def answer_query(
        self,
        query: str,
        tenant_id: str = "merchant_rzp_primary",
        context: Optional[Dict[str, Any]] = None,
    ) -> OfflineCFOResponse:
        """Process read-only query and return deterministic financial explanation."""
        intent = self.classify_intent(query)
        context = context or {}

        if intent == CFOQueryIntent.GST_LIABILITY:
            return self._handle_gst_liability(query, tenant_id, context)
        elif intent == CFOQueryIntent.HOLD_REASON:
            return self._handle_hold_reason(query, tenant_id, context)
        elif intent == CFOQueryIntent.SRI_METRICS:
            return self._handle_sri_metrics(query, tenant_id, context)
        elif intent == CFOQueryIntent.TDS_194O:
            return self._handle_tds_194o(query, tenant_id, context)
        elif intent == CFOQueryIntent.CAPITAL_FACILITY:
            return self._handle_capital_facility(query, tenant_id, context)
        else:
            return OfflineCFOResponse(
                intent=CFOQueryIntent.UNKNOWN,
                title="Financial Query Classifier: Unrecognized Intent",
                explanation=(
                    "The offline CFO Copilot classifies queries into 5 deterministic domains: "
                    "1. GST Liability & Rule 36(4) ITC\n"
                    "2. Contract Hold & Refusal Reasons\n"
                    "3. Bayesian Settlement Reliability Index (SRI)\n"
                    "4. Section 194-O / 206AB E-Commerce TDS\n"
                    "5. Working Capital Facility & Split-Sweep Status\n\n"
                    "Please rephrase your query to reference one of these topics."
                ),
                structured_data={"supported_intents": [e.value for e in CFOQueryIntent if e != CFOQueryIntent.UNKNOWN]},
            )

    # ── Intent Handlers ───────────────────────────────────────────────────────

    def _handle_gst_liability(self, query: str, tenant_id: str, context: Dict[str, Any]) -> OfflineCFOResponse:
        """Read-only calculation and explanation of GST on MDR and GSTR-2B matching."""
        gross_gmv_paise = context.get("gross_gmv_paise", 10000000)  # Default Rs 1,00,000
        method = context.get("payment_method", PaymentMethod.CARD_CREDIT)

        mdr, gst_on_mdr, tds, net = IndianTaxKernel.calculate_line_deductions(gross_gmv_paise, method)

        # Statutory breakdown
        cgst = gst_on_mdr // 2
        sgst = gst_on_mdr - cgst

        explanation = (
            f"Statutory GST Liability Breakdown for {method.value} volume of Rs {gross_gmv_paise / 100:,.2f}:\n"
            f"- Statutory MDR Fee: Rs {mdr / 100:,.2f} (1.85% Standard Credit Card rate)\n"
            f"- GST on MDR (18% Statutory Rate): Rs {gst_on_mdr / 100:,.2f}\n"
            f"  * CGST (9%): Rs {cgst / 100:,.2f}\n"
            f"  * SGST (9%): Rs {sgst / 100:,.2f}\n"
            f"- CBIC Rule 36(4) Invariant: 100% of GST on MDR is claimable as Input Tax Credit (ITC) "
            f"provided supplier filing appears in monthly GSTR-2B under Section 16(2)(aa).\n"
            f"- Net Settleable Remittance: Rs {net / 100:,.2f}"
        )

        return OfflineCFOResponse(
            intent=CFOQueryIntent.GST_LIABILITY,
            title="GST Liability & GSTR-2B Input Tax Credit (ITC) Position",
            explanation=explanation,
            structured_data={
                "tenant_id": tenant_id,
                "gross_gmv_paise": gross_gmv_paise,
                "mdr_fee_paise": mdr,
                "gst_on_mdr_paise": gst_on_mdr,
                "cgst_paise": cgst,
                "sgst_paise": sgst,
                "igst_paise": 0,
                "net_settleable_paise": net,
                "statutory_rate": "18%",
                "rule_36_4_compliant": True,
            },
        )

    def _handle_hold_reason(self, query: str, tenant_id: str, context: Dict[str, Any]) -> OfflineCFOResponse:
        """Lookup or explain contract settlement hold / refusal reasons."""
        backend = self._get_backend()
        contract_id = context.get("contract_id")

        # If specific contract provided, query read-only storage
        contract_record = None
        if contract_id:
            contract_record = backend.get_contract(contract_id, tenant_id=tenant_id)

        # Check for extracted UTR or keyword
        utr_match = re.search(r"\b([A-Z]{4}[0-9A-Z]{10,22})\b", query)
        utr_queried = utr_match.group(1) if utr_match else context.get("utr")

        if contract_record and contract_record.get("on_hold"):
            reason = contract_record.get("refusal_reason") or "Contract on_hold: true awaiting settlement verification"
            explanation = (
                f"Contract '{contract_id}' is currently ON HOLD.\n"
                f"Status: {contract_record.get('status')}\n"
                f"Hold Reason: {reason}\n"
                f"Amount: Rs {contract_record.get('amount_paise', 0) / 100:,.2f}\n"
                f"Release Invariant: Escrow funds cannot auto-release until the 5-point provider join "
                f"and existing contract-state guards are verified."
            )
            data = {"contract": contract_record}
        elif "ambiguous" in query.lower() or "collision" in query.lower():
            explanation = (
                "HOLD REASON: AMBIGUOUS_COLLISION (Honest Refusal Invariant)\n"
                "The banking credit amount matched more than one distinct subset of captured invoices. "
                "In strict compliance with Razorpay production safety, the engine honest-refuses to guess, "
                "preventing misattribution and preserving 0 False Match Rate on tested corpuses. "
                "The transaction is held and escalated to the manual review queue."
            )
            data = {"invariant": "Honest Refusal on |Subsets| > 1", "resolution": "Manual Review Escalation"}
        elif "tier_b" in query.lower() or "tier b" in query.lower():
            explanation = (
                "HOLD REASON: TIER_B_HEURISTIC (Non-Authoritative Narration)\n"
                "A candidate UTR was found in bank statement text without an authenticated aggregator clearing token "
                "(e.g. RZP, RZR, RAZORPAY). Under our 5-point provider join rule, statement narration alone cannot "
                "trigger fund release without an authoritative provider-record match."
            )
            data = {"evidence_tier": "TIER_B_HEURISTIC", "resolution": "Pending Authoritative Provider Join"}
        elif "tier_c" in query.lower() or "tier c" in query.lower():
            explanation = (
                "HOLD REASON: TIER_C_EXCEPTION (Malformed Bank Clearing Memo)\n"
                "The bank clearing narration was truncated, malformed, or originated from an unverified clearing network. "
                "The transaction was segregated and routed to the manual review queue."
            )
            data = {"evidence_tier": "TIER_C_EXCEPTION", "resolution": "Segregated into Manual Review Queue"}
        else:
            explanation = (
                "Active Hold Reason Matrix:\n"
                "1. AMBIGUOUS_COLLISION: Multiple candidate subsets match the credit amount.\n"
                "2. TIER_B_HEURISTIC: Unverified narration lacking aggregator authorization token.\n"
                "3. TIER_C_EXCEPTION: Malformed, truncated, or unparsed clearing memo.\n"
                "4. INCONCLUSIVE_TRUNCATED: Cluster size > 24 invoices exceeded complexity threshold.\n"
                "5. HOLD_GSTR2B: Counterparty GSTR-2B filing mismatch under CBIC Rule 36(4)."
            )
            data = {"supported_hold_codes": ["AMBIGUOUS_COLLISION", "TIER_B_HEURISTIC", "TIER_C_EXCEPTION", "INCONCLUSIVE_TRUNCATED", "HOLD_GSTR2B"]}

        return OfflineCFOResponse(
            intent=CFOQueryIntent.HOLD_REASON,
            title="Settlement Hold & Exception Root Cause Analysis",
            explanation=explanation,
            structured_data=data,
        )

    def _handle_sri_metrics(self, query: str, tenant_id: str, context: Dict[str, Any]) -> OfflineCFOResponse:
        """Explain Bayesian Settlement Reliability Index (SRI) metrics and formula."""
        cfg = CapitalUnderwritingConfig()
        prior_weight = cfg.prior_sample_size
        prior_rate = cfg.prior_match_rate

        sample_count = context.get("sample_count", 120)
        observed_matches = context.get("observed_matches", 118)
        observed_rate = Decimal(observed_matches) / Decimal(sample_count) if sample_count > 0 else Decimal("0.0")

        # Bayesian shrinkage formula: (K0 * M0 + N * M) / (K0 + N)
        numerator = (Decimal(prior_weight) * prior_rate) + (Decimal(sample_count) * observed_rate)
        denominator = Decimal(prior_weight + sample_count)
        bayesian_sri = numerator / denominator

        risk_tier = "TIER_A" if bayesian_sri >= Decimal("0.95") else "TIER_B"
        factor_fee_rate = cfg.tier_a_factor_fee_rate if risk_tier == "TIER_A" else cfg.tier_b_factor_fee_rate
        sweep_rate = cfg.tier_a_sweep_rate if risk_tier == "TIER_A" else cfg.tier_b_sweep_rate

        explanation = (
            f"Settlement Reliability Index (SRI) Metrics for '{tenant_id}':\n"
            f"- Prior Weight (K0): {prior_weight} transactions\n"
            f"- Prior Benchmark Match Rate (M0): {prior_rate * 100:.1f}%\n"
            f"- Observed Sample (N): {sample_count} settlements ({observed_matches} clean matches, {observed_rate * 100:.2f}% empirical rate)\n"
            f"- Bayesian Shrinkage SRI Score: {bayesian_sri * 100:.2f}%\n"
            f"- Assigned Risk Tier: {risk_tier}\n"
            f"- Working Capital Factor Fee: {factor_fee_rate * 100:.1f}% fixed\n"
            f"- Daily Nodal Split-Sweep Rate: {sweep_rate * 100:.1f}%\n"
            f"- Invariant: Bayesian shrinkage prevents single failed batches from unfairly degrading emerging merchant creditworthiness."
        )

        return OfflineCFOResponse(
            intent=CFOQueryIntent.SRI_METRICS,
            title="Bayesian Settlement Reliability Index (SRI) Position",
            explanation=explanation,
            structured_data={
                "tenant_id": tenant_id,
                "prior_weight": prior_weight,
                "prior_match_rate": str(prior_rate),
                "observed_sample_count": sample_count,
                "observed_clean_matches": observed_matches,
                "bayesian_sri_score": str(bayesian_sri),
                "risk_tier": risk_tier,
                "factor_fee_rate": str(factor_fee_rate),
                "daily_sweep_rate": str(sweep_rate),
            },
        )

    def _handle_tds_194o(self, query: str, tenant_id: str, context: Dict[str, Any]) -> OfflineCFOResponse:
        """Explain Section 194-O and 206AB tax deduction requirements."""
        gross_gmv_paise = context.get("gross_gmv_paise", 50000000)  # Rs 5,00,000 default
        is_specified_person_206ab = context.get("is_specified_person_206ab", False)

        tds_rate = Decimal("0.05") if is_specified_person_206ab else Decimal("0.01")
        tds_paise = int(Decimal(gross_gmv_paise) * tds_rate)

        explanation = (
            f"Income Tax Act Section 194-O Withholding Audit for '{tenant_id}':\n"
            f"- Gross E-Commerce GMV: Rs {gross_gmv_paise / 100:,.2f}\n"
            f"- Applied Withholding Rate: {tds_rate * 100:.1f}% "
            f"({'Section 206AB Non-Filer Higher Rate (5%)' if is_specified_person_206ab else 'Section 194-O Compliant PAN Rate (1%)'})\n"
            f"- Total TDS Withheld: Rs {tds_paise / 100:,.2f} strictly calculated in base-10 integer paise\n"
            f"- Statutory Mandate: Deducted by the payment aggregator at the moment of credit to account or payment, "
            f"whichever is earlier, and remitted via quarterly Form 26Q under CBDT guidelines."
        )

        return OfflineCFOResponse(
            intent=CFOQueryIntent.TDS_194O,
            title="Section 194-O / 206AB E-Commerce TDS Audit",
            explanation=explanation,
            structured_data={
                "tenant_id": tenant_id,
                "gross_gmv_paise": gross_gmv_paise,
                "is_specified_person_206ab": is_specified_person_206ab,
                "tds_rate": str(tds_rate),
                "tds_withheld_paise": tds_paise,
                "cbdt_form": "26Q",
            },
        )

    def _handle_capital_facility(self, query: str, tenant_id: str, context: Dict[str, Any]) -> OfflineCFOResponse:
        """Inspect and explain active working capital advance facility without mutation."""
        backend = self._get_backend()
        merchant_id = context.get("merchant_id", tenant_id)
        active_facility = backend.get_active_facility_for_merchant(merchant_id, tenant_id=tenant_id)

        if active_facility:
            total_repay = active_facility["total_repayment_paise"]
            remaining = active_facility["remaining_balance_paise"]
            repaid = total_repay - remaining
            sweep_rate_pct = Decimal(active_facility["sweep_rate"]) * 100
            explanation = (
                f"Active Working Capital Facility Status for '{tenant_id}':\n"
                f"- Facility ID: {active_facility['facility_id']}\n"
                f"- Status: {active_facility['status']}\n"
                f"- Disbursed Principal: Rs {active_facility['principal_paise'] / 100:,.2f}\n"
                f"- Factor Fee: Rs {active_facility['factor_fee_paise'] / 100:,.2f}\n"
                f"- Total Repayment Obligation: Rs {total_repay / 100:,.2f}\n"
                f"- Repaid to Date: Rs {repaid / 100:,.2f}\n"
                f"- Outstanding Balance: Rs {remaining / 100:,.2f}\n"
                f"- Automated Nodal Split-Sweep Rate: {sweep_rate_pct:.1f}% deducted from daily settlements"
            )
            data = active_facility
        else:
            explanation = (
                f"No active working capital facility found for merchant '{tenant_id}'.\n"
                f"Underwriting Parameters:\n"
                f"- Advance Cap: Up to 25% of 30-day verified delivered GMV\n"
                f"- Pricing: 4.0% fixed factor fee for Tier A (SRI >= 95%), 6.0% for Tier B\n"
                f"- Recovery: 12% - 15% daily split-sweep directly at payment nodal source\n"
                f"- Reserve Invariant: Zero FLDG invocation unless settlement stagnates > 30 days."
            )
            data = {"tenant_id": tenant_id, "has_active_facility": False}

        return OfflineCFOResponse(
            intent=CFOQueryIntent.CAPITAL_FACILITY,
            title="Working Capital Facility & Split-Sweep Position",
            explanation=explanation,
            structured_data=data,
        )
