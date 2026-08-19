"""
Portfolio Router — Sprint 6 Day 40.

GET /api/v1/portfolio/stats — Percentile statistics (P10 to P90) across universe.
"""

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter()

PORTFOLIO_STATS_PATH = "output/portfolio_stats.csv"


@router.get("/portfolio/stats")
async def get_portfolio_stats():
    """Returns P10, P25, P50, P75, P90 percentile distribution for 10 financial metrics across the Nifty 100 universe."""
    try:
        df = pd.read_csv(PORTFOLIO_STATS_PATH)
        return {
            "count": len(df),
            "stats": df.to_dict(orient="records")
        }
    except FileNotFoundError:
        # Fallback to generating on-the-fly if needed
        from src.analytics.clustering import generate_portfolio_stats
        df = generate_portfolio_stats()
        if df.empty:
            raise HTTPException(status_code=500, detail="Could not generate portfolio stats")
        return {
            "count": len(df),
            "stats": df.to_dict(orient="records")
        }
