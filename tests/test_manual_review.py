"""
Unit tests for the manual review / QA framework.

Tests the comparison logic, especially:
- Floating-point tolerance
- None/NaN handling
- String case insensitivity
- Exact numeric match
"""

import pytest
import numpy as np
from src.qa.manual_review import values_match


class TestValuesMatch:
    """Tests for the values_match comparison function."""

    # --- Both null ---
    def test_both_none(self):
        assert values_match(None, None) is True

    def test_both_nan(self):
        assert values_match(np.nan, np.nan) is True

    def test_none_and_nan(self):
        assert values_match(None, np.nan) is True

    # --- One null, one not ---
    def test_none_vs_value(self):
        assert values_match(None, 100) is False

    def test_value_vs_none(self):
        assert values_match(100, None) is False

    def test_nan_vs_string(self):
        assert values_match(np.nan, "hello") is False

    # --- Exact numeric match ---
    def test_exact_integer_match(self):
        assert values_match(100, 100) is True

    def test_exact_float_match(self):
        assert values_match(3.14, 3.14) is True

    def test_zero_and_zero(self):
        assert values_match(0, 0) is True

    def test_zero_and_zero_float(self):
        assert values_match(0.0, 0) is True

    # --- Floating-point tolerance ---
    def test_within_tolerance(self):
        # 0.5% difference should match with 1% tolerance
        assert values_match(100.0, 100.5, tolerance=0.01) is True

    def test_beyond_tolerance(self):
        # 2% difference should NOT match with 1% tolerance
        assert values_match(100.0, 102.0, tolerance=0.01) is False

    def test_negative_numbers_within_tolerance(self):
        assert values_match(-100.0, -100.5, tolerance=0.01) is True

    def test_very_small_difference(self):
        # Floating point arithmetic: 0.1 + 0.2 != 0.3 exactly
        assert values_match(0.3, 0.1 + 0.2) is True

    # --- String comparison ---
    def test_exact_string_match(self):
        assert values_match("TCS", "TCS") is True

    def test_case_insensitive_string(self):
        assert values_match("Tcs", "tcs") is True

    def test_string_with_whitespace(self):
        assert values_match("  TCS  ", "TCS") is True

    def test_string_mismatch(self):
        assert values_match("TCS", "INFY") is False

    # --- Mixed types ---
    def test_int_vs_float(self):
        assert values_match(100, 100.0) is True

    def test_numpy_int_vs_python_int(self):
        assert values_match(np.int64(100), 100) is True

    def test_numpy_float_vs_python_float(self):
        assert values_match(np.float64(3.14), 3.14) is True
