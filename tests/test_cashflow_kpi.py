"""
Unit tests for Cash Flow KPIs & Capital Allocation Engine (Day 11).
"""

import pytest
import os
import pandas as pd
from src.analytics.cashflow_kpi import (
    calculate_free_cash_flow, calculate_cfo_quality,
    calculate_capex_intensity, calculate_fcf_conversion,
    classify_capital_allocation, compute_cashflow_kpis,
    generate_capital_allocation_report
)

class TestCashFlowKPIs:
    def test_fcf_standard(self):
        # CFO = 500, CFI = -200 -> FCF = 300
        assert calculate_free_cash_flow(500, -200) == 300.0

    def test_cfo_quality_standard(self):
        # CFO = 150, Net Profit = 100 -> 1.5
        assert calculate_cfo_quality(150, 100) == 1.5

    def test_capex_intensity_standard(self):
        # CFI = -200, Sales = 1000 -> 20%
        assert calculate_capex_intensity(-200, 1000) == 20.0

    def test_fcf_conversion_standard(self):
        # FCF = 300, CFO = 500 -> 60%
        assert calculate_fcf_conversion(300, 500) == 60.0

    def test_classify_capital_allocation_strain(self):
        row = {"operating_cash_flow": 100, "investing_cash_flow": -150, "free_cash_flow": -50}
        assert classify_capital_allocation(row) == "CAPITAL_STRAIN"

    def test_classify_capital_allocation_growth(self):
        row = {"operating_cash_flow": 500, "investing_cash_flow": -300, "free_cash_flow": 200}
        assert classify_capital_allocation(row) == "EXPANSIVE_GROWTH"

    def test_generate_report(self, tmp_path):
        out = str(tmp_path / "capital_alloc.csv")
        data = [{"company_id": "TCS", "year": 2024, "cfo_sign": "+", "cfi_sign": "-", "cff_sign": "-", "pattern_label": "Shareholder Returns"}]
        res_path = generate_capital_allocation_report(data, out)
        assert os.path.exists(res_path)
        df = pd.read_csv(res_path)
        assert len(df) == 1
        assert df["company_id"].iloc[0] == "TCS"
        assert list(df.columns) == ["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "pattern_label"]

    def test_classify_cashflow_patterns_all_eight(self):
        from src.analytics.cashflow_kpi import classify_cashflow_pattern
        
        # (+,-,-) with high CFO/PAT
        assert classify_cashflow_pattern(150, -50, -50, 100)[3] == "Shareholder Returns"
        # (+,-,-) with normal CFO/PAT
        assert classify_cashflow_pattern(50, -50, -50, 100)[3] == "Reinvestor"
        # (+,+,-)
        assert classify_cashflow_pattern(100, 50, -50)[3] == "Liquidating Assets"
        # (-,+,+)
        assert classify_cashflow_pattern(-100, 50, 50)[3] == "Distress Signal"
        # (-,-,+)
        assert classify_cashflow_pattern(-100, -50, 50)[3] == "Growth Funded by Debt"
        # (+,+,+)
        assert classify_cashflow_pattern(100, 50, 50)[3] == "Cash Accumulator"
        # (-,-,-)
        assert classify_cashflow_pattern(-100, -50, -50)[3] == "Pre-Revenue"
        # (+,-,+)
        assert classify_cashflow_pattern(100, -50, 50)[3] == "Mixed"

