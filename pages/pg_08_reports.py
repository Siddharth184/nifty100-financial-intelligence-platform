"""
Annual Reports Screen — Sprint 4 Day 25.

Displays:
- Company search box
- Yearly annual report links (2024, 2023, 2022...)
- Clean buttons for available PDF links
- Red subtle badge for unavailable reports
- Safe missing data handling
"""

import streamlit as st
import pandas as pd
from src.dashboard.utils.db import get_companies, get_documents


def render():
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h1 style="font-size: 1.8rem; margin-bottom: 4px;">ANNUAL REPORTS</h1>
            <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">
                Access official BSE annual report filings and regulatory disclosures.
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

    selected = st.selectbox("🔎 Search Company", options=[""] + options, index=0, key="reports_company")
    if not selected:
        st.info("👆 Select a company to view available annual reports.")
        return

    ticker = ticker_map.get(selected)
    docs_df = get_documents(ticker=ticker)

    if docs_df.empty:
        st.info(f"No annual report records found for {selected}.")
        st.caption("BSE filing records depend on the documents table in the database.")
        return

    st.markdown(f"### Available Filings — {selected.split('(')[0].strip()}")
    st.markdown("<hr>", unsafe_allow_html=True)

    for _, row in docs_df.iterrows():
        year = row.get("year", "N/A")
        url = row.get("doc_url", "")

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown(f"**FY {year} Annual Report**")
        with col2:
            if url and str(url).strip() and str(url).strip().lower() != "nan":
                st.markdown(f"[📄 Open BSE PDF Filing]({url})")
            else:
                st.markdown('<span class="badge-con">Report unavailable</span>', unsafe_allow_html=True)
        with col3:
            if url and str(url).strip() and str(url).strip().lower() != "nan":
                st.markdown("🟢 Filing Available")
            else:
                st.markdown("🔴 Filing Missing")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("Direct links redirect to official BSE India filing archives.")
