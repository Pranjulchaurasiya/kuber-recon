"""Multi-Bank Narration Parser & Strict 5-Point Provider Join Engine.

Core Invariant:
"Narration data alone cannot trigger release. Release requires a verified provider-record join
and existing contract-state guards."

Evidence Tiers:
- TIER_A_CANDIDATE: Strong parsed evidence. Requires verified provider-record join before release.
- TIER_B_HEURISTIC: Batch/prefix match without full validated UTR. Non-authoritative; cannot auto-release funds.
- TIER_C_EXCEPTION: Malformed, truncated, or unverified memo. Emits exception and routes to manual review queue.

Paise-Exact Rule: Zero IEEE-754 floats; pure base-10 integer paise.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
import re
from typing import Dict, List, Optional, Tuple, Pattern


class NarrationEvidenceTier(str, Enum):
    TIER_A_CANDIDATE = "TIER_A_CANDIDATE"
    TIER_B_HEURISTIC = "TIER_B_HEURISTIC"
    TIER_C_EXCEPTION = "TIER_C_EXCEPTION"


@dataclass(frozen=True)
class BankProfile:
    """Bank-specific clearing memo pattern definitions."""
    bank_code: str
    bank_name: str
    utr_pattern: Pattern[str]
    aggregator_tokens: Tuple[str, ...]
    bank_identifiers: Tuple[str, ...] = ()
    min_utr_len: int = 12
    max_utr_len: int = 30


# Known bank clearing profiles with realistic synthetic patterns (no universal length constraint)
BANK_PROFILES: Dict[str, BankProfile] = {
    "SBI": BankProfile(
        bank_code="SBI",
        bank_name="State Bank of India",
        utr_pattern=re.compile(r"\b(SBIN[A-Z0-9]{12,22})\b", re.IGNORECASE),
        aggregator_tokens=("RZP", "RAZORPAY", "RZR", "SETTL"),
        bank_identifiers=("SBI", "SBIN"),
        min_utr_len=16,
        max_utr_len=26,
    ),
    "HDFC": BankProfile(
        bank_code="HDFC",
        bank_name="HDFC Bank",
        utr_pattern=re.compile(r"\b(HDFC[N0-9A-Z][A-Z0-9]{9,20})\b", re.IGNORECASE),
        aggregator_tokens=("RZR", "RAZORPAY", "SETTL", "NFX"),
        bank_identifiers=("HDFC", "HDFCN"),
        min_utr_len=14,
        max_utr_len=24,
    ),
    "ICICI": BankProfile(
        bank_code="ICICI",
        bank_name="ICICI Bank",
        utr_pattern=re.compile(r"\b(ICIC[A-Z0-9]{8,20}|[0-9]{12,18})\b", re.IGNORECASE),
        aggregator_tokens=("RZP", "RAZORPAY", "NODAL"),
        bank_identifiers=("ICICI", "ICIC", "INF/"),
        min_utr_len=12,
        max_utr_len=24,
    ),
    "AXIS": BankProfile(
        bank_code="AXIS",
        bank_name="Axis Bank",
        utr_pattern=re.compile(r"\b(AXIS[0-9A-Z]{6,18}|UTR[0-9]{10,14})\b", re.IGNORECASE),
        aggregator_tokens=("RZPAY", "RAZORPAY", "CMS"),
        bank_identifiers=("AXIS", "UTIB"),
        min_utr_len=10,
        max_utr_len=22,
    ),
    "KOTAK": BankProfile(
        bank_code="KOTAK",
        bank_name="Kotak Mahindra Bank",
        utr_pattern=re.compile(r"\b(KKBK[0-9A-Z]{6,18}|UTR[0-9]{10,14})\b", re.IGNORECASE),
        aggregator_tokens=("KOTAK", "RAZORPAY", "CMS"),
        bank_identifiers=("KOTAK", "KKBK"),
        min_utr_len=10,
        max_utr_len=22,
    ),
    "YES": BankProfile(
        bank_code="YES",
        bank_name="Yes Bank",
        utr_pattern=re.compile(r"\b(YESB[A-Z0-9]{10,18}|CMS[0-9]{5,16})\b", re.IGNORECASE),
        aggregator_tokens=("YESB", "RAZORPAY", "ESCROW"),
        bank_identifiers=("YES", "YESB"),
        min_utr_len=10,
        max_utr_len=22,
    ),
    "PNB": BankProfile(
        bank_code="PNB",
        bank_name="Punjab National Bank",
        utr_pattern=re.compile(r"\b(PUNB[A-Z0-9]{10,20}|[0-9]{12,18})\b", re.IGNORECASE),
        aggregator_tokens=("RZPAYNODAL", "RAZORPAY", "RTGS"),
        bank_identifiers=("PNB", "PUNB"),
        min_utr_len=12,
        max_utr_len=24,
    ),
    "BOB": BankProfile(
        bank_code="BOB",
        bank_name="Bank of Baroda",
        utr_pattern=re.compile(r"\b(BARB[A-Z0-9]{10,20})\b", re.IGNORECASE),
        aggregator_tokens=("BOB", "RAZORPAY", "SETTLEMENT"),
        bank_identifiers=("BOB", "BARB"),
        min_utr_len=14,
        max_utr_len=24,
    ),
}

# Generic fallback pattern for unknown-but-plausible RBI clearing identifiers
GENERIC_PLAUSIBLE_UTR_PATTERN = re.compile(r"\b([A-Z]{4}[0-9A-Z]{10,22})\b", re.IGNORECASE)
COMMON_AGGREGATOR_TOKENS = ("RZP", "RAZORPAY", "RZR", "NODAL", "SETTL")


@dataclass(frozen=True)
class ParsedNarrationCandidate:
    """Represents a parsed bank statement credit narration."""
    raw_narration: str
    detected_bank: str
    candidate_utr: Optional[str]
    has_aggregator_token: bool
    evidence_tier: NarrationEvidenceTier
    non_authoritative_reason: str
    extracted_date_token: Optional[str] = None


@dataclass(frozen=True)
class TrustedProviderRecord:
    """Authoritative provider record already linked to the contract/transfer."""
    provider_record_id: str
    expected_utr: str
    amount_paise: int
    currency: str
    merchant_account_id: str
    settlement_status: str  # Must be 'processed' or 'settled'
    settlement_date: date
    rail_type: str = "NEFT"
    source: str = "webhook"


@dataclass(frozen=True)
class RailSettlementConfig:
    """Configurable date window per payment rail."""
    rail_name: str
    allowed_date_variance_days: int = 2


RAIL_SETTLEMENT_CONFIGS: Dict[str, RailSettlementConfig] = {
    "RTGS": RailSettlementConfig(rail_name="RTGS", allowed_date_variance_days=1),
    "IMPS": RailSettlementConfig(rail_name="IMPS", allowed_date_variance_days=1),
    "UPI": RailSettlementConfig(rail_name="UPI", allowed_date_variance_days=1),
    "NEFT": RailSettlementConfig(rail_name="NEFT", allowed_date_variance_days=2),
}


def get_rail_config(rail_name: Optional[str]) -> RailSettlementConfig:
    """Derive rail configuration and allowed date variance dynamically."""
    norm = (rail_name or "NEFT").strip().upper()
    return RAIL_SETTLEMENT_CONFIGS.get(norm, RailSettlementConfig(rail_name=norm, allowed_date_variance_days=2))


class IndianBankNarrationParser:
    """Deterministic parser normalizing bank clearing narrations into auditable candidate tiers."""

    @staticmethod
    def parse_date_token(token: Optional[str]) -> Optional[date]:
        """Parse an extracted narration date token (YYYYMMDD, DDMMYYYY, YYYY-MM-DD, or DD-MM-YYYY) into a date object."""
        if not token:
            return None
        clean_nodash = token.strip().replace("-", "").replace("/", "")
        for fmt in ("%Y%m%d", "%d%m%Y"):
            try:
                return datetime.strptime(clean_nodash, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def parse_narration(raw_narration: str) -> ParsedNarrationCandidate:
        clean_text = raw_narration.strip()
        if not clean_text:
            return ParsedNarrationCandidate(
                raw_narration=raw_narration,
                detected_bank="UNKNOWN",
                candidate_utr=None,
                has_aggregator_token=False,
                evidence_tier=NarrationEvidenceTier.TIER_C_EXCEPTION,
                non_authoritative_reason="Empty or whitespace-only narration memo.",
            )

        # 1. Detect bank profile
        detected_profile: Optional[BankProfile] = None
        for code, profile in BANK_PROFILES.items():
            identifiers = profile.bank_identifiers if profile.bank_identifiers else (code,)
            if any(ident in clean_text.upper() for ident in identifiers):
                detected_profile = profile
                break

        # 2. Extract UTR and check aggregator token
        candidate_utr: Optional[str] = None
        has_aggregator = False
        tokens_to_check = detected_profile.aggregator_tokens if detected_profile else COMMON_AGGREGATOR_TOKENS
        for tok in tokens_to_check:
            if tok in clean_text.upper():
                has_aggregator = True
                break

        if detected_profile:
            match = detected_profile.utr_pattern.search(clean_text)
            if match:
                candidate_utr = match.group(1).upper()
        else:
            # Try generic plausible RBI UTR pattern
            gen_match = GENERIC_PLAUSIBLE_UTR_PATTERN.search(clean_text)
            if gen_match:
                candidate_utr = gen_match.group(1).upper()

        # 3. Extract date token if present (YYYYMMDD, DDMMYYYY, YYYY-MM-DD, DD-MM-YYYY)
        date_match = re.search(
            r"(?:^|[*\-/\s_])(202[5-7][01][0-9][0-3][0-9]|[0-3][0-9][01][0-9]202[5-7]|202[5-7]-[01][0-9]-[0-3][0-9]|[0-3][0-9]-[01][0-9]-202[5-7])(?:$|[*\-/\s_])",
            clean_text
        )
        extracted_date = date_match.group(1) if date_match else None

        # 4. Determine Evidence Tier with strict guardrails
        if candidate_utr and has_aggregator:
            # TIER_A_CANDIDATE: Strong parsed evidence, but explicitly non-authoritative without provider join
            return ParsedNarrationCandidate(
                raw_narration=raw_narration,
                detected_bank=detected_profile.bank_code if detected_profile else "GENERIC",
                candidate_utr=candidate_utr,
                has_aggregator_token=True,
                evidence_tier=NarrationEvidenceTier.TIER_A_CANDIDATE,
                non_authoritative_reason="TIER_A_CANDIDATE: Strong parsed evidence. Requires verified provider-record join before release.",
                extracted_date_token=extracted_date,
            )
        elif candidate_utr and not has_aggregator:
            # Unknown or unverified aggregator memo with valid-looking UTR -> Tier B
            return ParsedNarrationCandidate(
                raw_narration=raw_narration,
                detected_bank=detected_profile.bank_code if detected_profile else "GENERIC",
                candidate_utr=candidate_utr,
                has_aggregator_token=False,
                evidence_tier=NarrationEvidenceTier.TIER_B_HEURISTIC,
                non_authoritative_reason="TIER_B_HEURISTIC: Valid UTR candidate found but missing aggregator token. Non-authoritative; cannot auto-release funds.",
                extracted_date_token=extracted_date,
            )
        elif has_aggregator and not candidate_utr:
            # Mentions aggregator but lacks valid UTR format -> Tier B
            return ParsedNarrationCandidate(
                raw_narration=raw_narration,
                detected_bank=detected_profile.bank_code if detected_profile else "GENERIC",
                candidate_utr=None,
                has_aggregator_token=True,
                evidence_tier=NarrationEvidenceTier.TIER_B_HEURISTIC,
                non_authoritative_reason="TIER_B_HEURISTIC: Aggregator token detected but missing verifiable UTR. Non-authoritative; cannot auto-release funds.",
                extracted_date_token=extracted_date,
            )
        else:
            # Malformed, truncated, or cooperative bank memo without identifiers -> Tier C
            return ParsedNarrationCandidate(
                raw_narration=raw_narration,
                detected_bank=detected_profile.bank_code if detected_profile else "UNKNOWN",
                candidate_utr=None,
                has_aggregator_token=False,
                evidence_tier=NarrationEvidenceTier.TIER_C_EXCEPTION,
                non_authoritative_reason="TIER_C_EXCEPTION: Malformed or unverified bank narration memo. Emits exception and routes to manual review queue.",
                extracted_date_token=extracted_date,
            )

    @staticmethod
    def verify_provider_record_join(
        candidate: ParsedNarrationCandidate,
        linked_provider_record: TrustedProviderRecord,
        observed_amount_paise: int,
        observed_currency: str,
        observed_account_id: str,
        observed_date: date,
        rail_config: RailSettlementConfig,
    ) -> Tuple[bool, str]:
        """
        Strict 5-Point Provider Join:
        Validates parsed candidate narration against the trusted provider record
        already linked to the contract/transfer.
        
        Invariant:
        "Narration data alone cannot trigger release. Release requires a verified provider-record join
        and existing contract-state guards."
        """
        # Point 1: Candidate evidence must be TIER_A_CANDIDATE
        if candidate.evidence_tier != NarrationEvidenceTier.TIER_A_CANDIDATE or not candidate.candidate_utr:
            return False, f"Refused: Narration is in {candidate.evidence_tier.value}; only TIER_A_CANDIDATE can be joined for release."

        # Point 2: Provider Record Identity & UTR Match
        if candidate.candidate_utr != linked_provider_record.expected_utr:
            return False, f"Refused: Candidate UTR '{candidate.candidate_utr}' does not match provider record UTR '{linked_provider_record.expected_utr}'."

        # Point 3: Exact Integer Paise & Currency Match
        if observed_amount_paise != linked_provider_record.amount_paise or observed_currency != linked_provider_record.currency:
            return False, f"Refused: Amount/Currency mismatch: {observed_currency} {observed_amount_paise} != {linked_provider_record.currency} {linked_provider_record.amount_paise}."

        # Point 4: Linked Merchant Account Ownership
        if observed_account_id != linked_provider_record.merchant_account_id:
            return False, f"Refused: Merchant account ID mismatch: {observed_account_id} != {linked_provider_record.merchant_account_id}."

        # Point 5A: Expected Settlement Lifecycle State
        if linked_provider_record.settlement_status.lower() not in ("processed", "settled"):
            return False, f"Refused: Linked provider record in non-terminal state '{linked_provider_record.settlement_status}'. Must be 'processed' or 'settled'."

        # Point 5B: Rail-Configurable Date Window Variance
        days_diff = abs((observed_date - linked_provider_record.settlement_date).days)
        if days_diff > rail_config.allowed_date_variance_days:
            return False, f"Refused: Settlement date variance ({days_diff} days) exceeds {rail_config.rail_name} rail limit ({rail_config.allowed_date_variance_days} days)."

        return True, "Verified: 5-Point Provider Join passed. Authoritative settlement confirmation granted."
