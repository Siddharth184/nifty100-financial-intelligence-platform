import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from src.etl.validation_report import ValidationFailure

def current_time():
    return datetime.now().isoformat()

def dq_01_primary_key(df: pd.DataFrame, dataset: str, pk_col: str) -> List[ValidationFailure]:
    failures = []
    if pk_col not in df.columns: return failures
    duplicates = df[df.duplicated(subset=[pk_col], keep=False)]
    for _, row in duplicates.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-01", severity="CRITICAL", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column=pk_col,
            actual_value=row[pk_col], expected_value="Unique",
            failure_description="Duplicate primary key detected", suggested_fix="Remove duplicates"
        ))
    return failures

def dq_02_composite_key(df: pd.DataFrame, dataset: str, cols: List[str]) -> List[ValidationFailure]:
    failures = []
    if not all(c in df.columns for c in cols): return failures
    valid_df = df.dropna(subset=cols)
    duplicates = valid_df[valid_df.duplicated(subset=cols, keep=False)]
    for _, row in duplicates.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-02", severity="CRITICAL", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column=str(cols),
            actual_value=str([row[c] for c in cols]), expected_value="Unique",
            failure_description="Duplicate composite key detected", suggested_fix="Remove duplicate records for this year"
        ))
    return failures

def dq_03_foreign_key(df: pd.DataFrame, dataset: str, fk_col: str, parent_df: pd.DataFrame, pk_col: str) -> List[ValidationFailure]:
    failures = []
    if fk_col not in df.columns or pk_col not in parent_df.columns: return failures
    valid_ids = set(parent_df[pk_col].dropna())
    invalid = df[~df[fk_col].isin(valid_ids) & df[fk_col].notna()]
    for _, row in invalid.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-03", severity="CRITICAL", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column=fk_col,
            actual_value=row[fk_col], expected_value=f"Exists in parent {pk_col}",
            failure_description="Foreign key violation", suggested_fix="Add parent record or remove orphan"
        ))
    return failures

def dq_04_balance_sheet(df: pd.DataFrame, dataset: str) -> List[ValidationFailure]:
    failures = []
    required = ['total_assets', 'total_liabilities', 'total_equity']
    if not all(col in df.columns for col in required): return failures
    calc = df['total_liabilities'].fillna(0) + df['total_equity'].fillna(0)
    var = abs((df['total_assets'] - calc) / df['total_assets'].replace(0, np.nan))
    invalid = df[var > 0.01]
    for _, row in invalid.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-04", severity="CRITICAL", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column="total_assets",
            actual_value=row['total_assets'], expected_value=row['total_liabilities'] + row['total_equity'],
            failure_description="Assets != Liabilities + Equity", suggested_fix="Fix accounting equation"
        ))
    return failures

def dq_05_opm_crosscheck(df: pd.DataFrame, dataset: str) -> List[ValidationFailure]:
    failures = []
    required = ['operating_profit', 'sales', 'operating_profit_margin']
    if not all(col in df.columns for col in required): return failures
    calc_opm = df['operating_profit'] / df['sales'].replace(0, np.nan)
    var = abs(calc_opm - df['operating_profit_margin'])
    invalid = df[var > 0.05]
    for _, row in invalid.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-05", severity="WARNING", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column="operating_profit_margin",
            actual_value=row['operating_profit_margin'], expected_value=f"~{row['operating_profit']/row['sales'] if row['sales'] else 0}",
            failure_description="OPM doesn't match Profit/Sales ratio", suggested_fix="Verify margin calculation"
        ))
    return failures

def dq_06_positive_sales(df: pd.DataFrame, dataset: str) -> List[ValidationFailure]:
    failures = []
    if 'sales' not in df.columns: return failures
    invalid = df[df['sales'] < 0]
    for _, row in invalid.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-06", severity="CRITICAL", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column="sales",
            actual_value=row['sales'], expected_value=">= 0",
            failure_description="Negative sales detected", suggested_fix="Correct source data"
        ))
    return failures

def dq_07_net_cash(df: pd.DataFrame, dataset: str) -> List[ValidationFailure]:
    failures = []
    required = ['net_cash_flow', 'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow']
    if not all(col in df.columns for col in required): return failures
    calc = df['operating_cash_flow'].fillna(0) + df['investing_cash_flow'].fillna(0) + df['financing_cash_flow'].fillna(0)
    var = abs((df['net_cash_flow'] - calc) / df['net_cash_flow'].replace(0, np.nan))
    invalid = df[(var > 0.05) & (abs(df['net_cash_flow'] - calc) > 1)]
    for _, row in invalid.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-07", severity="CRITICAL", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column="net_cash_flow",
            actual_value=row['net_cash_flow'], expected_value=row['operating_cash_flow']+row['investing_cash_flow']+row['financing_cash_flow'],
            failure_description="Net Cash != CFO + CFI + CFF", suggested_fix="Review cash flow statements"
        ))
    return failures

def dq_08_tax_rate(df: pd.DataFrame, dataset: str) -> List[ValidationFailure]:
    failures = []
    if 'tax_rate' not in df.columns: return failures
    invalid = df[(df['tax_rate'] < 0) | (df['tax_rate'] > 1)]
    for _, row in invalid.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-08", severity="WARNING", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column="tax_rate",
            actual_value=row['tax_rate'], expected_value="0 to 1",
            failure_description="Abnormal tax rate", suggested_fix="Verify if rate is a percentage"
        ))
    return failures

def dq_09_dividend_payout(df: pd.DataFrame, dataset: str) -> List[ValidationFailure]:
    failures = []
    if 'dividend_payout_ratio' not in df.columns: return failures
    invalid = df[(df['dividend_payout_ratio'] < 0) | (df['dividend_payout_ratio'] > 5)]
    for _, row in invalid.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-09", severity="WARNING", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column="dividend_payout_ratio",
            actual_value=row['dividend_payout_ratio'], expected_value="0 to 1 typically",
            failure_description="Extreme dividend payout ratio", suggested_fix="Check dividend vs net profit"
        ))
    return failures

def dq_10_eps_sign(df: pd.DataFrame, dataset: str) -> List[ValidationFailure]:
    failures = []
    if 'eps' not in df.columns or 'net_profit' not in df.columns: return failures
    invalid = df[
        df['eps'].notna() & 
        df['net_profit'].notna() & 
        (df['eps'] != 0) & 
        (df['net_profit'] != 0) & 
        (np.sign(df['eps']) != np.sign(df['net_profit']))
    ]
    for _, row in invalid.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-10", severity="WARNING", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column="eps",
            actual_value=row['eps'], expected_value=f"Sign matches Net Profit ({row['net_profit']})",
            failure_description="EPS and Net Profit have opposite signs", suggested_fix="Check share count and earnings"
        ))
    return failures

def dq_11_valid_url(df: pd.DataFrame, dataset: str) -> List[ValidationFailure]:
    failures = []
    if 'website' not in df.columns: return failures
    invalid = df[~df['website'].astype(str).str.match(r'^https?://', na=False) & df['website'].notna()]
    for _, row in invalid.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-11", severity="INFO", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column="website",
            actual_value=row['website'], expected_value="Starts with http:// or https://",
            failure_description="Invalid URL format", suggested_fix="Append http://"
        ))
    return failures

def dq_12_mandatory_columns(df: pd.DataFrame, dataset: str, expected_cols: List[str]) -> List[ValidationFailure]:
    failures = []
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-12", severity="CRITICAL", dataset=dataset,
            company_id=None, year=None, column=str(missing), actual_value="Missing", expected_value="Present",
            failure_description="Mandatory columns missing from dataset", suggested_fix="Check source schema"
        ))
    return failures

def dq_13_duplicate_ticker(df: pd.DataFrame, dataset: str) -> List[ValidationFailure]:
    failures = []
    if 'ticker' not in df.columns: return failures
    duplicates = df[df.duplicated(subset=['ticker'], keep=False) & df['ticker'].notna()]
    for _, row in duplicates.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-13", severity="CRITICAL", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column="ticker",
            actual_value=row['ticker'], expected_value="Unique Ticker",
            failure_description="Multiple companies share the same ticker", suggested_fix="Resolve ticker conflict"
        ))
    return failures

def dq_14_fy_consistency(df: pd.DataFrame, dataset: str) -> List[ValidationFailure]:
    failures = []
    if 'year' not in df.columns: return failures
    current_year = datetime.now().year
    invalid = df[(df['year'] < 1990) | (df['year'] > current_year)]
    for _, row in invalid.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-14", severity="CRITICAL", dataset=dataset,
            company_id=row.get('company_id'), year=row.get('year'), column="year",
            actual_value=row['year'], expected_value=f"1990 to {current_year}",
            failure_description="Financial year out of bounds", suggested_fix="Check year normalization"
        ))
    return failures

def dq_15_missing_company_ref(df: pd.DataFrame, dataset: str) -> List[ValidationFailure]:
    failures = []
    if 'company_id' not in df.columns: return failures
    invalid = df[df['company_id'].isna()]
    for _, row in invalid.iterrows():
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-15", severity="CRITICAL", dataset=dataset,
            company_id=None, year=row.get('year'), column="company_id",
            actual_value="NaN", expected_value="Valid ID",
            failure_description="Missing company reference (Null ID)", suggested_fix="Assign valid company_id"
        ))
    return failures

def dq_16_coverage(df: pd.DataFrame, dataset: str, col: str, threshold: float = 0.5) -> List[ValidationFailure]:
    failures = []
    if col not in df.columns or df.empty: return failures
    null_ratio = df[col].isna().sum() / len(df)
    if null_ratio > threshold:
        failures.append(ValidationFailure(
            timestamp=current_time(), rule_id="DQ-16", severity="WARNING", dataset=dataset,
            company_id=None, year=None, column=col,
            actual_value=f"{null_ratio*100:.1f}%", expected_value=f"< {threshold*100}%",
            failure_description=f"High missing data coverage for {col}", suggested_fix="Investigate data source completeness"
        ))
    return failures
