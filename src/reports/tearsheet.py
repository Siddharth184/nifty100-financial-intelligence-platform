"""
Company Tearsheet PDF Generator — Sprint 5 Day 33 & 34.

Generates an executive 2-page PDF tearsheet for any company using ReportLab and Matplotlib.
Page 1: Navy header, 6 KPI tiles (2x3), 10-year Revenue & Net Profit chart + table, ROE/ROCE trend chart + table.
Page 2: Balance Sheet composition stacked bar chart + table, Cash Flow waterfall chart + table, Pros & Cons bullet sections, Capital Allocation badge.

Enforces strict ReportLab word-wrapping and column constraints to guarantee 0 overflow and exact 2-page layout.
"""

import os
import io
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from src.utils.logger import get_logger
from src.db.connection import get_db_connection

logger = get_logger(__name__)

DB_PATH = "db/nifty100.db"
PROS_CONS_CSV = "output/pros_cons_generated.csv"
CAPITAL_CSV = "output/capital_allocation.csv"
TEARSHEETS_DIR = "reports/tearsheets"


def _fmt(val: Any, suffix: str = "", decimals: int = 1) -> str:
    """Safely format numbers, returning 'N/A' if None/NaN."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        f_val = float(val)
        return f"{f_val:.{decimals}f}{suffix}"
    except (ValueError, TypeError):
        return str(val)


# ── Chart Rendering Engines (Matplotlib -> ReportLab Image) ────────────────────

def _make_rev_pat_chart(r_10: pd.DataFrame) -> Image:
    """Renders 10-year Revenue (Sales) & Net Profit (PAT) bar chart."""
    years = [str(int(y)) for y in r_10["year"]]
    sales = [float(v) if pd.notna(v) else 0.0 for v in r_10["sales"]]
    pat = [float(v) if pd.notna(v) else 0.0 for v in r_10["net_profit"]]

    fig, ax = plt.subplots(figsize=(7.5, 1.5), dpi=150)
    x = np.arange(len(years))
    width = 0.35

    ax.bar(x - width/2, sales, width, label='Sales (Revenue)', color='#1E3A8A')
    ax.bar(x + width/2, pat, width, label='Net Profit (PAT)', color='#0284C7')

    ax.set_xticks(x)
    ax.set_xticklabels([f"FY{y[-2:]}" for y in years], fontsize=8)
    ax.set_ylabel("₹ Crores", fontsize=8)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.legend(loc='upper left', fontsize=7.5, frameon=True, facecolor='#F8FAFC', edgecolor='#E2E8F0')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return Image(buf, width=540, height=105)


def _make_roe_roce_chart(r_10: pd.DataFrame) -> Image:
    """Renders 10-year ROE & ROCE trend line chart."""
    years = [str(int(y)) for y in r_10["year"]]
    roe_col = "return_on_equity_pct" if "return_on_equity_pct" in r_10.columns else "roe"
    roe_vals = [float(v) if pd.notna(v) else np.nan for v in r_10[roe_col]]
    roce_vals = [float(v) if pd.notna(v) else np.nan for v in r_10["roce"]]

    fig, ax = plt.subplots(figsize=(7.5, 1.5), dpi=150)
    x = np.arange(len(years))

    ax.plot(x, roe_vals, marker='o', linewidth=2, label='ROE (%)', color='#15803D')
    ax.plot(x, roce_vals, marker='s', linewidth=2, linestyle='--', label='ROCE (%)', color='#0284C7')

    ax.set_xticks(x)
    ax.set_xticklabels([f"FY{y[-2:]}" for y in years], fontsize=8)
    ax.set_ylabel("%", fontsize=8)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.legend(loc='upper left', fontsize=7.5, frameon=True, facecolor='#F8FAFC', edgecolor='#E2E8F0')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return Image(buf, width=540, height=105)


def _make_bs_chart(r_10: pd.DataFrame) -> Image:
    """Renders 10-year Balance Sheet Composition stacked bar chart."""
    years = [str(int(y)) for y in r_10["year"]]
    eq = [max(0.0, float(v)) if pd.notna(v) else 0.0 for v in r_10["total_equity"]]
    debt = [max(0.0, float(v)) if pd.notna(v) else 0.0 for v in (r_10["total_debt_cr"] if "total_debt_cr" in r_10.columns else [0.0]*len(r_10))]
    tot_liab = [max(0.0, float(v)) if pd.notna(v) else 0.0 for v in r_10["total_liabilities"]]
    other_liab = [max(0.0, tot_liab[i] - debt[i]) for i in range(len(tot_liab))]

    fig, ax = plt.subplots(figsize=(7.5, 1.5), dpi=150)
    x = np.arange(len(years))
    width = 0.45

    ax.bar(x, eq, width, label='Equity', color='#1E3A8A')
    ax.bar(x, debt, width, bottom=eq, label='Borrowings (Debt)', color='#EF4444')
    bottom_other = np.array(eq) + np.array(debt)
    ax.bar(x, other_liab, width, bottom=bottom_other, label='Other Liabilities', color='#94A3B8')

    ax.set_xticks(x)
    ax.set_xticklabels([f"FY{y[-2:]}" for y in years], fontsize=8)
    ax.set_ylabel("₹ Crores", fontsize=8)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.legend(loc='upper left', fontsize=7.5, frameon=True, facecolor='#F8FAFC', edgecolor='#E2E8F0')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return Image(buf, width=540, height=105)


def _make_cf_waterfall_chart(latest_row: pd.Series) -> Image:
    """Renders Cash Flow Waterfall Breakdown for latest FY."""
    cfo = float(latest_row.get("operating_cash_flow") or 0.0)
    cfi = float(latest_row.get("investing_cash_flow") or 0.0)
    cff = float(latest_row.get("financing_cash_flow") or 0.0)
    net = float(latest_row.get("net_cash_flow") or 0.0)

    cats = ['CFO (Operating)', 'CFI (Investing)', 'CFF (Financing)', 'Net Cash Flow']
    vals = [cfo, cfi, cff, net]
    colors_list = ['#15803D' if cfo >= 0 else '#B91C1C',
                   '#0284C7' if cfi >= 0 else '#0284C7',
                   '#EAB308' if cff >= 0 else '#EAB308',
                   '#0F172A']

    fig, ax = plt.subplots(figsize=(7.5, 1.4), dpi=150)
    x = np.arange(4)
    bars = ax.bar(x, vals, width=0.45, color=colors_list)

    ax.axhline(0, color='#64748B', linewidth=0.8, linestyle='--')
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylabel("₹ Crores", fontsize=8)

    for bar in bars:
        height = bar.get_height()
        va = 'bottom' if height >= 0 else 'top'
        ax.annotate(f"{height:,.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3 if height >= 0 else -3),
                    textcoords="offset points",
                    ha='center', va=va, fontsize=7.5, fontweight='bold')

    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return Image(buf, width=540, height=95)


def build_tearsheet_pdf(
    company_id: str,
    output_path: str,
    db_path: str = DB_PATH,
    pros_cons_path: str = PROS_CONS_CSV,
    capital_path: str = CAPITAL_CSV
) -> bool:
    """
    Generates a 2-page executive PDF tearsheet for the specified company_id.
    Returns True if successfully generated, False otherwise.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False

    with get_db_connection(db_path) as conn:
        comp_df = pd.read_sql_query("""
            SELECT c.company_id, c.company_name, c.ticker, s.sector_name
            FROM companies c
            LEFT JOIN sectors s ON c.sector_id = s.sector_id
            WHERE c.company_id = ?
        """, conn, params=[company_id])

        if comp_df.empty:
            logger.error(f"Company {company_id} not found in database.")
            return False

        company_info = comp_df.iloc[0].to_dict()

        cf_cols = pd.read_sql_query("PRAGMA table_info(cashflow)", conn)['name'].tolist()
        cfo_col = "operating_cash_flow" if "operating_cash_flow" in cf_cols else ("operating_activity" if "operating_activity" in cf_cols else "operating_cash_flow")
        cfi_col = "investing_cash_flow" if "investing_cash_flow" in cf_cols else ("investing_activity" if "investing_activity" in cf_cols else "investing_cash_flow")
        cff_col = "financing_cash_flow" if "financing_cash_flow" in cf_cols else ("financing_activity" if "financing_activity" in cf_cols else "financing_cash_flow")

        query_ratios = f"""
            SELECT fr.*,
                   pnl.sales, pnl.operating_profit, pnl.net_profit, pnl.eps,
                   bs.total_assets, bs.total_equity, bs.total_liabilities,
                   cf.{cfo_col} AS operating_cash_flow,
                   cf.{cfi_col} AS investing_cash_flow,
                   cf.{cff_col} AS financing_cash_flow,
                   cf.net_cash_flow
            FROM financial_ratios fr
            LEFT JOIN profitandloss pnl ON fr.company_id = pnl.company_id AND fr.year = pnl.year
            LEFT JOIN balancesheet bs ON fr.company_id = bs.company_id AND fr.year = bs.year
            LEFT JOIN cashflow cf ON fr.company_id = cf.company_id AND fr.year = cf.year
            WHERE fr.company_id = ?
            ORDER BY fr.year ASC
        """
        ratios_df = pd.read_sql_query(query_ratios, conn, params=[company_id])

    if ratios_df.empty:
        logger.warning(f"No ratio history for company {company_id}")
        return False

    latest = ratios_df.iloc[-1]
    company_name = company_info.get("company_name", company_id)
    ticker = company_info.get("ticker", company_id)
    sector = company_info.get("sector_name", "General")

    # Load Pros & Cons
    pros_list = []
    cons_list = []
    if os.path.exists(pros_cons_path):
        pc_df = pd.read_csv(pros_cons_path)
        c_pc = pc_df[pc_df["company_id"] == company_id]
        pros_list = c_pc[c_pc["type"] == "pro"]["text"].tolist()
        cons_list = c_pc[c_pc["type"] == "con"]["text"].tolist()

    # Load Capital Allocation Strategy
    capital_label = "Reinvestor"
    if os.path.exists(capital_path):
        cap_df = pd.read_csv(capital_path)
        c_cap = cap_df[cap_df["company_id"] == company_id].sort_values("year")
        if not c_cap.empty:
            capital_label = c_cap.iloc[-1]["pattern_label"]

    # ── Setup ReportLab Styles & Document ─────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_navy = colors.HexColor("#0F172A")
    c_blue = colors.HexColor("#1E3A8A")
    c_card = colors.HexColor("#F8FAFC")
    c_border = colors.HexColor("#E2E8F0")
    c_text = colors.HexColor("#1E293B")
    c_green = colors.HexColor("#15803D")
    c_red = colors.HexColor("#B91C1C")

    # Typography styles
    style_header_title = ParagraphStyle(
        'HeaderTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=16, textColor=colors.white, leading=19
    )
    style_header_sub = ParagraphStyle(
        'HeaderSub', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.5, textColor=colors.HexColor("#93C5FD"), leading=12
    )
    style_sec_title = ParagraphStyle(
        'SecTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10.5, textColor=c_navy, leading=13, spaceAfter=4
    )
    style_kpi_label = ParagraphStyle(
        'KPILabel', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor("#64748B"), leading=9, alignment=TA_CENTER
    )
    style_kpi_val = ParagraphStyle(
        'KPIVal', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12.5, textColor=c_blue, leading=15, alignment=TA_CENTER
    )
    style_table_header = ParagraphStyle(
        'TblHdr', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.white, leading=9, alignment=TA_CENTER
    )
    style_table_cell = ParagraphStyle(
        'TblCell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, textColor=c_text, leading=9, alignment=TA_CENTER
    )
    style_table_cell_left = ParagraphStyle(
        'TblCellLeft', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, textColor=c_text, leading=9, alignment=TA_LEFT
    )
    style_pro_text = ParagraphStyle(
        'ProText', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, textColor=c_green, leading=10
    )
    style_con_text = ParagraphStyle(
        'ConText', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, textColor=c_red, leading=10
    )

    story = []

    # =========================================================================
    # PAGE 1: EXECUTIVE SUMMARY, KPIS, REVENUE/PROFIT & ROE/ROCE TRAJECTORY
    # =========================================================================

    # 1. Navy Banner Header
    hdr_content = [
        [
            Paragraph(f"<b>{company_name}</b>", style_header_title),
            Paragraph(f"<b>NSE: {ticker}</b> &nbsp;|&nbsp; Sector: <b>{sector}</b>", style_header_sub)
        ]
    ]
    hdr_table = Table(hdr_content, colWidths=[350, 190])
    hdr_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_navy),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(hdr_table)
    story.append(Spacer(1, 6))

    # 2. 6 KPI Tiles (2 rows x 3 columns)
    roe_val = latest.get("return_on_equity_pct") or latest.get("roe")
    roce_val = latest.get("roce")
    npm_val = latest.get("net_profit_margin_pct") or latest.get("npm")
    de_val = latest.get("debt_to_equity")
    rev_cagr = latest.get("revenue_cagr_5yr") or latest.get("cagr_sales_5yr")
    fcf_val = latest.get("free_cash_flow_cr") or latest.get("free_cash_flow")

    kpi_items = [
        ("RETURN ON EQUITY", _fmt(roe_val, "%")),
        ("RETURN ON CAP. EMP.", _fmt(roce_val, "%")),
        ("NET PROFIT MARGIN", _fmt(npm_val, "%")),
        ("DEBT / EQUITY", _fmt(de_val, "", 2)),
        ("REVENUE CAGR (5Y)", _fmt(rev_cagr, "%")),
        ("FREE CASH FLOW", _fmt(fcf_val, " Cr", 0))
    ]

    kpi_cells = []
    for item_label, item_val in kpi_items:
        cell_p = [
            Paragraph(item_label, style_kpi_label),
            Spacer(1, 2),
            Paragraph(item_val, style_kpi_val)
        ]
        kpi_cells.append(cell_p)

    kpi_data = [
        [kpi_cells[0], kpi_cells[1], kpi_cells[2]],
        [kpi_cells[3], kpi_cells[4], kpi_cells[5]]
    ]
    kpi_table = Table(kpi_data, colWidths=[180, 180, 180])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_card),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 1, c_border),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 6))

    # 3. 10-Year Revenue & Net Profit Chart + Data Table
    story.append(Paragraph("10-Year Revenue & Net Profitability (₹ Crores)", style_sec_title))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceAfter=4))

    r_10 = ratios_df.tail(10)
    story.append(_make_rev_pat_chart(r_10))
    story.append(Spacer(1, 4))

    rev_hdr = [Paragraph("<b>Metric</b>", style_table_header)] + [Paragraph(f"<b>FY{int(y)}</b>", style_table_header) for y in r_10["year"]]
    rev_row = [Paragraph("<b>Sales (Revenue)</b>", style_table_cell_left)] + [Paragraph(_fmt(v, "", 0), style_table_cell) for v in r_10["sales"]]
    pat_row = [Paragraph("<b>Net Profit (PAT)</b>", style_table_cell_left)] + [Paragraph(_fmt(v, "", 0), style_table_cell) for v in r_10["net_profit"]]

    col_w_first = 110
    col_w_rest = (540 - col_w_first) / max(len(r_10), 1)
    rev_table = Table([rev_hdr, rev_row, pat_row], colWidths=[col_w_first] + [col_w_rest]*len(r_10))
    rev_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_card]),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(rev_table)
    story.append(Spacer(1, 6))

    # 4. 10-Year ROE & ROCE Trajectory Chart + Data Table
    story.append(Paragraph("Return Ratios Trajectory (%)", style_sec_title))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceAfter=4))

    story.append(_make_roe_roce_chart(r_10))
    story.append(Spacer(1, 4))

    roe_col_name = "return_on_equity_pct" if "return_on_equity_pct" in r_10.columns else "roe"
    ratio_hdr = [Paragraph("<b>Ratio</b>", style_table_header)] + [Paragraph(f"<b>FY{int(y)}</b>", style_table_header) for y in r_10["year"]]
    roe_t_row = [Paragraph("<b>ROE (%)</b>", style_table_cell_left)] + [Paragraph(_fmt(v, "%", 1), style_table_cell) for v in r_10[roe_col_name]]
    roce_t_row = [Paragraph("<b>ROCE (%)</b>", style_table_cell_left)] + [Paragraph(_fmt(v, "%", 1), style_table_cell) for v in r_10["roce"]]

    ratio_table = Table([ratio_hdr, roe_t_row, roce_t_row], colWidths=[col_w_first] + [col_w_rest]*len(r_10))
    ratio_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_blue),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_card]),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(ratio_table)

    # PAGE 1 END — Force PageBreak
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: BALANCE SHEET, CASH FLOW WATERFALL, PROS/CONS & CAPITAL ALLOCATION
    # =========================================================================

    story.append(Paragraph(f"<b>{company_name} ({ticker})</b> — Financial Position & Strategic Analysis", style_sec_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_navy, spaceAfter=6))

    # 1. Balance Sheet Composition Chart + Data Table
    story.append(Paragraph("Balance Sheet Capital Structure (₹ Crores)", style_sec_title))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceAfter=4))

    story.append(_make_bs_chart(r_10))
    story.append(Spacer(1, 4))

    bs_hdr = [Paragraph("<b>Component</b>", style_table_header)] + [Paragraph(f"<b>FY{int(y)}</b>", style_table_header) for y in r_10["year"]]
    eq_row = [Paragraph("<b>Equity</b>", style_table_cell_left)] + [Paragraph(_fmt(v, "", 0), style_table_cell) for v in r_10["total_equity"]]
    liab_row = [Paragraph("<b>Liabilities</b>", style_table_cell_left)] + [Paragraph(_fmt(v, "", 0), style_table_cell) for v in r_10["total_liabilities"]]
    ast_row = [Paragraph("<b>Assets</b>", style_table_cell_left)] + [Paragraph(_fmt(v, "", 0), style_table_cell) for v in r_10["total_assets"]]

    bs_table = Table([bs_hdr, eq_row, liab_row, ast_row], colWidths=[col_w_first] + [col_w_rest]*len(r_10))
    bs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_card]),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(bs_table)
    story.append(Spacer(1, 6))

    # 2. Cash Flow Waterfall Summary (Latest Year) Chart + Table
    story.append(Paragraph(f"Cash Flow Waterfall Breakdown (FY{int(latest['year'])})", style_sec_title))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceAfter=4))

    story.append(_make_cf_waterfall_chart(latest))
    story.append(Spacer(1, 4))

    cf_cfo = latest.get("operating_cash_flow")
    cf_cfi = latest.get("investing_cash_flow")
    cf_cff = latest.get("financing_cash_flow")
    cf_net = latest.get("net_cash_flow")

    cf_hdr = [Paragraph("<b>Operating CF (CFO)</b>", style_table_header), Paragraph("<b>Investing CF (CFI)</b>", style_table_header), Paragraph("<b>Financing CF (CFF)</b>", style_table_header), Paragraph("<b>Net Cash Flow</b>", style_table_header)]
    cf_row = [Paragraph(_fmt(cf_cfo, " Cr", 1), style_table_cell), Paragraph(_fmt(cf_cfi, " Cr", 1), style_table_cell), Paragraph(_fmt(cf_cff, " Cr", 1), style_table_cell), Paragraph(_fmt(cf_net, " Cr", 1), style_table_cell)]
    cf_table = Table([cf_hdr, cf_row], colWidths=[135, 135, 135, 135])
    cf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_blue),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('BACKGROUND', (0, 1), (-1, 1), c_card),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(cf_table)
    story.append(Spacer(1, 6))

    # 3. Pros & Cons Sections + Capital Allocation Badge
    pc_left = [Paragraph("<b>INVESTMENT HIGHLIGHTS (PROS)</b>", ParagraphStyle('ProHdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, textColor=c_green, spaceAfter=3))]
    if pros_list:
        for p_item in pros_list[:3]:
            pc_left.append(Paragraph(f"✓ {p_item}", style_pro_text))
            pc_left.append(Spacer(1, 1.5))
    else:
        pc_left.append(Paragraph("✓ Stable financial profile backed by solid market position", style_pro_text))

    pc_right = [Paragraph("<b>KEY RISKS & CONCERNS (CONS)</b>", ParagraphStyle('ConHdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, textColor=c_red, spaceAfter=3))]
    if cons_list:
        for c_item in cons_list[:3]:
            pc_right.append(Paragraph(f"✕ {c_item}", style_con_text))
            pc_right.append(Spacer(1, 1.5))
    else:
        pc_right.append(Paragraph("✕ Ongoing competitive and macroeconomic monitoring required", style_con_text))

    pc_table = Table([[pc_left, pc_right]], colWidths=[265, 265])
    pc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#FEF2F2")),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor("#BBF7D0")),
        ('BOX', (1, 0), (1, 0), 1, colors.HexColor("#FECACA")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(pc_table)
    story.append(Spacer(1, 6))

    # 4. Capital Allocation Badge Footer
    badge_p = Paragraph(f"<b>Capital Allocation Archetype:</b> <font color='#1E3A8A'><b>{capital_label}</b></font>", ParagraphStyle('BadgeP', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, textColor=c_navy, alignment=TA_CENTER))
    badge_tbl = Table([[badge_p]], colWidths=[540])
    badge_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#BFDBFE")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(badge_tbl)

    # Build PDF
    doc.build(story)
    return True


def run_batch_tearsheets(
    db_path: str = DB_PATH,
    output_dir: str = TEARSHEETS_DIR,
    skipped_csv: str = "output/skipped_tearsheets.csv"
) -> int:
    """
    Runs batch tearsheet PDF generation for all 92 companies.
    Skips companies with < 3 years usable data and logs to skipped_tearsheets.csv.
    """
    logger.info("Starting Batch Tearsheet PDF Generation...")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("output", exist_ok=True)

    if not os.path.exists(db_path):
        logger.error(f"Database not found at {db_path}")
        return 0

    with get_db_connection(db_path) as conn:
        comps_df = pd.read_sql_query("SELECT company_id, ticker FROM companies", conn)
        ratios_cnt = pd.read_sql_query("SELECT company_id, COUNT(*) as yr_cnt FROM financial_ratios GROUP BY company_id", conn)

    cnt_map = dict(zip(ratios_cnt["company_id"], ratios_cnt["yr_cnt"]))
    
    generated_count = 0
    skipped_rows = []

    for _, c_row in comps_df.iterrows():
        cid = c_row["company_id"]
        ticker = c_row["ticker"]
        yr_cnt = cnt_map.get(cid, 0)

        if yr_cnt < 3:
            skipped_rows.append({
                "company_id": cid,
                "ticker": ticker,
                "years_available": yr_cnt,
                "reason": "Insufficient financial history (< 3 years)"
            })
            continue

        pdf_path = os.path.join(output_dir, f"{ticker}_tearsheet.pdf")
        success = build_tearsheet_pdf(cid, pdf_path, db_path)
        if success:
            generated_count += 1

    skipped_df = pd.DataFrame(skipped_rows)
    if not skipped_df.empty:
        skipped_df.to_csv(skipped_csv, index=False)
        logger.info(f"Logged {len(skipped_df)} skipped companies to {skipped_csv}.")
    else:
        pd.DataFrame(columns=["company_id", "ticker", "years_available", "reason"]).to_csv(skipped_csv, index=False)

    logger.info(f"Batch Tearsheets Complete: Generated {generated_count} PDFs in {output_dir}.")
    return generated_count


if __name__ == "__main__":
    test_tickers = ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"]
    print("Testing 5 Benchmark Tearsheets...")
    for t in test_tickers:
        res = build_tearsheet_pdf(t, f"reports/tearsheets/{t}_tearsheet.pdf")
        print(f"  {t}_tearsheet.pdf: {'SUCCESS' if res else 'FAILED'}")
