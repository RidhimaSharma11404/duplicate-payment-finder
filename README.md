# Duplicate Payment Finder

A Python and Streamlit tool to detect duplicate vendor payments in Accounts Payable records.

---

## Problem

Companies process large volumes of vendor payments every month. Duplicate payments happen due to human error, re-submitted invoices, or multiple payment channels approving the same bill. If not identified promptly, these duplicate disbursements result in direct financial leakage.

---

## The Two Detection Rules

1. **Rule 1 — Exact Match:**
   - Same vendor, same invoice number, and exact same amount.
2. **Rule 2 — Likely Match:**
   - Same vendor and exact same amount, but with a different invoice number, paid within 1 to 7 days of each other.

---

## How to Run

1. **Generate synthetic data:**
   ```bash
   python generate_data.py
   ```
   *Generates `payments.csv` containing 5,000 transactions with 70 planted duplicates.*

2. **Run detection and analysis:**
   ```bash
   python find_duplicates.py
   ```
   *Runs detection rules, evaluates pair-based accuracy, exports findings to `results.xlsx` and `powerbi_data.xlsx`, and prints audit metrics.*

3. **Launch the dashboard:**
   ```bash
   streamlit run app.py
   ```
   *Opens the local web interface to filter and review flagged payments.*

---

## Results

### Detection Accuracy

| Metric | Count / Percentage |
| :--- | :--- |
| **Total Payments Tested** | 5,000 |
| **Planted Duplicates** | 70 |
| **Caught Duplicates** | 60 |
| **Missed Duplicates** | 10 |
| **False Alarms** | 0 |
| **Recall Rate** | 85.7% |
| **Precision Rate** | 100.0% |
| **Suspected Duplicates Flagged** | 60 |
| **Total Capital at Risk** | INR 14,238,885.84 |

---

## Why the Misses Happened

- **Typo in Invoice Number (10 cases):** The 10 missed payments were intentionally planted duplicates where the invoice number contains a typo (such as `INV-1001` vs `INV1001`) and was paid more than 7 days apart. Since exact string comparison is used, neither Rule 1 nor Rule 2 flags these.
- **False Alarms (0 cases):** With tie-breaking by payment ID on same-date records and evaluating matches as pairs, 0 false alarms were generated.

---

## Limitations

- **Synthetic Data:** The dataset is synthetically generated for testing and demonstration.
- **Invoice Typos Not Caught:** Exact string matching fails to detect invoice numbers with missing hyphens, extra spaces, or transposed characters.
- **Repeat Payments Risk:** Legitimate recurring payments that fall within a 7-day window can be falsely flagged if paid in quick succession.

---

## Next Steps

- **Fuzzy Matching:** Implement string similarity metrics (such as Levenshtein distance) to identify typos in invoice numbers and minor vendor spelling differences.
- **Amount Tolerance:** Add tolerance bands (for example, +/- Rs 50) to catch duplicates with minor currency rounding or deduction differences.
- **Recurring Payment Exclusion:** Automatically flag recurring retainer series across consecutive months to reduce potential false alarms.
