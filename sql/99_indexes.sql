-- sql/99_indexes.sql
CREATE INDEX IF NOT EXISTS idx_fact_date     ON fact_invoice_line(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_cust     ON fact_invoice_line(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_prod     ON fact_invoice_line(product_id);
CREATE INDEX IF NOT EXISTS idx_dim_date      ON dim_date(date_key);
CREATE INDEX IF NOT EXISTS idx_dim_customer  ON dim_customer(customer_id);
CREATE INDEX IF NOT EXISTS idx_dim_product   ON dim_product(product_id);
