"""
Nifty 100 Financial Intelligence Platform — Streamlit Dashboard (Sprint 4).

Main entry point for the 8-screen dashboard application.
Run with: streamlit run src/dashboard/app.py
"""

import sys
import os

# Ensure project root is in sys.path for all imports (pages, src, config)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from src.dashboard.utils.theme import apply_custom_css

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply global dark financial theme CSS
apply_custom_css()

# ── Sidebar Header ──────────────────────────────────────────────────────────
st.sidebar.markdown(
    """
    <div style="padding: 4px 0 16px 0; border-bottom: 1px solid #232D42; margin-bottom: 16px;">
        <div style="font-size: 1.25rem; font-weight: 800; color: #38BDF8; letter-spacing: 0.5px;">NIFTY 100</div>
        <div style="font-size: 0.825rem; font-weight: 500; color: #94A3B8;">Financial Intelligence</div>
    </div>
    """,
    unsafe_allow_html=True
)

SCREENS = {
    "Home": "home",
    "Company Profile": "profile",
    "Screener": "screener",
    "Peer Comparison": "peers",
    "Trend Analysis": "trends",
    "Sector Analysis": "sectors",
    "Capital Allocation": "capital",
    "Annual Reports": "reports",
}

selected = st.sidebar.radio("", list(SCREENS.keys()), label_visibility="collapsed")
screen_key = SCREENS[selected]

st.sidebar.markdown("<hr style='margin: 20px 0 12px 0;'>", unsafe_allow_html=True)
st.sidebar.caption("Sprint 4 • Financial Intelligence Platform")

# ── Dynamic Page Routing ─────────────────────────────────────────────────────
if screen_key == "home":
    from pages import pg_01_home
    pg_01_home.render()
elif screen_key == "profile":
    from pages import pg_02_profile
    pg_02_profile.render()
elif screen_key == "screener":
    from pages import pg_03_screener
    pg_03_screener.render()
elif screen_key == "peers":
    from pages import pg_04_peers
    pg_04_peers.render()
elif screen_key == "trends":
    from pages import pg_05_trends
    pg_05_trends.render()
elif screen_key == "sectors":
    from pages import pg_06_sectors
    pg_06_sectors.render()
elif screen_key == "capital":
    from pages import pg_07_capital
    pg_07_capital.render()
elif screen_key == "reports":
    from pages import pg_08_reports
    pg_08_reports.render()
