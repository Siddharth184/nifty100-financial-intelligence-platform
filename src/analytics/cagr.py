"""
Compound Annual Growth Rate (CAGR) Engine — Sprint 2 Day 10.

Computes 3-Year, 5-Year, and 10-Year CAGR for:
- Revenue (Sales)
- PAT (Net Profit)
- EPS

Handles edge cases (Negative base, Turnaround, Zero base, Insufficient history).
"""

from typing import Dict, Any, Optional, Tuple
import pandas as pd


def calculate_cagr(start_val: Optional[float], end_val: Optional[float], n_years: int) -> Tuple[Optional[float], str]:
    """
    Computes CAGR percentage over n_years.
    Returns a tuple of (cagr_pct, status_flag).
    """
    if start_val is None or end_val is None or pd.isna(start_val) or pd.isna(end_val):
        return None, "MISSING_DATA"
    if n_years <= 0:
        return None, "INVALID_PERIOD"
        
    start_v = float(start_val)
    end_v = float(end_val)

    if start_v == 0:
        return None, "ZERO_BASE"

    if start_v > 0 and end_v > 0:
        cagr = ((end_v / start_v) ** (1.0 / n_years)) - 1.0
        return round(cagr * 100, 2), "VALID"

    if start_v > 0 and end_v <= 0:
        return None, "TURNAROUND_LOSS"

    if start_v < 0 and end_v > 0:
        return None, "TURNAROUND_PROFIT"

    if start_v < 0 and end_v <= 0:
        return None, "CONTINUOUS_LOSS"

    return None, "UNDEFINED"

def compute_cagr_series(df: pd.DataFrame, metric_col: str, n_years: int) -> Dict[str, Tuple[Optional[float], str]]:
    """
    Computes N-Year CAGR for a company given a time-series DataFrame of historical financial records.
    Assumes df is ordered by year ascending.
    """
    if df.empty or metric_col not in df.columns or "year" not in df.columns:
        return {"value": None, "status": "INSUFFICIENT_HISTORY"}
        
    valid_df = df.dropna(subset=["year", metric_col]).sort_values("year")
    if valid_df["year"].max() - valid_df["year"].min() < n_years:
        return {"value": None, "status": "INSUFFICIENT_HISTORY"}

    latest_year = valid_df["year"].max()
    target_start_year = latest_year - n_years

    start_row = valid_df[valid_df["year"] == target_start_year]
    end_row = valid_df[valid_df["year"] == latest_year]

    if start_row.empty or end_row.empty:
        return {"value": None, "status": "INSUFFICIENT_HISTORY"}

    start_val = start_row[metric_col].values[0]
    end_val = end_row[metric_col].values[0]

    val, status = calculate_cagr(start_val, end_val, n_years)
    return {"value": val, "status": status}

def compute_all_cagr_metrics(company_history_df: pd.DataFrame) -> Dict[str, Any]:
    """Computes 3Y, 5Y, and 10Y CAGR metrics across Sales, Net Profit, and EPS."""
    res = {}
    for metric_name, col_name in [("sales", "sales"), ("pat", "net_profit"), ("eps", "eps")]:
        for period in [3, 5, 10]:
            key = f"cagr_{metric_name}_{period}yr"
            status_key = f"cagr_{metric_name}_{period}yr_status"
            calc = compute_cagr_series(company_history_df, col_name, period)
            res[key] = calc["value"]
            res[status_key] = calc["status"]
    return res
