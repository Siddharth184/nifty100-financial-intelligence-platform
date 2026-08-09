"""
Unit tests for Screener Filter Engine (Sprint 3 Day 15).
"""

import pytest
import os
import pandas as pd
from src.screener.engine import ScreenerEngine

@pytest.fixture
def mock_financial_df():
    """Creates a mock DataFrame representing company records for screener testing."""
    return pd.DataFrame([
        {
            "company_id": "TCS",
            "company_name": "Tata Consultancy Services",
            "roe": 45.0,
            "return_on_equity_pct": 45.0,
            "debt_to_equity": 0.05,
            "free_cash_flow": 35000.0,
            "cagr_sales_5yr": 12.0,
            "cagr_pat_5yr": 14.0,
            "opm": 26.0,
            "interest_coverage": 50.0,
            "debt_free_label": 1,
            "is_financial_sector": 0,
            "sales": 240000.0,
            "composite_quality_score": 92.0
        },
        {
            "company_id": "HDFCBANK",
            "company_name": "HDFC Bank",
            "roe": 17.0,
            "return_on_equity_pct": 17.0,
            "debt_to_equity": 6.5,  # High leverage, but Financial sector
            "free_cash_flow": -120000.0,
            "cagr_sales_5yr": 18.0,
            "cagr_pat_5yr": 19.0,
            "opm": 40.0,
            "interest_coverage": None,  # No standard ICR for Banks
            "debt_free_label": 0,
            "is_financial_sector": 1,  # Financials sector firm
            "sales": 150000.0,
            "composite_quality_score": 85.0
        },
        {
            "company_id": "INFY",
            "company_name": "Infosys",
            "roe": 30.0,
            "return_on_equity_pct": 30.0,
            "debt_to_equity": 0.0,  # Debt Free
            "free_cash_flow": 22000.0,
            "cagr_sales_5yr": 13.0,
            "cagr_pat_5yr": 11.0,
            "opm": 24.0,
            "interest_coverage": None,  # Debt Free -> ICR = infinity
            "debt_free_label": 1,
            "is_financial_sector": 0,
            "sales": 153000.0,
            "composite_quality_score": 88.0
        },
        {
            "company_id": "WEAKCO",
            "company_name": "Weak Company",
            "roe": 5.0,
            "return_on_equity_pct": 5.0,
            "debt_to_equity": 3.0,
            "free_cash_flow": -500.0,
            "cagr_sales_5yr": 2.0,
            "cagr_pat_5yr": -1.0,
            "opm": 6.0,
            "interest_coverage": 1.1,
            "debt_free_label": 0,
            "is_financial_sector": 0,
            "sales": 1000.0,
            "composite_quality_score": 30.0
        }
    ])

class TestScreenerEngine:
    def test_engine_init(self):
        engine = ScreenerEngine()
        assert engine is not None

    def test_single_filter_roe(self, mock_financial_df):
        engine = ScreenerEngine()
        res = engine.apply_filters(mock_financial_df, {"roe_min": 15.0})
        assert len(res) == 3
        assert "WEAKCO" not in res["company_id"].values

    def test_financials_de_exception(self, mock_financial_df):
        engine = ScreenerEngine()
        # D/E max filter set to 1.0 -> HDFCBANK (D/E=6.5) should pass because is_financial_sector=1
        res = engine.apply_filters(mock_financial_df, {"de_max": 1.0})
        assert "HDFCBANK" in res["company_id"].values
        assert "TCS" in res["company_id"].values
        assert "WEAKCO" not in res["company_id"].values

    def test_debt_free_icr_exception(self, mock_financial_df):
        engine = ScreenerEngine()
        # ICR min set to 5.0 -> INFY has interest_coverage=None but debt_free_label=1 so it passes
        res = engine.apply_filters(mock_financial_df, {"icr_min": 5.0})
        assert "INFY" in res["company_id"].values
        assert "TCS" in res["company_id"].values
        assert "WEAKCO" not in res["company_id"].values

    def test_combined_filters_and_sorting(self, mock_financial_df):
        engine = ScreenerEngine()
        filters = {
            "roe_min": 15.0,
            "de_max": 1.0,
            "fcf_min": 0.0,
            "revenue_cagr_5yr_min": 10.0
        }
        res = engine.apply_filters(mock_financial_df, filters)
        assert len(res) == 2  # TCS and INFY
        # Check sorted descending by composite_quality_score (TCS=92, INFY=88)
        assert list(res["company_id"].values) == ["TCS", "INFY"]
