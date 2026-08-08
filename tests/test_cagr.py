"""
Unit tests for CAGR Engine (Day 10).
"""

import pytest
import pandas as pd
from src.analytics.cagr import calculate_cagr, compute_cagr_series, compute_all_cagr_metrics

class TestCAGREngine:
    def test_cagr_positive_to_positive(self):
        # 100 to 200 over 3 years: ((200/100)^(1/3)) - 1 = 25.99%
        val, status = calculate_cagr(100, 200, 3)
        assert val == 25.99
        assert status == "VALID"

    def test_cagr_zero_growth(self):
        val, status = calculate_cagr(100, 100, 5)
        assert val == 0.0
        assert status == "VALID"

    def test_cagr_positive_to_negative(self):
        val, status = calculate_cagr(100, -50, 3)
        assert val is None
        assert status == "TURNAROUND_LOSS"

    def test_cagr_negative_to_positive(self):
        val, status = calculate_cagr(-50, 100, 3)
        assert val is None
        assert status == "TURNAROUND_PROFIT"

    def test_cagr_negative_to_negative(self):
        val, status = calculate_cagr(-50, -100, 3)
        assert val is None
        assert status == "CONTINUOUS_LOSS"

    def test_cagr_zero_base(self):
        val, status = calculate_cagr(0, 100, 3)
        assert val is None
        assert status == "ZERO_BASE"

    def test_compute_cagr_series_insufficient_data(self):
        df = pd.DataFrame([
            {"year": 2023, "sales": 100},
            {"year": 2024, "sales": 120}
        ])
        res = compute_cagr_series(df, "sales", 3)
        assert res["value"] is None
        assert res["status"] == "INSUFFICIENT_HISTORY"

    def test_compute_all_cagr_metrics_success(self):
        df = pd.DataFrame([
            {"year": 2014, "sales": 100, "net_profit": 10, "eps": 1.0},
            {"year": 2019, "sales": 150, "net_profit": 15, "eps": 1.5},
            {"year": 2021, "sales": 180, "net_profit": 18, "eps": 1.8},
            {"year": 2024, "sales": 200, "net_profit": 20, "eps": 2.0}
        ])
        res = compute_all_cagr_metrics(df)
        assert res["cagr_sales_10yr"] == 7.18
        assert res["cagr_sales_10yr_status"] == "VALID"
