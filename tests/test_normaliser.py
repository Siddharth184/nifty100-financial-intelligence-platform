import pytest
import numpy as np
from src.etl.normaliser import normalize_ticker, normalize_year

class TestNormalizeTicker:
    # --- Normal Inputs ---
    def test_normal_ticker(self):
        assert normalize_ticker("TCS") == "TCS"
    def test_lowercase_ticker(self):
        assert normalize_ticker("infy") == "INFY"
    def test_mixed_case_ticker(self):
        assert normalize_ticker("HdfcBank") == "HDFCBANK"
        
    # --- Edge Cases & Invalid Values ---
    def test_leading_trailing_spaces(self):
        assert normalize_ticker("  RELIANCE  ") == "RELIANCE"
    def test_empty_string(self):
        assert normalize_ticker("") is None
    def test_whitespace_string(self):
        assert normalize_ticker("   ") is None
    def test_none_value(self):
        assert normalize_ticker(None) is None
    def test_nan_value(self):
        assert normalize_ticker(np.nan) is None
    def test_numeric_ticker(self):
        assert normalize_ticker(500112) == "500112"
    def test_float_ticker(self):
        assert normalize_ticker(500.0) == "500.0"
        
    # --- Formatting Edge Cases ---
    def test_special_characters(self):
        assert normalize_ticker("M&M") == "M&M"
    def test_hyphenated_ticker(self):
        assert normalize_ticker("TATA-MOTORS") == "TATA-MOTORS"
    def test_multiple_spaces(self):
        assert normalize_ticker("BAJAJ  FIN") == "BAJAJ  FIN"
    def test_tab_characters(self):
        assert normalize_ticker("\tWIPRO\t") == "WIPRO"
    def test_newline_characters(self):
        assert normalize_ticker("\nITC\n") == "ITC"

class TestNormalizeYear:
    # --- Normal FY Formats ---
    def test_format_fy_yyyy(self):
        assert normalize_year("FY2024") == 2024
    def test_format_fy_space_yyyy(self):
        assert normalize_year("FY 2024") == 2024
    def test_format_fy_yy(self):
        assert normalize_year("FY24") == 2024
    def test_format_fy_space_yy(self):
        assert normalize_year("FY 24") == 2024
        
    # --- Standard Year Formats ---
    def test_format_yyyy(self):
        assert normalize_year("2024") == 2024
    def test_format_integer_yyyy(self):
        assert normalize_year(2024) == 2024
        
    # --- Hyphenated Formats ---
    def test_format_yyyy_yy(self):
        assert normalize_year("2023-24") == 2024
    def test_format_yyyy_yy_different_century(self):
        assert normalize_year("1999-00") == 2000
    def test_format_yyyy_yy_standard(self):
        assert normalize_year("2019-20") == 2020
    def test_format_yyyy_yyyy(self):
        assert normalize_year("2023-2024") == 2024
        
    # --- Month Formats ---
    def test_format_month_yy(self):
        assert normalize_year("Mar-24") == 2024
    def test_format_month_yy_dec(self):
        assert normalize_year("Dec-23") == 2023
    def test_format_month_space_yyyy(self):
        assert normalize_year("Mar 2024") == 2024
    def test_format_uppercase_month(self):
        assert normalize_year("MAR 2024") == 2024
    def test_format_lowercase_month(self):
        assert normalize_year("mar-24") == 2024
        
    # --- Invalid & Edge Cases ---
    def test_empty_string(self):
        assert normalize_year("") is None
    def test_whitespace_string(self):
        assert normalize_year("   ") is None
    def test_none_value(self):
        assert normalize_year(None) is None
    def test_nan_value(self):
        assert normalize_year(np.nan) is None
    def test_invalid_string(self):
        assert normalize_year("InvalidYear") is None
    def test_invalid_format(self):
        assert normalize_year("24-Mar") is None
    def test_unsupported_month(self):
        assert normalize_year("XYZ-24") is None
