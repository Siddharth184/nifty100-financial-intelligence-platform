"""
Capital Allocation Report Audit & Pattern Shift Engine — Sprint 5 Day 32.

Audits output/capital_allocation.csv across all 92 companies and all company-years.
Generates:
- output/pattern_changes.csv (tracks year-over-year capital allocation pattern shifts)
- Latest-year distribution summary across all 8 cash flow patterns.
"""

import os
import pandas as pd
from typing import List, Tuple

from src.utils.logger import get_logger
from src.db.connection import get_db_connection
from src.analytics.cashflow_kpis import classify_cashflow_pattern

logger = get_logger(__name__)


DB_PATH = "db/nifty100.db"
OUTPUT_CAPITAL_CSV = "output/capital_allocation.csv"
OUTPUT_PATTERN_CHANGES_CSV = "output/pattern_changes.csv"

VALID_PATTERNS = {
    "Reinvestor",
    "Shareholder Returns",
    "Liquidating Assets",
    "Distress Signal",
    "Growth Funded by Debt",
    "Cash Accumulator",
    "Pre-Revenue",
    "Mixed"
}


def audit_and_build_capital_allocation(db_path: str = DB_PATH) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Audits and regenerates output/capital_allocation.csv across all 92 companies & company-years.
    Tracks YoY pattern changes into output/pattern_changes.csv.
    """
    logger.info("Auditing Capital Allocation Report across all company-years...")

    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return pd.DataFrame(), pd.DataFrame()

    with get_db_connection(db_path) as conn:
        cf_cols = pd.read_sql_query("PRAGMA table_info(cashflow)", conn)['name'].tolist()
        cfo_col_name = "operating_cash_flow" if "operating_cash_flow" in cf_cols else ("operating_activity" if "operating_activity" in cf_cols else "operating_cash_flow")
        cfi_col_name = "investing_cash_flow" if "investing_cash_flow" in cf_cols else ("investing_activity" if "investing_activity" in cf_cols else "investing_cash_flow")
        cff_col_name = "financing_cash_flow" if "financing_cash_flow" in cf_cols else ("financing_activity" if "financing_activity" in cf_cols else "financing_cash_flow")

        df_cf = pd.read_sql_query(f"""
            SELECT fr.company_id, fr.year,
                   cf.{cfo_col_name} AS operating_cash_flow,
                   cf.{cfi_col_name} AS investing_cash_flow,
                   cf.{cff_col_name} AS financing_cash_flow,
                   pnl.net_profit
            FROM financial_ratios fr
            LEFT JOIN cashflow cf ON fr.company_id = cf.company_id AND fr.year = cf.year
            LEFT JOIN profitandloss pnl ON fr.company_id = pnl.company_id AND fr.year = pnl.year
            ORDER BY fr.company_id, fr.year ASC
        """, conn)

    if df_cf.empty:
        logger.warning("No cashflow data in database for capital allocation audit.")
        return pd.DataFrame(), pd.DataFrame()

    records = []
    for _, row in df_cf.iterrows():
        cid = row["company_id"]
        yr = int(row["year"])
        cfo = row.get("operating_cash_flow")
        cfi = row.get("investing_cash_flow")
        cff = row.get("financing_cash_flow")
        np_val = row.get("net_profit")

        cfo_s, cfi_s, cff_s, pattern_label = classify_cashflow_pattern(cfo, cfi, cff, np_val)

        records.append({
            "company_id": cid,
            "year": yr,
            "cfo_sign": cfo_s,
            "cfi_sign": cfi_s,
            "cff_sign": cff_s,
            "pattern_label": pattern_label
        })

    cap_df = pd.DataFrame(records)
    
    # Remove duplicate company_id, year if any
    cap_df = cap_df.drop_duplicates(subset=["company_id", "year"]).reset_index(drop=True)

    os.makedirs("output", exist_ok=True)
    cap_df.to_csv(OUTPUT_CAPITAL_CSV, index=False)
    logger.info(f"Generated {OUTPUT_CAPITAL_CSV} with {len(cap_df)} company-year records across {cap_df['company_id'].nunique()} companies.")

    # ── Track Year-over-Year Pattern Shifts ───────────────────────────────────
    pattern_change_rows = []
    for cid, g in cap_df.groupby("company_id"):
        g_sorted = g.sort_values("year")
        if len(g_sorted) >= 2:
            prev_row = g_sorted.iloc[-2]
            curr_row = g_sorted.iloc[-1]
            if prev_row["pattern_label"] != curr_row["pattern_label"]:
                pattern_change_rows.append({
                    "company_id": cid,
                    "previous_year": int(prev_row["year"]),
                    "previous_pattern": prev_row["pattern_label"],
                    "current_year": int(curr_row["year"]),
                    "current_pattern": curr_row["pattern_label"]
                })

    changes_df = pd.DataFrame(pattern_change_rows)
    if not changes_df.empty:
        changes_df.to_csv(OUTPUT_PATTERN_CHANGES_CSV, index=False)
        logger.info(f"Generated {OUTPUT_PATTERN_CHANGES_CSV} with {len(changes_df)} YoY pattern shifts.")
    else:
        pd.DataFrame(columns=[
            "company_id", "previous_year", "previous_pattern", "current_year", "current_pattern"
        ]).to_csv(OUTPUT_PATTERN_CHANGES_CSV, index=False)

    return cap_df, changes_df


if __name__ == "__main__":
    cdf, ch_df = audit_and_build_capital_allocation()
    print(f"Total Capital Allocation Records: {len(cdf)}")
    print(f"Pattern Shifts Detected: {len(ch_df)}")
