"""
Adversarial Stress-Test Diagnostic for APEX Capital Underwriting Pipeline.
========================================================================
Runs 4 targeted adversarial merchant scenarios through capital.py:
1. 'Unlucky month' merchant: clean 90-day history with 1-month isolated dispute spike.
2. 'Slow decline' merchant: 4-6 consecutive degrading 30-day windows.
3. 'Front-load then default' merchant: high-SRI qualification -> draws max -> volume drops to 0.
4. 'Just above threshold' merchant: SRI hovering across Tier A / Tier B boundary (0.9501 vs 0.9499).
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json

from kuber_recon.capital import (
    CapitalFacilityManager,
    CapitalOffer,
    CapitalUnderwriter,
    CapitalUnderwritingConfig,
    FacilityStatus,
)
from kuber_recon.engine import ReconciliationEngine
from kuber_recon.generator import ChaosDataGenerator
from kuber_recon.types import EvidenceTier, InvoiceRecord, ReconciledSettlementBlock, SettlementStatus


def run_scenario_1_unlucky_month():
    """Scenario 1: Unlucky month merchant with an isolated dispute spike."""
    underwriter = CapitalUnderwriter()
    config = underwriter.config

    # Case A: Mature merchant (N=500 records/month)
    # Month 1 & 2: 500 records, 495 matched, 0 disputes (baseline 99%)
    # Month 3 (Unlucky): 500 records, 420 matched, 30 disputes (bad supplier batch)
    
    # 90-day aggregate vs isolated 30-day window
    # Let's compare naive SRI vs Bayesian smoothed SRI on Month 3:
    n_month3 = 500
    matched_month3 = 420
    disputed_month3 = 30
    
    # Naive formula: 1 - (unmatched + 2*disputes)/N
    unmatched_month3 = n_month3 - matched_month3
    naive_sri_month3 = Decimal("1.0") - (Decimal(str(unmatched_month3)) + Decimal("2.0") * Decimal(str(disputed_month3))) / Decimal(str(n_month3))
    
    bayesian_sri_month3 = underwriter.compute_sri(
        total_records=n_month3,
        matched_records=matched_month3,
        disputed_records=disputed_month3,
    )
    
    # Case B: Small merchant (N=20 records/month) with 1 bad batch (3 disputes)
    n_small = 20
    matched_small = 16
    disputed_small = 3
    unmatched_small = n_small - matched_small
    naive_sri_small = Decimal("1.0") - (Decimal(str(unmatched_small)) + Decimal("2.0") * Decimal(str(disputed_small))) / Decimal(str(n_small))
    bayesian_sri_small = underwriter.compute_sri(
        total_records=n_small,
        matched_records=matched_small,
        disputed_records=disputed_small,
    )

    # 90-day pooled (N=60, 56 matched, 3 disputes)
    bayesian_sri_90d_pooled = underwriter.compute_sri(
        total_records=60,
        matched_records=56,
        disputed_records=3,
    )

    return {
        "large_merchant": {
            "n": n_month3,
            "matched": matched_month3,
            "disputed": disputed_month3,
            "naive_sri": float(naive_sri_month3),
            "bayesian_sri": float(bayesian_sri_month3),
            "swing_dampened_by": float(bayesian_sri_month3 - naive_sri_month3),
        },
        "small_merchant": {
            "n": n_small,
            "matched": matched_small,
            "disputed": disputed_small,
            "naive_sri": float(naive_sri_small),
            "bayesian_sri": float(bayesian_sri_small),
            "bayesian_sri_90d_pooled": float(bayesian_sri_90d_pooled),
            "swing_dampened_by": float(bayesian_sri_small - naive_sri_small),
        }
    }


def run_scenario_2_slow_decline():
    """Scenario 2: Slow decline merchant across 5 consecutive 30-day windows."""
    underwriter = CapitalUnderwriter()
    
    # Simulate 5 consecutive 30-day monthly windows (N=100 per window, VD-GMV = Rs 10,00,000 baseline)
    windows = [
        {"window": "Month 1", "n": 100, "matched": 98, "disputes": 0, "gmv_paise": 100000000},  # Clean
        {"window": "Month 2", "n": 100, "matched": 95, "disputes": 1, "gmv_paise": 95000000},   # Slight slip
        {"window": "Month 3", "n": 100, "matched": 92, "disputes": 2, "gmv_paise": 90000000},   # Degrading
        {"window": "Month 4", "n": 100, "matched": 88, "disputes": 3, "gmv_paise": 82000000},   # Warning
        {"window": "Month 5", "n": 100, "matched": 80, "disputes": 6, "gmv_paise": 70000000},   # Distress
    ]

    results = []
    for w in windows:
        # Build dummy invoices and blocks
        invs = [
            InvoiceRecord(
                invoice_id=f"INV-{w['window']}-{i}",
                order_id=f"order_{w['window']}_{i}",
                payment_id=f"pay_{w['window']}_{i}",
                supplier_gstin="29ABCDE1234F1Z5",
                amount_in_paise=w["gmv_paise"] // w["n"],
                captured_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
            )
            for i in range(w["n"])
        ]
        matched_ids = [invs[i].invoice_id for i in range(w["matched"])]
        disputed_ids = [invs[i].invoice_id for i in range(w["disputes"])]
        
        block = ReconciledSettlementBlock(
            settlement_id=f"setl_{w['window']}",
            utr_number=f"HDFC_{w['window']}",
            lump_sum_paise=sum(inv.amount_in_paise for inv in invs[:w["matched"]]),
            gross_gmv_paise=sum(inv.amount_in_paise for inv in invs[:w["matched"]]),
            total_mdr_fee_paise=0,
            total_gst_on_mdr_paise=0,
            total_tds_withheld_paise=0,
            rounding_variance_paise=0,
            status=SettlementStatus.SETTLED,
            matched_invoices=matched_ids,
            matched_refunds=[],
            evidence_tier=EvidenceTier.TIER_A,
            proof_hash="hash",
        )

        offer = underwriter.generate_offer(
            merchant_id="merch_slow_decline",
            reconciled_blocks=[block],
            invoices=invs,
            disputed_invoice_ids=disputed_ids,
        )

        results.append({
            "window": w["window"],
            "sri": float(offer.settlement_reliability_index),
            "tier": offer.risk_tier,
            "vd_gmv_inr": offer.verified_delivered_gmv_paise / 100,
            "max_advance_inr": offer.max_eligible_advance_paise / 100,
            "factor_fee_pct": f"{float(offer.factor_fee_paise / offer.offered_principal_paise * 100):.1f}%" if offer.offered_principal_paise else "N/A",
            "sweep_rate_pct": f"{int(offer.sweep_rate * 100)}%",
        })

    return results


def run_scenario_3_front_load_default():
    """Scenario 3: Front-load then default merchant."""
    underwriter = CapitalUnderwriter()
    manager = CapitalFacilityManager()
    
    # Month 1 Qualifying Window: 100 records, 99 matched, 0 disputes (Rs 20,00,000 GMV)
    n = 100
    invs = [
        InvoiceRecord(
            invoice_id=f"INV-QUAL-{i}",
            order_id=f"order_qual_{i}",
            payment_id=f"pay_qual_{i}",
            supplier_gstin="29ABCDE1234F1Z5",
            amount_in_paise=2000000,  # Rs 20,000 each = Rs 20,00,000 total
            captured_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
        for i in range(n)
    ]
    matched_ids = [invs[i].invoice_id for i in range(99)]
    block = ReconciledSettlementBlock(
        settlement_id="setl_qual",
        utr_number="HDFCQUAL",
        lump_sum_paise=198000000,  # Rs 19,80,000
        gross_gmv_paise=198000000,
        total_mdr_fee_paise=0,
        total_gst_on_mdr_paise=0,
        total_tds_withheld_paise=0,
        rounding_variance_paise=0,
        status=SettlementStatus.SETTLED,
        matched_invoices=matched_ids,
        matched_refunds=[],
        evidence_tier=EvidenceTier.TIER_A,
        proof_hash="hash",
    )
    
    offer = underwriter.generate_offer(
        merchant_id="merch_rogue_01",
        reconciled_blocks=[block],
        invoices=invs,
    )
    
    # Merchant draws maximum offered advance
    facility = manager.disburse_advance(offer)
    disbursed_principal_paise = facility.principal_paise
    total_repayment_obligation_paise = facility.total_repayment_paise
    
    # Trace timeline with zero settlement activity
    start_time = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    facility.disbursed_at = start_time
    facility.last_settlement_at = start_time
    
    timeline = []
    for day in range(1, 36):
        current_time = start_time + timedelta(days=day)
        fac = manager.evaluate_stagnancy(facility.facility_id, current_time=current_time)
        if day in (1, 7, 13, 14, 15, 29, 30, 31, 35):
            timeline.append({
                "day": day,
                "date": current_time.strftime("%Y-%m-%d"),
                "status": fac.status.value,
                "unrecovered_principal_inr": disbursed_principal_paise / 100,
                "unrecovered_total_inr": fac.remaining_balance_paise / 100,
            })
            
    return {
        "offer_summary": {
            "sri": float(offer.settlement_reliability_index),
            "tier": offer.risk_tier,
            "disbursed_principal_inr": disbursed_principal_paise / 100,
            "total_obligation_inr": total_repayment_obligation_paise / 100,
        },
        "timeline": timeline,
    }


def run_scenario_4_cliff_edge_boundary():
    """Scenario 4: Just above vs just below Tier A/B threshold (Before vs After Fix)."""
    underwriter = CapitalUnderwriter()
    
    # Fix VD-GMV at Rs 10,00,000 (100,000,000 paise)
    vd_gmv_paise = 100000000
    
    # Boundary 1: SRI = 0.9501
    # Boundary 2: SRI = 0.9499
    # Delta = 0.0002 (0.02% difference in reliability)
    
    from decimal import ROUND_FLOOR, ROUND_HALF_UP

    sri_a = Decimal("0.9501")
    sri_b = Decimal("0.9499")

    # 1. OLD STEP FUNCTION CALCULATION
    cap_a_old = int((Decimal(str(vd_gmv_paise)) * underwriter.config.advance_rate_heuristic * sri_a).to_integral_value(rounding=ROUND_FLOOR))
    fee_a_old = int((Decimal(str(cap_a_old)) * underwriter.config.tier_a_factor_fee_rate).to_integral_value(rounding=ROUND_HALF_UP))
    
    cap_b_old = int((Decimal(str(vd_gmv_paise)) * underwriter.config.advance_rate_heuristic * sri_b).to_integral_value(rounding=ROUND_FLOOR))
    fee_b_old = int((Decimal(str(cap_b_old)) * underwriter.config.tier_b_factor_fee_rate).to_integral_value(rounding=ROUND_HALF_UP))
    
    # 2. NEW SMOOTH INTERPOLATION (via capital.py implementation)
    band_low = Decimal("0.9300")
    band_high = Decimal("0.9700")
    fee_delta = underwriter.config.tier_b_factor_fee_rate - underwriter.config.tier_a_factor_fee_rate
    sweep_delta = underwriter.config.tier_b_sweep_rate - underwriter.config.tier_a_sweep_rate

    # SRI = 0.9501
    t_a = (sri_a - band_low) / (band_high - band_low)
    fee_rate_a_new = (underwriter.config.tier_b_factor_fee_rate - t_a * fee_delta).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    sweep_rate_a_new = (underwriter.config.tier_b_sweep_rate - t_a * sweep_delta).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    fee_a_new = int((Decimal(str(cap_a_old)) * fee_rate_a_new).to_integral_value(rounding=ROUND_HALF_UP))

    # SRI = 0.9499
    t_b = (sri_b - band_low) / (band_high - band_low)
    fee_rate_b_new = (underwriter.config.tier_b_factor_fee_rate - t_b * fee_delta).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    sweep_rate_b_new = (underwriter.config.tier_b_sweep_rate - t_b * sweep_delta).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    fee_b_new = int((Decimal(str(cap_b_old)) * fee_rate_b_new).to_integral_value(rounding=ROUND_HALF_UP))

    return {
        "before_fix_step_function": {
            "sri_0_9501_fee_inr": fee_a_old / 100,
            "sri_0_9499_fee_inr": fee_b_old / 100,
            "fee_increase_inr": (fee_b_old - fee_a_old) / 100,
            "fee_increase_pct": f"{float((Decimal(str(fee_b_old)) - Decimal(str(fee_a_old))) / Decimal(str(fee_a_old)) * 100):.2f}%",
            "sweep_rate_jump": "12.0% -> 15.0% (+300 bps)",
        },
        "after_fix_smooth_interpolation": {
            "sri_0_9501_fee_rate": f"{float(fee_rate_a_new * 100):.3f}%",
            "sri_0_9501_fee_inr": fee_a_new / 100,
            "sri_0_9501_sweep_rate": f"{float(sweep_rate_a_new * 100):.3f}%",
            "sri_0_9499_fee_rate": f"{float(fee_rate_b_new * 100):.3f}%",
            "sri_0_9499_fee_inr": fee_b_new / 100,
            "sri_0_9499_sweep_rate": f"{float(sweep_rate_b_new * 100):.3f}%",
            "fee_difference_inr": (fee_b_new - fee_a_new) / 100,
            "fee_difference_pct": f"{float((Decimal(str(fee_b_new)) - Decimal(str(fee_a_new))) / Decimal(str(fee_a_new)) * 100):.3f}%",
            "sweep_rate_difference": f"{float((sweep_rate_b_new - sweep_rate_a_new) * 10000):.1f} bps",
        }
    }


if __name__ == "__main__":
    report = {
        "scenario_1_unlucky_month": run_scenario_1_unlucky_month(),
        "scenario_2_slow_decline": run_scenario_2_slow_decline(),
        "scenario_3_front_load_default": run_scenario_3_front_load_default(),
        "scenario_4_cliff_edge_boundary": run_scenario_4_cliff_edge_boundary(),
    }
    print(json.dumps(report, indent=2))
