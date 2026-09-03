"""Tests for IndianBankNarrationParser & Strict 5-Point Provider Join Engine.

Verifies:
1. 100% pass rate on 25 named synthetic fixtures across 8 named Indian bank profiles.
2. Handling of bank-specific UTR formats (no rigid universal length constraint).
3. Non-authoritative Tier B handling (cannot auto-release funds).
4. Malformed/truncated memos routed to Tier C exception queue.
5. Strict 5-point provider record join validation (pass vs. fail).
"""

from datetime import date
import pytest

from kuber_recon.narration_parser import (
    IndianBankNarrationParser,
    NarrationEvidenceTier,
    TrustedProviderRecord,
    RailSettlementConfig,
)


# 25 Named Synthetic Fixtures
NAMED_SYNTHETIC_FIXTURES = [
    # SBI Profile (1-4)
    ("SBI_STANDARD_NEFT", "NEFT-SBIN001234567890-RZP*SETTL*10492-CORP", "SBI", "SBIN001234567890", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("SBI_LONG_RTGS", "RTGS-SBINR52026082000192847-RAZORPAY-NODAL", "SBI", "SBINR52026082000192847", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("SBI_MISSING_RZP", "NEFT-SBIN009988776655-DIRECT*DEP-MISC", "SBI", "SBIN009988776655", NarrationEvidenceTier.TIER_B_HEURISTIC),
    ("SBI_TRUNCATED", "SBIN-RZP-PAYOUT", "SBI", None, NarrationEvidenceTier.TIER_B_HEURISTIC),

    # HDFC Profile (5-8)
    ("HDFC_STANDARD_NFX", "NFX-RZR*SETTL*20260820-HDFCN0029381029", "HDFC", "HDFCN0029381029", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("HDFC_CMS_ESCROW", "HDFC*CMS*RAZORPAY*HDFC0019283746*ESCROW", "HDFC", "HDFC0019283746", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("HDFC_NO_AGGREGATOR", "HDFCN9928172635-TRANSFER-SELF", "HDFC", "HDFCN9928172635", NarrationEvidenceTier.TIER_B_HEURISTIC),
    ("HDFC_FRAGMENT", "HDFC BANK NFX SETTL", "HDFC", None, NarrationEvidenceTier.TIER_B_HEURISTIC),

    # ICICI Profile (9-11)
    ("ICICI_STANDARD_NODAL", "INF/NEFT/049182390123/RAZORPAY NODAL SETTLEMENT", "ICICI", "049182390123", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("ICICI_CMS_ALPHANUM", "CMS/ICICN00192837465/RZP PAYOUTS", "ICICI", "ICICN00192837465", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("ICICI_NO_UTR", "ICICI NODAL TRANSFER PAYOUT", "ICICI", None, NarrationEvidenceTier.TIER_B_HEURISTIC),

    # AXIS Profile (12-14)
    ("AXIS_STANDARD_CMS", "AXIS/CMS/RZPAY/UTR9928172635/SETTLEMENT", "AXIS", "UTR9928172635", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("AXIS_PREFIX_NEFT", "NEFT-AXIS0001928374-RAZORPAY-ESCROW", "AXIS", "AXIS0001928374", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("AXIS_UNVERIFIED", "AXIS BANK CMS SETTLEMENT", "AXIS", None, NarrationEvidenceTier.TIER_B_HEURISTIC),

    # KOTAK Profile (15-17)
    ("KOTAK_CMS_RZP", "KOTAK*CMS*RAZORPAY*KKBK0019283746", "KOTAK", "KKBK0019283746", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("KOTAK_UTR_NUMERIC", "KOTAK/CMS/UTR1092837465/RAZORPAY", "KOTAK", "UTR1092837465", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("KOTAK_MISSING_TOKENS", "KKBK9988776655 INTERNAL TRANSFER", "KOTAK", "KKBK9988776655", NarrationEvidenceTier.TIER_B_HEURISTIC),

    # YES BANK Profile (18-19)
    ("YES_STANDARD_ESCROW", "YESB-CMS-RAZORPAY-ESCROW-YESB0019283746", "YES", "YESB0019283746", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("YES_NO_UTR", "YESB CMS RAZORPAY SETTL", "YES", None, NarrationEvidenceTier.TIER_B_HEURISTIC),

    # PNB Profile (20-21)
    ("PNB_STANDARD_RTGS", "PNB/RTGS/RZPAYNODAL/PUNB001928374658", "PNB", "PUNB001928374658", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("PNB_NO_UTR", "PNB RTGS RZPAYNODAL BATCH", "PNB", None, NarrationEvidenceTier.TIER_B_HEURISTIC),

    # Bank of Baroda Profile (22-23)
    ("BOB_STANDARD_SETTL", "BOB-CMS-RAZORPAY-SETTLEMENT-BARB0019283746", "BOB", "BARB0019283746", NarrationEvidenceTier.TIER_A_CANDIDATE),
    ("BOB_NO_UTR", "BOB SETTLEMENT TRANSFER", "BOB", None, NarrationEvidenceTier.TIER_B_HEURISTIC),

    # Malformed & Rural Cooperative Bank Memos (24-25)
    ("COOP_BANK_MALFORMED", "DISTRICT COOP BANK CLG REF 99", "UNKNOWN", None, NarrationEvidenceTier.TIER_C_EXCEPTION),
    ("TRUNCATED_GARBAGE", "TXN//***//???", "UNKNOWN", None, NarrationEvidenceTier.TIER_C_EXCEPTION),
]


@pytest.mark.parametrize("fixture_name,raw_memo,expected_bank,expected_utr,expected_tier", NAMED_SYNTHETIC_FIXTURES)
def test_named_synthetic_bank_narration_fixtures(fixture_name, raw_memo, expected_bank, expected_utr, expected_tier):
    """Verify 100% pass rate across all 25 named synthetic bank narration fixtures."""
    parsed = IndianBankNarrationParser.parse_narration(raw_memo)
    
    assert parsed.detected_bank == expected_bank, f"Fixture {fixture_name} bank mismatch"
    assert parsed.candidate_utr == expected_utr, f"Fixture {fixture_name} UTR mismatch"
    assert parsed.evidence_tier == expected_tier, f"Fixture {fixture_name} tier mismatch"
    assert parsed.non_authoritative_reason is not None


def test_tier_b_cannot_auto_release():
    """Verify that Tier B evidence is non-authoritative and refused by provider join."""
    candidate = IndianBankNarrationParser.parse_narration("SBI_NO_AGGREGATOR: NEFT-SBIN009988776655-DIRECT")
    assert candidate.evidence_tier == NarrationEvidenceTier.TIER_B_HEURISTIC

    linked_record = TrustedProviderRecord(
        provider_record_id="trf_mock_001",
        expected_utr="SBIN009988776655",
        amount_paise=100000,
        currency="INR",
        merchant_account_id="acc_mock_merchant",
        settlement_status="processed",
        settlement_date=date(2026, 8, 20),
    )
    rail = RailSettlementConfig(rail_name="NEFT", allowed_date_variance_days=2)

    ok, reason = IndianBankNarrationParser.verify_provider_record_join(
        candidate=candidate,
        linked_provider_record=linked_record,
        observed_amount_paise=100000,
        observed_currency="INR",
        observed_account_id="acc_mock_merchant",
        observed_date=date(2026, 8, 20),
        rail_config=rail,
    )
    assert ok is False
    assert "Refused: Narration is in TIER_B_HEURISTIC" in reason


def test_strict_5_point_provider_join_success():
    """Verify clean 5-point provider join for TIER_A_CANDIDATE."""
    memo = "NFX-RZR*SETTL*20260820-HDFCN0029381029"
    candidate = IndianBankNarrationParser.parse_narration(memo)
    assert candidate.evidence_tier == NarrationEvidenceTier.TIER_A_CANDIDATE

    linked_record = TrustedProviderRecord(
        provider_record_id="trf_mock_hdfc_01",
        expected_utr="HDFCN0029381029",
        amount_paise=2500000,
        currency="INR",
        merchant_account_id="acc_merchant_alpha",
        settlement_status="processed",
        settlement_date=date(2026, 8, 20),
    )
    rail = RailSettlementConfig(rail_name="RTGS", allowed_date_variance_days=1)

    ok, reason = IndianBankNarrationParser.verify_provider_record_join(
        candidate=candidate,
        linked_provider_record=linked_record,
        observed_amount_paise=2500000,
        observed_currency="INR",
        observed_account_id="acc_merchant_alpha",
        observed_date=date(2026, 8, 20),
        rail_config=rail,
    )
    assert ok is True
    assert "5-Point Provider Join passed" in reason


def test_strict_5_point_provider_join_amount_mismatch_fails():
    """Verify amount mismatch fails the join even if UTR matches."""
    memo = "NFX-RZR*SETTL*20260820-HDFCN0029381029"
    candidate = IndianBankNarrationParser.parse_narration(memo)

    linked_record = TrustedProviderRecord(
        provider_record_id="trf_mock_hdfc_01",
        expected_utr="HDFCN0029381029",
        amount_paise=2500000,
        currency="INR",
        merchant_account_id="acc_merchant_alpha",
        settlement_status="processed",
        settlement_date=date(2026, 8, 20),
    )
    rail = RailSettlementConfig(rail_name="RTGS", allowed_date_variance_days=1)

    # Observed amount is 2,400,000 paise (different from linked provider record 2,500,000 paise)
    ok, reason = IndianBankNarrationParser.verify_provider_record_join(
        candidate=candidate,
        linked_provider_record=linked_record,
        observed_amount_paise=2400000,
        observed_currency="INR",
        observed_account_id="acc_merchant_alpha",
        observed_date=date(2026, 8, 20),
        rail_config=rail,
    )
    assert ok is False
    assert "Amount/Currency mismatch" in reason


def test_strict_5_point_provider_join_rail_date_variance_exceeded():
    """Verify that date variance exceeding rail config is refused."""
    memo = "NFX-RZR*SETTL*20260820-HDFCN0029381029"
    candidate = IndianBankNarrationParser.parse_narration(memo)

    linked_record = TrustedProviderRecord(
        provider_record_id="trf_mock_hdfc_01",
        expected_utr="HDFCN0029381029",
        amount_paise=2500000,
        currency="INR",
        merchant_account_id="acc_merchant_alpha",
        settlement_status="processed",
        settlement_date=date(2026, 8, 20),
    )
    # UPI rail allows at most 1 day variance; observed is 4 days later
    rail = RailSettlementConfig(rail_name="UPI", allowed_date_variance_days=1)

    ok, reason = IndianBankNarrationParser.verify_provider_record_join(
        candidate=candidate,
        linked_provider_record=linked_record,
        observed_amount_paise=2500000,
        observed_currency="INR",
        observed_account_id="acc_merchant_alpha",
        observed_date=date(2026, 8, 24),
        rail_config=rail,
    )
    assert ok is False
    assert "Settlement date variance (4 days) exceeds UPI rail limit (1 days)" in reason
