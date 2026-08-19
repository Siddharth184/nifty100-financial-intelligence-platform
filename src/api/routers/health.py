"""
Health Check Router — Sprint 6 Day 38.

GET /api/v1/health
Returns system status, DB row counts, uptime, and version.
"""

import sqlite3
from fastapi import APIRouter

from src.db.connection import get_db_connection

router = APIRouter()

DB_PATH = "db/nifty100.db"


@router.get("/health")
async def health_check():
    """Returns system health status including DB table counts."""
    try:
        with get_db_connection(DB_PATH) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            row_counts = {}
            for (tbl,) in tables:
                cnt = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
                row_counts[tbl] = cnt

        from src.api.main import get_uptime

        return {
            "status": "ok",
            "db_row_counts": row_counts,
            "uptime_seconds": get_uptime(),
            "version": "1.0.0",
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
