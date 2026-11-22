from src import db
from src.clean import load_raw, clean

df, rep = clean(load_raw())
con = db.build_db(df)
F = {"start": "2024-01-01", "end": "2025-12-31"}

def test_no_duplicates_and_no_nulls():
    assert not df["transaction_id"].duplicated().any()
    assert df["order_date"].notna().all() and (df["quantity"] > 0).all()

def test_total_revenue_matches_pandas():
    assert abs(db.kpis(con, F)["revenue"] - df["revenue"].sum()) < 0.01

def test_filter_matches_pandas():
    f = {**F, "region": ["South"], "category": ["Electronics"]}
    exp = df[(df.region == "South") & (df.category == "Electronics")]["revenue"].sum()
    assert abs(db.kpis(con, f)["revenue"] - exp) < 0.01

def test_monthly_sums_to_total():
    assert abs(db.monthly(con, F)["revenue"].sum() - df["revenue"].sum()) < 0.01

def test_empty_filter_returns_zero():
    assert db.kpis(con, {**F, "start": "2030-01-01", "end": "2030-12-31"})["orders"] == 0

def test_segments_cover_all_known_customers():
    seg = db.segment(db.customers(con, F))
    assert len(seg) == df[df.customer_id != "UNKNOWN"].customer_id.nunique()
