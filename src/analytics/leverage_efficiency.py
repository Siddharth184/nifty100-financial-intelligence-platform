"""
Leverage & Efficiency Ratios Analytics Engine — Sprint 2 Day 09.

Computes leverage and efficiency KPIs:
- Debt-to-Equity (D/E)
- Interest Coverage Ratio (ICR)
- Net Debt
- Asset Turnover
- Flags & Labels: high_leverage_flag, debt_free_label, icr_warning.
"""

from typing import Dict, Any, Optional
import pandas as pd
from src.analytics.profitability import safe_divide


def calculate_debt_to_equity(borrowings: Optional[float], total_equity: Optional[float]) -> Optional[float]:
    """Debt to Equity = Borrowings / Total Equity"""
    if total_equity is not None and not pd.isna(total_equity) and float(total_equity) <= 0:
        return None
    b = borrowings if borrowings is not None and not pd.isna(borrowings) else 0.0
    ratio = safe_divide(b, total_equity)
    return round(ratio, 4) if ratio is not None else None

def calculate_interest_coverage(operating_profit: Optional[float], interest: Optional[float]) -> Optional[float]:
    """Interest Coverage Ratio (ICR) = Operating Profit / Interest"""
    if interest is None or pd.isna(interest) or float(interest) <= 0:
        return None  # No interest expense or zero interest
    ratio = safe_divide(operating_profit, interest)
    return round(ratio, 2) if ratio is not None else None

def calculate_net_debt(borrowings: Optional[float], cash_and_equivalents: Optional[float] = 0.0) -> Optional[float]:
    """Net Debt = Total Borrowings - Cash and Equivalents"""
    b = float(borrowings) if borrowings is not None and not pd.isna(borrowings) else 0.0
    c = float(cash_and_equivalents) if cash_and_equivalents is not None and not pd.isna(cash_and_equivalents) else 0.0
    return round(b - c, 2)

def calculate_asset_turnover(sales: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """Asset Turnover = Sales / Total Assets"""
    ratio = safe_divide(sales, total_assets)
    return round(ratio, 4) if ratio is not None else None

def compute_leverage_kpis(row: Dict[str, Any], is_financial: bool = False) -> Dict[str, Any]:
    """Computes leverage and efficiency KPIs and evaluates risk flags."""
    borrowings = row.get("borrowings")
    if borrowings is None or pd.isna(borrowings):
        borrowings = row.get("total_debt_cr", row.get("raw_total_debt_cr"))

    total_equity = row.get("total_equity")
    operating_profit = row.get("operating_profit")
    interest = row.get("interest")
    sales = row.get("sales")
    total_assets = row.get("total_assets")
    cash = row.get("investments", 0.0)

    # 1. Debt-to-Equity: Calculate if borrowings present, otherwise fallback to raw_debt_to_equity
    if borrowings is not None and not pd.isna(borrowings) and float(borrowings) > 0 and total_equity is not None and not pd.isna(total_equity) and float(total_equity) > 0:
        de_ratio = calculate_debt_to_equity(borrowings, total_equity)
    elif "raw_debt_to_equity" in row and row["raw_debt_to_equity"] is not None and not pd.isna(row["raw_debt_to_equity"]):
        de_ratio = round(float(row["raw_debt_to_equity"]), 4)
    elif "debt_to_equity" in row and row["debt_to_equity"] is not None and not pd.isna(row["debt_to_equity"]):
        de_ratio = round(float(row["debt_to_equity"]), 4)
    elif borrowings is not None and not pd.isna(borrowings):
        de_ratio = calculate_debt_to_equity(borrowings, total_equity)
    else:
        de_ratio = None

    # 2. Interest Coverage Ratio: Calculate if interest present, otherwise fallback to raw_interest_coverage
    if is_financial:
        icr = None
    elif interest is not None and not pd.isna(interest):
        icr = calculate_interest_coverage(operating_profit, interest)
    elif "raw_interest_coverage" in row and row["raw_interest_coverage"] is not None and not pd.isna(row["raw_interest_coverage"]):
        icr = round(float(row["raw_interest_coverage"]), 2)
    elif "interest_coverage" in row and row["interest_coverage"] is not None and not pd.isna(row["interest_coverage"]):
        icr = round(float(row["interest_coverage"]), 2)
    else:
        icr = None

    net_debt = calculate_net_debt(borrowings, cash)
    asset_turnover = calculate_asset_turnover(sales, total_assets)

    # Risk evaluation & ICR Label
    b_val = float(borrowings) if borrowings is not None and not pd.isna(borrowings) else (
        de_ratio * float(total_equity) if de_ratio is not None and total_equity is not None and not pd.isna(total_equity) and float(total_equity) > 0 else 0.0
    )
    debt_free = (b_val <= 0) or (de_ratio == 0.0)
    high_leverage = (de_ratio is not None and de_ratio > 2.0) if not is_financial else False
    icr_warn = (icr is not None and icr < 1.5) if not is_financial else False

    if debt_free:
        icr_lbl = "DEBT_FREE"
    elif is_financial:
        icr_lbl = "FINANCIAL_SECTOR"
    elif icr is None:
        icr_lbl = "NO_INTEREST_EXPENSE"
    elif icr < 1.5:
        icr_lbl = "HIGH_RISK"
    elif icr < 3.0:
        icr_lbl = "MODERATE_RISK"
    else:
        icr_lbl = "SAFE"

    return {
        "debt_to_equity": de_ratio,
        "interest_coverage": icr,
        "net_debt": net_debt,
        "asset_turnover": asset_turnover,
        "high_leverage_flag": high_leverage,
        "debt_free_label": debt_free,
        "icr_warning": icr_warn,
        "icr_label": icr_lbl
    }

