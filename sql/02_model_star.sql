-- =========================================================
-- 02_model_star.sql  (run: sqlite3 retail.db ".read sql/02_model_star.sql")
-- Builds a clean staging table, then dims + fact
-- =========================================================

-- 0) Clean staging (no spaces in names)
DROP TABLE IF EXISTS stg_invoice;
CREATE TABLE stg_invoice AS
SELECT
  CAST(Invoice AS TEXT)                  AS invoice_no,
  TRIM(StockCode)                        AS stock_code,
  TRIM(Description)                      AS description,
  CAST(Quantity AS INT)                  AS quantity,
  DATETIME(InvoiceDate)                  AS invoice_dt,
  DATE(InvoiceDate)                      AS invoice_date,   -- handy for grouping by day
  CAST(Price AS REAL)                    AS unit_price,
  COALESCE(CAST("Customer ID" AS TEXT), 'UNKNOWN') AS customer_id,
  TRIM(Country)                          AS country
FROM stg_invoice_raw
WHERE Quantity IS NOT NULL
  AND Price    IS NOT NULL
  AND InvoiceDate IS NOT NULL;

-- 1) Customer dimension
DROP TABLE IF EXISTS dim_customer;
CREATE TABLE dim_customer AS
SELECT
  customer_id,
  COALESCE(NULLIF(TRIM(country), ''), 'UNKNOWN') AS country
FROM stg_invoice
GROUP BY 1, 2;

-- 2) Product dimension
DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product AS
SELECT
  stock_code                       AS product_id,
  MIN(TRIM(description))           AS product_name
FROM stg_invoice
GROUP BY stock_code;

-- 3) Date dimension
DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date AS
SELECT
  invoice_date                                AS date_key,
  CAST(STRFTIME('%Y', invoice_date) AS INT)   AS year,
  CAST(STRFTIME('%m', invoice_date) AS INT)   AS month,
  CAST(STRFTIME('%d', invoice_date) AS INT)   AS day,
  STRFTIME('%Y-%m', invoice_date)             AS year_month
FROM stg_invoice
GROUP BY invoice_date;

-- 4) Fact table
DROP TABLE IF EXISTS fact_invoice_line;
CREATE TABLE fact_invoice_line AS
SELECT
  invoice_date                                 AS date_key,
  customer_id,
  stock_code                                   AS product_id,
  invoice_no,
  quantity,
  unit_price,
  CAST(quantity * unit_price AS REAL)          AS line_revenue
FROM stg_invoice;

-- 5) Helpful indexes
CREATE INDEX IF NOT EXISTS idx_fact_date      ON fact_invoice_line(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_customer  ON fact_invoice_line(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_product   ON fact_invoice_line(product_id);
CREATE INDEX IF NOT EXISTS idx_fact_invoice   ON fact_invoice_line(invoice_no);

-- 6) Quick sanity checks
SELECT 'dim_customer' tbl, COUNT(*) FROM dim_customer
UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL SELECT 'fact_invoice_line', COUNT(*) FROM fact_invoice_line;

SELECT MIN(date_key) AS min_date, MAX(date_key) AS max_date FROM fact_invoice_line;
SELECT ROUND(SUM(line_revenue), 2) AS total_revenue FROM fact_invoice_line;
