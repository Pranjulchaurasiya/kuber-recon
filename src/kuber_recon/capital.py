"""APEX Capital: Autonomous Verified-Revenue Underwriting & Split-Settlement Recovery Engine.

Core Principles:
1. Pure Base-10 Integer (Paise) Arithmetic: No IEEE-754 floating point operations.
2. Bayesian Shrinkage SRI: Protects low-volume merchants from single-sample noise.
3. Verified-Truth Gating: Capital is underwritten exclusively against delivery-confirmed GMV.
4. Nodal Split-Sweep Amortization: Automated deduction at settlement source.
5. Explicit Failure State Handling: Stagnant recovery (>14 days) and FLDG 5% review queue.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from enum import Enum
import hashlib
from threading import RLock
from typing import Dict, List, Optional, Tuple

from kuber_recon.types import ReconciledSettlementBlock, InvoiceRecord


class ActiveFacilityExistsError(Exception):
    """Raised when attempting to disburse an advance to a merchant with an outstanding facility."""
    pass


class TerminalFacilitySweepError(Exception):
    """Raised when attempting to sweep against a repaid or written-off facility."""
    pass


class FacilityStatus(str, Enum):
    OFFERED = "OFFERED"
    ACTIVE = "ACTIVE"
    AMORTIZING = "AMORTIZING"
    REPAID = "REPAID"
    STAGNANT_RECOVERY = "STAGNANT_RECOVERY"
    FLDG_REVIEW = "FLDG_REVIEW"


@dataclass(frozen=True)
class CapitalUnderwritingConfig:
    """Configurable operational parameters for working capital advances."""
    # Operational starting heuristic cap (25% of 30-day verified delivered GMV)
    advance_rate_heuristic: Decimal = Decimal("0.25")
    
    # Bayesian shrinkage prior parameters for Settlement Reliability Index (SRI)
    prior_sample_size: int = 50
    prior_match_rate: Decimal = Decimal("0.98")
    
    # Risk-tier factor fees and sweep deductions
    tier_a_factor_fee_rate: Decimal = Decimal("0.04")  # 4% flat fixed factor fee
    tier_a_sweep_rate: Decimal = Decimal("0.12")       # 12% daily nodal settlement sweep
    tier_b_factor_fee_rate: Decimal = Decimal("0.06")  # 6% flat fixed factor fee
    tier_b_sweep_rate: Decimal = Decimal("0.15")       # 15% daily nodal settlement sweep
    
    # Minimum and maximum advance bounds in paise
    min_advance_paise: int = 1000000      # Rs 10,000 minimum
    max_advance_paise: int = 500000000    # Rs 50,00,000 maximum cap per facility
    
    # Failure threshold parameters
    stagnancy_days_threshold: int = 14     # Days without settlement before STAGNANT_RECOVERY
    fldg_invocation_days: int = 30         # Days without settlement before FLDG review


@dataclass
class CapitalOffer:
    """Underwritten credit facility offer generated from verified ledger truth."""
    merchant_id: str
    verified_delivered_gmv_paise: int
    settlement_reliability_index: Decimal
    risk_tier: str
    max_eligible_advance_paise: int
    offered_principal_paise: int
    factor_fee_paise: int
    total_repayment_paise: int
    sweep_rate: Decimal
    underwritten_at: datetime
    offer_expires_at: datetime
    explanation: str


@dataclass
class RepaymentSweepEvent:
    """Audit record of an automated split-settlement recovery sweep."""
    sweep_id: str
    settlement_utr: str
    gross_settlement_paise: int
    sweep_deduction_paise: int
    net_merchant_payout_paise: int
    remaining_balance_paise: int
    applied_at: datetime


@dataclass
class AdvanceFacility:
    """Live state machine for a merchant working capital advance."""
    facility_id: str
    merchant_id: str
    principal_paise: int
    factor_fee_paise: int
    total_repayment_paise: int
    remaining_balance_paise: int
    sweep_rate: Decimal
    status: FacilityStatus
    disbursed_at: datetime
    last_settlement_at: datetime
    payout_transfer_id: str
    repayment_events: List[RepaymentSweepEvent] = field(default_factory=list)


class CapitalUnderwriter:
    """Deterministic mathematical underwriting engine for Razorpay merchants."""

    def __init__(self, config: Optional[CapitalUnderwritingConfig] = None):
        self.config = config or CapitalUnderwritingConfig()

    def compute_sri(
        self,
        total_records: int,
        matched_records: int,
        disputed_records: int = 0,
    ) -> Decimal:
        """Compute Settlement Reliability Index (SRI) using Bayesian prior shrinkage.
        
        Formula:
            SRI = (N * (matched / N) + N_0 * p_0) / (N + N_0) - (2 * disputes / (N + N_0))
            
        Protects small merchants (N < 50) from punitive single-sample noise while
        allowing large merchants (N >= 1,000) to be judged purely on empirical truth.
        """
        n = total_records
        n0 = self.config.prior_sample_size
        p0 = self.config.prior_match_rate
        
        if n == 0:
            return p0

        empirical_matches = Decimal(str(matched_records))
        prior_matches = Decimal(str(n0)) * p0
        total_effective_weight = Decimal(str(n + n0))

        smoothed_rate = (empirical_matches + prior_matches) / total_effective_weight
        dispute_penalty = (Decimal("2.0") * Decimal(str(disputed_records))) / total_effective_weight

        sri = smoothed_rate - dispute_penalty
        if sri > Decimal("1.0"):
            sri = Decimal("1.0")
        elif sri < Decimal("0.0"):
            sri = Decimal("0.0")

        return sri.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    def generate_offer(
        self,
        merchant_id: str,
        reconciled_blocks: List[ReconciledSettlementBlock],
        invoices: List[InvoiceRecord],
        disputed_invoice_ids: Optional[List[str]] = None,
        requested_advance_paise: Optional[int] = None,
    ) -> CapitalOffer:
        """Underwrite working capital facility against verified delivered settlement blocks."""
        disputed_ids = set(disputed_invoice_ids or [])
        now = datetime.now(timezone.utc)

        # 1. Compute Verified Delivered GMV (VD-GMV)
        # Only line items matched via exact-cover in reconciled blocks count
        matched_invoice_ids = set()
        for block in reconciled_blocks:
            matched_invoice_ids.update(block.matched_invoices)

        verified_delivered_paise = sum(
            inv.amount_in_paise
            for inv in invoices
            if inv.invoice_id in matched_invoice_ids and inv.invoice_id not in disputed_ids
        )

        total_invoices = len(invoices)
        matched_count = len(matched_invoice_ids - disputed_ids)
        dispute_count = len(disputed_ids)

        # 2. Compute Bayesian SRI Score
        sri = self.compute_sri(total_invoices, matched_count, dispute_count)

        # 3. Determine Risk Tier & Smooth Continuous Pricing Terms
        # Uses continuous linear interpolation across SRI in [0.9300, 0.9700] to eliminate cliff-edge fee jumps
        band_low = Decimal("0.9300")
        band_high = Decimal("0.9700")

        if sri >= band_high:
            risk_tier = "TIER_A_PREMIER"
            fee_rate = self.config.tier_a_factor_fee_rate
            sweep_rate = self.config.tier_a_sweep_rate
        elif sri <= band_low:
            risk_tier = "TIER_B_STANDARD"
            fee_rate = self.config.tier_b_factor_fee_rate
            sweep_rate = self.config.tier_b_sweep_rate
        else:
            # Linear interpolation within transition band [0.9300, 0.9700]
            t = (sri - band_low) / (band_high - band_low)
            fee_delta = self.config.tier_b_factor_fee_rate - self.config.tier_a_factor_fee_rate
            sweep_delta = self.config.tier_b_sweep_rate - self.config.tier_a_sweep_rate
            
            fee_rate = (self.config.tier_b_factor_fee_rate - t * fee_delta).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
            sweep_rate = (self.config.tier_b_sweep_rate - t * sweep_delta).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
            risk_tier = "TIER_A_PREMIER" if sri >= Decimal("0.9500") else "TIER_B_STANDARD"

        # 4. Calculate Max Eligible Capacity in Pure Integer Paise
        # Max Advance = floor(VD_GMV * Advance_Rate_Heuristic * SRI)
        raw_capacity = Decimal(str(verified_delivered_paise)) * self.config.advance_rate_heuristic * sri
        capacity_paise = int(raw_capacity.to_integral_value(rounding=ROUND_FLOOR))
        
        # Bounded within system limits
        capacity_paise = max(0, min(capacity_paise, self.config.max_advance_paise))
        if capacity_paise < self.config.min_advance_paise:
            capacity_paise = 0

        # 5. Apply Requested Amount or Default to Max
        if requested_advance_paise is not None:
            offered_principal = min(requested_advance_paise, capacity_paise)
        else:
            offered_principal = capacity_paise

        # 6. Compute Fixed Factor Fee (Base-10 Paise)
        fee_decimal = Decimal(str(offered_principal)) * fee_rate
        factor_fee_paise = int(fee_decimal.to_integral_value(rounding=ROUND_HALF_UP))
        total_repayment_paise = offered_principal + factor_fee_paise

        explanation = (
            f"Underwritten off Rs {verified_delivered_paise/100:,.2f} Verified Delivered GMV "
            f"across {matched_count}/{total_invoices} reconciled records. "
            f"Bayesian Settlement Reliability Index (SRI): {sri:.4f} ({risk_tier}). "
            f"Daily settlement sweep: {int(sweep_rate*100)}%."
        )

        return CapitalOffer(
            merchant_id=merchant_id,
            verified_delivered_gmv_paise=verified_delivered_paise,
            settlement_reliability_index=sri,
            risk_tier=risk_tier,
            max_eligible_advance_paise=capacity_paise,
            offered_principal_paise=offered_principal,
            factor_fee_paise=factor_fee_paise,
            total_repayment_paise=total_repayment_paise,
            sweep_rate=sweep_rate,
            underwritten_at=now,
            offer_expires_at=now + timedelta(days=7),
            explanation=explanation,
        )


class CapitalFacilityManager:
    """Manages active advance disbursement, repayment split-sweeps, and failure states."""

    def __init__(self, config: Optional[CapitalUnderwritingConfig] = None):
        self.config = config or CapitalUnderwritingConfig()
        self._lock = RLock()
        self.facilities: Dict[str, AdvanceFacility] = {}

    def disburse_advance(
        self,
        offer: CapitalOffer,
        payout_transfer_id: Optional[str] = None,
    ) -> AdvanceFacility:
        """Disburse working capital advance to merchant current account with double-drawdown guard."""
        if offer.offered_principal_paise <= 0:
            raise ValueError("Cannot disburse advance with 0 eligible principal.")

        with self._lock:
            # Enforce single active facility constraint per merchant
            for existing in self.facilities.values():
                if existing.merchant_id == offer.merchant_id and existing.status in (
                    FacilityStatus.ACTIVE,
                    FacilityStatus.AMORTIZING,
                    FacilityStatus.STAGNANT_RECOVERY,
                ):
                    raise ActiveFacilityExistsError(
                        f"Merchant {offer.merchant_id} already has an active facility {existing.facility_id} "
                        f"in state {existing.status.value} with remaining balance Rs {existing.remaining_balance_paise/100:,.2f}."
                    )

            facility_id = f"CAP-FAC-{hashlib.sha256(f'{offer.merchant_id}:{datetime.now(timezone.utc).isoformat()}'.encode()).hexdigest()[:12].upper()}"
            transfer_id = payout_transfer_id or f"pout_{hashlib.sha256(facility_id.encode()).hexdigest()[:14]}"
            now = datetime.now(timezone.utc)

            facility = AdvanceFacility(
                facility_id=facility_id,
                merchant_id=offer.merchant_id,
                principal_paise=offer.offered_principal_paise,
                factor_fee_paise=offer.factor_fee_paise,
                total_repayment_paise=offer.total_repayment_paise,
                remaining_balance_paise=offer.total_repayment_paise,
                sweep_rate=offer.sweep_rate,
                status=FacilityStatus.ACTIVE,
                disbursed_at=now,
                last_settlement_at=now,
                payout_transfer_id=transfer_id,
            )
            self.facilities[facility_id] = facility
            return facility

    def process_settlement_sweep(
        self,
        facility_id: str,
        settlement_block: ReconciledSettlementBlock,
        current_time: Optional[datetime] = None,
    ) -> Tuple[AdvanceFacility, RepaymentSweepEvent]:
        """Apply automatic split-settlement deduction against an incoming nodal credit block atomically.
        
        Formula:
            Deduction = min(Remaining_Balance, floor(Net_Settlement_Paise * Sweep_Rate))
            Net_Payout = Net_Settlement_Paise - Deduction
            Remaining_Balance_New = Remaining_Balance - Deduction
        """
        with self._lock:
            facility = self.facilities.get(facility_id)
            if not facility:
                raise KeyError(f"Facility {facility_id} not found.")

            if facility.status in (FacilityStatus.REPAID, FacilityStatus.FLDG_REVIEW):
                raise TerminalFacilitySweepError(f"Facility {facility_id} is in terminal status: {facility.status.value}.")

            now = current_time or datetime.now(timezone.utc)
            gross_settlement = settlement_block.lump_sum_paise

            # Calculate exact paise deduction
            raw_sweep = Decimal(str(gross_settlement)) * facility.sweep_rate
            sweep_paise = int(raw_sweep.to_integral_value(rounding=ROUND_FLOOR))
            actual_deduction_paise = min(facility.remaining_balance_paise, sweep_paise)
            net_merchant_payout = gross_settlement - actual_deduction_paise
            new_balance = facility.remaining_balance_paise - actual_deduction_paise

            sweep_id = f"SWP-{hashlib.sha256(f'{facility_id}:{settlement_block.utr_number}:{now.isoformat()}'.encode()).hexdigest()[:10].upper()}"
            
            event = RepaymentSweepEvent(
                sweep_id=sweep_id,
                settlement_utr=settlement_block.utr_number,
                gross_settlement_paise=gross_settlement,
                sweep_deduction_paise=actual_deduction_paise,
                net_merchant_payout_paise=net_merchant_payout,
                remaining_balance_paise=new_balance,
                applied_at=now,
            )

            facility.remaining_balance_paise = new_balance
            facility.last_settlement_at = now
            facility.repayment_events.append(event)

            if new_balance == 0:
                facility.status = FacilityStatus.REPAID
            else:
                facility.status = FacilityStatus.AMORTIZING

            return facility, event

    def evaluate_stagnancy(
        self,
        facility_id: str,
        current_time: Optional[datetime] = None,
    ) -> AdvanceFacility:
        """Check for non-repayment / frozen settlement activity and trigger failure guards."""
        with self._lock:
            facility = self.facilities.get(facility_id)
            if not facility:
                raise KeyError(f"Facility {facility_id} not found.")

            if facility.status in (FacilityStatus.REPAID, FacilityStatus.FLDG_REVIEW):
                return facility

            now = current_time or datetime.now(timezone.utc)
            days_inactive = (now - facility.last_settlement_at).days

            if days_inactive >= self.config.fldg_invocation_days:
                facility.status = FacilityStatus.FLDG_REVIEW
            elif days_inactive >= self.config.stagnancy_days_threshold:
                facility.status = FacilityStatus.STAGNANT_RECOVERY

            return facility
