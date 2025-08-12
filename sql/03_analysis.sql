-- ================================
-- 03_analysis.sql
-- ================================

-- 0) Helpful sales/returns splits (optional)
DROP VIEW IF EXISTS v_sales;
CREATE VIEW v_sales AS
SELECT * FROM fact_invoice_line
WHERE quantity > 0 AND unit_price > 0;

DROP VIEW IF EXISTS v_returns;
CREATE VIEW v_returns AS
SELECT * FROM fact_invoice_line
WHERE quantity < 0 OR unit_price <= 0;

-- 1) Daily / Monthly revenue
DROP VIEW IF EXISTS v_daily_revenue;
CREATE VIEW v_daily_revenue AS
SELECT date_key, ROUND(SUM(line_revenue),2) AS revenue
FROM fact_invoice_line
GROUP BY date_key
ORDER BY date_key;

DROP VIEW IF EXISTS v_monthly_revenue;
CREATE VIEW v_monthly_revenue AS
SELECT d.year_month, ROUND(SUM(f.line_revenue),2) AS revenue
FROM fact_invoice_line f
JOIN dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month
ORDER BY d.year_month;

-- 2) Top countries / products / customers
DROP VIEW IF EXISTS v_country_revenue;
CREATE VIEW v_country_revenue AS
SELECT COALESCE(c.country,'UNKNOWN') AS country,
       ROUND(SUM(f.line_revenue),2) AS revenue
FROM fact_invoice_line f
JOIN dim_customer c ON c.customer_id = f.customer_id
GROUP BY country
ORDER BY revenue DESC;

DROP VIEW IF EXISTS v_top_products;
CREATE VIEW v_top_products AS
SELECT p.product_id, p.product_name,
       ROUND(SUM(f.line_revenue),2) AS revenue
FROM fact_invoice_line f
JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.product_id, p.product_name
ORDER BY revenue DESC
LIMIT 20;

DROP VIEW IF EXISTS v_top_customers;
CREATE VIEW v_top_customers AS
SELECT c.customer_id, c.country,
       ROUND(SUM(f.line_revenue),2) AS revenue,
       COUNT(DISTINCT f.invoice_no) AS orders
FROM fact_invoice_line f
JOIN dim_customer c ON c.customer_id = f.customer_id
GROUP BY c.customer_id, c.country
ORDER BY revenue DESC
LIMIT 20;

-- 3) RFM (Recency, Frequency, Monetary)
DROP VIEW IF EXISTS v_rfm;
CREATE VIEW v_rfm AS
WITH last_date AS (SELECT MAX(date_key) AS max_date FROM fact_invoice_line),
cust AS (
  SELECT
    customer_id,
    COUNT(DISTINCT invoice_no) AS frequency,
    ROUND(SUM(line_revenue),2) AS monetary,
    MAX(date_key) AS last_order
  FROM fact_invoice_line
  GROUP BY customer_id
)
SELECT
  c.customer_id,
  JULIANDAY(l.max_date) - JULIANDAY(c.last_order) AS recency_days,
  c.frequency,
  c.monetary
FROM cust c CROSS JOIN last_date l
ORDER BY monetary DESC;

-- 4) Cohort retention (monthly, 0–11 months)
DROP VIEW IF EXISTS v_cohort_pairs;
CREATE VIEW v_cohort_pairs AS
WITH firsts AS (
  SELECT customer_id, MIN(d.year_month) AS cohort
  FROM fact_invoice_line f
  JOIN dim_date d ON d.date_key = f.date_key
  GROUP BY customer_id
),
orders AS (
  SELECT f.customer_id, d.year_month AS ym
  FROM fact_invoice_line f
  JOIN dim_date d ON d.date_key = f.date_key
  GROUP BY f.customer_id, d.year_month
)
SELECT
  o.customer_id,
  f.cohort,
  o.ym,
  (CAST(SUBSTR(o.ym,1,4) AS INT)*12 + CAST(SUBSTR(o.ym,6,2) AS INT))
  - (CAST(SUBSTR(f.cohort,1,4) AS INT)*12 + CAST(SUBSTR(f.cohort,6,2) AS INT)) AS period
FROM orders o
JOIN firsts f ON f.customer_id = o.customer_id;

DROP VIEW IF EXISTS v_cohort_sizes;
CREATE VIEW v_cohort_sizes AS
SELECT cohort, COUNT(DISTINCT customer_id) AS cohort_size
FROM v_cohort_pairs
WHERE period = 0
GROUP BY cohort;

DROP VIEW IF EXISTS v_cohort_retention;
CREATE VIEW v_cohort_retention AS
SELECT p.cohort,
       p.period,
       CAST(COUNT(DISTINCT p.customer_id) AS REAL) / s.cohort_size AS retention
FROM v_cohort_pairs p
JOIN v_cohort_sizes s ON s.cohort = p.cohort
WHERE p.period BETWEEN 0 AND 11
GROUP BY p.cohort, p.period
ORDER BY p.cohort, p.period;

-- 5) Product affinity (co-basket pairs)
DROP VIEW IF EXISTS v_product_pairs;
CREATE VIEW v_product_pairs AS
SELECT
  MIN(a.product_id) AS product_a,
  MAX(b.product_id) AS product_b,
  COUNT(DISTINCT a.invoice_no) AS together
FROM fact_invoice_line a
JOIN fact_invoice_line b
  ON a.invoice_no = b.invoice_no AND a.product_id < b.product_id
WHERE a.quantity > 0 AND b.quantity > 0
GROUP BY MIN(a.product_id), MAX(b.product_id)
HAVING together >= 50
ORDER BY together DESC;
