"""
Unit tests for ETL loader functions — Sprint 6 Day 41.
"""

import pytest
import os
from src.etl.loader import get_dataset_type, validate_file_exists, load_excel


def test_get_dataset_type_core():
    assert get_dataset_type("companies.xlsx") == "core"
    assert get_dataset_type("profitandloss.xlsx") == "core"
    assert get_dataset_type("balancesheet.xlsx") == "core"


def test_get_dataset_type_supporting():
    assert get_dataset_type("sectors.xlsx") == "supporting"
    assert get_dataset_type("financial_ratios.xlsx") == "supporting"
    assert get_dataset_type("peer_groups.xlsx") == "supporting"


def test_get_dataset_type_unknown():
    assert get_dataset_type("random.xlsx") == "unknown"


def test_validate_file_exists_true(tmp_path):
    p = tmp_path / "test.txt"
    p.write_text("hello")
    assert validate_file_exists(str(p)) is True


def test_validate_file_exists_false():
    assert validate_file_exists("non_existent_file_xyz.xlsx") is False


def test_load_excel_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_excel("data/raw/non_existent_12345.xlsx")
