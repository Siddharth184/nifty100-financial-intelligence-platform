"""
Master Ratio & Financial KPI Engine — Sprint 2 Day 12.

Orchestrates Profitability, Leverage, CAGR, and Cash Flow calculations across all Nifty 100 companies.
Ensures SQLite table 'financial_ratios' is schema-aligned and fully populated.
"""

import sqlite3
import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.utils.logger import get_logger
from src.db.connection import get_db_connection
from src.analytics.profitability import compute_profitability_kpis
from src.analytics.leverage_efficiency import compute_leverage_kpis
from src.analytics.cagr import compute_all_cagr_metrics
from src.analytics.cashflow_kpi import compute_cashflow_kpis, generate_capital_allocation_report

logger = get_logger(__name__)

DB_PATH = "db/nifty100.db"
OUTPUT_CAPITAL_ALLOCATION = "output/capital_allocation.csv"

# Columns to ensure in financial_ratios table
RATIO_COLUMNS_SPEC = {
    "pe_ratio": "REAL",
    "pb_ratio": "REAL",
    "debt_to_equity": "REAL",
    "npm": "REAL",
    "opm": "REAL",
    "roe": "REAL",
    "roce": "REAL",
    "roa": "REAL",
    "interest_coverage": "REAL",
    "net_debt": "REAL",
    "asset_turnover": "REAL",
    "high_leverage_flag": "INTEGER",
    "debt_free_label": "INTEGER",
    "icr_warning": "INTEGER",
    "icr_label": "TEXT",
    "free_cash_flow": "REAL",
    "cfo_quality": "REAL",
    "capex_intensity": "REAL",
    "fcf_conversion": "REAL",
    "cagr_sales_3yr": "REAL",
    "cagr_sales_5yr": "REAL",
    "cagr_pat_3yr": "REAL",
    "cagr_pat_5yr": "REAL",
    "cagr_eps_3yr": "REAL",
    "cagr_eps_5yr": "REAL",
    "is_financial_sector": "INTEGER",
    "capital_allocation_strategy": "TEXT",
    "net_profit_margin_pct": "REAL",
    "operating_profit_margin_pct": "REAL",
    "return_on_equity_pct": "REAL",
    "free_cash_flow_cr": "REAL",
    "capex_cr": "REAL",
    "earnings_per_share": "REAL",
    "book_value_per_share": "REAL",
    "dividend_payout_ratio_pct": "REAL",
    "total_debt_cr": "REAL",
    "cash_from_operations_cr": "REAL",
    "revenue_cagr_5yr": "REAL",
    "pat_cagr_5yr": "REAL",
    "eps_cagr_5yr": "REAL",
    "composite_quality_score": "REAL"
}

def ensure_table_columns(conn: sqlite3.Connection):
    """Dynamically adds missing KPI columns to financial_ratios table if needed."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(financial_ratios);")
    existing_cols = {row[1] for row in cursor.fetchall()}

    for col_name, col_type in RATIO_COLUMNS_SPEC.items():
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE financial_ratios ADD COLUMN {col_name} {col_type};")
            logger.info(f"Added missing column '{col_name}' to financial_ratios table.")
    conn.commit()

def run_ratio_engine(db_path: str = DB_PATH) -> bool:
    """Executes the master ratio engine and updates SQLite financial_ratios table."""
    logger.info("Starting Master Financial Ratio Engine execution...")
    
    if not os.path.exists(db_path):
        logger.error(f"Database file not found at {db_path}")
        return False

    with get_db_connection(db_path) as conn:
        ensure_table_columns(conn)

        # Load input tables
        pnl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
        bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
        cf = pd.read_sql_query("SELECT * FROM cashflow", conn)
        companies = pd.read_sql_query("SELECT * FROM companies", conn)
        sectors = pd.read_sql_query("SELECT * FROM sectors", conn)
        fr_existing = pd.read_sql_query("SELECT * FROM financial_ratios", conn)

        # Map financial sectors (Financials, Banks, NBFCs)
        sec_map = dict(zip(sectors["sector_id"], sectors["sector_name"])) if "sector_name" in sectors.columns else {}
        comp_sector = dict(zip(companies["company_id"], companies["sector_id"]))
        
        financial_companies = set()
        for cid, sec_id in comp_sector.items():
            sec_name = str(sec_map.get(sec_id, sec_id)).lower()
            if "financial" in sec_name or "bank" in sec_name or "nbfc" in sec_name:
                financial_companies.add(cid)

        # Merge financial statements on (company_id, year)
        merged = pd.merge(pnl, bs, on=["company_id", "year"], how="outer", suffixes=('', '_bs'))
        merged = pd.merge(merged, cf, on=["company_id", "year"], how="outer", suffixes=('', '_cf'))

        # Sort for CAGR calculations
        merged = merged.sort_values(["company_id", "year"])

        # Precompute CAGR metrics per company
        cagr_cache = {}
        for cid, grp in merged.groupby("company_id"):
            cagr_cache[cid] = compute_all_cagr_metrics(grp)

        # Compute row-level KPIs
        computed_rows = []
        capital_alloc_records = []

        for _, row in merged.iterrows():
            cid = row["company_id"]
            year = row["year"]
            if pd.isna(cid) or pd.isna(year):
                continue

            year = int(year)
            is_fin = (cid in financial_companies)

            prof_kpis = compute_profitability_kpis(row.to_dict(), is_financial=is_fin)
            lev_kpis = compute_leverage_kpis(row.to_dict(), is_financial=is_fin)
            cf_kpis = compute_cashflow_kpis(row.to_dict())

            cagr_metrics = cagr_cache.get(cid, {})

            # Calculate additional Day 12 specific KPIs
            tot_equity = row.get("total_equity")
            tot_debt = row.get("borrowings", row.get("total_debt_cr"))
            cfo_val = row.get("operating_cash_flow")
            cfi_val = row.get("investing_cash_flow")
            eps_val = row.get("eps")
            net_prof = row.get("net_profit")
            capex_val = abs(float(cfi_val)) if cfi_val is not None and not pd.isna(cfi_val) else None

            # Score computation for quality score (0 - 100)
            score = 50.0
            if prof_kpis["roe"] is not None and prof_kpis["roe"] > 15:
                score += 15
            if lev_kpis["debt_to_equity"] is not None and lev_kpis["debt_to_equity"] < 1.0:
                score += 15
            if cf_kpis["free_cash_flow"] is not None and cf_kpis["free_cash_flow"] > 0:
                score += 20
            comp_score = min(score, 100.0)

            record = {
                "company_id": cid,
                "year": year,
                "npm": prof_kpis["npm"],
                "opm": prof_kpis["opm"],
                "roe": prof_kpis["roe"],
                "roce": prof_kpis["roce"],
                "roa": prof_kpis["roa"],
                "debt_to_equity": lev_kpis["debt_to_equity"],
                "interest_coverage": lev_kpis["interest_coverage"],
                "net_debt": lev_kpis["net_debt"],
                "asset_turnover": lev_kpis["asset_turnover"],
                "high_leverage_flag": 1 if lev_kpis["high_leverage_flag"] else 0,
                "debt_free_label": 1 if lev_kpis["debt_free_label"] else 0,
                "icr_warning": 1 if lev_kpis["icr_warning"] else 0,
                "icr_label": lev_kpis["icr_label"],
                "free_cash_flow": cf_kpis["free_cash_flow"],
                "cfo_quality": cf_kpis["cfo_quality"],
                "capex_intensity": cf_kpis["capex_intensity"],
                "fcf_conversion": cf_kpis["fcf_conversion"],
                "cagr_sales_3yr": cagr_metrics.get("cagr_sales_3yr"),
                "cagr_sales_5yr": cagr_metrics.get("cagr_sales_5yr"),
                "cagr_pat_3yr": cagr_metrics.get("cagr_pat_3yr"),
                "cagr_pat_5yr": cagr_metrics.get("cagr_pat_5yr"),
                "cagr_eps_3yr": cagr_metrics.get("cagr_eps_3yr"),
                "cagr_eps_5yr": cagr_metrics.get("cagr_eps_5yr"),
                "is_financial_sector": 1 if is_fin else 0,
                "capital_allocation_strategy": cf_kpis["capital_allocation_strategy"],
                "net_profit_margin_pct": prof_kpis["npm"],
                "operating_profit_margin_pct": prof_kpis["opm"],
                "return_on_equity_pct": prof_kpis["roe"],
                "free_cash_flow_cr": cf_kpis["free_cash_flow"],
                "capex_cr": capex_val,
                "earnings_per_share": eps_val,
                "book_value_per_share": tot_equity,
                "dividend_payout_ratio_pct": None,
                "total_debt_cr": tot_debt,
                "cash_from_operations_cr": cfo_val,
                "revenue_cagr_5yr": cagr_metrics.get("cagr_sales_5yr"),
                "pat_cagr_5yr": cagr_metrics.get("cagr_pat_5yr"),
                "eps_cagr_5yr": cagr_metrics.get("cagr_eps_5yr"),
                "composite_quality_score": comp_score
            }

            computed_rows.append(record)
            capital_alloc_records.append({
                "company_id": cid,
                "year": year,
                "cfo_sign": cf_kpis["cfo_sign"],
                "cfi_sign": cf_kpis["cfi_sign"],
                "cff_sign": cf_kpis["cff_sign"],
                "pattern_label": cf_kpis["pattern_label"],
                "is_financial": is_fin,
                "free_cash_flow": cf_kpis["free_cash_flow"],
                "cfo_quality": cf_kpis["cfo_quality"],
                "strategy": cf_kpis["capital_allocation_strategy"]
            })

        computed_df = pd.DataFrame(computed_rows)

        # Merge with existing PE/PB ratios from financial_ratios table if available
        if not fr_existing.empty:
            existing_pe_pb = fr_existing[["company_id", "year", "pe_ratio", "pb_ratio"]].drop_duplicates()
            computed_df = pd.merge(computed_df, existing_pe_pb, on=["company_id", "year"], how="left")

        # Replace financial_ratios table data
        conn.execute("DELETE FROM financial_ratios;")
        computed_df.to_sql("financial_ratios", conn, if_exists="append", index=False)
        conn.commit()

        # Generate capital allocation report
        generate_capital_allocation_report(capital_alloc_records, OUTPUT_CAPITAL_ALLOCATION)

        row_count = conn.execute("SELECT COUNT(*) FROM financial_ratios;").fetchone()[0]
        logger.info(f"Successfully populated {row_count} rows in financial_ratios table.")

        if row_count >= 1000:
            print(f"\n[SUCCESS] Ratio engine executed cleanly! Total populated records: {row_count}")
            return True
        else:
            logger.error(f"Row count check failed: only {row_count} rows populated.")
            return False

def main():
    run_ratio_engine()

if __name__ == "__main__":
    main()
