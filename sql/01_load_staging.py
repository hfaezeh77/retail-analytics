# sql/01_load_staging.py
import pandas as pd
import sqlite3
from pathlib import Path

# Resolve paths relative to project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH   = PROJECT_ROOT / "retail.db"
RAW_PATH  = PROJECT_ROOT / "data" / "online_retail.xlsx"   # .csv if needed
TABLE     = "stg_invoice_raw"

def load_raw_to_sqlite():
    # Read the file (Excel or CSV)
    if RAW_PATH.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(RAW_PATH)
    else:
        df = pd.read_csv(RAW_PATH)

    # Drop obviously broken rows, coerce types
    need_cols = ["Invoice", "StockCode", "InvoiceDate", "Price", "Quantity"]
    df = df.dropna(subset=need_cols)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df = df.dropna(subset=["InvoiceDate"])

    # Normalize text fields
    df["StockCode"] = df["StockCode"].astype(str).str.strip()
    if "Description" in df.columns:
        df["Description"] = df["Description"].astype(str).str.strip()

    # Numeric casting
    df["Quantity"]  = pd.to_numeric(df["Quantity"],  errors="coerce")
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    # Write to SQLite
    con = sqlite3.connect(DB_PATH)
    df.to_sql(TABLE, con, if_exists="replace", index=False)
    con.close()
    print(f"Wrote {len(df):,} rows to {DB_PATH.name}:{TABLE}")

if __name__ == "__main__":
    load_raw_to_sqlite()
