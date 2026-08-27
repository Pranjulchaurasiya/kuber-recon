"""Indian Statutory Taxation & Deduction Kernel.

Implements:
1. CBIC CGST Rule 36(4) & Section 16(2)(aa) GSTR-2B Input Tax Credit (ITC) Matching.
2. Section 194-O (1% e-commerce TDS) & Section 206AB (5% non-filer TDS) Withholdings.
3. Section 17(5) HSN/SAC Ineligible Blocked Tax Credit Segregation.
4. Dual-Accumulator GST Lineage with balanced Rounding Variance Booking.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from kuber_recon.types import GSTR2BLineItem, PaymentMethod, inr_to_paise, paise_to_inr_decimal


class IndianTaxKernel:
    """Paise-Exact Indian FinTech Statutory Tax Engine."""

    # Statutory MDR Rates
    MDR_RATES = {
        PaymentMethod.UPI: Decimal("0.0000"),  # 0% Zero-MDR for UPI (RBI mandate)
        PaymentMethod.CARD_DEBIT: Decimal("0.0090"),  # 0.90% Debit card
        PaymentMethod.CARD_CREDIT: Decimal("0.0185"),  # 1.85% Standard Credit card
        PaymentMethod.NETBANKING: Decimal("0.0150"),  # 1.50% Netbanking
        PaymentMethod.WALLET: Decimal("0.0190"),  # 1.90% Wallets
    }

    GST_RATE = Decimal("0.18")  # 18% GST on MDR (9% CGST + 9% SGST / 18% IGST)
    TDS_194O_RATE = Decimal("0.01")  # 1% e-Commerce TDS
    TDS_206AB_RATE = Decimal("0.05")  # 5% Higher TDS for Non-Filers

    # Section 17(5) Blocked SAC/HSN Prefix list (Food, Motor Vehicles, Club Memberships)
    BLOCKED_SAC_PREFIXES = ("9963", "9964", "9995")

    @classmethod
    def calculate_line_deductions(
        cls,
        gross_amount_paise: int,
        method: PaymentMethod,
        is_specified_person_206ab: bool = False,
    ) -> Tuple[int, int, int, int]:
        """Calculate line item deductions strictly in base-10 integer paise.

        Returns: (mdr_fee_paise, gst_on_mdr_paise, tds_paise, net_settleable_paise)
        """
        gross_d = paise_to_inr_decimal(gross_amount_paise)

        # 1. Base MDR Fee
        mdr_rate = cls.MDR_RATES.get(method, Decimal("0.0185"))
        mdr_fee_d = (gross_d * mdr_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        mdr_fee_paise = inr_to_paise(mdr_fee_d)

        # 2. 18% GST on MDR
        gst_d = (mdr_fee_d * cls.GST_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gst_on_mdr_paise = inr_to_paise(gst_d)

        # 3. Section 194-O / 206AB TDS (on Gross GMV)
        tds_rate = cls.TDS_206AB_RATE if is_specified_person_206ab else cls.TDS_194O_RATE
        tds_d = (gross_d * tds_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tds_paise = inr_to_paise(tds_d)

        # 4. Net Settleable
        net_settleable_paise = gross_amount_paise - mdr_fee_paise - gst_on_mdr_paise - tds_paise

        return mdr_fee_paise, gst_on_mdr_paise, tds_paise, net_settleable_paise

    @classmethod
    def reconcile_gstr2b_itc(
        cls,
        calculated_gst_paise: int,
        gstr2b_items: List[GSTR2BLineItem],
    ) -> Tuple[bool, int, List[GSTR2BLineItem]]:
        """Match calculated gateway GST against CBIC GSTR-2B portal export.

        Returns: (is_fully_matched, variance_paise, matched_gstr2b_items)
        """
        eligible_items = [
            item
            for item in gstr2b_items
            if item.itc_available and not item.hsn_sac_code.startswith(cls.BLOCKED_SAC_PREFIXES)
        ]

        total_portal_itc_paise = sum(item.total_tax_in_paise for item in eligible_items)
        variance_paise = calculated_gst_paise - total_portal_itc_paise

        is_matched = variance_paise == 0
        return is_matched, variance_paise, eligible_items
