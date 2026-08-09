"""
Trend Analysis Screen — Sprint 4 Day 25.

Displays:
- Company search box
- Multi-metric selector (overlay up to 3 metrics)
- 10-year line chart with YoY % change annotations (Plotly dark theme)
- Data table below
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.dashboard.utils.db import get_companies, get_ratios
from src.dashboard.utils.theme import apply_plotly_theme


AVAILABLE_METRICS = {
    "ROE (%)": "roe",
    "ROCE (%)": "roce",
    "Net Profit Margin (%)": "npm",
    "Operating Profit Margin (%)": "opm",
    "D/E Ratio": "debt_to_equity",
    "P/E Ratio": "pe_ratio",
    "P/B Ratio": "pb_ratio",
    "Interest Coverage": "interest_coverage",
    "Asset Turnover": "asset_turnover",
    "Free Cash Flow (Cr)": "free_cash_flow",
    "Revenue CAGR 5Y (%)": "cagr_sales_5yr",
    "PAT CAGR 5Y (%)": "cagr_pat_5yr",
}

COLORS = ["#38BDF8", "#F87171", "#4ADE80"]


def render():
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h1 style="font-size: 1.8rem; margin-bottom: 4px;">TREND ANALYSIS</h1>
            <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">
                Multi-metric historical performance analysis over 10 financial years with YoY trajectory tracking.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    companies_df = get_companies()
    if companies_df.empty:
        st.error("No companies found in database.")
        return

    options = []
    ticker_map = {}
    for _, row in companies_df.iterrows():
        label = f"{row['company_name']} ({row['ticker']})"
        options.append(label)
        ticker_map[label] = row["ticker"]

    ctrl1, ctrl2 = st.columns([1, 2])

    with ctrl1:
        selected = st.selectbox("🔎 Select Company", options=[""] + options, index=0, key="trend_company")

    if not selected:
        st.info("👆 Select a company to launch trend analysis.")
        return

    ticker = ticker_map.get(selected)

    with ctrl2:
        selected_metrics = st.multiselect(
            "📊 Overlay Metrics (max 3)",
            list(AVAILABLE_METRICS.keys()),
            default=["ROE (%)"],
            max_selections=3,
            key="trend_metrics"
        )

    if not selected_metrics:
        st.info("Select at least one metric to display.")
        return

    ratios_df = get_ratios(ticker=ticker)
    if ratios_df.empty:
        st.error("No data found for this company.")
        return

    df_sorted = ratios_df.sort_values("year").tail(10)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Line Chart ───────────────────────────────────────────────────────────
    fig = go.Figure()

    for i, metric_label in enumerate(selected_metrics):
        col_name = AVAILABLE_METRICS[metric_label]
        if col_name not in df_sorted.columns:
            continue

        values = df_sorted[col_name].values
        years = df_sorted["year"].values

        yoy = [None]
        for j in range(1, len(values)):
            if values[j-1] is not None and not pd.isna(values[j-1]) and values[j-1] != 0:
                pct = ((values[j] - values[j-1]) / abs(values[j-1])) * 100
                yoy.append(f"{pct:+.1f}%")
            else:
                yoy.append("N/A")

        hover_text = []
        for j, yr in enumerate(years):
            val = values[j]
            yoy_str = yoy[j] if yoy[j] else ""
            if val is not None and not pd.isna(val):
                hover_text.append(f"Year: {yr}<br>{metric_label}: {val:.2f}<br>YoY: {yoy_str}")
            else:
                hover_text.append(f"Year: {yr}<br>{metric_label}: N/A")

        fig.add_trace(go.Scatter(
            x=years, y=values,
            mode="lines+markers+text",
            name=metric_label,
            line=dict(color=COLORS[i % len(COLORS)], width=2),
            marker=dict(size=7),
            text=[y if y else "" for y in yoy],
            textposition="top center",
            textfont=dict(size=9, color=COLORS[i % len(COLORS)]),
            hovertext=hover_text,
            hoverinfo="text"
        ))

    fig.update_layout(
        title=f"10-Year Financial Trajectory — {selected.split('(')[0].strip()}",
        xaxis_title="Financial Year",
        yaxis_title="Metric Value",
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    # ── Raw Data Table ───────────────────────────────────────────────────────
    st.subheader("Historical Data Table")
    metric_cols = [AVAILABLE_METRICS[m] for m in selected_metrics if AVAILABLE_METRICS[m] in df_sorted.columns]
    show_cols = ["year"] + metric_cols
    display_tbl = df_sorted[show_cols].reset_index(drop=True)
    display_tbl = display_tbl.rename(columns={"year": "Year"})
    st.dataframe(display_tbl, use_container_width=True)
