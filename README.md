# SmartMart Sales & Customer Analytics
GitHub + Streamlit Community Cloud, free tier only. Data: synthetic CSV -> pandas cleaning -> in-memory SQLite star schema -> Streamlit.

## Run locally
    pip install -r requirements.txt
    python src/generate_data.py      # creates data/raw/sales_raw.csv
    python -m src.clean              # creates data/clean/sales_clean.csv + prints quality report
    python -m pytest -q tests        # validation + KPI accuracy tests
    streamlit run app.py

## KPI definitions
- Revenue = quantity x unit_price x (1 - discount_pct/100)
- Orders = distinct transaction_id
- Customers = distinct customer_id (excluding UNKNOWN)
- AOV = Revenue / Orders
- Repeat customer = customer with >= 2 orders in the filtered period
- VIP = top 20% of customers by total spend (in the filtered period)

## Deploy
share.streamlit.io -> New app -> repo, branch main, main file app.py -> Deploy.
