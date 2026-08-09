"""
Company Profile Screen — Sprint 4 Day 23.

Displays:
- Equity research header (company name, ticker, sector, sub-sector)
- Autocomplete search
- 6 KPI cards (ROE, ROCE, NPM, D/E, Revenue CAGR 5yr, FCF)
- 10-year Revenue & Net Profit bar chart (Plotly dark theme)
- ROE & ROCE dual-axis line chart
- Pros & Cons as green check / red cross badge items
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_proscons
from src.dashboard.utils.theme import apply_plotly_theme, kpi_card


def _fmt(value, suffix="", decimals=1):
    """Format a value for display, returning 'N/A' if None/NaN."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}{suffix}"


def render():
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h1 style="font-size: 1.8rem; margin-bottom: 4px;">COMPANY PROFILE</h1>
            <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">
                Comprehensive equity research profile, historical financials, and pros/cons analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── Company Search ───────────────────────────────────────────────────────
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

    selected = st.selectbox(
        "🔎 Search Company (name or ticker)",
        options=[""] + options,
        index=0,
        key="profile_search"
    )

    if not selected:
        st.info("👆 Select a company to view its equity profile.")
        return

    ticker = ticker_map.get(selected)
    if not ticker:
        st.error("Ticker not found — please try another.")
        return

    # ── Load Data ────────────────────────────────────────────────────────────
    ratios_df = get_ratios(ticker=ticker)
    pl_df = get_pl(ticker=ticker)
    company_info = companies_df[companies_df["ticker"] == ticker].iloc[0]

    if ratios_df.empty:
        st.error("Ticker not found — please try another.")
        return

    latest = ratios_df.sort_values("year", ascending=False).iloc[0]

    # ── Company Header Card ──────────────────────────────────────────────────
    sec_name = company_info.get("sector_name", "N/A")
    st.markdown(
        f"""
        <div class="fin-card" style="border-left: 4px solid #38BDF8; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h2 style="margin: 0; font-size: 1.5rem;">{company_info['company_name']}</h2>
                    <div style="color: #94A3B8; font-size: 0.875rem; margin-top: 4px;">
                        NSE: <code style="color: #38BDF8; background: #0B0F19; padding: 2px 6px; border-radius: 4px;">{ticker}</code>
                        &nbsp;|&nbsp; Sector: <strong>{sec_name}</strong>
                    </div>
                </div>
                <div style="text-align: right; color: #94A3B8; font-size: 0.8rem;">
                    Company ID: <strong>{company_info.get('company_id', 'N/A')}</strong><br>
                    History: <strong>{int(ratios_df['year'].min())}–{int(ratios_df['year'].max())}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── 6 KPI Cards ──────────────────────────────────────────────────────────
    roe_col = "return_on_equity_pct" if "return_on_equity_pct" in latest.index else "roe"
    npm_col = "net_profit_margin_pct" if "net_profit_margin_pct" in latest.index else "npm"
    fcf_col = "free_cash_flow_cr" if "free_cash_flow_cr" in latest.index else "free_cash_flow"
    rev_cagr_col = "revenue_cagr_5yr" if "revenue_cagr_5yr" in latest.index else "cagr_sales_5yr"

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        kpi_card("ROE", _fmt(latest.get(roe_col), "%"), "Return on Equity", "#38BDF8")
    with c2:
        kpi_card("ROCE", _fmt(latest.get("roce"), "%"), "Capital Employed", "#38BDF8")
    with c3:
        kpi_card("Net Profit Margin", _fmt(latest.get(npm_col), "%"), "NPM", "#38BDF8")
    with c4:
        kpi_card("D/E Ratio", _fmt(latest.get("debt_to_equity"), "", 2), "Financial Leverage", "#38BDF8")
    with c5:
        kpi_card("Rev CAGR 5Y", _fmt(latest.get(rev_cagr_col), "%"), "Topline Growth", "#38BDF8")
    with c6:
        fcf_val = latest.get(fcf_col)
        fcf_str = _fmt(fcf_val, " Cr", 0) if fcf_val is not None else "N/A"
        kpi_card("Free Cash Flow", fcf_str, "Latest FCF", "#22C55E" if (fcf_val or 0) > 0 else "#EF4444")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Charts ───────────────────────────────────────────────────────────────
    chart_left, chart_right = st.columns(2)

    # Revenue + Net Profit Bar Chart
    with chart_left:
        st.subheader("Revenue & Net Profit (10-Year)")
        if not pl_df.empty:
            pl_sorted = pl_df.sort_values("year").tail(10)
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=pl_sorted["year"], y=pl_sorted["sales"],
                name="Revenue (₹ Cr)", marker_color="#38BDF8"
            ))
            fig_bar.add_trace(go.Bar(
                x=pl_sorted["year"], y=pl_sorted["net_profit"],
                name="Net Profit (₹ Cr)", marker_color="#22C55E"
            ))
            fig_bar.update_layout(
                barmode="group", height=380,
                xaxis_title="Financial Year", yaxis_title="₹ Crores",
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            apply_plotly_theme(fig_bar)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("P&L data not available.")

    # ROE + ROCE Dual-Axis Line Chart
    with chart_right:
        st.subheader("ROE & ROCE Trajectory (10-Year)")
        if not ratios_df.empty:
            r_sorted = ratios_df.sort_values("year").tail(10)
            roe_data = r_sorted[roe_col] if roe_col in r_sorted.columns else None
            roce_data = r_sorted["roce"] if "roce" in r_sorted.columns else None

            fig_line = make_subplots(specs=[[{"secondary_y": True}]])
            if roe_data is not None:
                fig_line.add_trace(go.Scatter(
                    x=r_sorted["year"], y=roe_data,
                    mode="lines+markers", name="ROE (%)",
                    line=dict(color="#F87171", width=2)
                ), secondary_y=False)
            if roce_data is not None:
                fig_line.add_trace(go.Scatter(
                    x=r_sorted["year"], y=roce_data,
                    mode="lines+markers", name="ROCE (%)",
                    line=dict(color="#FBBF24", width=2)
                ), secondary_y=True)
            fig_line.update_layout(
                height=380,
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            apply_plotly_theme(fig_line)
            fig_line.update_yaxes(title_text="ROE (%)", secondary_y=False, gridcolor="#232D42")
            fig_line.update_yaxes(title_text="ROCE (%)", secondary_y=True, gridcolor="#232D42")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Ratio data not available.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Pros & Cons ──────────────────────────────────────────────────────────
    st.subheader("Pros & Cons Analysis")
    pc_df = get_proscons(ticker=ticker)
    if not pc_df.empty:
        latest_pc = pc_df.iloc[0]
        pros_text = latest_pc.get("pros", "")
        cons_text = latest_pc.get("cons", "")

        p_col, c_col = st.columns(2)
        with p_col:
            st.markdown("<div style='color: #4ADE80; font-weight: 600; margin-bottom: 8px;'>Positive Investment Highlights</div>", unsafe_allow_html=True)
            if pros_text and str(pros_text).strip():
                for item in str(pros_text).split("\n"):
                    item = item.strip()
                    if item:
                        st.markdown(f'<div class="badge-pro">✓ {item}</div>', unsafe_allow_html=True)
            else:
                st.caption("No pros data available.")
        with c_col:
            st.markdown("<div style='color: #F87171; font-weight: 600; margin-bottom: 8px;'>Key Risks & Concerns</div>", unsafe_allow_html=True)
            if cons_text and str(cons_text).strip():
                for item in str(cons_text).split("\n"):
                    item = item.strip()
                    if item:
                        st.markdown(f'<div class="badge-con">✕ {item}</div>', unsafe_allow_html=True)
            else:
                st.caption("No cons data available.")
    else:
        st.caption("Pros & Cons data not available for this company.")
