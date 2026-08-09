"""
Sector Analysis Screen — Sprint 4 Day 25.

Displays:
- Sector selector dropdown
- Plotly bubble chart (X=Revenue, Y=ROE, bubble size=Market Cap, color=Company)
- Sector median KPI bar chart (Plotly dark theme)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard.utils.db import get_ratios_all, get_sectors
from src.dashboard.utils.theme import apply_plotly_theme


def render():
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h1 style="font-size: 1.8rem; margin-bottom: 4px;">SECTOR ANALYSIS</h1>
            <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">
                Sector-wide landscape analysis, revenue-vs-ROE positioning, and sectoral median benchmarks.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    sectors_df = get_sectors()
    if sectors_df.empty:
        st.error("No sectors found.")
        return

    sector_names = sectors_df["sector_name"].dropna().unique().tolist()
    selected_sector = st.selectbox("📂 Select Sector", sorted(sector_names), key="sector_select")

    all_df = get_ratios_all(year=2024)
    if all_df.empty:
        all_df = get_ratios_all()
        if not all_df.empty:
            max_year = all_df["year"].max()
            all_df = all_df[all_df["year"] == max_year]

    if all_df.empty:
        st.warning("No financial data available.")
        return

    all_df = all_df.drop_duplicates(subset=["company_id"], keep="first")
    sector_df = all_df[all_df["sector_name"] == selected_sector].copy()

    if sector_df.empty:
        st.info(f"No companies found in sector '{selected_sector}'.")
        return

    st.markdown(f"**{len(sector_df)} active companies** in {selected_sector}")
    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Bubble Chart ─────────────────────────────────────────────────────────
    st.subheader(f"Landscape — {selected_sector} (Revenue vs ROE)")

    roe_col = "return_on_equity_pct" if "return_on_equity_pct" in sector_df.columns else "roe"
    bubble_df = sector_df[["company_name", "sales", roe_col, "market_cap"]].dropna().copy()
    bubble_df.columns = ["Company", "Revenue", "ROE", "Market_Cap"]
    bubble_df["Market_Cap_Size"] = bubble_df["Market_Cap"].clip(lower=1)

    if not bubble_df.empty:
        fig_bubble = px.scatter(
            bubble_df,
            x="Revenue", y="ROE",
            size="Market_Cap_Size",
            text="Company",
            color="Company",
            size_max=50,
            title=f"{selected_sector} — Revenue vs ROE (Bubble Size = Market Cap)",
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        fig_bubble.update_traces(textposition="top center", textfont=dict(size=9))
        fig_bubble.update_layout(
            height=460,
            xaxis_title="Revenue (₹ Cr)",
            yaxis_title="ROE (%)",
            showlegend=False
        )
        apply_plotly_theme(fig_bubble)
        st.plotly_chart(fig_bubble, use_container_width=True)
    else:
        st.info("Insufficient data for bubble chart.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Sector Median KPI Bar Chart ──────────────────────────────────────────
    st.subheader(f"Sector Median Benchmarks — {selected_sector}")

    kpi_metrics = {
        "ROE (%)": roe_col,
        "ROCE (%)": "roce",
        "NPM (%)": "npm",
        "OPM (%)": "opm",
        "D/E": "debt_to_equity",
        "P/E": "pe_ratio",
        "Asset Turnover": "asset_turnover",
    }

    median_values = {}
    for label, col in kpi_metrics.items():
        if col in sector_df.columns:
            med = sector_df[col].dropna().median()
            if med is not None and not pd.isna(med):
                median_values[label] = round(float(med), 2)

    if median_values:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=list(median_values.keys()),
            y=list(median_values.values()),
            marker_color="#38BDF8",
            text=[f"{v:.2f}" for v in median_values.values()],
            textposition="outside",
            textfont=dict(color="#F8FAFC")
        ))
        fig_bar.update_layout(
            title=f"Median KPIs — {selected_sector}",
            height=360,
            yaxis_title="Median Metric Value"
        )
        apply_plotly_theme(fig_bar)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Insufficient data for median KPI chart.")
