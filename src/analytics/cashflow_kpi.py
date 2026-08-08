"""
Cash Flow KPIs & Capital Allocation Engine — Sprint 2 Day 11.

Computes:
- Free Cash Flow (FCF)
- CFO Quality (CFO / Net Profit)
- CapEx Intensity (CapEx / Sales)
- FCF Conversion (FCF / CFO)
- Capital Allocation Strategy classification
- Exports capital_allocation.csv summary report
"""

from typing import Dict, Any, Optional, List, Tuple
import os
import numpy as np
import pandas as pd
from src.analytics.profitability import safe_divide

def calculate_free_cash_flow(operating_cf: Optional[float], investing_cf: Optional[float]) -> Optional[float]:
    """Free Cash Flow = Operating Cash Flow + Investing Cash Flow (investing_cf is usually negative)."""
    if operating_cf is None or pd.isna(operating_cf):
        return None
    inv = float(investing_cf) if investing_cf is not None and not pd.isna(investing_cf) else 0.0
    return round(float(operating_cf) + inv, 2)

def calculate_cfo_quality(operating_cf: Optional[float], net_profit: Optional[float]) -> Optional[float]:
    """CFO Quality = Operating Cash Flow / Net Profit"""
    if net_profit is None or pd.isna(net_profit) or float(net_profit) <= 0:
        return None
    ratio = safe_divide(operating_cf, net_profit)
    return round(ratio, 4) if ratio is not None else None

def calculate_capex_intensity(investing_cf: Optional[float], sales: Optional[float]) -> Optional[float]:
    """CapEx Intensity = |Investing Cash Flow| / Sales"""
    if sales is None or pd.isna(sales) or float(sales) <= 0:
        return None
    inv = abs(float(investing_cf)) if investing_cf is not None and not pd.isna(investing_cf) else 0.0
    ratio = safe_divide(inv, sales)
    return round(ratio * 100, 2) if ratio is not None else None

def calculate_fcf_conversion(fcf: Optional[float], operating_cf: Optional[float]) -> Optional[float]:
    """FCF Conversion = (FCF / Operating Cash Flow) * 100"""
    if operating_cf is None or pd.isna(operating_cf) or float(operating_cf) <= 0:
        return None
    ratio = safe_divide(fcf, operating_cf)
    return round(ratio * 100, 2) if ratio is not None else None

def classify_cashflow_pattern(
    cfo: Optional[float], 
    cfi: Optional[float], 
    cff: Optional[float], 
    net_profit: Optional[float] = None
) -> Tuple[str, str, str, str]:
    """
    Classifies 8 Cash Flow Patterns based on signs (+/-) of CFO, CFI, CFF and CFO/PAT quality:
    - (+,-,-) = Reinvestor (or Shareholder Returns if high CFO/PAT > 1.0)
    - (+,+,-) = Liquidating Assets
    - (-,+,+) = Distress Signal
    - (-,-,+) = Growth Funded by Debt
    - (+,+,+) = Cash Accumulator
    - (-,-,-) = Pre-Revenue
    - (+,-,+) = Mixed
    - (-,+,-) = Distress Signal
    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label).
    """
    cfo_val = float(cfo) if cfo is not None and not pd.isna(cfo) else 0.0
    cfi_val = float(cfi) if cfi is not None and not pd.isna(cfi) else 0.0
    cff_val = float(cff) if cff is not None and not pd.isna(cff) else 0.0

    cfo_sign = "+" if cfo_val >= 0 else "-"
    cfi_sign = "+" if cfi_val >= 0 else "-"
    cff_sign = "+" if cff_val >= 0 else "-"

    signs = (cfo_sign, cfi_sign, cff_sign)

    if signs == ("+", "-", "-"):
        cfo_pat = (cfo_val / net_profit) if (net_profit is not None and not pd.isna(net_profit) and float(net_profit) > 0) else None
        if cfo_pat is not None and cfo_pat > 1.0:
            pattern_label = "Shareholder Returns"
        else:
            pattern_label = "Reinvestor"
    elif signs == ("+", "+", "-"):
        pattern_label = "Liquidating Assets"
    elif signs == ("-", "+", "+"):
        pattern_label = "Distress Signal"
    elif signs == ("-", "-", "+"):
        pattern_label = "Growth Funded by Debt"
    elif signs == ("+", "+", "+"):
        pattern_label = "Cash Accumulator"
    elif signs == ("-", "-", "-"):
        pattern_label = "Pre-Revenue"
    elif signs == ("+", "-", "+"):
        pattern_label = "Mixed"
    else:
        # (-, +, -)
        pattern_label = "Distress Signal"

    return cfo_sign, cfi_sign, cff_sign, pattern_label

def classify_capital_allocation(row: Dict[str, Any]) -> str:
    """Classifies company capital allocation strategy based on cash flow metrics."""
    cfo = float(row.get("operating_cash_flow", 0.0) or 0.0)
    cfi = float(row.get("investing_cash_flow", 0.0) or 0.0)
    fcf = float(row.get("free_cash_flow", 0.0) or 0.0)
    capex = abs(cfi)

    if fcf < 0:
        return "CAPITAL_STRAIN"
    if capex > (0.5 * cfo) and cfo > 0:
        return "EXPANSIVE_GROWTH"
    if fcf > 0 and capex < (0.2 * cfo):
        return "CASH_HOARDING"
    if fcf > 0:
        return "BALANCED_ALLOCATION"
    return "NEUTRAL"

def compute_cashflow_kpis(row: Dict[str, Any]) -> Dict[str, Any]:
    """Computes all cash flow KPIs, 8 pattern labels, and capital allocation strategy for a financial record."""
    cfo = row.get("operating_cash_flow")
    cfi = row.get("investing_cash_flow")
    cff = row.get("financing_cash_flow")
    net_profit = row.get("net_profit")
    sales = row.get("sales")

    fcf = calculate_free_cash_flow(cfo, cfi)
    cfo_quality = calculate_cfo_quality(cfo, net_profit)
    capex_intensity = calculate_capex_intensity(cfi, sales)
    fcf_conv = calculate_fcf_conversion(fcf, cfo)

    eval_row = {
        "operating_cash_flow": cfo,
        "investing_cash_flow": cfi,
        "free_cash_flow": fcf,
        "net_profit": net_profit
    }
    strategy = classify_capital_allocation(eval_row)
    cfo_s, cfi_s, cff_s, pattern_label = classify_cashflow_pattern(cfo, cfi, cff, net_profit)

    return {
        "free_cash_flow": fcf,
        "cfo_quality": cfo_quality,
        "capex_intensity": capex_intensity,
        "fcf_conversion": fcf_conv,
        "capital_allocation_strategy": strategy,
        "cfo_sign": cfo_s,
        "cfi_sign": cfi_s,
        "cff_sign": cff_s,
        "pattern_label": pattern_label
    }

def generate_capital_allocation_report(records: List[Dict[str, Any]], output_path: str = "output/capital_allocation.csv") -> str:
    """Exports capital allocation classifications across companies to CSV with required 6 columns."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = pd.DataFrame(records)
    
    # Required six columns per Sprint 2 Day 11 specification
    required_cols = ["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "pattern_label"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    # Keep exactly the six required columns
    df = df[required_cols]
    df.to_csv(output_path, index=False)
    return output_path


