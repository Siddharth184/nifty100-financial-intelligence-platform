"""
Sprint 4 Master Verification Script.

Generates valuation outputs and verifies all Sprint 4 deliverables.
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def main():
    print("=" * 60)
    print("  SPRINT 4 — MASTER VERIFICATION SCRIPT")
    print("=" * 60)

    # ── Step 1: Generate Valuation Outputs ────────────────────────────────────
    print("\n--- Step 1: Generating Valuation Outputs ---")
    from src.analytics.valuation import compute_valuation_summary, generate_valuation_outputs
    val_df = compute_valuation_summary()
    generate_valuation_outputs(val_df)
    print(f"  Valuation Summary: {len(val_df)} companies")
    print(f"  Flag Distribution: {val_df['flag'].value_counts().to_dict()}")

    # ── Step 2: Verify Output Files ──────────────────────────────────────────
    print("\n--- Step 2: Verifying Output Files ---")
    required_files = [
        "output/valuation_summary.xlsx",
        "output/valuation_flags.csv",
        "output/screener_output.xlsx",
        "output/peer_comparison.xlsx",
        "src/dashboard/app.py",
        "src/dashboard/utils/db.py",
        "src/analytics/valuation.py",
        "pages/pg_01_home.py",
        "pages/pg_02_profile.py",
        "pages/pg_03_screener.py",
        "pages/pg_04_peers.py",
        "pages/pg_05_trends.py",
        "pages/pg_06_sectors.py",
        "pages/pg_07_capital.py",
        "pages/pg_08_reports.py",
    ]
    all_exist = True
    for f in required_files:
        exists = os.path.exists(f)
        status = "✅" if exists else "❌"
        print(f"  {status} {f}")
        if not exists:
            all_exist = False

    # ── Step 3: Verify Valuation Excel Content ───────────────────────────────
    print("\n--- Step 3: Verifying Valuation Excel Content ---")
    import pandas as pd
    try:
        vdf = pd.read_excel("output/valuation_summary.xlsx")
        print(f"  Rows: {len(vdf)}")
        required_cols = [
            "company_id", "company_name", "sector", "P/E", "P/B",
            "EV/EBITDA", "FCF_yield_pct", "5yr_median_PE",
            "PE_vs_sector_median_pct", "flag"
        ]
        missing_cols = [c for c in required_cols if c not in vdf.columns]
        if missing_cols:
            print(f"  ❌ Missing columns: {missing_cols}")
        else:
            print(f"  ✅ All {len(required_cols)} required columns present")
        print(f"  Unique companies: {vdf['company_id'].nunique()}")
    except Exception as e:
        print(f"  ❌ Error reading valuation_summary.xlsx: {e}")

    # ── Step 4: Verify Valuation Flags CSV ───────────────────────────────────
    print("\n--- Step 4: Verifying Valuation Flags CSV ---")
    try:
        flags_df = pd.read_csv("output/valuation_flags.csv")
        print(f"  Flagged companies: {len(flags_df)}")
        print(f"  Flags: {flags_df['flag'].value_counts().to_dict()}")
    except Exception as e:
        print(f"  ❌ Error reading valuation_flags.csv: {e}")

    # ── Step 5: Database Integrity ───────────────────────────────────────────
    print("\n--- Step 5: Database Integrity Check ---")
    import sqlite3
    conn = sqlite3.connect("db/nifty100.db")
    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    print(f"  FK Violations: {len(fk_violations)} (Expected 0)")
    dup_count = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT company_id, year FROM financial_ratios
            GROUP BY company_id, year HAVING COUNT(*) > 1
        )
    """).fetchone()[0]
    print(f"  Duplicate Records: {dup_count} (Expected 0)")
    conn.close()

    # ── Step 6: Run Existing Tests ───────────────────────────────────────────
    print("\n--- Step 6: Running Existing Test Suite ---")
    import pytest
    exit_code = pytest.main(["-v", "--tb=short", "tests"])
    print(f"  Pytest Exit Code: {exit_code} (0 = ALL PASS)")

    # ── Step 7: Import Verification (Streamlit modules) ──────────────────────
    print("\n--- Step 7: Import Verification ---")
    try:
        from src.dashboard.utils.db import (
            get_companies, get_ratios, get_pl, get_bs, get_cf,
            get_sectors, get_peers, get_valuation
        )
        print("  ✅ src.dashboard.utils.db imports successfully")
    except Exception as e:
        print(f"  ❌ Import error: {e}")

    try:
        from src.analytics.valuation import compute_valuation_summary
        print("  ✅ src.analytics.valuation imports successfully")
    except Exception as e:
        print(f"  ❌ Import error: {e}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  SPRINT 4 VERIFICATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
