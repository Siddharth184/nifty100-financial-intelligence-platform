"""
Cached Data Loader — Sprint 4 Dashboard Utility.

Provides @st.cache_data(ttl=600) wrapped functions for all database queries
used by the 8-screen Streamlit dashboard. Queries the existing SQLite database
at db/nifty100.db without modifying any data.
"""

import sqlite3
import os
import pandas as pd
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "db", "nifty100.db")
DB_PATH = os.path.abspath(DB_PATH)


def _get_conn():
    """Returns a read-only SQLite connection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """Returns all companies with sector information."""
    conn = _get_conn()
    query = """
        SELECT c.company_id, c.company_name, c.ticker, c.sector_id,
               s.sector_name
        FROM companies c
        LEFT JOIN sectors s ON c.sector_id = s.sector_id
        ORDER BY c.company_name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker: str = None, year: int = None) -> pd.DataFrame:
    """
    Returns financial ratios. Optionally filtered by ticker and/or year.
    Joins companies, sectors, P&L, balance sheet, cashflow, and market_cap.
    """
    conn = _get_conn()
    query = """
        SELECT fr.*,
               c.company_name, c.ticker, s.sector_name,
               pnl.sales, pnl.operating_profit, pnl.net_profit, pnl.eps,
               bs.total_assets, bs.total_equity,
               cf.operating_cash_flow, cf.investing_cash_flow,
               cf.financing_cash_flow, cf.net_cash_flow,
               mc.market_cap
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.company_id
        LEFT JOIN sectors s ON c.sector_id = s.sector_id
        LEFT JOIN profitandloss pnl ON fr.company_id = pnl.company_id AND fr.year = pnl.year
        LEFT JOIN balancesheet bs ON fr.company_id = bs.company_id AND fr.year = bs.year
        LEFT JOIN cashflow cf ON fr.company_id = cf.company_id AND fr.year = cf.year
        LEFT JOIN market_cap mc ON fr.company_id = mc.company_id AND CAST(mc.date AS INTEGER) = fr.year
    """
    conditions = []
    params = []
    if ticker:
        conditions.append("c.ticker = ?")
        params.append(ticker)
    if year:
        conditions.append("fr.year = ?")
        params.append(year)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY fr.year DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios_all(year: int = None) -> pd.DataFrame:
    """Returns all financial ratios, optionally filtered by year. Used for aggregate screens."""
    conn = _get_conn()
    query = """
        SELECT fr.*,
               c.company_name, c.ticker, s.sector_name,
               pnl.sales, pnl.operating_profit, pnl.net_profit, pnl.eps,
               bs.total_assets, bs.total_equity,
               cf.operating_cash_flow, cf.investing_cash_flow,
               cf.financing_cash_flow, cf.net_cash_flow,
               mc.market_cap
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.company_id
        LEFT JOIN sectors s ON c.sector_id = s.sector_id
        LEFT JOIN profitandloss pnl ON fr.company_id = pnl.company_id AND fr.year = pnl.year
        LEFT JOIN balancesheet bs ON fr.company_id = bs.company_id AND fr.year = bs.year
        LEFT JOIN cashflow cf ON fr.company_id = cf.company_id AND fr.year = cf.year
        LEFT JOIN market_cap mc ON fr.company_id = mc.company_id AND CAST(mc.date AS INTEGER) = fr.year
    """
    if year:
        query += " WHERE fr.year = ?"
        df = pd.read_sql_query(query, conn, params=[year])
    else:
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    """Returns Profit & Loss data for a given ticker."""
    conn = _get_conn()
    query = """
        SELECT pnl.* FROM profitandloss pnl
        JOIN companies c ON pnl.company_id = c.company_id
        WHERE c.ticker = ?
        ORDER BY pnl.year
    """
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    """Returns Balance Sheet data for a given ticker."""
    conn = _get_conn()
    query = """
        SELECT bs.* FROM balancesheet bs
        JOIN companies c ON bs.company_id = c.company_id
        WHERE c.ticker = ?
        ORDER BY bs.year
    """
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    """Returns Cash Flow data for a given ticker."""
    conn = _get_conn()
    query = """
        SELECT cf.* FROM cashflow cf
        JOIN companies c ON cf.company_id = c.company_id
        WHERE c.ticker = ?
        ORDER BY cf.year
    """
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Returns all sectors."""
    conn = _get_conn()
    query = "SELECT * FROM sectors ORDER BY sector_name"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    """Returns peer comparison data for a given peer group."""
    conn = _get_conn()
    query = """
        SELECT pp.*, c.company_name, c.ticker
        FROM peer_percentiles pp
        JOIN companies c ON pp.company_id = c.company_id
        WHERE pp.peer_group_name = ?
        ORDER BY pp.company_id, pp.metric
    """
    df = pd.read_sql_query(query, conn, params=[group_name])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peer_group_names() -> list:
    """Returns distinct peer group names."""
    conn = _get_conn()
    query = "SELECT DISTINCT peer_group_name FROM peer_percentiles ORDER BY peer_group_name"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df["peer_group_name"].tolist()


@st.cache_data(ttl=600)
def get_valuation(ticker: str) -> pd.DataFrame:
    """Returns valuation data for a given ticker (from valuation_summary if available)."""
    conn = _get_conn()
    # First check if valuation table exists
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='valuation_summary'", conn
    )
    if tables.empty:
        conn.close()
        return pd.DataFrame()
    query = """
        SELECT vs.* FROM valuation_summary vs
        WHERE vs.company_id = (SELECT company_id FROM companies WHERE ticker = ?)
    """
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_proscons(ticker: str) -> pd.DataFrame:
    """Returns pros and cons for a given ticker."""
    conn = _get_conn()
    query = """
        SELECT pc.* FROM prosandcons pc
        JOIN companies c ON pc.company_id = c.company_id
        WHERE c.ticker = ?
        ORDER BY pc.year DESC
    """
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_documents(ticker: str) -> pd.DataFrame:
    """Returns documents (annual reports) for a given ticker."""
    conn = _get_conn()
    query = """
        SELECT d.* FROM documents d
        JOIN companies c ON d.company_id = c.company_id
        WHERE c.ticker = ?
        ORDER BY d.year DESC
    """
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_available_years() -> list:
    """Returns list of available years in the financial_ratios table."""
    conn = _get_conn()
    query = "SELECT DISTINCT year FROM financial_ratios ORDER BY year"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df["year"].tolist()
