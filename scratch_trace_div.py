import os
import pandas as pd

raw_dir = "data/raw"
for f in os.listdir(raw_dir):
    if f.endswith(".xlsx") or f.endswith(".csv"):
        fp = os.path.join(raw_dir, f)
        try:
            if f.endswith(".xlsx"):
                xl = pd.ExcelFile(fp)
                print(f"File {f} sheets: {xl.sheet_names}")
                df = pd.read_excel(fp, nrows=5)
            else:
                df = pd.read_csv(fp, nrows=5)
            div_cols = [c for c in df.columns if 'div' in str(c).lower() or 'payout' in str(c).lower() or 'yield' in str(c).lower()]
            print(f"  Columns in {f}: {len(df.columns)} total. Dividend related: {div_cols}")
        except Exception as e:
            print(f"  Error reading {f}: {e}")
