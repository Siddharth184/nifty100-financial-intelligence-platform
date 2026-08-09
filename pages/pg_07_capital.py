"""
Capital Allocation Map Screen — Sprint 4 Day 25.

Displays:
- Plotly treemap of 92 companies grouped by 8 capital allocation patterns
- Meaningful color palette per pattern
- Interactive pattern selector showing company lists
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.utils.db import get_ratios_all
from src.dashboard.utils.theme import apply_plotly_theme


PATTERN_COLORS = {
    "High Growth Reinvestor": "#38BDF8",
    "Cash Cow Distributor": "#22C55E",
    "Debt Reducer": "#F59E0B",
    "Balanced Allocator": "#818CF8",
    "Aggressive Acquirer": "#EC4899",
    "Conservative Saver": "#FACC15",
    "Turnaround Restructurer": "#A855F7",
    "Unclassified": "#64748B",
}


def render():
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h1 style="font-size: 1.8rem; margin-bottom: 4px;">CAPITAL ALLOCATION MAP</h1>
            <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">
                Visualizing corporate capital deployment strategies across 8 strategic allocation archetypes.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

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

    cap_col = "capital_allocation_strategy"
    if cap_col not in all_df.columns or all_df[cap_col].isna().all():
        st.warning("Capital allocation strategy data not available.")
        return

    treemap_df = all_df[["company_id", "company_name", cap_col, "market_cap", "sector_name"]].copy()
    treemap_df[cap_col] = treemap_df[cap_col].fillna("Unclassified")
    treemap_df["market_cap"] = treemap_df["market_cap"].fillna(1).clip(lower=1)

    pattern_counts = treemap_df[cap_col].value_counts()
    st.markdown(f"**{len(treemap_df)} companies** classified into **{len(pattern_counts)} capital allocation patterns**")
    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Treemap ──────────────────────────────────────────────────────────────
    fig = px.treemap(
        treemap_df,
        path=[cap_col, "company_name"],
        values="market_cap",
        color=cap_col,
        color_discrete_map=PATTERN_COLORS,
        title="Capital Allocation Map (Tile Size = Market Cap)",
        hover_data={"sector_name": True, "market_cap": ":.0f"}
    )
    fig.update_layout(
        height=580,
        margin=dict(t=40, b=20, l=10, r=10)
    )
    fig.update_traces(
        textinfo="label+value",
        textfont=dict(size=11, color="#F8FAFC")
    )
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Pattern Company Breakdown ─────────────────────────────────────────────
    st.subheader("Companies by Capital Allocation Pattern")
    selected_pattern = st.selectbox(
        "Select pattern archetype to inspect companies",
        sorted(pattern_counts.index.tolist()),
        key="capital_pattern_select"
    )

    if selected_pattern:
        pattern_df = treemap_df[treemap_df[cap_col] == selected_pattern][
            ["company_name", "sector_name", "market_cap"]
        ].sort_values("market_cap", ascending=False).reset_index(drop=True)
        pattern_df.index = pattern_df.index + 1
        pattern_df.columns = ["Company Name", "Sector", "Market Cap (₹ Cr)"]
        pattern_df["Market Cap (₹ Cr)"] = pattern_df["Market Cap (₹ Cr)"].round(0)
        st.dataframe(pattern_df, use_container_width=True)
        st.caption(f"{len(pattern_df)} companies categorized under '{selected_pattern}'")
