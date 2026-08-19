"""
Cash Flow Intelligence & Analytics Module — Sprint 5 Day 31.

Implements:
- 5-year average CFO / PAT quality score and labels (High Quality, Moderate, Accrual Risk)
- CapEx Intensity calculation and labels (Asset Light, Moderate, Capital Intensive)
- Distress signal detection (CFO < 0 and CFF > 0)
- Deleveraging flag detection (CFF < 0 and borrowings declining YoY)
- Exports output/cashflow_intelligence.xlsx and output/distress_alerts.csv
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple

from src.utils.logger import get_logger
from src.db.connection import get_db_connection
from src.analytics.profitability import safe_divide

logger = get_logger(__name__)

DB_PATH = "db/nifty100.db"
OUTPUT_CASHFLOW_XLSX = "output/cashflow_intelligence.xlsx"
OUTPUT_DISTRESS_CSV = "output/distress_alerts.csv"


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
    """CapEx Intensity = |Investing Cash Flow| / Sales * 100"""
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
    Classifies 8 Cash Flow Patterns based on signs (+/-) of CFO, CFI, CFF and CFO/PAT quality.
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


def generate_capital_allocation_report(records: List[Dict[str, Any]], output_path: str = "output/capital_allocation.csv") -> str:
    """Exports capital allocation classifications across companies to CSV with required 6 columns (Sprint 2 compatibility)."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = pd.DataFrame(records)
    required_cols = ["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "pattern_label"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    df = df[required_cols]
    df.to_csv(output_path, index=False)
    return output_path


def generate_cashflow_intelligence_report(db_path: str = DB_PATH) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes cashflow intelligence metrics across all 92 companies for the latest year and 5-year windows.
    Exports:
    - output/cashflow_intelligence.xlsx
    - output/distress_alerts.csv
    """
    logger.info("Computing Cash Flow Intelligence for all companies...")
    
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return pd.DataFrame(), pd.DataFrame()

    with get_db_connection(db_path) as conn:
        cf_cols = pd.read_sql_query("PRAGMA table_info(cashflow)", conn)['name'].tolist()
        cfo_col_name = "operating_cash_flow" if "operating_cash_flow" in cf_cols else ("operating_activity" if "operating_activity" in cf_cols else "operating_cash_flow")
        cfi_col_name = "investing_cash_flow" if "investing_cash_flow" in cf_cols else ("investing_activity" if "investing_activity" in cf_cols else "investing_cash_flow")
        cff_col_name = "financing_cash_flow" if "financing_cash_flow" in cf_cols else ("financing_activity" if "financing_activity" in cf_cols else "financing_cash_flow")

        bs_cols = pd.read_sql_query("PRAGMA table_info(balancesheet)", conn)['name'].tolist()
        b_col_name = "borrowings" if "borrowings" in bs_cols else ("total_liabilities" if "total_liabilities" in bs_cols else "borrowings")

        query = f"""
            SELECT fr.company_id, fr.year, fr.free_cash_flow, fr.free_cash_flow_cr,
                   fr.cfo_quality, fr.capex_intensity, fr.fcf_conversion,
                   fr.total_debt_cr, fr.net_debt, fr.debt_to_equity,
                   c.company_name, s.sector_name,
                   pnl.sales, pnl.operating_profit, pnl.net_profit,
                   cf.{cfo_col_name} AS operating_cash_flow,
                   cf.{cfi_col_name} AS investing_cash_flow,
                   cf.{cff_col_name} AS financing_cash_flow,
                   bs.{b_col_name} AS borrowings
            FROM financial_ratios fr
            JOIN companies c ON fr.company_id = c.company_id
            LEFT JOIN sectors s ON c.sector_id = s.sector_id
            LEFT JOIN profitandloss pnl ON fr.company_id = pnl.company_id AND fr.year = pnl.year
            LEFT JOIN cashflow cf ON fr.company_id = cf.company_id AND fr.year = cf.year
            LEFT JOIN balancesheet bs ON fr.company_id = bs.company_id AND fr.year = bs.year
            ORDER BY fr.company_id, fr.year ASC
        """
        df_all = pd.read_sql_query(query, conn)

    if df_all.empty:
        logger.warning("No financial data found in database.")
        return pd.DataFrame(), pd.DataFrame()

    intelligence_rows = []
    distress_rows = []

    for cid, df_comp in df_all.groupby("company_id"):
        df_sorted = df_comp.sort_values("year")
        latest = df_sorted.iloc[-1]
        prev = df_sorted.iloc[-2] if len(df_sorted) >= 2 else latest
        sector = latest.get("sector_name") or "General"
        
        # ── 1. CFO Quality Score (5-Year Average) ─────────────────────────────
        cfo_pat_ratios = []
        for _, r in df_sorted.tail(5).iterrows():
            cfo_val = r.get("operating_cash_flow")
            pat_val = r.get("net_profit")
            if cfo_val is not None and pat_val is not None and not pd.isna(cfo_val) and not pd.isna(pat_val):
                if float(pat_val) > 0:
                    cfo_pat_ratios.append(float(cfo_val) / float(pat_val))
        
        if cfo_pat_ratios:
            cfo_quality_score = round(float(np.mean(cfo_pat_ratios)), 2)
        else:
            cfo_quality_score = latest.get("cfo_quality")
            if cfo_quality_score is not None and not pd.isna(cfo_quality_score):
                cfo_quality_score = round(float(cfo_quality_score), 2)
            else:
                cfo_quality_score = None
                
        if cfo_quality_score is not None and not pd.isna(cfo_quality_score):
            if cfo_quality_score > 1.0:
                cfo_quality_label = "High Quality"
            elif cfo_quality_score >= 0.5:
                cfo_quality_label = "Moderate"
            else:
                cfo_quality_label = "Accrual Risk"
        else:
            cfo_quality_label = np.nan


        # ── 2. CapEx Intensity (% of Sales) ───────────────────────────────────
        latest_cfi = latest.get("investing_cash_flow")
        latest_sales = latest.get("sales")
        if latest_cfi is not None and latest_sales is not None and not pd.isna(latest_cfi) and not pd.isna(latest_sales) and float(latest_sales) > 0:
            capex_intensity_pct = round((abs(float(latest_cfi)) / float(latest_sales)) * 100.0, 2)
        else:
            capex_intensity_pct = latest.get("capex_intensity")
            if capex_intensity_pct is not None and not pd.isna(capex_intensity_pct):
                capex_intensity_pct = round(float(capex_intensity_pct), 2)
            else:
                capex_intensity_pct = None

        if capex_intensity_pct is not None and not pd.isna(capex_intensity_pct):
            if capex_intensity_pct < 3.0:
                capex_label = "Asset Light"
            elif capex_intensity_pct <= 8.0:
                capex_label = "Moderate"
            else:
                capex_label = "Capital Intensive"
        else:
            capex_label = np.nan


        # ── 3. FCF CAGR 5-Year ────────────────────────────────────────────────
        fcf_series = df_sorted["free_cash_flow_cr"].dropna() if "free_cash_flow_cr" in df_sorted.columns and df_sorted["free_cash_flow_cr"].notna().any() else df_sorted["free_cash_flow"].dropna()
        if len(fcf_series) >= 5:
            start_fcf = fcf_series.iloc[-5]
            end_fcf = fcf_series.iloc[-1]
            if start_fcf > 0 and end_fcf > 0:
                fcf_cagr_5yr = round((((end_fcf / start_fcf) ** (1.0 / 4.0)) - 1.0) * 100.0, 2)
            else:
                fcf_cagr_5yr = None
        else:
            fcf_cagr_5yr = None

        # ── 4. FCF Conversion % ───────────────────────────────────────────────
        latest_cfo = latest.get("operating_cash_flow")
        latest_fcf = fcf_series.iloc[-1] if not fcf_series.empty else None
        if latest_fcf is not None and latest_cfo is not None and not pd.isna(latest_fcf) and not pd.isna(latest_cfo) and float(latest_cfo) > 0:
            fcf_conversion_pct = round((float(latest_fcf) / float(latest_cfo)) * 100.0, 2)
        else:
            fcf_conversion_pct = latest.get("fcf_conversion")
            if fcf_conversion_pct is not None and not pd.isna(fcf_conversion_pct):
                fcf_conversion_pct = round(float(fcf_conversion_pct), 2)
            else:
                fcf_conversion_pct = None

        # ── 5. Distress Signal Detection ──────────────────────────────────────
        latest_cff = latest.get("financing_cash_flow")
        cfo_val_num = float(latest_cfo) if latest_cfo is not None and not pd.isna(latest_cfo) else 0.0
        cff_val_num = float(latest_cff) if latest_cff is not None and not pd.isna(latest_cff) else 0.0
        
        distress_flag = bool(cfo_val_num < 0 and cff_val_num > 0)
        
        if distress_flag:
            distress_rows.append({
                "company_id": cid,
                "sector": sector,
                "CFO": round(cfo_val_num, 2),
                "CFF": round(cff_val_num, 2),
                "latest_net_profit": round(float(latest.get("net_profit", 0.0) or 0.0), 2),
                "distress_reason": "Negative operating cash flow accompanied by positive financing cash flow (burning cash from operations while relying on external funding)"
            })

        # ── 6. Deleveraging Flag Detection ────────────────────────────────────
        debt_curr = latest.get("borrowings") if (latest.get("borrowings") is not None and not pd.isna(latest.get("borrowings"))) else (
            latest.get("total_debt_cr") if (latest.get("total_debt_cr") is not None and not pd.isna(latest.get("total_debt_cr"))) else latest.get("net_debt")
        )
        debt_prev = prev.get("borrowings") if (prev.get("borrowings") is not None and not pd.isna(prev.get("borrowings"))) else (
            prev.get("total_debt_cr") if (prev.get("total_debt_cr") is not None and not pd.isna(prev.get("total_debt_cr"))) else prev.get("net_debt")
        )
        
        debt_declining = False
        if debt_curr is not None and debt_prev is not None and not pd.isna(debt_curr) and not pd.isna(debt_prev):
            debt_declining = bool(float(debt_curr) < float(debt_prev))

        deleveraging_flag = bool(cff_val_num < 0 and debt_declining)

        # ── 7. Capital Allocation Label ───────────────────────────────────────
        latest_cfi = latest.get("investing_cash_flow")
        _, _, _, pattern_label = classify_cashflow_pattern(
            latest_cfo, latest_cfi, latest_cff, latest.get("net_profit")
        )

        intelligence_rows.append({
            "company_id": cid,
            "sector": sector,
            "cfo_quality_score": cfo_quality_score,
            "cfo_quality_label": cfo_quality_label,
            "capex_intensity_pct": capex_intensity_pct,
            "capex_label": capex_label,
            "fcf_cagr_5yr": fcf_cagr_5yr,
            "fcf_conversion_pct": fcf_conversion_pct,
            "distress_flag": distress_flag,
            "deleveraging_flag": deleveraging_flag,
            "capital_allocation_label": pattern_label
        })

    intel_df = pd.DataFrame(intelligence_rows)
    distress_df = pd.DataFrame(distress_rows)

    os.makedirs("output", exist_ok=True)
    if not intel_df.empty:
        intel_df.to_excel(OUTPUT_CASHFLOW_XLSX, index=False, sheet_name="Cash Flow Intelligence")
        logger.info(f"Generated {OUTPUT_CASHFLOW_XLSX} with {len(intel_df)} companies.")

    if not distress_df.empty:
        distress_df.to_csv(OUTPUT_DISTRESS_CSV, index=False)
        logger.info(f"Generated {OUTPUT_DISTRESS_CSV} with {len(distress_df)} distress alert companies.")
    else:
        pd.DataFrame(columns=["company_id", "sector", "CFO", "CFF", "latest_net_profit", "distress_reason"]).to_csv(OUTPUT_DISTRESS_CSV, index=False)

    return intel_df, distress_df


if __name__ == "__main__":
    idf, ddf = generate_cashflow_intelligence_report()
    print(f"Cash Flow Intelligence Rows: {len(idf)}")
    print(f"Distress Alerts: {len(ddf)}")
