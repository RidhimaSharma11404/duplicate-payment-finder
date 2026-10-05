# Audit Memorandum: Accounts Payable Duplicate Payment Testing

**To:** Finance Controller / Internal Audit Committee  
**From:** Accounts Payable Audit Analytics Team  
**Date:** October 5, 2026  
**Subject:** Substantive Testing Results for Suspected Duplicate Disbursements (FY 2025)

---

### 1. Observation

Substantive testing of the **5,000 Accounts Payable transactions** (totaling disbursements across 30 illustrative vendors in FY 2025) identified **60 suspected duplicate payments** representing **INR 14,238,885.84 (~₹1.42 Crore)** in potential overpayments across **26 unique vendors**.

#### Breakdown of Flagged Payments:
- **Exact Matches (Rule 1):** **30 disbursements** totaling **INR 6,989,617.91 (~₹69.90 Lakh)** sharing identical vendor names, exact amounts, and identical invoice numbers disbursed within 0 to 3 days.
- **Likely Matches (Rule 2):** **30 disbursements** totaling **INR 7,249,267.93 (~₹72.49 Lakh)** sharing identical vendor names and amounts, but differing invoice reference numbers, disbursed within **1 to 7 calendar days**.

#### Concentration & Timing:
- **Top 3 Vendors by Amount at Risk:**
  1. *Dr Reddys Laboratories:* INR 2,533,266.42 (17.8% of total risk)
  2. *BPCL Supplies:* INR 1,114,023.59 (7.8% of total risk)
  3. *Marico Limited:* INR 1,075,053.74 (7.5% of total risk)
- **Peak Exposure Period:** March 2025 recorded the highest duplicate disbursement exposure at **INR 2,627,310.98**.

---

### 2. Risk Assessment

1. **Direct Working Capital Leakage:** Unrecovered duplicate disbursements directly deplete operating cash flows.
2. **Control Deficiencies in Invoice Ingestion:** The prevalence of likely duplicates (paid 1–7 days apart under alternate invoice numbers) indicates that multi-channel invoice intake (e.g. portal and email) lacks automated duplicate-detection gates prior to payment release.
3. **Typographical Blind Spots:** Testing against planted edge cases revealed that strict equality rules miss typographical formatting variations (such as `INV-1001` vs `INV1001`) when payments are spaced more than 7 days apart (15–30 days in test data).

---

### 3. Recommendations

1. **Immediate Recovery Action:**
   - Issue formal statements of account to the 26 affected vendors to reconcile the **₹1.42 Crore** flagged exposure and obtain immediate credit notes or cash refunds.
2. **Pre-Payment ERP Control Enhancement:**
   - Enforce automated system controls in the ERP Accounts Payable module to prevent processing invoices with identical vendor names and amounts within a 7-day window without supervisory override.
3. **Deploy Machine Learning / Approximate Matching:**
   - Pilot the candidate-pair Machine Learning model (`ml_step.py`). On the held-out test split (47 candidate pairs), the standardized Logistic Regression model achieved **100.0% recall** and caught **4 of the 4 typo cases** that deterministic rules missed.

---

### 4. Audit & Testing Limitations

- **Synthetic Test Data:** Results are evaluated on a synthetic benchmark dataset. While precision was 100.0% against planted repeat payments (which were spaced 30–60 days apart), precision is expected to be lower in live ERP environments with legitimate same-month recurring retainers.
- **Small Sample Size for Edge Cases:** The test set contained 4 planted typo cases; statistical validation on a larger, real-world AP population is recommended before full production automation.
- *Note: Vendor names in the dataset are illustrative.*
