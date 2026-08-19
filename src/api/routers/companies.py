"""
Companies Router — Sprint 6 Days 39.

7 endpoints for company data:
- GET /companies             — List all / filtered by sector/search
- GET /companies/{ticker}    — Full company profile + latest KPIs
- GET /companies/{ticker}/pl — P&L history
- GET /companies/{ticker}/bs — Balance sheet history
- GET /companies/{ticker}/cashflow — Cash flow history
- GET /companies/{ticker}/ratios   — Financial ratios per year
- GET /companies/{ticker}/tearsheet — Download pre-generated PDF
"""

import os
import pandas as pd
import numpy as np
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.db.connection import get_db_connection

router = APIRouter()
DB_PATH = "db/nifty100.db"
TEARSHEET_DIR = "reports/tearsheets"


def _clean_records(records: list[dict]) -> list[dict]:
    """Helper to sanitize record dictionaries for JSON response (replacing NaN/Inf with None)."""
    clean = []
    for r in records:
        clean_r = {}
        for k, v in r.items():
            if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                clean_r[k] = None
            elif pd.isna(v):
                clean_r[k] = None
            else:
                clean_r[k] = v
        clean.append(clean_r)
    return clean


def _clean_df(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    return _clean_records(df.to_dict(orient="records"))


def _ticker_to_company_id(conn, ticker: str) -> Optional[str]:
    """Resolves a ticker to company_id. Tries ticker match first, then company_id match."""
    row = conn.execute(
        "SELECT company_id FROM companies WHERE UPPER(ticker) = UPPER(?) OR UPPER(company_id) = UPPER(?)",
        (ticker, ticker)
    ).fetchone()
    return row[0] if row else None


@router.get("/companies")
async def list_companies(
    sector: Optional[str] = Query(None, description="Filter by sector name"),
    search: Optional[str] = Query(None, description="Search by company name or ticker"),
):
    """Lists all 92 companies with optional sector/search filters."""
    with get_db_connection(DB_PATH) as conn:
        query = """
            SELECT c.company_id, c.company_name, c.ticker, s.sector_name
            FROM companies c
            LEFT JOIN sectors s ON c.sector_id = s.sector_id
            WHERE 1=1
        """
        params = []
        if sector:
            query += " AND LOWER(s.sector_name) LIKE LOWER(?)"
            params.append(f"%{sector}%")
        if search:
            query += " AND (LOWER(c.company_name) LIKE LOWER(?) OR LOWER(c.ticker) LIKE LOWER(?) OR LOWER(c.company_id) LIKE LOWER(?))"
            params.extend([f"%{search}%"] * 3)
        query += " ORDER BY c.company_id"

        df = pd.read_sql_query(query, conn, params=params)

    records = _clean_df(df)
    return {"count": len(records), "companies": records}


@router.get("/companies/{ticker}")
async def get_company_profile(ticker: str):
    """Returns full company profile with latest-year KPIs."""
    with get_db_connection(DB_PATH) as conn:
        cid = _ticker_to_company_id(conn, ticker)
        if not cid:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        comp = pd.read_sql_query("""
            SELECT c.*, s.sector_name
            FROM companies c LEFT JOIN sectors s ON c.sector_id = s.sector_id
            WHERE c.company_id = ?
        """, conn, params=[cid])

        kpis = pd.read_sql_query("""
            SELECT * FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year DESC LIMIT 1
        """, conn, params=[cid])

        cluster = None
        try:
            cluster_df = pd.read_csv("output/cluster_labels.csv")
            match = cluster_df[cluster_df["company_id"] == cid]
            if not match.empty:
                cluster = {
                    "cluster_id": int(match.iloc[0]["cluster_id"]),
                    "cluster_name": match.iloc[0]["cluster_name"],
                }
        except FileNotFoundError:
            pass

    comp_rec = _clean_df(comp)
    kpis_rec = _clean_df(kpis)

    result = comp_rec[0] if comp_rec else {}
    result["latest_kpis"] = kpis_rec[0] if kpis_rec else {}
    result["cluster"] = cluster
    return result


@router.get("/companies/{ticker}/pl")
async def get_pl_history(
    ticker: str,
    from_year: Optional[int] = None,
    to_year: Optional[int] = None,
):
    """Returns P&L history for a company with optional year range filter."""
    with get_db_connection(DB_PATH) as conn:
        cid = _ticker_to_company_id(conn, ticker)
        if not cid:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        query = "SELECT * FROM profitandloss WHERE company_id = ?"
        params = [cid]
        if from_year:
            query += " AND year >= ?"
            params.append(from_year)
        if to_year:
            query += " AND year <= ?"
            params.append(to_year)
        query += " ORDER BY year"
        df = pd.read_sql_query(query, conn, params=params)

    records = _clean_df(df)
    return {"company_id": cid, "count": len(records), "data": records}


@router.get("/companies/{ticker}/bs")
async def get_bs_history(
    ticker: str,
    from_year: Optional[int] = None,
    to_year: Optional[int] = None,
):
    """Returns balance sheet history for a company."""
    with get_db_connection(DB_PATH) as conn:
        cid = _ticker_to_company_id(conn, ticker)
        if not cid:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        query = "SELECT * FROM balancesheet WHERE company_id = ?"
        params = [cid]
        if from_year:
            query += " AND year >= ?"
            params.append(from_year)
        if to_year:
            query += " AND year <= ?"
            params.append(to_year)
        query += " ORDER BY year"
        df = pd.read_sql_query(query, conn, params=params)

    records = _clean_df(df)
    return {"company_id": cid, "count": len(records), "data": records}


@router.get("/companies/{ticker}/cashflow")
async def get_cashflow_history(
    ticker: str,
    from_year: Optional[int] = None,
    to_year: Optional[int] = None,
):
    """Returns cash flow history for a company."""
    with get_db_connection(DB_PATH) as conn:
        cid = _ticker_to_company_id(conn, ticker)
        if not cid:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        query = "SELECT * FROM cashflow WHERE company_id = ?"
        params = [cid]
        if from_year:
            query += " AND year >= ?"
            params.append(from_year)
        if to_year:
            query += " AND year <= ?"
            params.append(to_year)
        query += " ORDER BY year"
        df = pd.read_sql_query(query, conn, params=params)

    records = _clean_df(df)
    return {"company_id": cid, "count": len(records), "data": records}


@router.get("/companies/{ticker}/ratios")
async def get_ratios_history(ticker: str):
    """Returns all financial ratios per year for a company."""
    with get_db_connection(DB_PATH) as conn:
        cid = _ticker_to_company_id(conn, ticker)
        if not cid:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        df = pd.read_sql_query(
            "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year",
            conn, params=[cid]
        )

    records = _clean_df(df)
    return {"company_id": cid, "years": len(records), "data": records}


@router.get("/companies/{ticker}/tearsheet")
async def download_tearsheet(ticker: str):
    """Downloads pre-generated PDF tearsheet for a company."""
    candidates = [
        os.path.join(TEARSHEET_DIR, f"{ticker}_tearsheet.pdf"),
        os.path.join(TEARSHEET_DIR, f"{ticker.upper()}_tearsheet.pdf"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return FileResponse(
                path,
                media_type="application/pdf",
                filename=os.path.basename(path),
            )
    raise HTTPException(
        status_code=404,
        detail=f"Tearsheet not found for '{ticker}'. Company may have insufficient data (e.g., JIOFIN has <3 years)."
    )
