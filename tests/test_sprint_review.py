"""
Unit tests for the Sprint Review utility functions.

Tests the parsing and summarization logic used in the
sprint review process.
"""

import pytest
import os
import pandas as pd
from src.qa.sprint_review import review_audit_csv, review_dq_report


@pytest.fixture
def tmp_audit_csv(tmp_path):
    """Creates a mock load_audit.csv for testing."""
    data = pd.DataFrame([
        {"timestamp": "2026-01-01", "table_name": "companies", "rows_read": 100,
         "rows_inserted": 100, "status": "SUCCESS", "error_message": "", "execution_time_sec": 0.5},
        {"timestamp": "2026-01-01", "table_name": "profitandloss", "rows_read": 500,
         "rows_inserted": 500, "status": "SUCCESS", "error_message": "", "execution_time_sec": 1.2},
    ])
    path = tmp_path / "audit.csv"
    data.to_csv(path, index=False)
    return str(path)


@pytest.fixture
def tmp_audit_csv_with_failure(tmp_path):
    """Creates a mock audit CSV with a failed table."""
    data = pd.DataFrame([
        {"timestamp": "2026-01-01", "table_name": "companies", "rows_read": 100,
         "rows_inserted": 100, "status": "SUCCESS", "error_message": "", "execution_time_sec": 0.5},
        {"timestamp": "2026-01-01", "table_name": "cashflow", "rows_read": 200,
         "rows_inserted": 0, "status": "FAILED", "error_message": "FK violation", "execution_time_sec": 0.1},
    ])
    path = tmp_path / "audit_fail.csv"
    data.to_csv(path, index=False)
    return str(path)


@pytest.fixture
def tmp_dq_csv_clean(tmp_path):
    """Creates an empty DQ report (clean data)."""
    path = tmp_path / "dq_clean.csv"
    pd.DataFrame(columns=["rule_id", "severity", "dataset"]).to_csv(path, index=False)
    return str(path)


@pytest.fixture
def tmp_dq_csv_with_issues(tmp_path):
    """Creates a DQ report with CRITICAL and WARNING findings."""
    data = pd.DataFrame([
        {"rule_id": "DQ-01", "severity": "CRITICAL", "dataset": "companies.xlsx"},
        {"rule_id": "DQ-08", "severity": "WARNING", "dataset": "profitandloss.xlsx"},
        {"rule_id": "DQ-11", "severity": "INFO", "dataset": "companies.xlsx"},
    ])
    path = tmp_path / "dq_issues.csv"
    data.to_csv(path, index=False)
    return str(path)


# ----------------------------------------------------------------
# AUDIT CSV TESTS
# ----------------------------------------------------------------

class TestReviewAuditCsv:

    def test_all_success(self, tmp_audit_csv):
        summary = review_audit_csv(tmp_audit_csv)
        assert summary["exists"] is True
        assert summary["total_tables"] == 2
        assert summary["success_count"] == 2
        assert summary["failed_count"] == 0
        assert summary["total_rows_inserted"] == 600

    def test_with_failure(self, tmp_audit_csv_with_failure):
        summary = review_audit_csv(tmp_audit_csv_with_failure)
        assert summary["failed_count"] == 1
        assert "cashflow" in summary["failed_tables"]

    def test_missing_file(self):
        summary = review_audit_csv("nonexistent/audit.csv")
        assert summary["exists"] is False
        assert summary["total_tables"] == 0


# ----------------------------------------------------------------
# DQ REPORT TESTS
# ----------------------------------------------------------------

class TestReviewDqReport:

    def test_clean_data(self, tmp_dq_csv_clean):
        summary = review_dq_report(tmp_dq_csv_clean)
        assert summary["exists"] is True
        assert summary["critical_count"] == 0
        assert summary["warning_count"] == 0

    def test_with_issues(self, tmp_dq_csv_with_issues):
        summary = review_dq_report(tmp_dq_csv_with_issues)
        assert summary["critical_count"] == 1
        assert summary["warning_count"] == 1
        assert summary["info_count"] == 1
        assert "DQ-01" in summary["critical_rules"]

    def test_missing_file(self):
        summary = review_dq_report("nonexistent/dq.csv")
        assert summary["exists"] is False
