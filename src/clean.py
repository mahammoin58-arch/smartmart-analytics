"""Load raw CSV(s), validate, de-duplicate and write a clean dataset."""
import glob
import pandas as pd
from pathlib import Path

REQUIRED = ["transaction_id", "order_date", "customer_id", "customer_name", "city", "region",
            "channel", "category", "product", "quantity", "unit_price", "discount_pct"]

def load_raw(pattern="data/raw/*.csv") -> pd.DataFrame:
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No CSV files match {pattern}")
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df[REQUIRED]

def clean(df: pd.DataFrame):
    rep = {"raw_rows": len(df)}
    df = df.copy()
    for c in ["customer_name", "city", "region", "channel", "category", "product"]:
        df[c] = df[c].astype("string").str.strip().str.title()
    rep["exact_duplicates_removed"] = int(df.duplicated().sum())
    df = df.drop_duplicates()
    rep["duplicate_txn_ids_removed"] = int(df.duplicated("transaction_id").sum())
    df = df.drop_duplicates("transaction_id", keep="first")
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    for c in ["quantity", "unit_price", "discount_pct"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    bad = df["order_date"].isna() | ~(df["quantity"] > 0) | ~(df["unit_price"] > 0) \
          | ~df["discount_pct"].between(0, 100)
    rep["invalid_rows_removed"] = int(bad.sum())
    df = df[~bad]
    rep["missing_customer_id"] = int(df["customer_id"].isna().sum())
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN")
    df["customer_name"] = df["customer_name"].fillna("Unknown")
    df["revenue"] = (df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)).round(2)
    rep["clean_rows"] = len(df)
    return df.reset_index(drop=True), rep

if __name__ == "__main__":
    df, rep = clean(load_raw())
    Path("data/clean").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/clean/sales_clean.csv", index=False)
    import json; json.dump(rep, open("data/clean/quality_report.json", "w"), indent=2)
    print(rep)
