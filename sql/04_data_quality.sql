-- sql/04_data_quality.sql

-- Quick high-level counts
SELECT 'row_count_fact' AS metric, COUNT(*) AS value FROM fact_invoice_line;

SELECT 'min_date' AS metric, MIN(date_key) AS value FROM fact_invoice_line;
SELECT 'max_date' AS metric, MAX(date_key) AS value FROM fact_invoice_line;

-- Row-quality checks (one row per metric)
WITH q AS (
  SELECT 'negative_revenue'      AS metric, COUNT(*) AS value FROM fact_invoice_line WHERE line_revenue < 0
  UNION ALL SELECT 'qty_null_or_zero',            COUNT(*) FROM fact_invoice_line WHERE quantity IS NULL OR quantity = 0
  UNION ALL SELECT 'unitprice_null_or_le0',       COUNT(*) FROM fact_invoice_line WHERE unit_price IS NULL OR unit_price <= 0
  UNION ALL SELECT 'returns_lines',               COUNT(*) FROM fact_invoice_line WHERE quantity < 0 OR invoice_no LIKE 'C%'
  UNION ALL SELECT 'null_customer_id',            COUNT(*) FROM fact_invoice_line WHERE customer_id IS NULL OR TRIM(customer_id) = ''
  UNION ALL SELECT 'null_product_id',             COUNT(*) FROM fact_invoice_line WHERE product_id  IS NULL OR TRIM(product_id)  = ''
)
SELECT * FROM q;

-- Orphan fact rows (keys not in dims)
SELECT 'orphan_customer_dim' AS metric, COUNT(*) AS value
FROM fact_invoice_line f
LEFT JOIN dim_customer d ON d.customer_id = f.customer_id
WHERE d.customer_id IS NULL;

SELECT 'orphan_product_dim' AS metric, COUNT(*) AS value
FROM fact_invoice_line f
LEFT JOIN dim_product p ON p.product_id = f.product_id
WHERE p.product_id IS NULL;

SELECT 'orphan_date_dim' AS metric, COUNT(*) AS value
FROM fact_invoice_line f
LEFT JOIN dim_date dd ON dd.date_key = f.date_key
WHERE dd.date_key IS NULL;

-- Totals
SELECT 'total_revenue' AS metric, ROUND(SUM(line_revenue), 2) AS value
FROM fact_invoice_line;
