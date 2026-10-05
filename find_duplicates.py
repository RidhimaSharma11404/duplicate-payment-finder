"""
find_duplicates.py
Simple duplicate payment detection using two basic rules:
1. Exact Match: Same vendor, invoice number, and amount.
2. Likely Match: Same vendor and amount, different invoice number, paid within 7 days.

Exports findings to results.xlsx and powerbi_data.xlsx, and prints audit memo numbers.
"""

import pandas as pd

def find_duplicates(df):
    """
    Finds duplicate payments using Rule 1 (Exact) and Rule 2 (Likely).
    When payments have the same date, sorts by payment_id so lower ID is original and higher ID is duplicate.
    """
    flagged = []
    
    # Group payments that have the exact same vendor and amount
    for (vendor, amount), group in df.groupby(["vendor", "amount"]):
        if len(group) < 2:
            continue
        
        # Sort by payment date then payment_id
        sorted_records = group.sort_values(by=["payment_date", "payment_id"]).to_dict("records")
        matched_indices = set()
        
        for i in range(len(sorted_records)):
            for j in range(i + 1, len(sorted_records)):
                if j in matched_indices:
                    continue
                
                orig = sorted_records[i]
                dup = sorted_records[j]
                
                inv_orig = str(orig["invoice_number"]).strip()
                inv_dup = str(dup["invoice_number"]).strip()
                days_diff = abs((pd.to_datetime(dup["payment_date"]) - pd.to_datetime(orig["payment_date"])).days)
                
                confidence = None
                reason = ""
                
                # Rule 1: Exact Match (same vendor, amount, and invoice number)
                if inv_orig.upper() == inv_dup.upper():
                    confidence = "Exact"
                    reason = "Same vendor, invoice number, and amount"
                
                # Rule 2: Likely Match (same vendor and amount, paid 1 to 7 days apart)
                elif 1 <= days_diff <= 7:
                    confidence = "Likely"
                    reason = f"Paid {days_diff} day(s) apart with different invoice"
                
                # If matched by either rule, add to flagged list
                if confidence:
                    flagged.append({
                        "duplicate_payment_id": dup["payment_id"],
                        "original_payment_id": orig["payment_id"],
                        "vendor": vendor,
                        "amount": float(amount),
                        "duplicate_date": dup["payment_date"],
                        "original_date": orig["payment_date"],
                        "days_apart": days_diff,
                        "duplicate_invoice": inv_dup,
                        "original_invoice": inv_orig,
                        "confidence_level": confidence,
                        "reason": reason,
                        "paid_by": dup["paid_by"]
                    })
                    matched_indices.add(j)
                    break
                    
    return pd.DataFrame(flagged)

def calculate_accuracy(df_raw, df_flagged):
    """
    Evaluates flagged pairs against planted duplicates:
    A flagged pair is evaluated as correct if either of its payment IDs is a planted duplicate.
    """
    planted_df = df_raw[df_raw["planted"] != "none"]
    planted_ids = set(planted_df["payment_id"])
    total_planted = len(planted_ids)
    
    caught_planted_ids = set()
    correct_pair_count = 0
    false_alarm_records = []
    
    for _, row in df_flagged.iterrows():
        dup_id = row["duplicate_payment_id"]
        orig_id = row["original_payment_id"]
        if (dup_id in planted_ids) or (orig_id in planted_ids):
            correct_pair_count += 1
            if dup_id in planted_ids:
                caught_planted_ids.add(dup_id)
            if orig_id in planted_ids:
                caught_planted_ids.add(orig_id)
        else:
            false_alarm_records.append({
                "duplicate_payment_id": dup_id,
                "original_payment_id": orig_id,
                "vendor": row["vendor"],
                "amount": row["amount"],
                "duplicate_date": row["duplicate_date"],
                "original_date": row["original_date"],
                "duplicate_invoice": row["duplicate_invoice"],
                "original_invoice": row["original_invoice"],
                "reason": "coincidence"
            })
            
    caught_count = len(caught_planted_ids)
    missed_count = total_planted - caught_count
    false_alarms_count = len(false_alarm_records)
    total_flagged = len(df_flagged)
    
    recall_pct = (caught_count / total_planted) * 100.0 if total_planted > 0 else 0.0
    precision_pct = (correct_pair_count / total_flagged) * 100.0 if total_flagged > 0 else 0.0
    
    accuracy_df = pd.DataFrame([{
        "Planted": total_planted,
        "Caught": caught_count,
        "Missed": missed_count,
        "False Alarms": false_alarms_count,
        "Recall %": f"{recall_pct:.1f}%",
        "Precision %": f"{precision_pct:.1f}%"
    }])
    
    fa_df = pd.DataFrame(false_alarm_records)
    
    # Remaining missed payments
    missed_raw = df_raw[(df_raw["planted"] != "none") & (~df_raw["payment_id"].isin(caught_planted_ids))].copy()
    missed_records = []
    for _, row in missed_raw.iterrows():
        p_type = row["planted"]
        if p_type == "typo":
            reason = "typo in invoice number"
        elif p_type == "likely":
            reason = "paid more than 7 days apart"
        else:
            reason = "other"
            
        missed_records.append({
            "payment_id": row["payment_id"],
            "vendor": row["vendor"],
            "amount": row["amount"],
            "payment_date": row["payment_date"],
            "planted_type": p_type,
            "reason": reason
        })
    missed_df = pd.DataFrame(missed_records)
    
    return accuracy_df, fa_df, missed_df, total_planted, caught_count, missed_count, false_alarms_count, recall_pct, precision_pct

def export_powerbi_data(df_flagged, accuracy_df, total_risk, vendors_affected):
    """
    Creates powerbi_data.xlsx with 3 plain sheets: Flagged, Accuracy, Summary.
    """
    # 1. Flagged
    flagged_pbi = df_flagged[[
        "duplicate_payment_id", "original_payment_id", "vendor", "amount",
        "duplicate_date", "original_date", "days_apart", "confidence_level"
    ]].copy()
    flagged_pbi["month"] = pd.to_datetime(flagged_pbi["duplicate_date"]).dt.strftime("%Y-%m")
    flagged_pbi = flagged_pbi.rename(columns={
        "duplicate_payment_id": "duplicate_id",
        "original_payment_id": "original_id",
        "confidence_level": "match_type"
    })
    flagged_pbi = flagged_pbi[[
        "duplicate_id", "original_id", "vendor", "amount",
        "duplicate_date", "original_date", "month", "days_apart", "match_type"
    ]]
    
    # 2. Accuracy
    acc_pbi = pd.DataFrame([{
        "planted": accuracy_df["Planted"].iloc[0],
        "caught": accuracy_df["Caught"].iloc[0],
        "missed": accuracy_df["Missed"].iloc[0],
        "false_alarms": accuracy_df["False Alarms"].iloc[0],
        "recall_pct": float(accuracy_df["Recall %"].iloc[0].replace("%", "")),
        "precision_pct": float(accuracy_df["Precision %"].iloc[0].replace("%", ""))
    }])
    
    # 3. Summary
    summary_pbi = pd.DataFrame([{
        "suspected_duplicates": len(df_flagged),
        "total_amount_at_risk": total_risk,
        "vendors_affected": vendors_affected
    }])
    
    with pd.ExcelWriter("powerbi_data.xlsx", engine="openpyxl") as writer:
        flagged_pbi.to_excel(writer, sheet_name="Flagged", index=False)
        acc_pbi.to_excel(writer, sheet_name="Accuracy", index=False)
        summary_pbi.to_excel(writer, sheet_name="Summary", index=False)

def print_memo_metrics(df_raw, df_flagged):
    """
    Computes and prints exact numbers for audit memo.
    """
    total_payments = len(df_raw)
    min_date = df_raw["payment_date"].min()
    max_date = df_raw["payment_date"].max()
    
    # Exact and Likely breakdown
    exact_df = df_flagged[df_flagged["confidence_level"] == "Exact"]
    likely_df = df_flagged[df_flagged["confidence_level"] == "Likely"]
    
    exact_count = len(exact_df)
    exact_rupees = exact_df["amount"].sum()
    
    likely_count = len(likely_df)
    likely_rupees = likely_df["amount"].sum()
    
    # Top 3 vendors
    top3_vendors = df_flagged.groupby("vendor")["amount"].sum().sort_values(ascending=False).head(3)
    
    # Month with highest amount
    df_temp = df_flagged.copy()
    df_temp["month"] = pd.to_datetime(df_temp["duplicate_date"]).dt.strftime("%Y-%m")
    month_summary = df_temp.groupby("month")["amount"].sum().sort_values(ascending=False)
    top_month = month_summary.index[0]
    top_month_rupees = month_summary.iloc[0]
    
    print("\n" + "=" * 55)
    print("AUDIT MEMO NUMBERS")
    print("=" * 55)
    print(f"1. Total Payments:       {total_payments:,}")
    print(f"2. Date Range:          {min_date} to {max_date}")
    print(f"3. Suspected Duplicates Breakdown:")
    print(f"   - Exact:             {exact_count} payments | INR {exact_rupees:,.2f}")
    print(f"   - Likely:            {likely_count} payments | INR {likely_rupees:,.2f}")
    print(f"   - Total:             {len(df_flagged)} payments | INR {df_flagged['amount'].sum():,.2f}")
    print(f"4. Top 3 Vendors by Amount at Risk:")
    for idx, (v_name, v_amt) in enumerate(top3_vendors.items(), 1):
        print(f"   {idx}. {v_name:<28s} INR {v_amt:>12,.2f}")
    print(f"5. Month with Highest Amount at Risk:")
    print(f"   - {top_month}: INR {top_month_rupees:,.2f}")
    print("=" * 55 + "\n")

def main():
    print("=" * 55)
    print("DUPLICATE PAYMENT FINDER")
    print("=" * 55)
    
    # 1. Load data
    df_raw = pd.read_csv("payments.csv")
    print(f"Total payments loaded: {len(df_raw):,}")
    
    # 2. Run detection rules
    df_flagged = find_duplicates(df_raw)
    total_risk = df_flagged["amount"].sum() if not df_flagged.empty else 0.0
    vendors_affected = df_flagged["vendor"].nunique() if not df_flagged.empty else 0
    
    print(f"Suspected duplicates found: {len(df_flagged)}")
    print(f"Total amount at risk: INR {total_risk:,.2f}")
    print(f"Vendors affected: {vendors_affected}")
    
    # 3. Calculate detection accuracy with pair-based evaluation
    accuracy_df, fa_df, missed_df, planted, caught, missed, false_alarms, recall, precision = calculate_accuracy(df_raw, df_flagged)
    
    print("\n" + "-" * 55)
    print("DETECTION ACCURACY")
    print("-" * 55)
    print(f"Planted:      {planted}")
    print(f"Caught:       {caught}")
    print(f"Missed:       {missed}")
    print(f"False Alarms: {false_alarms}")
    print(f"Recall:       {recall:.1f}%")
    print(f"Precision:    {precision:.1f}%")
    print("-" * 55)
    
    # 4. Error Analysis: False Alarms & Missed Duplicates
    print(f"\n--- FALSE ALARMS ({len(fa_df)}) ---")
    if len(fa_df) == 0:
        print("  None (0 false alarms)")
    else:
        for _, row in fa_df.iterrows():
            print(f"  - Dup ID: {row['duplicate_payment_id']} | Orig ID: {row['original_payment_id']} | Vendor: {row['vendor']} | Amount: INR {row['amount']:,.2f} | Reason: {row['reason']}")
            
    print(f"\n--- MISSED DUPLICATES ({len(missed_df)}) ---")
    for _, row in missed_df.iterrows():
        print(f"  - ID: {row['payment_id']} | Vendor: {row['vendor']} | Amount: INR {row['amount']:,.2f} | Reason: {row['reason']}")
        
    miss_counts = missed_df["reason"].value_counts().reset_index() if not missed_df.empty else pd.DataFrame(columns=["Reason", "Count"])
    miss_counts.columns = ["Reason", "Count"]
    print("\n--- MISSES COUNT BY REASON ---")
    print(miss_counts.to_string(index=False))
    
    # 5. Print Audit Memo Metrics
    print_memo_metrics(df_raw, df_flagged)
    
    # 6. Save results to results.xlsx (including False Alarms and Missed sheets)
    output_file = "results.xlsx"
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_flagged.to_excel(writer, sheet_name="Suspected Duplicates", index=False)
        accuracy_df.to_excel(writer, sheet_name="Detection Accuracy", index=False)
        
        summary_df = pd.DataFrame([
            {"Metric": "Suspected Duplicates", "Value": str(len(df_flagged))},
            {"Metric": "Total Amount at Risk", "Value": f"{total_risk:,.2f}"},
            {"Metric": "Vendors Affected", "Value": str(vendors_affected)}
        ])
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        
        fa_df.to_excel(writer, sheet_name="False Alarms", index=False)
        missed_df.to_excel(writer, sheet_name="Missed", index=False)
        
    print(f"Results saved to '{output_file}' with 'False Alarms' and 'Missed' sheets.")
    
    # 7. Export Power BI dataset
    export_powerbi_data(df_flagged, accuracy_df, total_risk, vendors_affected)
    print("Power BI data exported to 'powerbi_data.xlsx' (Flagged, Accuracy, Summary sheets).")
    print("=" * 55)

if __name__ == "__main__":
    main()
