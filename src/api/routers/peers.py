"""
Peers Router — Sprint 6 Day 40.

GET /api/v1/peers/{group_name}                    — Peer group data
GET /api/v1/companies/{ticker}/peers/compare       — Radar chart data for a company's peer group
"""

import pandas as pd
from fastapi import APIRouter, HTTPException

from src.db.connection import get_db_connection
from src.analytics.peer import DEFAULT_PEER_GROUPS

router = APIRouter()
DB_PATH = "db/nifty100.db"


@router.get("/peers/{group_name}")
async def get_peer_group(group_name: str):
    """Returns all peer percentile data for a named peer group."""
    # Find matching group (case-insensitive partial match)
    matched = None
    for name in DEFAULT_PEER_GROUPS:
        if group_name.lower() in name.lower() or name.lower() in group_name.lower():
            matched = name
            break

    if not matched:
        raise HTTPException(
            status_code=404,
            detail=f"Peer group '{group_name}' not found. Valid groups: {list(DEFAULT_PEER_GROUPS.keys())}"
        )

    members = DEFAULT_PEER_GROUPS[matched]

    with get_db_connection(DB_PATH) as conn:
        placeholders = ",".join("?" * len(members))
        df = pd.read_sql_query(f"""
            SELECT pp.company_id, pp.metric, pp.value, pp.percentile_rank, pp.year,
                   c.company_name
            FROM peer_percentiles pp
            JOIN companies c ON pp.company_id = c.company_id
            WHERE pp.peer_group_name = ? AND pp.company_id IN ({placeholders})
            ORDER BY pp.company_id, pp.metric
        """, conn, params=[matched] + members)

    return {
        "peer_group": matched,
        "members": members,
        "data_count": len(df),
        "data": df.to_dict(orient="records"),
    }


@router.get("/companies/{ticker}/peers/compare")
async def compare_with_peers(ticker: str):
    """Returns radar-chart-ready comparison data for a company within its peer group."""
    ticker_upper = ticker.upper()

    # Find which peer group this ticker belongs to
    peer_group = None
    for name, members in DEFAULT_PEER_GROUPS.items():
        if ticker_upper in members:
            peer_group = name
            break

    if not peer_group:
        raise HTTPException(
            status_code=404,
            detail=f"'{ticker}' not found in any peer group. Available groups: {list(DEFAULT_PEER_GROUPS.keys())}"
        )

    members = DEFAULT_PEER_GROUPS[peer_group]

    with get_db_connection(DB_PATH) as conn:
        placeholders = ",".join("?" * len(members))
        df = pd.read_sql_query(f"""
            SELECT pp.company_id, pp.metric, pp.value, pp.percentile_rank
            FROM peer_percentiles pp
            WHERE pp.peer_group_name = ? AND pp.company_id IN ({placeholders})
        """, conn, params=[peer_group] + members)

    if df.empty:
        raise HTTPException(status_code=404, detail="No peer data found")

    # Pivot to radar format: {metric: {company_id: percentile_rank}}
    pivot = df.pivot_table(
        index="metric", columns="company_id", values="percentile_rank"
    )

    return {
        "peer_group": peer_group,
        "ticker": ticker_upper,
        "members": members,
        "metrics": list(pivot.index),
        "radar_data": pivot.to_dict(),
    }
