"""
Unit tests for Leverage & Efficiency Ratios Engine (Day 09).
"""

import pytest
from src.analytics.leverage_efficiency import (
    calculate_debt_to_equity, calculate_interest_coverage,
    calculate_net_debt, calculate_asset_turnover, compute_leverage_kpis
)

class TestLeverageEfficiencyRatios:
    def test_de_ratio_standard(self):
        assert calculate_debt_to_equity(500, 1000) == 0.5

    def test_de_ratio_zero_equity(self):
        assert calculate_debt_to_equity(500, 0) is None

    def test_icr_standard(self):
        assert calculate_interest_coverage(300, 50) == 6.0

    def test_icr_zero_interest(self):
        assert calculate_interest_coverage(300, 0) is None

    def test_net_debt_standard(self):
        assert calculate_net_debt(500, 100) == 400.0

    def test_asset_turnover_standard(self):
        assert calculate_asset_turnover(2000, 1000) == 2.0

    def test_leverage_flags_non_financial(self):
        row = {
            "borrowings": 2500,
            "total_equity": 1000,
            "operating_profit": 100,
            "interest": 100,
            "sales": 1000,
            "total_assets": 2000
        }
        res = compute_leverage_kpis(row, is_financial=False)
        assert res["debt_to_equity"] == 2.5
        assert res["high_leverage_flag"] is True
        assert res["debt_free_label"] is False
        assert res["icr_warning"] is True
        assert res["icr_label"] == "HIGH_RISK"

    def test_leverage_flags_financial_suppression(self):
        row = {
            "borrowings": 2500,
            "total_equity": 1000,
            "operating_profit": 100,
            "interest": 100,
            "sales": 1000,
            "total_assets": 2000
        }
        res = compute_leverage_kpis(row, is_financial=True)
        # Financial companies suppress high leverage & ICR warnings
        assert res["high_leverage_flag"] is False
        assert res["icr_warning"] is False
        assert res["icr_label"] == "FINANCIAL_SECTOR"

