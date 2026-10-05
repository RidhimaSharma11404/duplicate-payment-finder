"""
generate_data.py
Creates synthetic Accounts Payable data (5,000 payments) with planted duplicates.
"""

import random
from datetime import datetime, timedelta
import pandas as pd

# Set random seed so the results are the same every time
random.seed(42)

# List of 30 Indian vendors
VENDORS = [
    "Tata Consultancy Services", "Infosys Limited", "Wipro Technologies",
    "Reliance Industries", "Larsen & Toubro", "HCL Technologies",
    "Bharti Airtel", "ITC Limited", "Mahindra & Mahindra", "Tech Mahindra",
    "Sun Pharma Logistics", "Bajaj Auto", "Titan Company", "UltraTech Cement",
    "Asian Paints", "Kotak Services", "Power Grid Corporation", "NTPC Solutions",
    "Hindalco Industries", "Coal India Logistics", "BPCL Supplies", "JSW Steel",
    "Tata Motors", "Dr Reddys Laboratories", "Cipla Healthcare", "Godrej Consumer",
    "Hero MotoCorp", "Havells India", "Marico Limited", "Blue Dart Express"
]

PAID_BY_NAMES = [
    "Rahul Sharma", "Sneha Patel", "Vikram Malhotra", "Ananya Iyer", "Priya Nair"
]

def random_date(year=2025):
    """Returns a random date within the specified year."""
    start = datetime(year, 1, 1)
    end = datetime(year, 12, 31)
    days_between = (end - start).days
    random_days = random.randint(0, days_between)
    return start + timedelta(days=random_days)

def create_dataset():
    records = []
    payment_id_counter = 10001
    
    # 1. Create 4,820 normal, legitimate payments (so total rows = 5,000)
    num_normal = 4820
    for _ in range(num_normal):
        vendor = random.choice(VENDORS)
        inv_num = f"INV-{random.randint(10000, 99999)}"
        amount = round(random.uniform(5000, 750000), 2)
        p_date = random_date(2025)
        paid_by = random.choice(PAID_BY_NAMES)
        
        records.append({
            "payment_id": f"PAY-{payment_id_counter}",
            "vendor": vendor,
            "invoice_number": inv_num,
            "amount": amount,
            "payment_date": p_date.strftime("%Y-%m-%d"),
            "paid_by": paid_by,
            "planted": "none"
        })
        payment_id_counter += 1

    # 2. Add 20 legitimate repeat payments (same vendor, same amount, different month)
    # These are monthly retainer/rent payments and are NOT duplicates.
    for _ in range(20):
        vendor = random.choice(VENDORS)
        amount = round(random.uniform(25000, 200000), 2)
        first_date = datetime(2025, random.randint(1, 6), random.randint(1, 28))
        second_date = first_date + timedelta(days=random.randint(30, 60))
        
        # Original payment
        records.append({
            "payment_id": f"PAY-{payment_id_counter}",
            "vendor": vendor,
            "invoice_number": f"INV-{random.randint(10000, 99999)}",
            "amount": amount,
            "payment_date": first_date.strftime("%Y-%m-%d"),
            "paid_by": random.choice(PAID_BY_NAMES),
            "planted": "none"
        })
        payment_id_counter += 1
        
        # Repeat payment (legitimate)
        records.append({
            "payment_id": f"PAY-{payment_id_counter}",
            "vendor": vendor,
            "invoice_number": f"INV-{random.randint(10000, 99999)}",
            "amount": amount,
            "payment_date": second_date.strftime("%Y-%m-%d"),
            "paid_by": random.choice(PAID_BY_NAMES),
            "planted": "none"
        })
        payment_id_counter += 1

    # 3. Plant 30 Exact Duplicates (same vendor, invoice, amount, paid 0-3 days later)
    for _ in range(30):
        vendor = random.choice(VENDORS)
        inv_num = f"INV-{random.randint(10000, 99999)}"
        amount = round(random.uniform(10000, 500000), 2)
        orig_date = random_date(2025)
        dup_date = orig_date + timedelta(days=random.randint(0, 3))
        if dup_date.year > 2025:
            dup_date = orig_date
            
        # Original
        records.append({
            "payment_id": f"PAY-{payment_id_counter}",
            "vendor": vendor,
            "invoice_number": inv_num,
            "amount": amount,
            "payment_date": orig_date.strftime("%Y-%m-%d"),
            "paid_by": random.choice(PAID_BY_NAMES),
            "planted": "none"
        })
        payment_id_counter += 1
        
        # Duplicate
        records.append({
            "payment_id": f"PAY-{payment_id_counter}",
            "vendor": vendor,
            "invoice_number": inv_num,
            "amount": amount,
            "payment_date": dup_date.strftime("%Y-%m-%d"),
            "paid_by": random.choice(PAID_BY_NAMES),
            "planted": "exact"
        })
        payment_id_counter += 1

    # 4. Plant 30 Likely Duplicates (same vendor & amount, different invoice, paid 1-7 days apart)
    for _ in range(30):
        vendor = random.choice(VENDORS)
        inv_num_orig = f"INV-{random.randint(10000, 99999)}"
        inv_num_dup = f"INV-{random.randint(10000, 99999)}"
        amount = round(random.uniform(10000, 500000), 2)
        orig_date = random_date(2025)
        dup_date = orig_date + timedelta(days=random.randint(1, 7))
        if dup_date.year > 2025:
            dup_date = orig_date - timedelta(days=random.randint(1, 7))
            
        # Original
        records.append({
            "payment_id": f"PAY-{payment_id_counter}",
            "vendor": vendor,
            "invoice_number": inv_num_orig,
            "amount": amount,
            "payment_date": orig_date.strftime("%Y-%m-%d"),
            "paid_by": random.choice(PAID_BY_NAMES),
            "planted": "none"
        })
        payment_id_counter += 1
        
        # Duplicate
        records.append({
            "payment_id": f"PAY-{payment_id_counter}",
            "vendor": vendor,
            "invoice_number": inv_num_dup,
            "amount": amount,
            "payment_date": dup_date.strftime("%Y-%m-%d"),
            "paid_by": random.choice(PAID_BY_NAMES),
            "planted": "likely"
        })
        payment_id_counter += 1

    # 5. Plant 10 Harder Duplicates with Typo in Invoice (e.g., INV-1001 vs INV1001, paid > 7 days apart)
    # The simple 2-rule tool is NOT expected to catch these.
    for _ in range(10):
        vendor = random.choice(VENDORS)
        base_num = random.randint(1000, 9999)
        inv_num_orig = f"INV-{base_num}"
        inv_num_dup = f"INV{base_num}"  # Typo (missing hyphen)
        amount = round(random.uniform(10000, 300000), 2)
        orig_date = random_date(2025)
        dup_date = orig_date + timedelta(days=random.randint(15, 30))
        if dup_date.year > 2025:
            dup_date = orig_date - timedelta(days=random.randint(15, 30))
            
        # Original
        records.append({
            "payment_id": f"PAY-{payment_id_counter}",
            "vendor": vendor,
            "invoice_number": inv_num_orig,
            "amount": amount,
            "payment_date": orig_date.strftime("%Y-%m-%d"),
            "paid_by": random.choice(PAID_BY_NAMES),
            "planted": "none"
        })
        payment_id_counter += 1
        
        # Duplicate
        records.append({
            "payment_id": f"PAY-{payment_id_counter}",
            "vendor": vendor,
            "invoice_number": inv_num_dup,
            "amount": amount,
            "payment_date": dup_date.strftime("%Y-%m-%d"),
            "paid_by": random.choice(PAID_BY_NAMES),
            "planted": "typo"
        })
        payment_id_counter += 1

    df = pd.DataFrame(records)
    # Shuffle the records so duplicates are distributed throughout the year
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df

def main():
    print("Generating synthetic payment data...")
    df = create_dataset()
    print(f"Total payments created: {len(df):,}")
    
    # Count planted duplicates
    planted_counts = df["planted"].value_counts()
    print("\nPlanted Duplicates Breakdown:")
    for p_type, count in planted_counts.items():
        if p_type != "none":
            print(f" - {p_type.capitalize()}: {count}")
            
    total_planted = len(df[df["planted"] != "none"])
    print(f"Total planted duplicates: {total_planted}")
    
    output_file = "payments.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved payments to '{output_file}'.")

if __name__ == "__main__":
    main()
