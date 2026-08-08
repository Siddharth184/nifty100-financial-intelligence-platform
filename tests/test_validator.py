import pytest
import pandas as pd
from src.etl.dq_rules import (
    dq_01_primary_key, dq_04_balance_sheet, dq_06_positive_sales, 
    dq_08_tax_rate, dq_10_eps_sign, dq_11_valid_url, dq_14_fy_consistency
)
from src.etl.validator import ValidatorEngine

def test_dq_01_primary_key():
    data = pd.DataFrame({'company_id': [1, 2, 2, 3]})
    f = dq_01_primary_key(data, "test.xlsx", "company_id")
    assert len(f) == 2
    assert f[0].rule_id == "DQ-01"
    
def test_dq_04_balance_sheet():
    data = pd.DataFrame({
        'total_assets': [100, 100],
        'total_liabilities': [60, 50],
        'total_equity': [40, 40]
    })
    f = dq_04_balance_sheet(data, "test.xlsx")
    assert len(f) == 1
    assert f[0].severity == "CRITICAL"
    
def test_dq_06_positive_sales():
    data = pd.DataFrame({'sales': [100, -50, 0]})
    f = dq_06_positive_sales(data, "test.xlsx")
    assert len(f) == 1
    assert f[0].actual_value == -50

def test_dq_08_tax_rate():
    data = pd.DataFrame({'tax_rate': [0.25, 1.5, -0.1]})
    f = dq_08_tax_rate(data, "test.xlsx")
    assert len(f) == 2
    assert f[0].severity == "WARNING"

def test_dq_10_eps_sign():
    data = pd.DataFrame({'eps': [5, -5, -5], 'net_profit': [100, -100, 100]})
    f = dq_10_eps_sign(data, "test.xlsx")
    assert len(f) == 1
    assert f[0].actual_value == -5

def test_dq_11_valid_url():
    data = pd.DataFrame({'website': ['http://tcs.com', 'www.tcs.com', None]})
    f = dq_11_valid_url(data, "test.xlsx")
    assert len(f) == 1
    assert f[0].actual_value == 'www.tcs.com'
    
def test_dq_14_fy_consistency():
    data = pd.DataFrame({'year': [1989, 2024, 2150]})
    f = dq_14_fy_consistency(data, "test.xlsx")
    assert len(f) == 2
    
def test_validator_engine_crash_handling():
    engine = ValidatorEngine()
    def bad_rule(df, ds):
        return df['missing_col'] / 0
    engine.run_validation("DQ-CRASH", bad_rule, pd.DataFrame(), "test.xlsx")
    assert engine.report.critical_count == 1
    assert engine.report.failures[0].rule_id == "DQ-CRASH_CRASH"
