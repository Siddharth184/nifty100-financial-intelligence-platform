import sqlite3
import sys
import os
import pandas as pd
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform")

DB_PATH = r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform\db\nifty100.db"

def main():
    print("=== STEP 1: Running Database Migration & Ratio Engine ===")
    from scratch_migrate_db import main as run_mig
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    rows_count = cursor.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
    cols = [r[1] for r in cursor.fetchall() if False]
    cols = [r[1] for r in cursor.execute("PRAGMA table_info(financial_ratios)").fetchall()]

    required_17 = [
        'net_profit_margin_pct','operating_profit_margin_pct','return_on_equity_pct',
        'debt_to_equity','interest_coverage','asset_turnover','free_cash_flow_cr',
        'capex_cr','earnings_per_share','book_value_per_share','dividend_payout_ratio_pct',
        'total_debt_cr','cash_from_operations_cr','revenue_cagr_5yr','pat_cagr_5yr',
        'eps_cagr_5yr','composite_quality_score'
    ]

    present_17 = [x for x in required_17 if x in cols]
    icr_present = 'icr_label' in cols
    debt_free_present = 'debt_free_label' in cols

    # Check duplicate (company_id, year) records
    dup_count = cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT company_id, year, COUNT(*) 
            FROM financial_ratios 
            GROUP BY company_id, year 
            HAVING COUNT(*) > 1
        )
    """).fetchone()[0]

    # Check Foreign Key integrity
    fk_violations = cursor.execute("PRAGMA foreign_key_check").fetchall()

    print("\n=== VERIFICATION METRICS ===")
    print(f"Total rows in financial_ratios: {rows_count}")
    print(f"Required KPI columns present: {len(present_17)} / 17")
    print(f"icr_label present: {icr_present}")
    print(f"debt_free_label preserved: {debt_free_present}")
    print(f"Duplicate records check: {dup_count} (PASS if 0)")
    print(f"Foreign Key check: {len(fk_violations)} violations (PASS if 0)")

    print("\n=== STEP 2: Running Unit Test Suite ===")
    test_path = r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform\tests"
    exit_code = pytest.main(["-v", test_path])
    print(f"Pytest exit code: {exit_code} (0 = ALL PASS)")

    conn.close()

if __name__ == "__main__":
    main()
