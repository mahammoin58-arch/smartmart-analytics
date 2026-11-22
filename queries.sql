-- Total KPIs
SELECT SUM(revenue) AS revenue, COUNT(DISTINCT transaction_id) AS orders,
       SUM(revenue) / COUNT(DISTINCT transaction_id) AS aov, SUM(quantity) AS units
FROM v_sales;

-- Monthly trend
SELECT year_month AS month, SUM(revenue) AS revenue
FROM v_sales GROUP BY year_month ORDER BY year_month;

-- Top 10 products
SELECT product, SUM(revenue) AS revenue FROM v_sales
GROUP BY product ORDER BY revenue DESC LIMIT 10;

-- Revenue by region
SELECT region, SUM(revenue) AS revenue FROM v_sales GROUP BY region ORDER BY revenue DESC;

-- New vs repeat customers
SELECT CASE WHEN n = 1 THEN 'New' ELSE 'Repeat' END AS buyer_type, COUNT(*) AS customers
FROM (SELECT customer_id, COUNT(DISTINCT transaction_id) AS n FROM v_sales
      WHERE customer_id != 'UNKNOWN' GROUP BY customer_id)
GROUP BY buyer_type;
