# Retail Analytics (SQLite + SQL + Python + Streamlit)
Why this project? What did we learn?
This project aims to understand where revenue comes from, which products drive sales, and how well customers are retained—using a simple, reproducible stack (SQLite + SQL + Python).

Key results (from the UCI Online Retail dataset):

Revenue trend: strong seasonality; clear spikes near year-end.

Geography: one market dominates revenue; a handful of countries contribute the rest (classic long-tail).

Products: a small set of SKUs account for a disproportionate share of sales (Pareto pattern).

Customers (RFM): most customers are low-frequency / low-monetary; a small core buys frequently and spends more.

Cohorts: retention drops steeply after the first month; subsequent months decay more gradually.

See the saved visuals in notebooks/figures/:

monthly_revenue.png • top_countries.png • top_products.png • rfm_scatter.png • cohort_retention.png

Quickstart
Requirements: Python 3.10+, sqlite3, pip

Create a virtual environment & install deps

bash
Copy
Edit
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
Add data
Place the UCI Online Retail file at: data/online_retail.xlsx
(If your file/columns differ, adjust sql/01_load_staging.py accordingly.)

Build the SQLite database

bash
Copy
Edit
python sql/01_load_staging.py
sqlite3 retail.db < sql/02_model_star.sql
sqlite3 retail.db < sql/03_analysis.sql
(Optional) Create figures or explore in the notebook
Open notebooks/01_analysis.ipynb or run:

bash
Copy
Edit
python notebooks/01_analysis.ipynb   # run in Jupyter/VS Code
Run the dashboard

bash
Copy
Edit
streamlit run app.py
Project structure
bash
Copy
Edit
retail-analytics/
├─ app.py                        # Streamlit app (KPIs + charts)
├─ retail.db                     # SQLite DB (created after steps above)
├─ notebooks/
│  ├─ 01_analysis.ipynb          # EDA & chart generation
│  └─ figures/                   # Saved figures (PNG)
├─ sql/
│  ├─ 01_load_staging.py         # Load raw Excel/CSV → SQLite staging
│  ├─ 02_model_star.sql          # Build star schema (dims + fact)
│  ├─ 03_analysis.sql            # Analysis views (KPIs, RFM, cohorts)
│  ├─ 04_data_quality.sql        # Basic data checks (optional)
│  └─ 99_indexes.sql             # Helpful indexes (optional)
├─ data/
│  └─ online_retail.xlsx         # (you supply this file)
├─ requirements.txt
└─ README.md
Data source: UCI Machine Learning Repository — Online Retail.
(You can use the 2010–2011 Excel file commonly distributed for this dataset.)

Reproduce & extend
Swap in your own retail CSV/XLSX by updating sql/01_load_staging.py.

Add metrics: AOV, returns rate, LTV approximations, weekly seasonality.

Extend the Streamlit app with filters (date range, country, product).
