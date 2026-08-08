import os
import sys
import pandas as pd
import sqlite3

# Ensure project root is in sys.path
sys.path.insert(0, r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform")

from src.etl.loader import load_excel, load_all_datasets
from src.etl.normaliser import normalize_ticker, normalize_year
from src.utils.helpers import normalize_dataframe
from src.db.loader import transform_df_for_schema

DATA_DIR = r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform\data\raw"
DB_PATH = r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform\db\nifty100.db"

def trace_file(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        print(f"File {filename} missing!")
        return

    # 1. Raw Excel row count (without headers)
    excel_file = pd.ExcelFile(filepath)
    df_raw_no_header = pd.read_excel(filepath, header=None)
    
    # 2. Loader (header=1 for core, header=0 for supporting)
    df_loaded = load_excel(filepath)

    # 3. Normalizer
    df_norm = normalize_dataframe(df_loaded)
    if 'ticker' in df_norm.columns:
        df_norm['ticker'] = df_norm['ticker'].apply(normalize_ticker)
    if 'year' in df_norm.columns:
        df_norm['year'] = df_norm['year'].apply(normalize_year)
        df_norm_valid_year = df_norm.dropna(subset=['year'])
    else:
        df_norm_valid_year = df_norm

    if 'company_id' in df_norm_valid_year.columns and 'year' in df_norm_valid_year.columns:
        df_norm_dedup = df_norm_valid_year.drop_duplicates(subset=['company_id', 'year'])
    else:
        df_norm_dedup = df_norm_valid_year

    print(f"=== TRACE FOR {filename} ===")
    print(f"1. Total Excel Sheet Rows (header=None): {len(df_raw_no_header)}")
    print(f"2. Loaded DF (header setting): {len(df_loaded)}")
    print(f"3. Normalized DF: {len(df_norm)}")
    print(f"4. Valid Year DF (dropna year): {len(df_norm_valid_year)}")
    print(f"5. Dedup DF (company_id + year): {len(df_norm_dedup)}")

def main():
    for fn in ["companies.xlsx", "profitandloss.xlsx", "balancesheet.xlsx", "cashflow.xlsx", "financial_ratios.xlsx"]:
        trace_file(fn)

if __name__ == "__main__":
    main()
