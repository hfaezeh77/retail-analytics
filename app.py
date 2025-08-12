# app.py
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
import altair as alt
import streamlit as st

# ---- Paths ----
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "retail.db"

# ---- Streamlit page config ----
st.set_page_config(page_title="Retail Analytics", layout="wide")

# ---- Helpers ----
@st.cache_resource
def get_connection(db_path=DB_PATH):
    return sqlite3.connect(db_path)

@st.cache_data(ttl=300)
def get_df(sql: str, params: tuple = ()):
    con = get_connection()
    return pd.read_sql_query(sql, con, params=params)

def in_clause(col: str, values: list[str]) -> tuple[str, list]:
    """Builds a dynamic IN (...) clause and params."""
    if not values:
        return "", []
    placeholders = ",".join(["?"] * len(values))
    return f" AND {col} IN ({placeholders})", list(values)

# ---- Load filter options from DB ----
st.title("🛒 Retail Analytics Dashboard")

if not DB_PATH.exists():
    st.error(f"Database not found at: {DB_PATH}")
    st.stop()

# date range from dim_date
date_minmax = get_df("""
    SELECT MIN(date_key) AS min_date, MAX(date_key) AS max_date
    FROM dim_date
""")
min_date = pd.to_datetime(date_minmax.at[0, "min_date"])
max_date = pd.to_datetime(date_minmax.at[0, "max_date"])

# countries
countries = get_df("SELECT DISTINCT country FROM dim_customer ORDER BY country")
country_list = countries["country"].dropna().tolist()

# ---- Sidebar filters ----
with st.sidebar:
    st.header("Filters")
    date_range = st.date_input(
        "Date range", value=(min_date.date(), max_date.date()),
        min_value=min_date.date(), max_value=max_date.date()
    )
    selected_countries = st.multiselect(
        "Countries (blank = all)",
        options=country_list,
        default=[],
    )
start_date, end_date = date_range

country_sql, country_params = in_clause("c.country", selected_countries)

# ---- KPI queries ----
# Total revenue & AOV
kpi_rev_aov = get_df(f"""
WITH base AS (
  SELECT f.invoice_no, f.line_revenue
  FROM fact_invoice_line f
  JOIN dim_date d ON d.date_key = f.date_key
  JOIN dim_customer c ON c.customer_id = f.customer_id
  WHERE d.date_key BETWEEN DATE(?) AND DATE(?)
  {country_sql}
)
SELECT
  ROUND(SUM(line_revenue), 2) AS revenue,
  ROUND(SUM(line_revenue) * 1.0 / COUNT(DISTINCT invoice_no), 2) AS aov
FROM base;
""", params=(str(start_date), str(end_date), *country_params))

# Repeat purchase rate
kpi_repeat = get_df(f"""
WITH base AS (
  SELECT f.customer_id, f.invoice_no
  FROM fact_invoice_line f
  JOIN dim_date d ON d.date_key = f.date_key
  JOIN dim_customer c ON c.customer_id = f.customer_id
  WHERE d.date_key BETWEEN DATE(?) AND DATE(?)
  {country_sql}
  GROUP BY f.customer_id, f.invoice_no
),
per_customer AS (
  SELECT customer_id, COUNT(*) AS orders
  FROM base GROUP BY customer_id
)
SELECT
  ROUND(100.0 * SUM(CASE WHEN orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_rate_pct
FROM per_customer;
""", params=(str(start_date), str(end_date), *country_params))

# Render KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Revenue", f"{kpi_rev_aov.at[0,'revenue'] or 0:,.2f}")
c2.metric("AOV", f"{kpi_rev_aov.at[0,'aov'] or 0:,.2f}")
c3.metric("Repeat Rate", f"{kpi_repeat.at[0,'repeat_rate_pct'] or 0:.2f}%")

st.markdown("---")

# ---- Monthly Revenue ----
monthly = get_df(f"""
SELECT d.year_month, SUM(f.line_revenue) AS revenue
FROM fact_invoice_line f
JOIN dim_date d ON d.date_key = f.date_key
JOIN dim_customer c ON c.customer_id = f.customer_id
WHERE d.date_key BETWEEN DATE(?) AND DATE(?)
{country_sql}
GROUP BY d.year_month
ORDER BY d.year_month;
""", params=(str(start_date), str(end_date), *country_params))

if not monthly.empty:
    monthly["year_month"] = pd.to_datetime(monthly["year_month"], format="%Y-%m")
    line = alt.Chart(monthly).mark_line(point=True).encode(
        x=alt.X("year_month:T", title="Month"),
        y=alt.Y("revenue:Q", title="Revenue"),
        tooltip=["year_month:T", alt.Tooltip("revenue:Q", format=",.2f")]
    ).properties(title="Monthly Revenue")
    st.altair_chart(line, use_container_width=True)
else:
    st.info("No monthly data for current filters.")

# ---- Two columns: Top Countries / Top Products ----
col1, col2 = st.columns(2)

top_countries = get_df(f"""
SELECT c.country, ROUND(SUM(f.line_revenue),2) AS revenue
FROM fact_invoice_line f
JOIN dim_date d ON d.date_key = f.date_key
JOIN dim_customer c ON c.customer_id = f.customer_id
WHERE d.date_key BETWEEN DATE(?) AND DATE(?)
{country_sql}
GROUP BY c.country
ORDER BY revenue DESC
LIMIT 10;
""", params=(str(start_date), str(end_date), *country_params))

if not top_countries.empty:
    bar_c = alt.Chart(top_countries).mark_bar().encode(
        x=alt.X("revenue:Q", title="Revenue"),
        y=alt.Y("country:N", sort="-x", title="")
    ).properties(title="Top Countries by Revenue")
    col1.altair_chart(bar_c, use_container_width=True)
else:
    col1.info("No country breakdown for current filters.")

top_products = get_df(f"""
SELECT p.product_name, ROUND(SUM(f.line_revenue),2) AS revenue
FROM fact_invoice_line f
JOIN dim_date d ON d.date_key = f.date_key
JOIN dim_product p ON p.product_id = f.product_id
JOIN dim_customer c ON c.customer_id = f.customer_id
WHERE d.date_key BETWEEN DATE(?) AND DATE(?)
{country_sql}
GROUP BY p.product_name
ORDER BY revenue DESC
LIMIT 10;
""", params=(str(start_date), str(end_date), *country_params))

if not top_products.empty:
    bar_p = alt.Chart(top_products).mark_bar().encode(
        x=alt.X("revenue:Q", title="Revenue"),
        y=alt.Y("product_name:N", sort="-x", title="")
    ).properties(title="Top Products by Revenue")
    col2.altair_chart(bar_p, use_container_width=True)
else:
    col2.info("No product breakdown for current filters.")

st.markdown("---")

# ---- RFM (within selected range; recency as days since last purchase up to end_date) ----
rfm = get_df(f"""
WITH base AS (
  SELECT f.customer_id, f.invoice_no, f.line_revenue, f.date_key, c.country
  FROM fact_invoice_line f
  JOIN dim_date d ON d.date_key = f.date_key
  JOIN dim_customer c ON c.customer_id = f.customer_id
  WHERE d.date_key BETWEEN DATE(?) AND DATE(?)
  {country_sql}
),
agg AS (
  SELECT
    customer_id,
    MAX(date_key) AS last_date,
    COUNT(DISTINCT invoice_no) AS frequency,
    SUM(line_revenue) AS monetary
  FROM base
  GROUP BY customer_id
)
SELECT
  customer_id,
  CAST(julianday(?) - julianday(last_date) AS INT) AS recency_days,
  frequency,
  monetary
FROM agg
ORDER BY monetary DESC
LIMIT 2000;
""", params=(str(start_date), str(end_date), *country_params, str(end_date)))

if not rfm.empty:
    scatter = alt.Chart(rfm).mark_circle(opacity=0.6).encode(
        x=alt.X("recency_days:Q", title="Recency (days since last order)"),
        y=alt.Y("monetary:Q", title="Monetary"),
        size=alt.Size("frequency:Q", title="Frequency", legend=None),
        tooltip=["customer_id:N", "recency_days:Q", "frequency:Q", alt.Tooltip("monetary:Q", format=",.2f")]
    ).properties(title="RFM — Monetary vs Recency (size = Frequency)")
    st.altair_chart(scatter, use_container_width=True)
else:
    st.info("No RFM data for current filters.")

st.markdown("---")

# ---- Cohort Retention (cohorts within selected date range) ----
cohort = get_df(f"""
WITH first_order AS (
  SELECT customer_id, MIN(STRFTIME('%Y-%m', date_key)) AS cohort
  FROM fact_invoice_line
  GROUP BY customer_id
),
base AS (
  SELECT
    f.customer_id,
    STRFTIME('%Y-%m', f.date_key) AS ym,
    fo.cohort
  FROM fact_invoice_line f
  JOIN first_order fo USING (customer_id)
  JOIN dim_date d ON d.date_key = f.date_key
  JOIN dim_customer c ON c.customer_id = f.customer_id
  WHERE d.date_key BETWEEN DATE(?) AND DATE(?)
  {country_sql}
),
counted AS (
  SELECT
    cohort,
    ((CAST(substr(ym,1,4) AS INT) - CAST(substr(cohort,1,4) AS INT)) * 12
      + (CAST(substr(ym,6,2) AS INT) - CAST(substr(cohort,6,2) AS INT))) AS period,
    COUNT(DISTINCT customer_id) AS customers
  FROM base
  GROUP BY cohort, period
),
cohort_size AS (
  SELECT cohort, customers AS size
  FROM counted WHERE period = 0
)
SELECT c.cohort, c.period, 1.0 * c.customers / cs.size AS retention
FROM counted c
JOIN cohort_size cs USING (cohort)
WHERE c.period BETWEEN 0 AND 11
ORDER BY c.cohort, c.period;
""", params=(str(start_date), str(end_date), *country_params))

if not cohort.empty:
    heat = alt.Chart(cohort).mark_rect().encode(
        x=alt.X("period:O", title="Months since first order"),
        y=alt.Y("cohort:N", title="Cohort (YYYY-MM)"),
        color=alt.Color("retention:Q", scale=alt.Scale(scheme="blues"), title="Retention"),
        tooltip=["cohort:N", "period:Q", alt.Tooltip("retention:Q", format=".0%")]
    ).properties(title="Cohort Retention (0–11 months)")
    st.altair_chart(heat, use_container_width=True)
else:
    st.info("No cohort data for current filters.")

st.caption("Data source: Online Retail (UCI). SQLite-backed | Built with Streamlit.")
