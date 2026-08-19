"""
Unit tests for financial ratio engines — Sprint 6 Day 41.
"""

import pytest
from src.analytics.profitability import safe_divide, calculate_npm, calculate_opm, calculate_roe, calculate_roce
from src.analytics.leverage_efficiency import calculate_debt_to_equity, calculate_interest_coverage, calculate_net_debt
from src.analytics.cagr import calculate_cagr


def test_safe_divide_valid():
    assert safe_divide(100, 50) == 2.0
    assert safe_divide(0, 50) == 0.0


def test_safe_divide_zero_denominator():
    assert safe_divide(100, 0) is None


def test_safe_divide_none_inputs():
    assert safe_divide(None, 50) is None
    assert safe_divide(100, None) is None


def test_calculate_npm():
    assert calculate_npm(15, 100) == 15.0
    assert calculate_npm(None, 100) is None


def test_calculate_opm():
    assert calculate_opm(25, 100) == 25.0


def test_calculate_roe():
    assert calculate_roe(20, 100) == 20.0
    assert calculate_roe(20, -50) is None  # Negative equity handled


def test_calculate_roce():
    assert calculate_roce(30, 200, 50) == 20.0  # 30 / (200 - 50) * 100 = 20%
    assert calculate_roce(30, 200, 0, is_financial=True) is None  # Suppressed for financial sector


def test_calculate_debt_to_equity():
    assert calculate_debt_to_equity(50, 100) == 0.5
    assert calculate_debt_to_equity(0, 100) == 0.0
    assert calculate_debt_to_equity(50, -10) is None


def test_calculate_interest_coverage():
    assert calculate_interest_coverage(100, 20) == 5.0
    assert calculate_interest_coverage(100, 0) is None  # Zero interest -> None (debt free)


def test_calculate_net_debt():
    assert calculate_net_debt(100, 30) == 70.0
    assert calculate_net_debt(50, 100) == -50.0


def test_calculate_cagr_positive():
    cagr, status = calculate_cagr(100, 200, 5)
    assert status == "VALID"
    assert cagr == 14.87


def test_calculate_cagr_turnaround_loss():
    cagr, status = calculate_cagr(100, -50, 5)
    assert status == "TURNAROUND_LOSS"
    assert cagr is None


def test_calculate_cagr_zero_base():
    cagr, status = calculate_cagr(0, 100, 5)
    assert status == "ZERO_BASE"
    assert cagr is None
