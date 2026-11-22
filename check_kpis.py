"""Compare SQL KPIs with independently calculated pandas KPIs."""
import sqlite3, pandas as pd
from src.clean import load_raw, clean

con = sqlite3.connect("data/smartmart.db")
sql = pd.read_sql("SELECT SUM(revenue) AS revenue, COUNT(DISTINCT transaction_id) AS orders, "
                  "SUM(revenue)/COUNT(DISTINCT transaction_id) AS aov, SUM(quantity) AS units FROM v_sales", con)
df, _ = clean(load_raw())
pdk = {"revenue": df.revenue.sum(), "orders": df.transaction_id.nunique(),
       "aov": round(df.revenue.sum() / df.transaction_id.nunique(), 2), "units": int(df.quantity.sum())}
print("--- SQL KPIs ---"); print(sql.to_string())
print("\n--- pandas KPIs (should match) ---"); print(pdk)
print("\n--- Top 5 products ---")
print(pd.read_sql("SELECT product, SUM(revenue) revenue FROM v_sales GROUP BY product ORDER BY revenue DESC LIMIT 5", con).to_string())
print("\n--- Revenue by region ---")
print(pd.read_sql("SELECT region, SUM(revenue) revenue FROM v_sales GROUP BY region ORDER BY revenue DESC", con).to_string())
ok = abs(sql.revenue[0] - pdk["revenue"]) < 0.01 and sql.orders[0] == pdk["orders"] and sql.units[0] == pdk["units"]
print("\nRESULT:", "MATCH" if ok else "MISMATCH")
