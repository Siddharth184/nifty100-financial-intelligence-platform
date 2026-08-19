"""
Portfolio Summary PDF Generator — Sprint 5 Day 35.

Generates reports/portfolio/portfolio_summary.pdf (1 page per company in alphabetical order by ticker).
Each page includes:
- Company Name, Ticker, Sector
- Top 6 KPIs
- Trend arrows (↑ improved > +2%, ↓ declined < -2%, → flat within ±2%)
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from src.utils.logger import get_logger
from src.db.connection import get_db_connection

logger = get_logger(__name__)

DB_PATH = "db/nifty100.db"
PORTFOLIO_PDF = "reports/portfolio/portfolio_summary.pdf"


def get_trend_arrow(curr_val: Optional[float], prev_val: Optional[float], invert: bool = False) -> Tuple[str, str]:
    """
    Returns trend arrow character and color tuple: (arrow_char, hex_color).
    ↑ improved > +2%, ↓ declined < -2%, → flat within ±2%.
    If invert is True (e.g. D/E), lower is better.
    """
    if curr_val is None or prev_val is None or pd.isna(curr_val) or pd.isna(prev_val) or prev_val == 0:
        return "→", "#64748B"

    curr = float(curr_val)
    prev = float(prev_val)
    pct_change = ((curr - prev) / abs(prev)) * 100.0

    if pct_change > 2.0:
        return ("↓", "#EF4444") if invert else ("↑", "#22C55E")
    elif pct_change < -2.0:
        return ("↑", "#22C55E") if invert else ("↓", "#EF4444")
    else:
        return "→", "#64748B"


def generate_portfolio_summary_pdf(db_path: str = DB_PATH, output_path: str = PORTFOLIO_PDF) -> bool:
    """
    Generates reports/portfolio/portfolio_summary.pdf with 1 page per company in alphabetical ticker order.
    """
    logger.info("Generating Portfolio Summary PDF...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return False

    with get_db_connection(db_path) as conn:
        comp_df = pd.read_sql_query("""
            SELECT c.company_id, c.company_name, c.ticker, s.sector_name
            FROM companies c
            LEFT JOIN sectors s ON c.sector_id = s.sector_id
            ORDER BY c.ticker ASC
        """, conn)

        ratios_df = pd.read_sql_query("""
            SELECT fr.*, mc.market_cap
            FROM financial_ratios fr
            LEFT JOIN market_cap mc ON fr.company_id = mc.company_id AND CAST(mc.date AS INTEGER) = fr.year
            ORDER BY fr.company_id, fr.year ASC
        """, conn)

    if comp_df.empty or ratios_df.empty:
        logger.warning("No data found for portfolio summary PDF.")
        return False

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36
    )

    styles = getSampleStyleSheet()
    c_navy = colors.HexColor("#0F172A")
    c_blue = colors.HexColor("#1E3A8A")
    c_card = colors.HexColor("#F8FAFC")
    c_border = colors.HexColor("#E2E8F0")

    style_title = ParagraphStyle('PortTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.white)
    style_sub = ParagraphStyle('PortSub', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#93C5FD"))
    style_h2 = ParagraphStyle('PortH2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=c_navy, spaceAfter=6)
    
    style_kpi_lbl = ParagraphStyle('KPILbl', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor("#64748B"), alignment=TA_CENTER)
    style_kpi_val = ParagraphStyle('KPIVal', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=c_blue, alignment=TA_CENTER)

    story = []
    comp_count = len(comp_df)

    for idx, (_, c_row) in enumerate(comp_df.iterrows()):
        cid = c_row["company_id"]
        c_name = c_row["company_name"]
        ticker = c_row["ticker"]
        sector = c_row.get("sector_name") or "General"

        c_ratios = ratios_df[ratios_df["company_id"] == cid].sort_values("year")
        if c_ratios.empty:
            continue

        latest = c_ratios.iloc[-1]
        prev = c_ratios.iloc[-2] if len(c_ratios) >= 2 else latest

        # KPI values & trend arrows
        roe_curr = latest.get("return_on_equity_pct") or latest.get("roe")
        roe_prev = prev.get("return_on_equity_pct") or prev.get("roe")
        arrow_roe, col_roe = get_trend_arrow(roe_curr, roe_prev)

        roce_curr = latest.get("roce")
        roce_prev = prev.get("roce")
        arrow_roce, col_roce = get_trend_arrow(roce_curr, roce_prev)

        npm_curr = latest.get("net_profit_margin_pct") or latest.get("npm")
        npm_prev = prev.get("net_profit_margin_pct") or prev.get("npm")
        arrow_npm, col_npm = get_trend_arrow(npm_curr, npm_prev)

        de_curr = latest.get("debt_to_equity")
        de_prev = prev.get("debt_to_equity")
        arrow_de, col_de = get_trend_arrow(de_curr, de_prev, invert=True)

        rev_cagr = latest.get("revenue_cagr_5yr") or latest.get("cagr_sales_5yr")
        prev_rev_cagr = prev.get("revenue_cagr_5yr") or prev.get("cagr_sales_5yr")
        arrow_rev, col_rev = get_trend_arrow(rev_cagr, prev_rev_cagr)

        fcf_curr = latest.get("free_cash_flow_cr") or latest.get("free_cash_flow")
        fcf_prev = prev.get("free_cash_flow_cr") or prev.get("free_cash_flow")
        arrow_fcf, col_fcf = get_trend_arrow(fcf_curr, fcf_prev)

        # 1. Header Banner
        hdr_data = [[
            Paragraph(f"<b>{c_name} ({ticker})</b>", style_title),
            Paragraph(f"<b>{sector}</b> &nbsp;|&nbsp; Page {idx+1} of {comp_count}", style_sub)
        ]]
        hdr_tbl = Table(hdr_data, colWidths=[360, 180])
        hdr_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), c_navy),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        story.append(hdr_tbl)
        story.append(Spacer(1, 16))

        # 2. Top 6 KPIs & Trend Arrows
        story.append(Paragraph("Executive Financial Performance & Trajectory", style_h2))
        story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceAfter=10))

        def make_kpi_cell(lbl, val_str, arrow, color_hex):
            p_lbl = Paragraph(lbl, style_kpi_lbl)
            p_val = Paragraph(f"{val_str} <font color='{color_hex}'><b>{arrow}</b></font>", style_kpi_val)
            return [p_lbl, Spacer(1, 4), p_val]

        c1 = make_kpi_cell("ROE (%)", f"{float(roe_curr):.1f}%" if roe_curr is not None and not pd.isna(roe_curr) else "N/A", arrow_roe, col_roe)
        c2 = make_kpi_cell("ROCE (%)", f"{float(roce_curr):.1f}%" if roce_curr is not None and not pd.isna(roce_curr) else "N/A", arrow_roce, col_roce)
        c3 = make_kpi_cell("NPM (%)", f"{float(npm_curr):.1f}%" if npm_curr is not None and not pd.isna(npm_curr) else "N/A", arrow_npm, col_npm)
        c4 = make_kpi_cell("D/E Ratio", f"{float(de_curr):.2f}" if de_curr is not None and not pd.isna(de_curr) else "N/A", arrow_de, col_de)
        c5 = make_kpi_cell("Rev CAGR 5Y", f"{float(rev_cagr):.1f}%" if rev_cagr is not None and not pd.isna(rev_cagr) else "N/A", arrow_rev, col_rev)
        c6 = make_kpi_cell("FCF (Cr)", f"{float(fcf_curr):.0f}" if fcf_curr is not None and not pd.isna(fcf_curr) else "N/A", arrow_fcf, col_fcf)

        kpi_grid = Table([[c1, c2, c3], [c4, c5, c6]], colWidths=[175, 175, 175])
        kpi_grid.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), c_card),
            ('BOX', (0, 0), (-1, -1), 1, c_border),
            ('INNERGRID', (0, 0), (-1, -1), 1, c_border),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(kpi_grid)
        story.append(Spacer(1, 20))

        # 3. 5-Year Historical Performance Summary Table
        story.append(Paragraph("5-Year Financial Trend Summary", style_h2))
        story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceAfter=8))

        c_5 = c_ratios.tail(5)
        h_style = ParagraphStyle('TH2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.white, alignment=TA_CENTER)
        b_style = ParagraphStyle('TD2', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor("#1E293B"), alignment=TA_CENTER)
        b_style_l = ParagraphStyle('TDL2', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor("#1E293B"), alignment=TA_LEFT)

        th_row = [Paragraph("<b>Metric</b>", h_style)] + [Paragraph(f"<b>FY{int(y)}</b>", h_style) for y in c_5["year"]]
        s_row = [Paragraph("<b>Revenue (Cr)</b>", b_style_l)] + [Paragraph(f"{float(v):.0f}" if pd.notna(v) else "N/A", b_style) for v in c_5.get("sales", [])]
        p_row = [Paragraph("<b>Net Profit (Cr)</b>", b_style_l)] + [Paragraph(f"{float(v):.0f}" if pd.notna(v) else "N/A", b_style) for v in c_5.get("net_profit", [])]
        roe_col = "return_on_equity_pct" if "return_on_equity_pct" in c_5.columns else ("roe" if "roe" in c_5.columns else None)
        roe_vals = c_5[roe_col] if roe_col and roe_col in c_5.columns else []
        r_row = [Paragraph("<b>ROE (%)</b>", b_style_l)] + [Paragraph(f"{float(v):.1f}" if pd.notna(v) else "N/A", b_style) for v in roe_vals]

        col_w_1 = 140
        col_w_r = (540 - col_w_1) / max(len(c_5), 1)
        tbl_5 = Table([th_row, s_row, p_row, r_row], colWidths=[col_w_1] + [col_w_r]*len(c_5))
        tbl_5.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), c_navy),
            ('GRID', (0, 0), (-1, -1), 0.5, c_border),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_card]),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(tbl_5)

        # Force page break for next company unless last
        if idx < comp_count - 1:
            story.append(PageBreak())

    doc.build(story)
    logger.info(f"Generated {output_path} with {comp_count} company summary pages.")
    return True


if __name__ == "__main__":
    res = generate_portfolio_summary_pdf()
    print(f"Portfolio Summary PDF: {'SUCCESS' if res else 'FAILED'}")
