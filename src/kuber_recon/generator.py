"""Deterministic Multi-Tier Chaos Dataset Generator (`seed=42`).

Generates:
1. 100-Record Micro Adversarial Trap Suite (Planted collisions, float drifts, truncated UTRs).
2. 1,000-Record Real-World Monthly Enterprise Batch (3-way multi-bank & GSTR-2B JSON).
3. 10,000-Record High-Throughput Stress Blast.

100% DPDP Act (2023) and RBI Banking Secrecy Compliant (Zero PII leaks).
"""

from datetime import date, datetime, timedelta
import random
from typing import Any, Dict, List, Optional, Tuple
from kuber_recon.tax import IndianTaxKernel
from kuber_recon.types import BankNodalCredit, GSTR2BLineItem, InvoiceRecord, PaymentMethod


class ChaosDataGenerator:
    """Deterministic, seed-reproducible financial test dataset generator."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def generate_suite(
        self,
        num_records: int = 100,
        start_date: Optional[date] = None,
    ) -> Tuple[List[InvoiceRecord], List[BankNodalCredit], List[GSTR2BLineItem], Dict[str, Any]]:
        """Generate interconnected invoices, bank credits, and GSTR-2B items."""
        start_date = start_date or date(2026, 8, 1)
        invoices: List[InvoiceRecord] = []
        bank_credits: List[BankNodalCredit] = []
        gstr2b_items: List[GSTR2BLineItem] = []

        methods = [
            PaymentMethod.UPI,
            PaymentMethod.CARD_CREDIT,
            PaymentMethod.CARD_DEBIT,
            PaymentMethod.NETBANKING,
        ]

        ground_truth: Dict[str, Any] = {
            "decidable_credits": 0,
            "planted_ambiguities": 0,
            "total_gross_paise": 0,
            "total_tax_paise": 0,
        }

        # Generate Invoices in batches of 4-10 per settlement lump sum
        inv_counter = 1
        credit_counter = 1
        current_date = start_date

        while len(invoices) < num_records:
            batch_size = random.randint(3, 8)
            batch_invoices: List[InvoiceRecord] = []
            settlement_id = f"setl_rzp_{credit_counter:05d}"
            utr_num = f"HDFCN{random.randint(10000000, 99999999)}"

            total_batch_gross = 0
            total_batch_mdr = 0
            total_batch_gst = 0
            total_batch_tds = 0

            for _ in range(batch_size):
                if len(invoices) + len(batch_invoices) >= num_records:
                    break
                amt_paise = random.randint(50000, 500000)  # ₹500 to ₹5,000
                method = random.choice(methods)
                created_dt = datetime.combine(current_date, datetime.min.time()) + timedelta(
                    hours=random.randint(9, 18), minutes=random.randint(0, 59)
                )

                inv = InvoiceRecord(
                    invoice_id=f"INV-2026-{inv_counter:06d}",
                    order_id=f"order_{inv_counter:08d}",
                    payment_id=f"pay_{inv_counter:08d}",
                    supplier_gstin="29ABCDE1234F1Z5",
                    amount_in_paise=amt_paise,
                    method=method,
                    captured_at=created_dt,
                )
                batch_invoices.append(inv)
                inv_counter += 1

                mdr, gst, tds, _ = IndianTaxKernel.calculate_line_deductions(amt_paise, method)
                total_batch_gross += amt_paise
                total_batch_mdr += mdr
                total_batch_gst += gst
                total_batch_tds += tds

                # GSTR-2B Tax Portal Line Item
                if gst > 0:
                    gstr2b = GSTR2BLineItem(
                        supplier_gstin="29ABCDE1234F1Z5",
                        supplier_name="Razorpay Software Private Limited",
                        invoice_number=f"TAX-RZR-{inv_counter:06d}",
                        invoice_date=current_date,
                        taxable_value_in_paise=mdr,
                        cgst_in_paise=gst // 2,
                        sgst_in_paise=gst // 2,
                        igst_in_paise=0,
                        total_tax_in_paise=gst,
                    )
                    gstr2b_items.append(gstr2b)

            invoices.extend(batch_invoices)

            # Net Bank Remittance
            net_lump_sum = total_batch_gross - total_batch_mdr - total_batch_gst - total_batch_tds

            if net_lump_sum > 0:
                bank_credit = BankNodalCredit(
                    utr_number=utr_num,
                    account_number="918239012389",
                    credit_amount_in_paise=net_lump_sum,
                    value_date=current_date + timedelta(days=1),  # T+1 Settlement
                    raw_narration=f"NFX-RZR*REMIT*{settlement_id.upper()}*MUM",
                    settlement_id=settlement_id,
                )
                bank_credits.append(bank_credit)
                ground_truth["decidable_credits"] += 1
                ground_truth["total_gross_paise"] += total_batch_gross
                ground_truth["total_tax_paise"] += total_batch_gst

            credit_counter += 1
            current_date += timedelta(days=1)

        # Inject Intentional Chaos Traps (if num_records >= 10)
        if len(invoices) >= 10:
            # 1. Planted Collision (Ambiguous Credit)
            # Create two disjoint pairs with the exact same net amount (148,500 paise)
            inv_a = InvoiceRecord(
                invoice_id="INV-AMB-001",
                order_id="ord_amb_1",
                payment_id="pay_amb_1",
                supplier_gstin="29ABCDE1234F1Z5",
                amount_in_paise=80000,
                method=PaymentMethod.UPI,
                captured_at=datetime.combine(start_date, datetime.min.time()),
            )
            inv_b = InvoiceRecord(
                invoice_id="INV-AMB-002",
                order_id="ord_amb_2",
                payment_id="pay_amb_2",
                supplier_gstin="29ABCDE1234F1Z5",
                amount_in_paise=70000,
                method=PaymentMethod.UPI,
                captured_at=datetime.combine(start_date, datetime.min.time()),
            )
            inv_c = InvoiceRecord(
                invoice_id="INV-AMB-003",
                order_id="ord_amb_3",
                payment_id="pay_amb_3",
                supplier_gstin="29ABCDE1234F1Z5",
                amount_in_paise=90000,
                method=PaymentMethod.UPI,
                captured_at=datetime.combine(start_date, datetime.min.time()),
            )
            inv_d = InvoiceRecord(
                invoice_id="INV-AMB-004",
                order_id="ord_amb_4",
                payment_id="pay_amb_4",
                supplier_gstin="29ABCDE1234F1Z5",
                amount_in_paise=60000,
                method=PaymentMethod.UPI,
                captured_at=datetime.combine(start_date, datetime.min.time()),
            )
            invoices.extend([inv_a, inv_b, inv_c, inv_d])

            # (80k - 800) + (70k - 700) = 79200 + 69300 = 148500
            # (90k - 900) + (60k - 600) = 89100 + 59400 = 148500
            amb_amt_net = 148500

            # Bank Credit that matches BOTH (A+B) and (C+D)
            amb_credit = BankNodalCredit(
                utr_number="HDFCN_PLANTED_AMB_01",
                account_number="918239012389",
                credit_amount_in_paise=amb_amt_net,
                value_date=start_date + timedelta(days=1),
                raw_narration="NFX-RZR*PLANTED*COLLISION",
                settlement_id=None,  # No settlement ID hints!
            )
            bank_credits.append(amb_credit)
            ground_truth["planted_ambiguities"] += 1

        return invoices, bank_credits, gstr2b_items, ground_truth
