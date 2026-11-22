"""In-memory SQLite star schema + KPI queries (no external database needed)."""
import sqlite3
import pandas as pd

def build_db(df: pd.DataFrame, path: str = ":memory:") -> sqlite3.Connection:
    con = sqlite3.connect(path, check_same_thread=False)
    d = df.copy()
    d["order_date"] = d["order_date"].dt.strftime("%Y-%m-%d")
    for c in d.select_dtypes("string").columns:
        d[c] = d[c].astype(object)
    d.to_sql("sales_clean", con, index=False, if_exists="replace")
    con.executescript("""
    DROP VIEW IF EXISTS v_sales; DROP TABLE IF EXISTS dim_customer; DROP TABLE IF EXISTS dim_product; DROP TABLE IF EXISTS dim_date;
    CREATE TABLE dim_customer AS SELECT customer_id, MIN(customer_name) AS customer_name
        FROM sales_clean GROUP BY customer_id;
    CREATE TABLE dim_product AS SELECT DISTINCT product, category FROM sales_clean;
    CREATE TABLE dim_date AS SELECT DISTINCT order_date,
        CAST(strftime('%Y', order_date) AS INT) AS year,
        CAST(strftime('%m', order_date) AS INT) AS month,
        strftime('%Y-%m', order_date) AS year_month
        FROM sales_clean;
    CREATE VIEW v_sales AS
        SELECT s.transaction_id, s.order_date, dd.year_month, dd.year, s.customer_id,
               s.city, s.region, s.channel, s.category, s.product,
               s.quantity, s.revenue
        FROM sales_clean s JOIN dim_date dd USING (order_date);
    """)
    return con

def _where(f: dict):
    clauses, params = ["order_date BETWEEN ? AND ?"], [f["start"], f["end"]]
    for col in ("region", "city", "category", "channel"):
        vals = f.get(col) or []
        if vals:
            clauses.append(f"{col} IN ({','.join('?'*len(vals))})"); params += list(vals)
    return " WHERE " + " AND ".join(clauses), params

def q(con, sql_tail: str, select: str, f: dict) -> pd.DataFrame:
    w, p = _where(f)
    return pd.read_sql_query(f"{select} FROM v_sales{w} {sql_tail}", con, params=p)

def kpis(con, f):
    return q(con, "", """SELECT COALESCE(SUM(revenue),0) revenue,
        COUNT(DISTINCT transaction_id) orders,
        COUNT(DISTINCT CASE WHEN customer_id!='UNKNOWN' THEN customer_id END) customers,
        COALESCE(SUM(revenue)/NULLIF(COUNT(DISTINCT transaction_id),0),0) aov""", f).iloc[0]

def monthly(con, f):    return q(con, "GROUP BY year_month ORDER BY year_month", "SELECT year_month, SUM(revenue) revenue, COUNT(*) orders", f)
def daily(con, f):      return q(con, "GROUP BY order_date ORDER BY order_date", "SELECT order_date, SUM(revenue) revenue", f)
def by_product(con, f): return q(con, "GROUP BY product, category ORDER BY revenue DESC", "SELECT product, category, SUM(quantity) units, SUM(revenue) revenue", f)
def by_region(con, f):  return q(con, "GROUP BY region, city ORDER BY revenue DESC", "SELECT region, city, SUM(revenue) revenue", f)
def customers(con, f):
    return q(con, "GROUP BY customer_id", """SELECT customer_id, COUNT(DISTINCT transaction_id) orders,
        SUM(revenue) total_spend, MIN(order_date) first_order, MAX(order_date) last_order""", f)

def segment(cust: pd.DataFrame) -> pd.DataFrame:
    c = cust[cust.customer_id != "UNKNOWN"].copy()
    if c.empty: return c
    c["buyer_type"] = c["orders"].map(lambda n: "Repeat" if n >= 2 else "New (one-time)")
    top, low = c["total_spend"].quantile(0.8), c["total_spend"].quantile(0.4)
    c["value_tier"] = c["total_spend"].map(lambda s: "VIP (top 20%)" if s >= top else ("Regular" if s >= low else "Low value"))
    return c
