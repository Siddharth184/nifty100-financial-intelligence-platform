"""
Unit tests for ETL normalization functions — Sprint 6 Day 41.
"""

import pytest
from src.etl.normaliser import normalize_year, normalize_ticker


def test_normalize_year_standard_4digit():
    assert normalize_year(2024) == 2024
    assert normalize_year("2024") == 2024
    assert normalize_year(2024.0) == 2024


def test_normalize_year_fy_prefix():
    assert normalize_year("FY2024") == 2024
    assert normalize_year("FY 2024") == 2024
    assert normalize_year("FY24") == 2024
    assert normalize_year("FY 24") == 2024


def test_normalize_year_range_formats():
    assert normalize_year("2023-24") == 2024
    assert normalize_year("2019-20") == 2020
    assert normalize_year("2023-2024") == 2024


def test_normalize_year_month_year_formats():
    assert normalize_year("Mar-24") == 2024
    assert normalize_year("Mar 2024") == 2024
    assert normalize_year("Dec-23") == 2023


def test_normalize_year_none_and_invalid():
    assert normalize_year(None) is None
    assert normalize_year("") is None
    assert normalize_year("TTM") is None
    assert normalize_year("NAN") is None


def test_normalize_ticker_basic():
    assert normalize_ticker("tcs") == "TCS"
    assert normalize_ticker(" INFYS ") == "INFYS"
    assert normalize_ticker("reliance") == "RELIANCE"


def test_normalize_ticker_none_and_empty():
    assert normalize_ticker(None) is None
    assert normalize_ticker("") is None
    assert normalize_ticker("   ") is None
