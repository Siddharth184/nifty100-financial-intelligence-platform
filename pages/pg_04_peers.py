"""
Peer Comparison Screen — Sprint 4 Day 24.

Displays:
- Peer group dropdown (11 groups)
- Company selector
- Radar chart (Plotly Scatterpolar) showing selected company vs peer group average
- Side-by-side KPI comparison table with benchmark company highlighted in gold/amber
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.dashboard.utils.db import get_peers, get_peer_group_names
from src.dashboard.utils.theme import apply_plotly_theme


def render():
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h1 style="font-size: 1.8rem; margin-bottom: 4px;">PEER COMPARISON</h1>
            <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">
                Benchmarking company percentile ranks against sector peer groups.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── Peer Group Dropdown ──────────────────────────────────────────────────
    groups = get_peer_group_names()
    if not groups:
        st.warning("No peer groups found. Please run the peer engine first.")
        return

    sel_col1, sel_col2 = st.columns(2)

    with sel_col1:
        selected_group = st.selectbox("📂 Select Peer Group", groups, key="peer_group_select")

    if not selected_group:
        return

    peer_df = get_peers(selected_group)
    if peer_df.empty:
        st.info(f"No peer data available for '{selected_group}'.")
        return

    companies_in_group = peer_df["company_id"].unique().tolist()
    ticker_names = peer_df[["company_id", "company_name", "ticker"]].drop_duplicates()

    company_options = []
    company_id_map = {}
    for _, row in ticker_names.iterrows():
        label = f"{row['company_name']} ({row['ticker']})"
        company_options.append(label)
        company_id_map[label] = row["company_id"]

    with sel_col2:
        selected_company = st.selectbox(
            "🎯 Select Company for Radar Analysis", company_options, key="peer_company_select"
        )

    selected_cid = company_id_map.get(selected_company)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Radar Chart ──────────────────────────────────────────────────────────
    st.subheader(f"Radar Analysis — {selected_company.split('(')[0].strip()} vs Peer Group Average")

    pivot_df = peer_df.pivot_table(
        index="company_id", columns="metric", values="percentile_rank", aggfunc="first"
    )

    metrics = list(pivot_df.columns)
    if not metrics:
        st.info("No metrics available for radar chart.")
        return

    avg_values = pivot_df.mean().values.tolist()

    if selected_cid in pivot_df.index:
        company_values = pivot_df.loc[selected_cid].values.tolist()
    else:
        company_values = [0.5] * len(metrics)

    radar_metrics = metrics + [metrics[0]]
    company_radar = company_values + [company_values[0]]
    avg_radar = avg_values + [avg_values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=company_radar, theta=radar_metrics, fill="toself",
        name=selected_company.split("(")[0].strip(),
        line=dict(color="#38BDF8", width=2),
        fillcolor="rgba(56, 189, 248, 0.2)"
    ))
    fig.add_trace(go.Scatterpolar(
        r=avg_radar, theta=radar_metrics, fill="toself",
        name="Peer Average",
        line=dict(color="#94A3B8", width=2, dash="dash"),
        fillcolor="rgba(148, 163, 184, 0.1)"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], gridcolor="#232D42", tickfont=dict(color="#94A3B8")),
            angularaxis=dict(gridcolor="#232D42", tickfont=dict(color="#F8FAFC"))
        ),
        showlegend=True,
        height=480,
        margin=dict(t=30, b=30)
    )
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Side-by-Side KPI Table ───────────────────────────────────────────────
    st.subheader(f"Peer Group Metric Ranks — {selected_group}")

    display_pivot = pivot_df.copy().round(3)
    name_map = dict(zip(ticker_names["company_id"], ticker_names["company_name"]))
    display_pivot.insert(0, "Company", display_pivot.index.map(name_map))
    display_pivot = display_pivot.reset_index(drop=True)

    def highlight_benchmark(row):
        if company_id_map.get(selected_company) and name_map.get(company_id_map[selected_company]) == row["Company"]:
            return ["background-color: rgba(245, 158, 11, 0.2); color: #FBBF24; font-weight: bold;"] * len(row)
        return [""] * len(row)

    styled = display_pivot.style.apply(highlight_benchmark, axis=1)
    st.dataframe(styled, use_container_width=True, height=380)

    st.caption(f"Percentile rankings (0.0 to 1.0) for {len(companies_in_group)} peers in {selected_group}. Gold row highlights selected benchmark company.")
