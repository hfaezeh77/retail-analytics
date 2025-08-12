# Retail Analytics (SQLite + SQL + Python + Streamlit)

## Why this project? What did we learn?
This project analyzes retail transactions to understand where revenue comes from, which products drive sales, and how well customers are retained—using a simple, reproducible stack (**SQLite + SQL + Python**).

**Key results** (UCI Online Retail dataset):
- **Revenue trend:** strong seasonality with clear year-end spikes.
- **Geography:** one market dominates; the rest follow a long-tail pattern.
- **Products:** a small set of SKUs drives a disproportionate share of sales (Pareto).
- **Customers (RFM):** many low-frequency/low-monetary buyers; a small loyal core spends more.
- **Cohorts:** retention drops steeply after month 1, then decays gradually.

See visuals in `notebooks/figures/`:
`monthly_revenue.png`, `top_countries.png`, `top_products.png`, `rfm_scatter.png`, `cohort_retention.png`.

---

## Quickstart

**Requirements:** Python 3.10+, `sqlite3`, `pip`

### 1) Create a virtual environment & install deps
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
