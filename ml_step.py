"""
ml_step.py
Lightweight Machine Learning enhancement for Duplicate Payment Finder.
Uses Logistic Regression on candidate payment pairs to identify duplicates and catch typo variations.
"""

import difflib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score

def build_candidate_pairs(df):
    """
    Builds candidate payment pairs: same vendor and amount within Rs 50.
    Computes 5 features per pair: days_apart, invoice_similarity, amount_difference, same_invoice, same_paid_by.
    """
    pairs = []
    
    for vendor, vgroup in df.groupby("vendor"):
        sorted_v = vgroup.sort_values(by=["payment_date", "payment_id"]).to_dict("records")
        
        for i in range(len(sorted_v)):
            for j in range(i + 1, len(sorted_v)):
                r1 = sorted_v[i]
                r2 = sorted_v[j]
                
                amt_diff = abs(r2["amount"] - r1["amount"])
                if amt_diff <= 50.0:
                    inv1 = str(r1["invoice_number"]).strip()
                    inv2 = str(r2["invoice_number"]).strip()
                    d1 = pd.to_datetime(r1["payment_date"])
                    d2 = pd.to_datetime(r2["payment_date"])
                    days = abs((d2 - d1).days)
                    
                    # 5 Features
                    inv_sim = difflib.SequenceMatcher(None, inv1.upper(), inv2.upper()).ratio()
                    same_inv = 1 if inv1.upper() == inv2.upper() else 0
                    same_pb = 1 if str(r1["paid_by"]).strip() == str(r2["paid_by"]).strip() else 0
                    
                    # Planted duplicate label
                    p1_type = r1.get("planted", "none")
                    p2_type = r2.get("planted", "none")
                    
                    is_planted_pair = 0
                    planted_type = "none"
                    
                    if p2_type in ["exact", "likely", "typo"] and p1_type == "none" and amt_diff == 0:
                        if p2_type == "exact" and same_inv == 1:
                            is_planted_pair = 1
                            planted_type = "exact"
                        elif p2_type == "likely" and 1 <= days <= 7:
                            is_planted_pair = 1
                            planted_type = "likely"
                        elif p2_type == "typo" and inv_sim >= 0.8:
                            is_planted_pair = 1
                            planted_type = "typo"
                    elif p1_type in ["exact", "likely", "typo"] and p2_type == "none" and amt_diff == 0:
                        if p1_type == "exact" and same_inv == 1:
                            is_planted_pair = 1
                            planted_type = "exact"
                        elif p1_type == "likely" and 1 <= days <= 7:
                            is_planted_pair = 1
                            planted_type = "likely"
                        elif p1_type == "typo" and inv_sim >= 0.8:
                            is_planted_pair = 1
                            planted_type = "typo"
                            
                    pairs.append({
                        "p1_id": r1["payment_id"],
                        "p2_id": r2["payment_id"],
                        "vendor": vendor,
                        "days_apart": days,
                        "invoice_similarity": inv_sim,
                        "amount_difference": amt_diff,
                        "same_invoice": same_inv,
                        "same_paid_by": same_pb,
                        "label": is_planted_pair,
                        "planted_type": planted_type
                    })
                    
    return pd.DataFrame(pairs)

def main():
    print("=" * 60)
    print("DUPLICATE PAYMENT FINDER - MACHINE LEARNING MODULE")
    print("=" * 60)
    
    # 1. Load data
    df_raw = pd.read_csv("payments.csv")
    print(f"Total payments loaded: {len(df_raw):,}")
    
    # 2. Build candidate pairs
    pairs_df = build_candidate_pairs(df_raw)
    print(f"Candidate pairs constructed: {len(pairs_df)}")
    print(f" - True planted duplicates:  {pairs_df['label'].sum()}")
    print(f" - Non-duplicate pairs:      {len(pairs_df) - pairs_df['label'].sum()}")
    
    # 3. Train/Test Split (70/30 stratified)
    features = ["days_apart", "invoice_similarity", "amount_difference", "same_invoice", "same_paid_by"]
    X = pairs_df[features]
    y = pairs_df["label"]
    
    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X, y, pairs_df, test_size=0.30, random_state=42, stratify=y
    )
    print(f"\nTrain pairs: {len(X_train)} | Test pairs: {len(X_test)}")
    
    # 4. Train Logistic Regression
    clf = LogisticRegression(random_state=42)
    clf.fit(X_train, y_train)
    
    print("\n--- MODEL COEFFICIENTS (Plain Words) ---")
    for feat, coef in zip(features, clf.coef_[0]):
        direction = "increases" if coef > 0 else "decreases"
        impact = "strong positive" if coef > 0.5 else ("strong negative" if coef < -0.5 else "moderate")
        print(f" - {feat:<20s}: {coef:+.4f} ({direction} probability of duplicate)")
    print(f" - Intercept           : {clf.intercept_[0]:+.4f}")
    
    # 5. Evaluate on Test Pairs (Rules vs ML)
    # Rules prediction on test set
    rule_pred = ((df_test["same_invoice"] == 1) & (df_test["amount_difference"] == 0)) | \
                ((df_test["same_invoice"] == 0) & (df_test["amount_difference"] == 0) & (df_test["days_apart"] >= 1) & (df_test["days_apart"] <= 7))
    rule_pred = rule_pred.astype(int)
    
    # ML model prediction on test set
    ml_pred = clf.predict(X_test)
    
    # Precision and Recall
    rule_prec = precision_score(y_test, rule_pred)
    rule_rec = recall_score(y_test, rule_pred)
    
    ml_prec = precision_score(y_test, ml_pred)
    ml_rec = recall_score(y_test, ml_pred)
    
    # Typo Duplicates Caught
    typo_mask = df_test["planted_type"] == "typo"
    total_typos_test = typo_mask.sum()
    rule_typos_caught = (rule_pred[typo_mask] == 1).sum()
    ml_typos_caught = (ml_pred[typo_mask] == 1).sum()
    
    comparison_df = pd.DataFrame([
        {
            "Approach": "Detection Rules (Exact + Likely)",
            "Precision %": f"{rule_prec * 100:.1f}%",
            "Recall %": f"{rule_rec * 100:.1f}%",
            "Typo Duplicates Caught": f"{rule_typos_caught} / {total_typos_test}"
        },
        {
            "Approach": "Logistic Regression ML Model",
            "Precision %": f"{ml_prec * 100:.1f}%",
            "Recall %": f"{ml_rec * 100:.1f}%",
            "Typo Duplicates Caught": f"{ml_typos_caught} / {total_typos_test}"
        }
    ])
    
    print("\n--- TEST SET COMPARISON: RULES vs ML ---")
    print(comparison_df.to_string(index=False))
    print("=" * 60)
    
    # 6. Save comparison to "ML vs Rules" sheet in results.xlsx
    excel_file = "results.xlsx"
    with pd.ExcelWriter(excel_file, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        comparison_df.to_excel(writer, sheet_name="ML vs Rules", index=False)
        
    print(f"\nSaved comparison table to sheet 'ML vs Rules' in '{excel_file}'.")

if __name__ == "__main__":
    main()
