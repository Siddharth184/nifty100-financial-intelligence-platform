"""
Home Screen — Sprint 4 Day 23.

Displays:
- Header & subtitle
- 6 summary KPI cards (Average ROE, Median P/E, Median D/E, Total Companies,
  Median Revenue CAGR 5yr, Debt-Free Companies count)
- Sector breakdown donut chart (Plotly dark theme)
- Top-5 companies table by composite quality score
- Year selector in sidebar (2019 to 2024)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.utils.db import get_ratios_all, get_available_years
from src.dashboard.utils.theme import apply_plotly_theme, kpi_card


def render():
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 1.8rem; margin-bottom: 4px;">NIFTY 100 ANALYTICS</h1>
            <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">
                Institutional-grade financial intelligence & performance analytics across Nifty 100 companies.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── Year Selector ────────────────────────────────────────────────────────
    available_years = get_available_years()
    if not available_years:
        st.error("No data available in the database.")
        return

    selected_year = st.sidebar.selectbox(
        "Select Year", sorted(available_years, reverse=True),
        index=0, key="home_year_selector"
    )

    # ── Load Data ────────────────────────────────────────────────────────────
    df = get_ratios_all(year=selected_year)
    if df.empty:
        st.warning(f"No data available for year {selected_year}.")
        return

    df = df.drop_duplicates(subset=["company_id"], keep="first")

    # ── 6 KPI Cards ──────────────────────────────────────────────────────────
    roe_col = "return_on_equity_pct" if "return_on_equity_pct" in df.columns else "roe"
    avg_roe = df[roe_col].dropna().mean() if roe_col in df.columns else None
    median_pe = df["pe_ratio"].dropna().median() if "pe_ratio" in df.columns else None
    median_de = df["debt_to_equity"].dropna().median() if "debt_to_equity" in df.columns else None
    total_companies = df["company_id"].nunique()
    rev_cagr_col = "revenue_cagr_5yr" if "revenue_cagr_5yr" in df.columns else "cagr_sales_5yr"
    median_rev_cagr = df[rev_cagr_col].dropna().median() if rev_cagr_col in df.columns else None
    debt_free_count = int((df["debt_to_equity"] == 0).sum()) if "debt_to_equity" in df.columns else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        kpi_card("Average ROE", f"{avg_roe:.1f}%" if avg_roe is not None else "N/A", f"FY{selected_year}", "#38BDF8")
    with c2:
        kpi_card("Median P/E", f"{median_pe:.1f}" if median_pe is not None else "N/A", "Valuation Multiple", "#38BDF8")
    with c3:
        kpi_card("Median D/E", f"{median_de:.2f}" if median_de is not None else "N/A", "Financial Leverage", "#38BDF8")
    with c4:
        kpi_card("Total Companies", str(total_companies), "Active Universe", "#38BDF8")
    with c5:
        kpi_card("Median Rev CAGR", f"{median_rev_cagr:.1f}%" if median_rev_cagr is not None else "N/A", "5-Year Trajectory", "#38BDF8")
    with c6:
        kpi_card("Debt-Free Count", str(debt_free_count), "Zero Debt Companies", "#22C55E")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Layout: Donut Chart + Top-5 Table ────────────────────────────────────
    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.subheader(f"Sector Distribution (FY{selected_year})")
        if "sector_name" in df.columns:
            sector_counts = df.groupby("sector_name")["company_id"].nunique().reset_index()
            sector_counts.columns = ["Sector", "Companies"]
            sector_counts = sector_counts.sort_values("Companies", ascending=False)

            fig = px.pie(
                sector_counts, names="Sector", values="Companies",
                hole=0.48,
                color_discrete_sequence=["#38BDF8", "#818CF8", "#C084FC", "#F472B6", "#F87171", "#FB923C", "#FACC15", "#4ADE80", "#2DD4BF", "#38BDF8", "#A78BFA"],
            )
            fig.update_traces(textposition="inside", textinfo="label+value", marker=dict(line=dict(color='#0B0F19', width=2)))
            apply_plotly_theme(fig)
            fig.update_layout(
                height=380,
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, font=dict(size=10)),
                margin=dict(t=20, b=0, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sector information not available.")

    with right_col:
        st.subheader(f"Top 5 by Composite Quality Score (FY{selected_year})")
        score_col = "composite_quality_score"
        if score_col in df.columns and df[score_col].notna().any():
            top5 = df.nlargest(5, score_col)[
                ["company_name", "ticker", "sector_name", score_col]
            ].reset_index(drop=True)
            top5.index = top5.index + 1
            top5.columns = ["Company", "Ticker", "Sector", "Quality Score"]
            top5["Quality Score"] = top5["Quality Score"].round(2)
            st.dataframe(top5, use_container_width=True, height=320)
        else:
            st.info("Composite quality scores not available for this year.")

    st.caption(f"Universe: {total_companies} active Nifty 100 companies • Data snapshot for FY{selected_year}")
