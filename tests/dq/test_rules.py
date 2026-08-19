"""
Unit tests for Data Quality (DQ) rules — Sprint 6 Day 41.
"""

import pandas as pd
import pytest
from src.etl.dq_rules import (
    dq_01_primary_key,
    dq_02_composite_key,
    dq_03_foreign_key,
    dq_04_balance_sheet,
)


def test_dq_01_primary_key_pass():
    df = pd.DataFrame([{"company_id": "TCS"}, {"company_id": "INFY"}])
    failures = dq_01_primary_key(df, "companies", "company_id")
    assert len(failures) == 0


def test_dq_01_primary_key_fail():
    df = pd.DataFrame([{"company_id": "TCS"}, {"company_id": "TCS"}])
    failures = dq_01_primary_key(df, "companies", "company_id")
    assert len(failures) == 2


def test_dq_02_composite_key_pass():
    df = pd.DataFrame([
        {"company_id": "TCS", "year": 2023},
        {"company_id": "TCS", "year": 2024},
    ])
    failures = dq_02_composite_key(df, "profitandloss", ["company_id", "year"])
    assert len(failures) == 0


def test_dq_02_composite_key_fail():
    df = pd.DataFrame([
        {"company_id": "TCS", "year": 2024},
        {"company_id": "TCS", "year": 2024},
    ])
    failures = dq_02_composite_key(df, "profitandloss", ["company_id", "year"])
    assert len(failures) == 2


def test_dq_03_foreign_key_pass():
    parent = pd.DataFrame([{"company_id": "TCS"}, {"company_id": "INFY"}])
    child = pd.DataFrame([{"company_id": "TCS", "year": 2024}])
    failures = dq_03_foreign_key(child, "profitandloss", "company_id", parent, "company_id")
    assert len(failures) == 0


def test_dq_03_foreign_key_fail():
    parent = pd.DataFrame([{"company_id": "TCS"}])
    child = pd.DataFrame([{"company_id": "ORPHAN_COMP", "year": 2024}])
    failures = dq_03_foreign_key(child, "profitandloss", "company_id", parent, "company_id")
    assert len(failures) == 1


def test_dq_04_balance_sheet_pass():
    df = pd.DataFrame([{
        "company_id": "TCS", "year": 2024,
        "total_assets": 100.0, "total_liabilities": 40.0, "total_equity": 60.0
    }])
    failures = dq_04_balance_sheet(df, "balancesheet")
    assert len(failures) == 0


def test_dq_04_balance_sheet_fail():
    df = pd.DataFrame([{
        "company_id": "TCS", "year": 2024,
        "total_assets": 100.0, "total_liabilities": 40.0, "total_equity": 90.0  # Assets != L + E
    }])
    failures = dq_04_balance_sheet(df, "balancesheet")
    assert len(failures) == 1
