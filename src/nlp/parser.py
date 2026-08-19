r"""
Analysis Text Parser — Sprint 5 Day 29.

Parses text fields in data/raw/analysis.xlsx using regex.
Target fields: compounded_sales_growth, compounded_profit_growth, stock_price_cagr, roe.
Regex pattern: (\d+)\s*Years?:?\s*(-?[\d.]+)%

Generates:
- output/analysis_parsed.csv (company_id, metric_type, period_years, value_pct)
- output/parse_failures.csv (unmatched text entries)
- Cross-validates parsed CAGRs against database financial_ratios and flags divergence > 5%.
"""

import os
import re
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any

from src.utils.logger import get_logger
from src.db.connection import get_db_connection

logger = get_logger(__name__)

ANALYSIS_FILE = "data/raw/analysis.xlsx"
DB_PATH = "db/nifty100.db"
OUTPUT_PARSED_CSV = "output/analysis_parsed.csv"
OUTPUT_FAILURES_CSV = "output/parse_failures.csv"
OUTPUT_DIVERGENCE_CSV = "output/cagr_divergence.csv"

# Required regex pattern matching e.g. "10 Years: 21%", "5 Years: -3.5%", "3 Years: 17%"
REGEX_PATTERN = r"(\d+)\s*Years?:?\s*(-?[\d.]+)%"

TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe"
]


def parse_text_entry(text: str) -> List[Tuple[int, float]]:
    """
    Parses a single text cell containing year-period percentage metrics.
    Returns list of (period_years, value_pct) tuples.
    """
    if text is None or pd.isna(text):
        return []
    
    text_str = str(text)
    matches = re.findall(REGEX_PATTERN, text_str, re.IGNORECASE)
    results = []
    for period_str, val_str in matches:
        try:
            period = int(period_str)
            val = float(val_str)
            results.append((period, val))
        except (ValueError, TypeError):
            continue
    return results


def load_analysis_dataframe(filepath: str) -> pd.DataFrame:
    """
    Loads analysis.xlsx with automatic header detection and column normalization.
    """
    if not os.path.exists(filepath):
        return pd.DataFrame()
    
    xl = pd.ExcelFile(filepath)
    all_dfs = []
    
    for sheet in xl.sheet_names:
        matched_df = None
        # Try header offsets 0, 1, 2, 3
        for h in range(4):
            try:
                df_try = pd.read_excel(filepath, sheet_name=sheet, header=h)
                # Normalize column names
                norm_cols = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df_try.columns]
                df_try.columns = norm_cols
                
                # Check if company_id or any target field is present
                if any(tf in norm_cols for tf in TARGET_FIELDS) or "company_id" in norm_cols or "company" in norm_cols:
                    matched_df = df_try
                    break
            except Exception:
                continue
        
        if matched_df is None:
            # Fallback to header=0
            matched_df = pd.read_excel(filepath, sheet_name=sheet)
            matched_df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in matched_df.columns]
            
        all_dfs.append(matched_df)
        
    return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()


def run_analysis_parser(
    analysis_file: str = ANALYSIS_FILE,
    db_path: str = DB_PATH
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Reads analysis.xlsx, applies regex parsing on target fields,
    generates parsed & failure CSVs, and cross-validates against database ratios.
    """
    logger.info("Starting Analysis Text Parser...")
    
    if not os.path.exists(analysis_file):
        logger.error(f"Analysis file not found: {analysis_file}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    df_raw = load_analysis_dataframe(analysis_file)
    if df_raw.empty:
        logger.warning("Empty data in analysis.xlsx")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    parsed_rows = []
    failure_rows = []
    
    company_col = None
    for candidate in ["company_id", "company", "ticker", "company_name", "id"]:
        if candidate in df_raw.columns:
            company_col = candidate
            break
    if not company_col:
        company_col = df_raw.columns[0]
    
    for idx, row in df_raw.iterrows():
        cid = str(row[company_col]).strip() if pd.notna(row[company_col]) else f"ROW_{idx}"
        
        for field in TARGET_FIELDS:
            if field not in df_raw.columns:
                continue
            
            raw_text = row[field]
            if raw_text is None or pd.isna(raw_text) or str(raw_text).strip() == "" or str(raw_text).strip().lower() == "nan":
                continue
            
            matches = parse_text_entry(str(raw_text))
            if matches:
                for period_years, value_pct in matches:
                    parsed_rows.append({
                        "company_id": cid,
                        "metric_type": field,
                        "period_years": period_years,
                        "value_pct": value_pct
                    })
            else:
                failure_rows.append({
                    "company_id": cid,
                    "field_name": field,
                    "raw_text": str(raw_text),
                    "reason": "Regex pattern mismatch"
                })
    
    parsed_df = pd.DataFrame(parsed_rows)
    failures_df = pd.DataFrame(failure_rows)
    
    # Export parsed results and failure logs
    os.makedirs("output", exist_ok=True)
    if not parsed_df.empty:
        parsed_df = parsed_df.drop_duplicates(subset=["company_id", "metric_type", "period_years"])
        parsed_df.to_csv(OUTPUT_PARSED_CSV, index=False)
        logger.info(f"Generated {OUTPUT_PARSED_CSV} with {len(parsed_df)} parsed records.")
    else:
        pd.DataFrame(columns=["company_id", "metric_type", "period_years", "value_pct"]).to_csv(OUTPUT_PARSED_CSV, index=False)
        
    if not failures_df.empty:
        failures_df.to_csv(OUTPUT_FAILURES_CSV, index=False)
        logger.info(f"Generated {OUTPUT_FAILURES_CSV} with {len(failures_df)} failure records.")
    else:
        pd.DataFrame(columns=["company_id", "field_name", "raw_text", "reason"]).to_csv(OUTPUT_FAILURES_CSV, index=False)

    # ── Cross-Validation with Database Ratio Engine ──────────────────────────
    divergence_rows = []
    if os.path.exists(db_path) and not parsed_df.empty:
        with get_db_connection(db_path) as conn:
            query = """
                SELECT company_id, year, cagr_sales_5yr, cagr_pat_5yr, roe,
                       revenue_cagr_5yr, pat_cagr_5yr, return_on_equity_pct
                FROM financial_ratios
                WHERE year = (SELECT MAX(year) FROM financial_ratios fr2 WHERE fr2.company_id = financial_ratios.company_id)
            """
            db_ratios = pd.read_sql_query(query, conn)
        
        db_map = {row["company_id"]: row for _, row in db_ratios.iterrows()}
        
        for _, p_row in parsed_df.iterrows():
            cid = p_row["company_id"]
            metric = p_row["metric_type"]
            period = p_row["period_years"]
            parsed_val = p_row["value_pct"]
            
            if cid in db_map and period == 5:
                db_record = db_map[cid]
                computed_val = None
                
                if metric == "compounded_sales_growth":
                    computed_val = db_record.get("revenue_cagr_5yr") or db_record.get("cagr_sales_5yr")
                elif metric == "compounded_profit_growth":
                    computed_val = db_record.get("pat_cagr_5yr") or db_record.get("cagr_pat_5yr")
                elif metric == "roe":
                    computed_val = db_record.get("return_on_equity_pct") or db_record.get("roe")
                
                if computed_val is not None and not pd.isna(computed_val):
                    divergence = abs(float(parsed_val) - float(computed_val))
                    if divergence > 5.0:
                        divergence_rows.append({
                            "company_id": cid,
                            "metric_type": metric,
                            "period_years": period,
                            "parsed_value_pct": parsed_val,
                            "computed_value_pct": round(float(computed_val), 2),
                            "divergence_pct": round(divergence, 2),
                            "status": "FLAGGED_FOR_MANUAL_REVIEW"
                        })
    
    divergence_df = pd.DataFrame(divergence_rows)
    if not divergence_df.empty:
        divergence_df.to_csv(OUTPUT_DIVERGENCE_CSV, index=False)
        logger.info(f"Flagged {len(divergence_df)} CAGR divergence records (>5%) in {OUTPUT_DIVERGENCE_CSV}.")
    else:
        pd.DataFrame(columns=[
            "company_id", "metric_type", "period_years", "parsed_value_pct",
            "computed_value_pct", "divergence_pct", "status"
        ]).to_csv(OUTPUT_DIVERGENCE_CSV, index=False)
        
    return parsed_df, failures_df, divergence_df


if __name__ == "__main__":
    p_df, f_df, d_df = run_analysis_parser()
    print(f"Parsed: {len(p_df)} rows, Failures: {len(f_df)} rows, Divergences >5%: {len(d_df)} rows")
