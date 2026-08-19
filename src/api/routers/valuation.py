"""
Valuation Router — Sprint 6 Day 40.

GET /api/v1/market-cap/{ticker} — Historical P/E, P/B, market cap data
"""

import pandas as pd
from fastapi import APIRouter, HTTPException

from src.db.connection import get_db_connection

router = APIRouter()
DB_PATH = "db/nifty100.db"


@router.get("/market-cap/{ticker}")
async def get_market_cap_data(ticker: str):
    """
    Returns historical market cap, P/E, P/B, and valuation metrics for a company.
    Note: Dividend yield is unavailable in source data and is not fabricated.
    """
    with get_db_connection(DB_PATH) as conn:
        # Resolve company
        row = conn.execute(
            "SELECT company_id, company_name FROM companies WHERE UPPER(ticker) = UPPER(?) OR UPPER(company_id) = UPPER(?)",
            (ticker, ticker)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        cid, name = row

        # Market cap history
        mc_df = pd.read_sql_query(
            "SELECT * FROM market_cap WHERE company_id = ? ORDER BY date",
            conn, params=[cid]
        )

        # Valuation ratios by year
        ratios_df = pd.read_sql_query("""
            SELECT year, pe_ratio, pb_ratio, roe, roce, opm, npm,
                   free_cash_flow_cr, composite_quality_score
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year
        """, conn, params=[cid])

        # Compute 5yr median P/E
        pe_vals = ratios_df["pe_ratio"].dropna()
        median_pe = round(float(pe_vals.median()), 2) if len(pe_vals) >= 3 else None

    return {
        "company_id": cid,
        "company_name": name,
        "median_pe_5yr": median_pe,
        "note": "Dividend yield unavailable in source data (not fabricated).",
        "market_cap_history": mc_df.to_dict(orient="records"),
        "valuation_ratios": ratios_df.to_dict(orient="records"),
    }
