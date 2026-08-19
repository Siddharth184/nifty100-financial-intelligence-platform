"""
Screener Router — Sprint 6 Day 40.

GET /api/v1/screener — Run screener with optional preset/custom filters.
"""

from typing import Optional
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.screener.engine import ScreenerEngine

router = APIRouter()


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


@router.get("/screener")
async def run_screener(
    preset: Optional[str] = Query(None, description="Preset name: quality_compounder, value_pick, growth_accelerator, dividend_champion, debt_free_blue_chip, turnaround_watch"),
    roe_min: Optional[float] = Query(None, description="Min ROE %"),
    de_max: Optional[float] = Query(None, description="Max D/E ratio"),
    pe_max: Optional[float] = Query(None, description="Max P/E ratio"),
    revenue_cagr_5yr_min: Optional[float] = Query(None, description="Min Revenue CAGR 5yr %"),
    pat_cagr_5yr_min: Optional[float] = Query(None, description="Min PAT CAGR 5yr %"),
    fcf_min: Optional[float] = Query(None, description="Min FCF (Cr)"),
):
    """
    Runs the screener engine with either a named preset or custom filter thresholds.
    Returns filtered companies with composite quality scores.
    """
    try:
        engine = ScreenerEngine()
        df = engine.load_universe_data(latest_year_only=True)

        if preset:
            valid_presets = list(engine.config.get("presets", {}).keys())
            if preset not in valid_presets:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid preset '{preset}'. Valid presets: {valid_presets}"
                )
            result_df = engine.run_preset(preset, df=df)
            filters = engine.config.get("presets", {}).get(preset, {}).get("filters", {})
        else:
            filters = {}
            if roe_min is not None:
                filters["roe_min"] = roe_min
            if de_max is not None:
                filters["de_max"] = de_max
            if pe_max is not None:
                filters["pe_max"] = pe_max
            if revenue_cagr_5yr_min is not None:
                filters["revenue_cagr_5yr_min"] = revenue_cagr_5yr_min
            if pat_cagr_5yr_min is not None:
                filters["pat_cagr_5yr_min"] = pat_cagr_5yr_min
            if fcf_min is not None:
                filters["fcf_min"] = fcf_min

            result_df = engine.apply_filters(df, filters)

        records = _clean_df(result_df)

        return {
            "preset": preset,
            "filters_applied": filters,
            "count": len(records),
            "companies": records,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screener error: {str(e)}")
