# Audit Memorandum: Accounts Payable Duplicate Payment Test

> Illustrative memo. Based on a synthetic dataset created for a portfolio
> project. Vendor names are illustrative and the findings are not from a
> real client.

**To:** Finance Controller | **From:** Ridhima Sharma | **Date:** 5 October 2026  
**Subject:** Duplicate payment test results, FY 2025

## Scope and procedure
Population: 5,000 vendor payments, 1 January to 31 December 2025, 30
vendors. Two tests were run: (1) Exact: same vendor, invoice number and
amount; (2) Likely: same vendor and amount, different invoice number,
paid 1 to 7 days apart.

## 1. Observation
The tests flagged 60 suspected duplicate payments worth INR 14,238,885.84
(about Rs 1.42 crore) across 26 vendors.

- Exact matches: 30 payments, INR 6,989,617.91
- Likely matches: 30 payments, INR 7,249,267.93
- Top 3 vendors: Dr Reddys Laboratories (INR 2,533,266.42, 17.8%), BPCL
  Supplies (INR 1,114,023.59, 7.8%), Marico Limited (INR 1,075,053.74,
  7.6%), together 33% of the flagged amount
- Highest month: March 2025, INR 2,627,310.98

**Reliability of the test.** The data contained 70 planted duplicates. The
rules caught 60 (85.7%) with no false alarms. All 10 misses were invoice
number typos (for example INV-1001 and INV1001) paid 15 to 30 days apart.

## 2. Risk
1. Duplicate payments are direct cash losses.
2. Likely matches paid under different invoice numbers may indicate that
   invoices received through more than one channel are not checked for
   duplicates before payment. This needs to be confirmed with management.
3. The rules do not detect invoice number typos paid more than 7 days
   apart, so exceptions of that kind would be missed.

## 3. Recommendations
1. Validate each exception against the invoice and bank record before
   contacting vendors.
2. For confirmed duplicates, management should request refunds or credit
   notes.
3. Add a pre-payment system check that blocks or flags the same vendor and
   amount within 7 days, with a supervisor override.
4. Add an approximate invoice-number check (similar invoice numbers, same
   vendor and amount, within 45 days). A trial logistic regression on
   candidate pairs caught 4 of 4 typo cases on 47 held-out pairs (100%
   recall, 95.5% precision, 1 false alarm), but the test set is small, so
   a simple rule should be tried first.
5. Run this test every quarter.

## 4. Conclusion
On the test data, the two rules found material exceptions with no false
alarms but missed typo duplicates. Every exception needs manual review.

## 5. Limitations
- Synthetic data. Legitimate repeat payments were planted 30 to 60 days
  apart, so precision is likely to be lower on real data.
- Only 4 typo cases in the ML test set, and the date gap carried the most
  weight in the model, so the result is indicative only.
- Vendor name variations are not tested.
