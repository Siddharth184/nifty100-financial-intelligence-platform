import sys
import os
import pytest
import pandas as pd

# Ensure project root is in sys.path
sys.path.insert(0, r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform")

from src.screener.engine import ScreenerEngine

def main():
    print("=== STEP 1: Testing ScreenerEngine against SQLite Database ===")
    engine = ScreenerEngine()
    df = engine.load_universe_data()
    print(f"Loaded universe data: {len(df)} rows across {df['company_id'].nunique()} distinct companies.")

    print("\n=== STEP 2: Testing Single Filters ===")
    roe_filtered = engine.apply_filters(df, {"roe_min": 15.0})
    print(f"Filter ROE > 15%: {len(roe_filtered)} companies returned.")

    de_filtered = engine.apply_filters(df, {"de_max": 1.0})
    print(f"Filter D/E < 1.0 (with Financials Exception): {len(de_filtered)} companies returned.")

    fcf_filtered = engine.apply_filters(df, {"fcf_min": 0.0})
    print(f"Filter FCF > 0: {len(fcf_filtered)} companies returned.")

    print("\n=== STEP 3: Testing Special Rules ===")
    # Financials D/E exception check
    fin_in_de_filtered = de_filtered[de_filtered["is_financial_sector"] == 1]
    print(f"Financial sector companies passing D/E < 1.0 filter: {len(fin_in_de_filtered)} (Expected > 0)")

    # Debt free ICR exception check
    icr_filtered = engine.apply_filters(df, {"icr_min": 3.0})
    debt_free_in_icr = icr_filtered[icr_filtered["debt_free_label"] == 1]
    print(f"Debt-free companies passing ICR > 3.0 filter: {len(debt_free_in_icr)} (Expected > 0)")

    print("\n=== STEP 4: Testing Quality Compounder Preset ===")
    qc_res = engine.run_preset("quality_compounder")
    print(f"Quality Compounder preset returned {len(qc_res)} companies.")
    print("Top 5 Results sorted by composite_quality_score descending:")
    top_cols = ["company_id", "company_name", "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr", "revenue_cagr_5yr", "composite_quality_score"]
    disp_cols = [c for c in top_cols if c in qc_res.columns]
    print(qc_res[disp_cols].head(5).to_string())

    print("\n=== STEP 5: Running Pytest Test Suite ===")
    exit_code = pytest.main(["-v", r"d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform\tests"])
    print(f"Pytest exit code: {exit_code} (0 = ALL PASS)")

if __name__ == "__main__":
    main()
