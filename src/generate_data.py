"""Create a synthetic, intentionally 'dirty' SmartMart dataset."""
import numpy as np, pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
CATALOG = {
    "Electronics": [("Smartphone", 450), ("Headphones", 60), ("Laptop", 900), ("Smart Watch", 150)],
    "Clothing": [("T-Shirt", 15), ("Jeans", 40), ("Jacket", 85), ("Sneakers", 70)],
    "Home Appliances": [("Microwave", 120), ("Blender", 45), ("Vacuum Cleaner", 180), ("Air Fryer", 95)],
    "Grocery": [("Rice 5kg", 12), ("Cooking Oil", 9), ("Tea Pack", 6), ("Snack Box", 8)],
}
CITIES = {"Karachi": "South", "Hyderabad": "South", "Lahore": "Central", "Faisalabad": "Central",
          "Islamabad": "North", "Peshawar": "North"}

def generate(n=3000, n_customers=1500):
    dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 730, n), unit="D")
    cust = rng.integers(1, n_customers + 1, n)
    rows = []
    for i in range(n):
        cat = str(rng.choice(list(CATALOG)))
        prod, price = CATALOG[cat][rng.integers(0, 4)]
        city = str(rng.choice(list(CITIES)))
        rows.append({
            "transaction_id": f"T{i+1:05d}", "order_date": dates[i].strftime("%Y-%m-%d"),
            "customer_id": f"C{cust[i]:04d}", "customer_name": f"Customer {cust[i]}",
            "city": city, "region": CITIES[city],
            "channel": str(rng.choice(["Store", "Online"], p=[0.6, 0.4])),
            "category": cat, "product": prod, "quantity": int(rng.integers(1, 5)),
            "unit_price": round(price * rng.uniform(0.9, 1.1), 2),
            "discount_pct": float(rng.choice([0, 0, 5, 10, 20])),
        })
    df = pd.DataFrame(rows)
    # ---- inject data-quality problems ----
    df = pd.concat([df, df.sample(60, random_state=1)])                      # duplicates
    df.loc[df.sample(40, random_state=2).index, "customer_id"] = np.nan      # missing customer
    idx = df.sample(30, random_state=3).index
    df.loc[idx, "category"] = df.loc[idx, "category"].str.upper()            # inconsistent text
    df.loc[df.sample(25, random_state=4).index, "city"] = " karachi "       # whitespace/case
    df.loc[df.sample(10, random_state=5).index, "quantity"] = -1             # invalid qty
    df.loc[df.sample(8, random_state=6).index, "order_date"] = "not-a-date"  # bad date
    return df.sample(frac=1, random_state=7).reset_index(drop=True)

if __name__ == "__main__":
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    for old in Path("data/raw").glob("*.csv"): old.unlink()
    df = generate()
    yr = df["order_date"].str[:4].where(df["order_date"].str[:4].isin(["2024", "2025"]), "2025")
    for y, part in df.groupby(yr):
        part.to_csv(f"data/raw/sales_{y}.csv", index=False); print("Wrote", f"data/raw/sales_{y}.csv", len(part), "rows")
