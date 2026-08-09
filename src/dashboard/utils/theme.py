"""
Unified Theme & Styling System — Nifty 100 Financial Intelligence Platform.

Provides custom CSS, Plotly dark theme configuration, and reusable metric card components
for a clean, modern, professional financial dashboard look.
"""

import streamlit as st
import plotly.graph_objects as go

# ── Color Palette Tokens ─────────────────────────────────────────────────────
THEME_COLORS = {
    "bg_dark": "#0B0F19",
    "bg_card": "#151C2C",
    "bg_sidebar": "#070A10",
    "border": "#232D42",
    "border_light": "#2E3B54",
    "primary": "#38BDF8",       # Cyan/Blue
    "primary_dark": "#0284C7",
    "text_main": "#F8FAFC",
    "text_muted": "#94A3B8",
    "positive": "#22C55E",     # Green
    "negative": "#EF4444",     # Red
    "warning": "#F59E0B",      # Amber
}

def apply_custom_css():
    """Injects global custom CSS for dark professional financial dashboard aesthetics."""
    css = f"""
    <style>
    /* Main Background & Fonts */
    .stApp {{
        background-color: {THEME_COLORS['bg_dark']};
        color: {THEME_COLORS['text_main']};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {THEME_COLORS['bg_sidebar']} !important;
        border-right: 1px solid {THEME_COLORS['border']} !important;
    }}

    /* Completely hide any widget label container / text above Home in st.radio */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stWidgetLabel"],
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > label:not([data-baseweb="radio"]) {{
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        visibility: hidden !important;
    }}

    /* Hide default radio circle indicator */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label input,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label svg {{
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
    }}

    /* Container div around radio options */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {{
        gap: 6px !important;
    }}
    
    /* Convert radio item to full-width rectangular button card */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {{
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        min-height: 44px !important;
        padding: 10px 16px !important;
        margin: 0 !important;
        border-radius: 6px !important;
        background-color: {THEME_COLORS['bg_card']} !important;
        border: 1px solid {THEME_COLORS['border']} !important;
        border-left: 3px solid transparent !important;
        color: {THEME_COLORS['text_muted']} !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.15s ease-in-out !important;
        box-sizing: border-box !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {{
        color: inherit !important;
        font-size: 0.9rem !important;
        font-weight: inherit !important;
        margin: 0 !important;
    }}

    /* Hover State (Inactive) */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {{
        background-color: #1E293B !important;
        border-color: {THEME_COLORS['border_light']} !important;
        border-left-color: {THEME_COLORS['primary']} !important;
        color: {THEME_COLORS['text_main']} !important;
    }}

    /* Active Selected State */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked),
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[aria-checked="true"] {{
        background-color: #1E3A8A !important;
        border-color: {THEME_COLORS['primary']} !important;
        border-left: 4px solid {THEME_COLORS['primary']} !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[aria-checked="true"] div[data-testid="stMarkdownContainer"] p {{
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }}

    /* Card Styling */
    .fin-card {{
        background-color: {THEME_COLORS['bg_card']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }}
    
    .fin-card-title {{
        color: {THEME_COLORS['text_muted']};
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }}
    
    .fin-card-value {{
        color: {THEME_COLORS['text_main']};
        font-size: 1.6rem;
        font-weight: 700;
        line-height: 1.2;
    }}
    
    .fin-card-sub {{
        color: {THEME_COLORS['text_muted']};
        font-size: 0.75rem;
        margin-top: 4px;
    }}

    /* Streamlit Native Metric Overrides */
    div[data-testid="stMetric"] {{
        background-color: {THEME_COLORS['bg_card']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 8px;
        padding: 14px 18px;
    }}
    
    div[data-testid="stMetricLabel"] > div {{
        color: {THEME_COLORS['text_muted']} !important;
        font-size: 0.825rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }}
    
    div[data-testid="stMetricValue"] > div {{
        color: {THEME_COLORS['text_main']} !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }}

    /* Headers */
    h1, h2, h3, h4 {{
        color: {THEME_COLORS['text_main']} !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }}
    
    /* Tables & DataFrames */
    .stDataFrame, .stTable {{
        border: 1px solid {THEME_COLORS['border']} !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }}
    
    /* Form Inputs & Selectboxes */
    .stSelectbox > div > div, .stMultiSelect > div > div, .stTextInput > div > div {{
        background-color: {THEME_COLORS['bg_card']} !important;
        border: 1px solid {THEME_COLORS['border']} !important;
        color: {THEME_COLORS['text_main']} !important;
        border-radius: 6px !important;
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: {THEME_COLORS['bg_card']} !important;
        color: {THEME_COLORS['text_main']} !important;
        border: 1px solid {THEME_COLORS['border']} !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }}
    
    .stButton > button:hover {{
        border-color: {THEME_COLORS['primary']} !important;
        color: {THEME_COLORS['primary']} !important;
        background-color: #1A233A !important;
    }}

    .stDownloadButton > button {{
        background-color: {THEME_COLORS['primary_dark']} !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }}
    
    .stDownloadButton > button:hover {{
        background-color: {THEME_COLORS['primary']} !important;
    }}

    /* Badges */
    .badge-pro {{
        background-color: rgba(34, 197, 94, 0.12);
        color: #4ADE80;
        border: 1px solid rgba(34, 197, 94, 0.3);
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.85rem;
        margin-bottom: 6px;
        display: block;
    }}

    .badge-con {{
        background-color: rgba(239, 68, 68, 0.12);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.85rem;
        margin-bottom: 6px;
        display: block;
    }}

    /* Horizontal Rules */
    hr {{
        border-color: {THEME_COLORS['border']} !important;
        margin: 1.2rem 0 !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def apply_plotly_theme(fig: go.Figure) -> go.Figure:
    """Applies a consistent dark financial theme layout to Plotly figures."""
    fig.update_layout(
        paper_bgcolor=THEME_COLORS["bg_card"],
        plot_bgcolor=THEME_COLORS["bg_card"],
        font=dict(color=THEME_COLORS["text_main"], family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"),
        xaxis=dict(
            gridcolor=THEME_COLORS["border"],
            zerolinecolor=THEME_COLORS["border"],
            tickfont=dict(color=THEME_COLORS["text_muted"])
        ),
        yaxis=dict(
            gridcolor=THEME_COLORS["border"],
            zerolinecolor=THEME_COLORS["border"],
            tickfont=dict(color=THEME_COLORS["text_muted"])
        ),
        legend=dict(
            font=dict(color=THEME_COLORS["text_muted"]),
            bgcolor="rgba(0,0,0,0)"
        ),
        margin=dict(t=40, b=40, l=40, r=40)
    )
    return fig


def kpi_card(title: str, value: str, subtitle: str = None, accent_color: str = None):
    """Renders a custom styled KPI card."""
    acc_style = f"border-top: 2px solid {accent_color};" if accent_color else ""
    sub_html = f'<div class="fin-card-sub">{subtitle}</div>' if subtitle else ''
    html = f"""
    <div class="fin-card" style="{acc_style}">
        <div class="fin-card-title">{title}</div>
        <div class="fin-card-value">{value}</div>
        {sub_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
