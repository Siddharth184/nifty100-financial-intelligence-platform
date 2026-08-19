"""
Unit tests for Day 31 Cash Flow Intelligence Module & ATGL QA Inspection.
"""

import pytest
import os
import sqlite3
import pandas as pd
from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow, calculate_cfo_quality, calculate_capex_intensity,
    classify_cashflow_pattern, generate_cashflow_intelligence_report
)

class TestCashFlowIntelligence:
    def test_calculate_free_cash_flow(self):
        fcf = calculate_free_cash_flow(100.0, -30.0)
        assert fcf == 70.0

    def test_calculate_cfo_quality(self):
        q = calculate_cfo_quality(120.0, 100.0)
        assert q == 1.2

    def test_calculate_capex_intensity(self):
        intensity = calculate_capex_intensity(-50.0, 1000.0)
        assert intensity == 5.0

    def test_classify_cashflow_pattern(self):
        cfo_s, cfi_s, cff_s, label = classify_cashflow_pattern(100.0, -40.0, -30.0, 80.0)
        assert (cfo_s, cfi_s, cff_s) == ("+", "-", "-")
        assert label in ["Reinvestor", "Shareholder Returns"]

    def test_generate_cashflow_intelligence_report(self):
        intel_df, distress_df = generate_cashflow_intelligence_report()
        assert not intel_df.empty
        assert "cfo_quality_label" in intel_df.columns
        assert "capex_label" in intel_df.columns
        assert "distress_flag" in intel_df.columns
        assert "deleveraging_flag" in intel_df.columns
        assert "capital_allocation_label" in intel_df.columns

    def test_atgl_data_inspection(self):
        conn = sqlite3.connect("db/nifty100.db")
        df_cf = pd.read_sql_query("SELECT * FROM cashflow WHERE company_id='ATGL'", conn)
        df_pnl = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id='ATGL'", conn)
        df_fr = pd.read_sql_query("SELECT * FROM financial_ratios WHERE company_id='ATGL'", conn)
        conn.close()
        
        print("\n--- ATGL Cashflow Rows ---")
        print(f"Count: {len(df_cf)}")
        if not df_cf.empty:
            print(df_cf.to_string())
            
        print("\n--- ATGL PnL Rows ---")
        print(f"Count: {len(df_pnl)}")
        if not df_pnl.empty:
            print(df_pnl.to_string())

        print("\n--- ATGL Financial Ratios Rows ---")
        print(f"Count: {len(df_fr)}")
        if not df_fr.empty:
            print(df_fr.to_string())
