"""
Profitability Ratios Analytics Engine — Sprint 2 Day 08.

Computes core profitability KPIs:
- Net Profit Margin (NPM)
- Operating Profit Margin (OPM)
- Return on Equity (ROE)
- Return on Capital Employed (ROCE)
- Return on Assets (ROA)

Handles edge cases: zero denominators, negative equity, financial sector ROCE logic.
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

def safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Safely divides two values, returning None on zero, NaN, or null denominator."""
    if numerator is None or denominator is None:
        return None
    if pd.isna(numerator) or pd.isna(denominator):
        return None
    try:
        num = float(numerator)
        den = float(denominator)
        if den == 0 or np.isnan(den) or np.isnan(num):
            return None
        return round(num / den, 4)
    except (ValueError, TypeError, ZeroDivisionError):
        return None

def calculate_npm(net_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
    """Net Profit Margin = (Net Profit / Sales) * 100"""
    ratio = safe_divide(net_profit, sales)
    return round(ratio * 100, 2) if ratio is not None else None

def calculate_opm(operating_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
    """Operating Profit Margin = (Operating Profit / Sales) * 100"""
    ratio = safe_divide(operating_profit, sales)
    return round(ratio * 100, 2) if ratio is not None else None

def calculate_roe(net_profit: Optional[float], total_equity: Optional[float]) -> Optional[float]:
    """
    Return on Equity = (Net Profit / Total Equity) * 100.
    Returns None if equity is zero or negative (to prevent misleading figures).
    """
    if total_equity is not None and not pd.isna(total_equity) and float(total_equity) <= 0:
        return None
    ratio = safe_divide(net_profit, total_equity)
    return round(ratio * 100, 2) if ratio is not None else None

def calculate_roce(
    operating_profit: Optional[float], 
    total_assets: Optional[float], 
    current_liabilities: Optional[float] = 0.0,
    is_financial: bool = False
) -> Optional[float]:
    """
    Return on Capital Employed = (Operating Profit / Capital Employed) * 100.
    Capital Employed = Total Assets - Current Liabilities.
    Suppressed for financial sector firms (Banks/NBFCs).
    """
    if is_financial:
        return None
    curr_liab = current_liabilities if current_liabilities is not None and not pd.isna(current_liabilities) else 0.0
    if total_assets is None or pd.isna(total_assets):
        return None
    capital_employed = float(total_assets) - float(curr_liab)
    if capital_employed <= 0:
        return None
    ratio = safe_divide(operating_profit, capital_employed)
    return round(ratio * 100, 2) if ratio is not None else None

def calculate_roa(net_profit: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """Return on Assets = (Net Profit / Total Assets) * 100"""
    if total_assets is not None and not pd.isna(total_assets) and float(total_assets) <= 0:
        return None
    ratio = safe_divide(net_profit, total_assets)
    return round(ratio * 100, 2) if ratio is not None else None

def compute_profitability_kpis(row: Dict[str, Any], is_financial: bool = False) -> Dict[str, Optional[float]]:
    """Computes all profitability KPIs for a given financial record."""
    sales = row.get("sales")
    net_profit = row.get("net_profit")
    operating_profit = row.get("operating_profit")
    total_equity = row.get("total_equity")
    total_assets = row.get("total_assets")
    current_liabilities = row.get("other_liabilities", 0.0)

    return {
        "npm": calculate_npm(net_profit, sales),
        "opm": calculate_opm(operating_profit, sales),
        "roe": calculate_roe(net_profit, total_equity),
        "roce": calculate_roce(operating_profit, total_assets, current_liabilities, is_financial),
        "roa": calculate_roa(net_profit, total_assets)
    }
