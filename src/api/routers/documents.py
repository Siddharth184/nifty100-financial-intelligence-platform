"""
Documents Router — Sprint 6 Day 40.

GET /api/v1/companies/{ticker}/documents — Annual report links and document metadata.
"""

import urllib.request
import pandas as pd
from typing import Optional
from fastapi import APIRouter, HTTPException

from src.db.connection import get_db_connection

router = APIRouter()
DB_PATH = "db/nifty100.db"


def _check_url_validity(url: Optional[str]) -> bool:
    """Checks if a document URL is valid/reachable (non-blocking basic check)."""
    if not url or pd.isna(url):
        return False
    url_str = str(url).strip()
    if not (url_str.startswith("http://") or url_str.startswith("https://")):
        return False
    return True


@router.get("/companies/{ticker}/documents")
async def get_company_documents(ticker: str):
    """
    Returns annual report links and document metadata for a company.
    Includes is_url_valid flag for each document URL.
    """
    with get_db_connection(DB_PATH) as conn:
        # Resolve company_id
        row = conn.execute(
            "SELECT company_id, company_name FROM companies WHERE UPPER(ticker) = UPPER(?) OR UPPER(company_id) = UPPER(?)",
            (ticker, ticker)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        cid, name = row

        # Fetch documents
        df = pd.read_sql_query(
            "SELECT * FROM documents WHERE company_id = ?",
            conn, params=[cid]
        )

    docs = []
    for _, r in df.iterrows():
        doc_dict = r.to_dict()
        # Find any url field
        url = doc_dict.get("doc_url", doc_dict.get("url", doc_dict.get("file_path", None)))
        doc_dict["is_url_valid"] = _check_url_validity(url)
        docs.append(doc_dict)

    return {
        "company_id": cid,
        "company_name": name,
        "count": len(docs),
        "documents": docs,
    }
