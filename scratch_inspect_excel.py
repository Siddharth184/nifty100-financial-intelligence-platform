import os
import pandas as pd

DATA_DIR = r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform\data\raw"
OUT_FILE = r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform\scratch_excel_info.txt"

files = [
    "companies.xlsx", "profitandloss.xlsx", "balancesheet.xlsx",
    "cashflow.xlsx", "sectors.xlsx", "financial_ratios.xlsx"
]

out = []

for fn in files:
    fp = os.path.join(DATA_DIR, fn)
    if not os.path.exists(fp):
        out.append(f"File {fn} missing!")
        continue

    xl = pd.ExcelFile(fp)
    df_h0 = pd.read_excel(fp, header=0)
    df_h1 = pd.read_excel(fp, header=1)
    df_none = pd.read_excel(fp, header=None)

    out.append(f"=== {fn} ===")
    out.append(f"Total Sheet Rows (header=None): {len(df_none)}")
    out.append(f"header=0 shape: {df_h0.shape}, columns: {list(df_h0.columns[:5])}")
    out.append(f"header=1 shape: {df_h1.shape}, columns: {list(df_h1.columns[:5])}")
    out.append("First 3 rows of header=None:")
    out.append(df_none.iloc[:3, :5].to_string())
    out.append("-" * 50)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("Wrote inspection info to scratch_excel_info.txt")
