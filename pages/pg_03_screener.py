"""
Screener Screen — Sprint 4 Day 24.

Displays:
- Compact sidebar filter controls (10 financial metrics)
- 6 preset buttons (Quality, Value, Growth, Dividend, Debt-Free, Turnaround)
- Clean, analyst-friendly live results table
- Clear result count label
- Primary CSV Download button
- Preserves Sprint 3 dividend data limitation notice cleanly
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.screener.engine import ScreenerEngine
from src.dashboard.utils.theme import kpi_card


def render():
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h1 style="font-size: 1.8rem; margin-bottom: 4px;">FINANCIAL SCREENER</h1>
            <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">
                Screen Nifty 100 companies using analyst criteria or quick preset investment strategies.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── Initialize Screener Engine ───────────────────────────────────────────
    engine = ScreenerEngine()
    universe_df = engine.load_universe_data()

    if universe_df.empty:
        st.error("No data available. Please ensure the database is populated.")
        return

    # ── Quick Presets Section ────────────────────────────────────────────────
    st.markdown("<div style='font-size: 0.9rem; font-weight: 600; color: #94A3B8; margin-bottom: 8px;'>PRESET STRATEGIES</div>", unsafe_allow_html=True)
    preset_cols = st.columns(6)

    preset_map = {
        "Quality Compounder": "quality_compounder",
        "Value Pick": "value_pick",
        "Growth Accelerator": "growth_accelerator",
        "Dividend Champion": "dividend_champion",
        "Debt-Free Blue Chip": "debt_free_blue_chip",
        "Turnaround Watch": "turnaround_watch",
    }

    defaults = {
        "roe_min": 0.0, "de_max": 100.0, "fcf_min": -10000.0,
        "rev_cagr_min": -100.0, "pat_cagr_min": -100.0, "opm_min": -100.0,
        "pe_max": 500.0, "pb_max": 100.0, "div_yield_min": 0.0, "icr_min": 0.0,
    }

    active_preset = st.session_state.get("active_preset", None)

    for i, (label, key) in enumerate(preset_map.items()):
        with preset_cols[i]:
            if st.button(label, key=f"preset_{key}", use_container_width=True):
                active_preset = key
                st.session_state["active_preset"] = key

    slider_vals = defaults.copy()
    if active_preset:
        presets = engine.config.get("presets", {})
        if active_preset in presets:
            filt = presets[active_preset].get("filters", {})
            if "roe_min" in filt:
                slider_vals["roe_min"] = float(filt["roe_min"])
            if "de_max" in filt:
                slider_vals["de_max"] = float(filt["de_max"])
            if "fcf_min" in filt:
                slider_vals["fcf_min"] = float(filt["fcf_min"])
            if "revenue_cagr_5yr_min" in filt:
                slider_vals["rev_cagr_min"] = float(filt["revenue_cagr_5yr_min"])
            if "pat_cagr_5yr_min" in filt:
                slider_vals["pat_cagr_min"] = float(filt["pat_cagr_5yr_min"])
            if "opm_min" in filt:
                slider_vals["opm_min"] = float(filt["opm_min"])
            if "pe_max" in filt:
                slider_vals["pe_max"] = float(filt["pe_max"])
            if "pb_max" in filt:
                slider_vals["pb_max"] = float(filt["pb_max"])
            if "dividend_yield_min" in filt:
                slider_vals["div_yield_min"] = float(filt["dividend_yield_min"])
            if "icr_min" in filt:
                slider_vals["icr_min"] = float(filt["icr_min"])

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Sidebar Filter Sliders ────────────────────────────────────────────────
    st.sidebar.markdown(
        "<div style='font-size: 0.9rem; font-weight: 700; color: #38BDF8; margin-bottom: 12px;'>SCREENER FILTERS</div>",
        unsafe_allow_html=True
    )

    roe_min = st.sidebar.slider("ROE Min (%)", 0.0, 50.0, slider_vals["roe_min"], 1.0, key="scr_roe")
    de_max = st.sidebar.slider("D/E Max", 0.0, 100.0, slider_vals["de_max"], 0.5, key="scr_de")
    fcf_min = st.sidebar.slider("FCF Min (Cr)", -10000.0, 50000.0, slider_vals["fcf_min"], 100.0, key="scr_fcf")
    rev_cagr_min = st.sidebar.slider("Revenue CAGR Min (%)", -100.0, 100.0, slider_vals["rev_cagr_min"], 1.0, key="scr_rev")
    pat_cagr_min = st.sidebar.slider("PAT CAGR Min (%)", -100.0, 100.0, slider_vals["pat_cagr_min"], 1.0, key="scr_pat")
    opm_min = st.sidebar.slider("OPM Min (%)", -100.0, 100.0, slider_vals["opm_min"], 1.0, key="scr_opm")
    pe_max = st.sidebar.slider("P/E Max", 0.0, 500.0, slider_vals["pe_max"], 1.0, key="scr_pe")
    pb_max = st.sidebar.slider("P/B Max", 0.0, 100.0, slider_vals["pb_max"], 0.5, key="scr_pb")
    div_yield_min = st.sidebar.slider("Dividend Yield Min (%)", 0.0, 20.0, slider_vals["div_yield_min"], 0.5, key="scr_div")
    icr_min = st.sidebar.slider("ICR Min", 0.0, 50.0, slider_vals["icr_min"], 0.5, key="scr_icr")

    if div_yield_min > 0:
        st.sidebar.warning(
            "⚠️ **DATA LIMITATION:** Dividend Yield source data is unavailable "
            "in raw export files. Filters requiring Dividend Yield return 0 results."
        )

    # ── Build Filter Dict ────────────────────────────────────────────────────
    filters = {}
    if roe_min > 0:
        filters["roe_min"] = roe_min
    if de_max < 100:
        filters["de_max"] = de_max
    if fcf_min > -10000:
        filters["fcf_min"] = fcf_min
    if rev_cagr_min > -100:
        filters["revenue_cagr_5yr_min"] = rev_cagr_min
    if pat_cagr_min > -100:
        filters["pat_cagr_5yr_min"] = pat_cagr_min
    if opm_min > -100:
        filters["opm_min"] = opm_min
    if pe_max < 500:
        filters["pe_max"] = pe_max
    if pb_max < 100:
        filters["pb_max"] = pb_max
    if div_yield_min > 0:
        filters["dividend_yield_min"] = div_yield_min
    if icr_min > 0:
        filters["icr_min"] = icr_min

    # ── Apply Filters ────────────────────────────────────────────────────────
    if filters:
        result_df = engine.apply_filters(universe_df, filters)
    else:
        result_df = universe_df.copy()
        score_col = "composite_quality_score"
        if score_col in result_df.columns:
            result_df = result_df.sort_values(score_col, ascending=False)

    # ── Result Header & CSV Download ─────────────────────────────────────────
    top_col, dl_col = st.columns([3, 1])

    with top_col:
        st.markdown(
            f"""
            <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC; padding: 6px 0;">
                <span style="color: #38BDF8;">{len(result_df)}</span> companies match your active filters
            </div>
            """,
            unsafe_allow_html=True
        )

    # ── Display Table ────────────────────────────────────────────────────────
    display_cols = [
        "company_id", "company_name", "sector_name", "composite_quality_score",
        "return_on_equity_pct", "roe", "debt_to_equity", "free_cash_flow_cr",
        "revenue_cagr_5yr", "operating_profit_margin_pct",
        "pe_ratio", "pb_ratio", "interest_coverage", "market_cap", "sales"
    ]
    available_cols = [c for c in display_cols if c in result_df.columns]

    if not result_df.empty:
        display_df = result_df[available_cols].copy()
        display_df = display_df.rename(columns={
            "company_id": "Ticker Code",
            "company_name": "Company Name",
            "sector_name": "Sector",
            "composite_quality_score": "Composite Score",
            "return_on_equity_pct": "ROE (%)",
            "debt_to_equity": "D/E",
            "free_cash_flow_cr": "FCF (Cr)",
            "revenue_cagr_5yr": "Rev CAGR 5Y (%)",
            "operating_profit_margin_pct": "OPM (%)",
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "interest_coverage": "ICR",
            "market_cap": "Market Cap (Cr)",
            "sales": "Sales (Cr)"
        })
        display_df = display_df.reset_index(drop=True)
        display_df.index = display_df.index + 1

        with dl_col:
            csv_data = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Export CSV",
                data=csv_data,
                file_name="screener_results.csv",
                mime="text/csv",
                key="screener_csv_download",
                use_container_width=True
            )

        st.dataframe(display_df, use_container_width=True, height=520)
    else:
        st.info("No companies match the current filter criteria.")
        if div_yield_min > 0:
            st.warning(
                "**Data Unavailable:** Dividend Yield data is not present in raw Screener.in dump files. "
                "Presets requiring Dividend Yield (Value Pick, Dividend Champion) return 0 results."
            )
