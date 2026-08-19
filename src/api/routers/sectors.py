"""
Sectors Router — Sprint 6 Day 40.

GET /api/v1/sectors                  — All 10 sectors with stats
GET /api/v1/sectors/{sector}/companies — Companies in a sector
"""

import pandas as pd
from fastapi import APIRouter, HTTPException

from src.db.connection import get_db_connection

router = APIRouter()
DB_PATH = "db/nifty100.db"


def _clean_df(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    clean = []
    for r in records:
        clean_r = {}
        for k, v in r.items():
            if v is None or pd.isna(v):
                clean_r[k] = None
            else:
                clean_r[k] = v
        clean.append(clean_r)
    return clean


@router.get("/sectors")
async def list_sectors():
    """Lists all sectors with company count and basic financial stats."""
    with get_db_connection(DB_PATH) as conn:
        sectors = pd.read_sql_query("""
            SELECT s.sector_name,
                   COUNT(c.company_id) as company_count,
                   AVG(fr.roe) as avg_roe,
                   AVG(fr.debt_to_equity) as avg_de,
                   AVG(fr.opm) as avg_opm
            FROM sectors s
            LEFT JOIN companies c ON s.sector_id = c.sector_id
            LEFT JOIN financial_ratios fr ON c.company_id = fr.company_id
                AND fr.year = (SELECT MAX(fr2.year) FROM financial_ratios fr2 WHERE fr2.company_id = fr.company_id)
            GROUP BY s.sector_name
            ORDER BY s.sector_name
        """, conn)

    for col in ["avg_roe", "avg_roce", "avg_de", "avg_opm"]:
        if col in sectors.columns:
            sectors[col] = pd.to_numeric(sectors[col], errors="coerce").round(2)

    return {
        "count": len(sectors),
        "sectors": _clean_df(sectors),
    }


@router.get("/sectors/{sector}/companies")
async def get_sector_companies(sector: str):
    """Lists all companies in a given sector with latest KPIs."""
    with get_db_connection(DB_PATH) as conn:
        exists = conn.execute(
            "SELECT 1 FROM sectors WHERE LOWER(sector_name) LIKE LOWER(?)",
            (f"%{sector}%",)
        ).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found")

        df = pd.read_sql_query("""
            SELECT c.company_id, c.company_name, c.ticker, s.sector_name,
                   fr.roe, fr.roce, fr.opm, fr.npm, fr.debt_to_equity,
                   fr.free_cash_flow, fr.pe_ratio, fr.pb_ratio,
                   fr.composite_quality_score, fr.year
            FROM companies c
            LEFT JOIN sectors s ON c.sector_id = s.sector_id
            LEFT JOIN financial_ratios fr ON c.company_id = fr.company_id
                AND fr.year = (SELECT MAX(fr2.year) FROM financial_ratios fr2 WHERE fr2.company_id = fr.company_id)
            WHERE LOWER(s.sector_name) LIKE LOWER(?)
            ORDER BY c.company_id
        """, conn, params=[f"%{sector}%"])

    return {
        "sector": sector,
        "count": len(df),
        "companies": _clean_df(df),
    }

