"""
Manual Data Quality Review & ETL Verification Module.
Compares raw Excel source files against database tables for manual validation.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger
from src.etl.loader import load_excel
from src.utils.helpers import normalize_dataframe
from src.etl.normaliser import normalize_ticker, normalize_year
from src.db.connection import get_db_connection

logger = get_logger(__name__)


# Default paths
DB_PATH = "db/nifty100.db"
DATA_DIR = "data/raw"
REVIEW_REPORT_PATH = "output/review_report.csv"


# ----------------------------------------------------------------
# 1. SAMPLING
# ----------------------------------------------------------------

def sample_companies(db_path: str, n: int = 5) -> List[Tuple[str, str]]:
    """
    Randomly selects N companies from the SQLite database for spot-checking.

    Uses SQLite's ORDER BY RANDOM() to get an unbiased sample.
    Returns a list of (company_id, company_name) tuples.

    Args:
        db_path: Path to the SQLite database file.
        n: Number of companies to sample.

    Returns:
        List of (company_id, company_name) tuples.
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT company_id, company_name FROM companies ORDER BY RANDOM() LIMIT ?",
                (n,)
            )
            results = cursor.fetchall()
            logger.info(f"Sampled {len(results)} companies for manual review.")
            return results
    except Exception as e:
        logger.error(f"Failed to sample companies: {e}")
        return []


# ----------------------------------------------------------------
# 2. EXCEL SOURCE RE-READING
# ----------------------------------------------------------------

def load_excel_for_comparison(filename: str, data_dir: str = DATA_DIR) -> pd.DataFrame:
    """
    Re-reads an Excel file and applies the same normalization that the
    pipeline uses, so we get the 'expected' values.

    This is critical: we must apply the *exact same* transformation chain
    as the pipeline, otherwise we would flag normalization changes as
    'mismatches' when they are intentional.

    Args:
        filename: The Excel filename (e.g. 'companies.xlsx').
        data_dir: Directory containing the raw Excel files.

    Returns:
        Normalized Pandas DataFrame representing the expected values.
    """
    filepath = os.path.join(data_dir, filename)
    if not os.path.exists(filepath):
        logger.error(f"Source file not found for comparison: {filepath}")
        return pd.DataFrame()

    try:
        df = load_excel(filepath)
        df = normalize_dataframe(df)

        if 'ticker' in df.columns:
            df['ticker'] = df['ticker'].apply(normalize_ticker)
        if 'year' in df.columns:
            df['year'] = df['year'].apply(normalize_year)
            df = df.dropna(subset=['year'])

        return df
    except Exception as e:
        logger.error(f"Failed to load Excel for comparison: {e}")
        return pd.DataFrame()


# ----------------------------------------------------------------
# 3. DATABASE QUERYING
# ----------------------------------------------------------------

def query_db_for_company(
    db_path: str,
    table: str,
    company_id: str
) -> pd.DataFrame:
    """
    Queries the SQLite database for all records of a given company
    in a specific table. Returns the 'actual' loaded values.

    Args:
        db_path: Path to the SQLite database.
        table: Table name to query (e.g. 'profitandloss').
        company_id: The company_id to filter on.

    Returns:
        DataFrame containing the database records.
    """
    try:
        with get_db_connection(db_path) as conn:
            query = f"SELECT * FROM {table} WHERE company_id = ?"
            df = pd.read_sql_query(query, conn, params=(company_id,))
            return df
    except Exception as e:
        logger.error(f"Failed to query {table} for {company_id}: {e}")
        return pd.DataFrame()


# ----------------------------------------------------------------
# 4. VALUE COMPARISON
# ----------------------------------------------------------------

def values_match(
    excel_val: Any,
    db_val: Any,
    tolerance: float = 0.01
) -> bool:
    """
    Compares two values with special handling for:
    - None / NaN: Both null → match. One null, one not → mismatch.
    - Floats: Uses relative tolerance (floating-point math creates
      tiny rounding differences that aren't real bugs).
    - Strings: Case-insensitive stripped comparison.

    Args:
        excel_val: The value from the Excel source.
        db_val: The value from the SQLite database.
        tolerance: Relative tolerance for numeric comparisons.

    Returns:
        True if values match, False otherwise.
    """
    # Both null
    if pd.isna(excel_val) and pd.isna(db_val):
        return True
    # One null, one not
    if pd.isna(excel_val) or pd.isna(db_val):
        return False

    # Numeric comparison with tolerance
    if isinstance(excel_val, (int, float, np.integer, np.floating)) and \
       isinstance(db_val, (int, float, np.integer, np.floating)):
        if excel_val == 0 and db_val == 0:
            return True
        if excel_val == 0:
            return bool(abs(db_val) < tolerance)
        return bool(abs((excel_val - db_val) / excel_val) < tolerance)

    # String comparison
    return bool(str(excel_val).strip().lower() == str(db_val).strip().lower())


def compare_records(
    excel_row: pd.Series,
    db_row: pd.Series,
    company_name: str,
    dataset: str
) -> List[Dict]:
    """
    Compares a single Excel row against a single DB row, column by column.

    Returns a list of comparison results (one dict per column).

    Args:
        excel_row: A single row from the Excel DataFrame.
        db_row: A single row from the SQLite DataFrame.
        company_name: For the report.
        dataset: For the report (e.g. 'profitandloss').

    Returns:
        List of dicts with comparison results.
    """
    results = []
    # Only compare columns that exist in both
    common_cols = set(excel_row.index) & set(db_row.index)

    for col in common_cols:
        excel_val = excel_row[col]
        db_val = db_row[col]
        match = values_match(excel_val, db_val)

        results.append({
            "timestamp": datetime.now().isoformat(),
            "company_name": company_name,
            "dataset": dataset,
            "column": col,
            "excel_value": str(excel_val),
            "db_value": str(db_val),
            "status": "MATCH" if match else "MISMATCH",
            "reviewer_notes": "" if match else f"Excel={excel_val}, DB={db_val}"
        })

    return results


# ----------------------------------------------------------------
# 5. COVERAGE ANALYSIS
# ----------------------------------------------------------------

def check_coverage(db_path: str, min_years: int = 5) -> pd.DataFrame:
    """
    Identifies companies with fewer than `min_years` of financial history
    in the profitandloss table.

    In financial analytics, a company with only 1-2 years of data
    produces unreliable trend analysis. This check flags thin data.

    Args:
        db_path: Path to the SQLite database.
        min_years: Minimum expected years of financial data.

    Returns:
        DataFrame of under-covered companies.
    """
    try:
        with get_db_connection(db_path) as conn:
            query = """
                SELECT
                    c.company_id,
                    c.company_name,
                    COUNT(p.year) as year_count
                FROM companies c
                LEFT JOIN profitandloss p ON c.company_id = p.company_id
                GROUP BY c.company_id, c.company_name
                HAVING year_count < ?
                ORDER BY year_count ASC
            """
            df = pd.read_sql_query(query, conn, params=(min_years,))
            if not df.empty:
                logger.warning(
                    f"Found {len(df)} companies with fewer than {min_years} years of data."
                )
            else:
                logger.info(f"All companies have >= {min_years} years of data.")
            return df
    except Exception as e:
        logger.error(f"Coverage check failed: {e}")
        return pd.DataFrame()


# ----------------------------------------------------------------
# 6. ROW COUNT RECONCILIATION
# ----------------------------------------------------------------

def reconcile_row_counts(
    db_path: str,
    data_dir: str = DATA_DIR
) -> List[Dict]:
    from src.db.loader import LOAD_ORDER

    # Get valid company IDs for foreign key filtering
    comp_df = load_excel_for_comparison("companies.xlsx", data_dir)
    valid_companies = set(comp_df["id"]) if "id" in comp_df.columns else set()

    results = []
    for table_name in LOAD_ORDER:
        filename = f"{table_name}.xlsx"
        filepath = os.path.join(data_dir, filename)

        # Excel row count (normalized and filtered for valid FKs)
        excel_rows = 0
        if os.path.exists(filepath):
            try:
                df = load_excel_for_comparison(filename, data_dir)
                if table_name == "sectors":
                    excel_rows = len(df["broad_sector"].dropna().unique()) if "broad_sector" in df.columns else len(df)
                else:
                    if "company_id" in df.columns and valid_companies:
                        df = df[df["company_id"].isin(valid_companies)]
                    if "company_id" in df.columns and "year" in df.columns:
                        df = df.drop_duplicates(subset=["company_id", "year"])
                    elif "company_id" in df.columns and "date" in df.columns:
                        df = df.drop_duplicates(subset=["company_id", "date"])
                    excel_rows = len(df)
            except Exception:
                excel_rows = -1  # Signal a read error

        # Database row count
        db_rows = 0
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                db_rows = cursor.fetchone()[0]
        except Exception:
            db_rows = -1

        match = excel_rows == db_rows and excel_rows >= 0
        results.append({
            "table": table_name,
            "excel_rows": excel_rows,
            "db_rows": db_rows,
            "status": "MATCH" if match else "MISMATCH",
            "notes": "" if match else f"Diff: {abs(excel_rows - db_rows)}"
        })

        level = logger.info if match else logger.warning
        level(f"Row count {table_name}: Excel={excel_rows}, DB={db_rows} -> {'MATCH' if match else 'MISMATCH'}")

    return results


# ----------------------------------------------------------------
# 7. MASTER ORCHESTRATOR
# ----------------------------------------------------------------

def run_manual_review(
    db_path: str = DB_PATH,
    data_dir: str = DATA_DIR,
    report_path: str = REVIEW_REPORT_PATH,
    sample_size: int = 5
) -> bool:
    """
    Orchestrates the full manual QA review:
    1. Row count reconciliation across all tables
    2. Random company sampling & value-level comparison
    3. Financial year coverage analysis
    4. Report generation

    Args:
        db_path: Path to the SQLite database.
        data_dir: Directory containing the raw Excel files.
        report_path: Where to save the review report CSV.
        sample_size: Number of companies to sample.

    Returns:
        True if all checks pass, False if mismatches found.
    """
    logger.info("=" * 50)
    logger.info("STARTING MANUAL DATA QUALITY REVIEW")
    logger.info("=" * 50)

    all_results = []
    has_mismatches = False

    # --- Step 1: Row Count Reconciliation ---
    logger.info("Step 1: Row Count Reconciliation...")
    recon = reconcile_row_counts(db_path, data_dir)
    for r in recon:
        all_results.append({
            "timestamp": datetime.now().isoformat(),
            "company_name": "ALL",
            "dataset": r["table"],
            "column": "ROW_COUNT",
            "excel_value": str(r["excel_rows"]),
            "db_value": str(r["db_rows"]),
            "status": r["status"],
            "reviewer_notes": r["notes"]
        })
        if r["status"] == "MISMATCH":
            has_mismatches = True

    # --- Step 2: Sample Companies & Compare Values ---
    logger.info("Step 2: Sampling companies for value-level comparison...")
    sampled = sample_companies(db_path, sample_size)

    # Tables to spot-check (those with company_id + year composite keys)
    tables_to_check = ["profitandloss", "balancesheet", "cashflow"]

    for company_id, company_name in sampled:
        logger.info(f"Reviewing: {company_name} ({company_id})")

        for table in tables_to_check:
            filename = f"{table}.xlsx"

            # Get expected (Excel) data for this company
            excel_df = load_excel_for_comparison(filename, data_dir)
            if excel_df.empty:
                continue

            # Filter Excel for this company
            if 'company_id' in excel_df.columns:
                excel_company = excel_df[excel_df['company_id'] == company_id]
            else:
                continue

            # Get actual (DB) data
            db_company = query_db_for_company(db_path, table, company_id)

            if excel_company.empty and db_company.empty:
                continue

            if excel_company.empty and not db_company.empty:
                all_results.append({
                    "timestamp": datetime.now().isoformat(),
                    "company_name": company_name,
                    "dataset": table,
                    "column": "EXISTENCE",
                    "excel_value": "NOT FOUND",
                    "db_value": f"{len(db_company)} rows",
                    "status": "MISMATCH",
                    "reviewer_notes": "Company exists in DB but not in Excel source"
                })
                has_mismatches = True
                continue

            if not excel_company.empty and db_company.empty:
                all_results.append({
                    "timestamp": datetime.now().isoformat(),
                    "company_name": company_name,
                    "dataset": table,
                    "column": "EXISTENCE",
                    "excel_value": f"{len(excel_company)} rows",
                    "db_value": "NOT FOUND",
                    "status": "MISMATCH",
                    "reviewer_notes": "Company exists in Excel but not in DB"
                })
                has_mismatches = True
                continue

            # Compare row-by-row on matching years
            if 'year' in excel_company.columns and 'year' in db_company.columns:
                common_years = set(excel_company['year']) & set(db_company['year'])
                for year in common_years:
                    excel_row = excel_company[excel_company['year'] == year].iloc[0]
                    db_row = db_company[db_company['year'] == year].iloc[0]
                    comparisons = compare_records(excel_row, db_row, company_name, table)
                    for c in comparisons:
                        if c["status"] == "MISMATCH":
                            has_mismatches = True
                    all_results.extend(comparisons)

    # --- Step 3: Coverage Analysis ---
    logger.info("Step 3: Financial Year Coverage Analysis...")
    thin_companies = check_coverage(db_path)
    for _, row in thin_companies.iterrows():
        all_results.append({
            "timestamp": datetime.now().isoformat(),
            "company_name": row.get("company_name", ""),
            "dataset": "profitandloss",
            "column": "COVERAGE",
            "excel_value": f"{row.get('year_count', 0)} years",
            "db_value": "< 5 years",
            "status": "WARNING",
            "reviewer_notes": "Insufficient financial history for trend analysis"
        })

    # --- Step 4: Save Report ---
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    report_df = pd.DataFrame(all_results)
    report_df.to_csv(report_path, index=False)
    logger.info(f"Review report saved to {report_path}")

    # --- Summary ---
    total_checks = len(all_results)
    matches = sum(1 for r in all_results if r["status"] == "MATCH")
    mismatches = sum(1 for r in all_results if r["status"] == "MISMATCH")
    warnings = sum(1 for r in all_results if r["status"] == "WARNING")

    logger.info("=" * 50)
    logger.info("MANUAL REVIEW SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total Checks    : {total_checks}")
    logger.info(f"Matches         : {matches}")
    logger.info(f"Mismatches      : {mismatches}")
    logger.info(f"Warnings        : {warnings}")
    logger.info(f"Overall Status  : {'PASS' if not has_mismatches else 'FAIL'}")
    logger.info("=" * 50)

    return not has_mismatches


if __name__ == "__main__":
    run_manual_review()
