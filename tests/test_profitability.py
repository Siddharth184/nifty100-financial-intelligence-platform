"""
Unit tests for Profitability Ratios Engine (Day 08).
"""

import pytest
import numpy as np
from src.analytics.profitability import (
    calculate_npm, calculate_opm, calculate_roe,
    calculate_roce, calculate_roa, compute_profitability_kpis
)

class TestProfitabilityRatios:
    def test_npm_standard(self):
        assert calculate_npm(150, 1000) == 15.0

    def test_npm_zero_sales(self):
        assert calculate_npm(150, 0) is None

    def test_opm_standard(self):
        assert calculate_opm(200, 1000) == 20.0

    def test_roe_standard(self):
        assert calculate_roe(150, 1000) == 15.0

    def test_roe_negative_equity(self):
        # Negative equity should return None to avoid fake positive ROE
        assert calculate_roe(-50, -200) is None
        assert calculate_roe(50, -200) is None

    def test_roce_standard(self):
        assert calculate_roce(200, 1000, 200, is_financial=False) == 25.0

    def test_roce_financial_sector_suppression(self):
        # ROCE is suppressed for Financials/Banks
        assert calculate_roce(200, 1000, 200, is_financial=True) is None

    def test_roa_standard(self):
        assert calculate_roa(100, 1000) == 10.0

    def test_compute_profitability_kpis_dict(self):
        row = {
            "sales": 1000,
            "net_profit": 150,
            "operating_profit": 200,
            "total_equity": 1000,
            "total_assets": 1200
        }
        res = compute_profitability_kpis(row)
        assert res["npm"] == 15.0
        assert res["opm"] == 20.0
        assert res["roe"] == 15.0
        assert res["roa"] == 12.5
