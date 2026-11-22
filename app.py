import pandas as pd
import streamlit as st
from src import db
from src.clean import load_raw, clean

st.set_page_config(page_title="SmartMart Analytics", page_icon="🛒", layout="wide")

@st.cache_data(show_spinner="Loading and cleaning data...")
def get_data():
    df, report = clean(load_raw())
    return df, report

@st.cache_resource
def get_con(_df):
    return db.build_db(_df)

try:
    df, report = get_data()
    con = get_con(df)
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

st.title("🛒 SmartMart Sales & Customer Analytics")

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
dmin, dmax = df["order_date"].min().date(), df["order_date"].max().date()
rng = st.sidebar.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
if not (isinstance(rng, tuple) and len(rng) == 2):
    st.info("Select both a start and an end date."); st.stop()
f = {"start": str(rng[0]), "end": str(rng[1])}
for col, label in [("region", "Region"), ("city", "City"), ("category", "Category"), ("channel", "Channel")]:
    f[col] = st.sidebar.multiselect(label, sorted(df[col].dropna().unique()))

k = db.kpis(con, f)
if k["orders"] == 0:
    st.warning("No data for the selected filters."); st.stop()

# ---------- KPI cards ----------
cust = db.customers(con, f); seg = db.segment(cust)
repeat_rate = (seg["orders"] >= 2).mean() * 100 if len(seg) else 0
c = st.columns(5)
c[0].metric("Revenue", f"{k['revenue']:,.0f}")
c[1].metric("Orders", f"{int(k['orders']):,}")
c[2].metric("Customers", f"{int(k['customers']):,}")
c[3].metric("Avg order value", f"{k['aov']:,.2f}")
c[4].metric("Repeat customers", f"{repeat_rate:.1f}%")

tab1, tab2, tab3, tab4 = st.tabs(["Trends", "Products", "Regions", "Customers"])
with tab1:
    grain = st.radio("Granularity", ["Monthly", "Daily"], horizontal=True)
    t = db.monthly(con, f).set_index("year_month") if grain == "Monthly" else db.daily(con, f).set_index("order_date")
    st.line_chart(t["revenue"])
with tab2:
    p = db.by_product(con, f)
    a, b = st.columns(2)
    a.subheader("Top 10 products"); a.bar_chart(p.head(10).set_index("product")["revenue"])
    b.subheader("Bottom 10 products"); b.bar_chart(p.tail(10).set_index("product")["revenue"])
    st.dataframe(p, use_container_width=True)
with tab3:
    r = db.by_region(con, f)
    a, b = st.columns(2)
    a.subheader("By region"); a.bar_chart(r.groupby("region")["revenue"].sum())
    b.subheader("By city"); b.bar_chart(r.set_index("city")["revenue"])
with tab4:
    if seg.empty:
        st.info("No identified customers in this selection.")
    else:
        a, b = st.columns(2)
        a.subheader("New vs repeat"); a.bar_chart(seg["buyer_type"].value_counts())
        b.subheader("Value tiers"); b.bar_chart(seg["value_tier"].value_counts())
        st.subheader("Top 10 customers")
        st.dataframe(seg.sort_values("total_spend", ascending=False).head(10), use_container_width=True)

# ---------- Export + data quality ----------
st.sidebar.divider()
export = db.q(con, "ORDER BY order_date", "SELECT *", f)
st.sidebar.download_button("⬇ Download filtered data (CSV)", export.to_csv(index=False),
                           "smartmart_filtered.csv", "text/csv")
if not seg.empty:
    st.sidebar.download_button("⬇ Download customer segments", seg.to_csv(index=False),
                               "customer_segments.csv", "text/csv")
with st.expander("Data quality report"):
    st.json(report)
