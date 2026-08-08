import sqlite3
import sys
import shutil

# Ensure project root is in sys.path
sys.path.insert(0, r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform")

DB_PATH = r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform\db\nifty100.db"
BACKUP_PATH = r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform\db\nifty100_backup.db"

# Step 1: Backup database
shutil.copyfile(DB_PATH, BACKUP_PATH)
print(f"Backed up database to {BACKUP_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Record before count & schema
rows_before = cursor.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
cols_before = [r[1] for r in cursor.execute("PRAGMA table_info(financial_ratios)").fetchall()]
print(f"Rows before migration: {rows_before}")
print(f"Columns before migration: {len(cols_before)} columns")

cols_to_add = {
    "net_profit_margin_pct": "REAL",
    "operating_profit_margin_pct": "REAL",
    "return_on_equity_pct": "REAL",
    "free_cash_flow_cr": "REAL",
    "capex_cr": "REAL",
    "earnings_per_share": "REAL",
    "book_value_per_share": "REAL",
    "dividend_payout_ratio_pct": "REAL",
    "total_debt_cr": "REAL",
    "cash_from_operations_cr": "REAL",
    "revenue_cagr_5yr": "REAL",
    "pat_cagr_5yr": "REAL",
    "eps_cagr_5yr": "REAL",
    "composite_quality_score": "REAL",
    "icr_label": "TEXT"
}

added = []
for col, col_type in cols_to_add.items():
    if col not in cols_before:
        cursor.execute(f"ALTER TABLE financial_ratios ADD COLUMN {col} {col_type}")
        added.append(col)

conn.commit()
print(f"Safe migration added {len(added)} columns: {added}")

# Step 2: Run Ratio Engine to populate columns
from src.analytics.ratio_engine import run_ratio_engine
engine_ok = run_ratio_engine(DB_PATH)
print(f"Ratio Engine execution status: {engine_ok}")

# Step 3: Verification Checks
rows_after = cursor.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
cols_after = [r[1] for r in cursor.execute("PRAGMA table_info(financial_ratios)").fetchall()]

print(f"\n=== MIGRATION VERIFICATION ===")
print(f"Rows before vs after: {rows_before} vs {rows_after} (Difference: {rows_after - rows_before})")
print(f"Columns before vs after: {len(cols_before)} vs {len(cols_after)}")

required_17 = [
    'net_profit_margin_pct','operating_profit_margin_pct','return_on_equity_pct',
    'debt_to_equity','interest_coverage','asset_turnover','free_cash_flow_cr',
    'capex_cr','earnings_per_share','book_value_per_share','dividend_payout_ratio_pct',
    'total_debt_cr','cash_from_operations_cr','revenue_cagr_5yr','pat_cagr_5yr',
    'eps_cagr_5yr','composite_quality_score'
]

present_17 = [x for x in required_17 if x in cols_after]
print(f"Required 17 KPI Columns present: {len(present_17)} / 17")
print(f"icr_label present: {'icr_label' in cols_after}")
print(f"debt_free_label preserved: {'debt_free_label' in cols_after}")

# Check duplicate (company_id, year) records
dup_count = cursor.execute("""
    SELECT COUNT(*) FROM (
        SELECT company_id, year, COUNT(*) 
        FROM financial_ratios 
        GROUP BY company_id, year 
        HAVING COUNT(*) > 1
    )
""").fetchone()[0]
print(f"Duplicate (company_id, year) records: {dup_count} (Expected 0)")

# Check Foreign Key integrity
fk_violations = cursor.execute("PRAGMA foreign_key_check").fetchall()
print(f"Foreign key violations: {len(fk_violations)} (Expected 0)")

conn.close()
