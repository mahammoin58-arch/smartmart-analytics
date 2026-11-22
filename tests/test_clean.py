import pandas as pd, pytest
from src.clean import clean, REQUIRED, load_raw

def _row(**kw):
    r = dict(transaction_id="T1", order_date="2025-01-01", customer_id="C1", customer_name="A", city="Lahore",
             region="Central", channel="Store", category="Grocery", product="Rice", quantity=2, unit_price=100, discount_pct=10)
    r.update(kw); return r

def test_duplicates_removed():
    df, rep = clean(pd.DataFrame([_row(), _row()]))
    assert len(df) == 1 and rep["exact_duplicates_removed"] == 1

def test_invalid_rows_dropped():
    df, rep = clean(pd.DataFrame([_row(), _row(transaction_id="T2", quantity=-1)]))
    assert len(df) == 1 and rep["invalid_rows_removed"] == 1

def test_revenue_formula():
    df, _ = clean(pd.DataFrame([_row()]))
    assert df.revenue[0] == 180

def test_missing_column_raises(tmp_path):
    pd.DataFrame({"a": [1]}).to_csv(tmp_path / "x.csv", index=False)
    with pytest.raises(ValueError):
        load_raw(str(tmp_path / "*.csv"))
