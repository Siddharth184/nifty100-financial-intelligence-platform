"""
Sector Report PDF Generator — Sprint 5 Day 34.

Generates 11 sector PDF reports saved in reports/sector/<sector_name>_report.pdf.
Each sector PDF contains:
- Sector summary page with median KPIs across member companies
- Member company directory with 8 financial metrics per company
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
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from src.utils.logger import get_logger
from src.db.connection import get_db_connection

logger = get_logger(__name__)

DB_PATH = "db/nifty100.db"
SECTOR_DIR = "reports/sector"


def _fmt(val: Any, suffix: str = "", decimals: int = 1) -> str:
    """Safely format numbers, returning 'N/A' if None/NaN."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        f_val = float(val)
        return f"{f_val:.{decimals}f}{suffix}"
    except (ValueError, TypeError):
        return str(val)


def generate_sector_pdf(sector_name: str, df_sector: pd.DataFrame, output_path: str) -> bool:
    """
    Generates a sector report PDF for the given sector_name and company dataframe.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if df_sector.empty:
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

    style_title = ParagraphStyle('SecTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.white)
    style_sub = ParagraphStyle('SecSub', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#93C5FD"))
    style_h2 = ParagraphStyle('SecH2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=c_navy, spaceAfter=6)
    
    style_th = ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.white, alignment=TA_CENTER)
    style_td = ParagraphStyle('TD', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor("#1E293B"), alignment=TA_CENTER)
    style_td_l = ParagraphStyle('TDL', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor("#1E293B"), alignment=TA_LEFT)

    story = []

    # 1. Header Banner
    hdr_data = [[
        Paragraph(f"<b>SECTOR REPORT: {sector_name.upper()}</b>", style_title),
        Paragraph(f"<b>Universe: {len(df_sector)} Companies</b>", style_sub)
    ]]
    hdr_tbl = Table(hdr_data, colWidths=[360, 180])
    hdr_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_navy),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 14))

    # 2. Sector Median KPIs
    story.append(Paragraph("Sector Median Benchmarks", style_h2))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceAfter=8))

    roe_col = "return_on_equity_pct" if "return_on_equity_pct" in df_sector.columns else "roe"
    rev_col = "revenue_cagr_5yr" if "revenue_cagr_5yr" in df_sector.columns else "cagr_sales_5yr"

    med_roe = df_sector[roe_col].dropna().median() if roe_col in df_sector.columns else None
    med_roce = df_sector["roce"].dropna().median() if "roce" in df_sector.columns else None
    med_de = df_sector["debt_to_equity"].dropna().median() if "debt_to_equity" in df_sector.columns else None
    med_rev = df_sector[rev_col].dropna().median() if rev_col in df_sector.columns else None
    med_pe = df_sector["pe_ratio"].dropna().median() if "pe_ratio" in df_sector.columns else None

    med_kpis = [
        [Paragraph("<b>Median ROE</b>", style_th), Paragraph("<b>Median ROCE</b>", style_th), Paragraph("<b>Median D/E</b>", style_th), Paragraph("<b>Median Rev CAGR</b>", style_th), Paragraph("<b>Median P/E</b>", style_th)],
        [Paragraph(_fmt(med_roe, "%"), style_td), Paragraph(_fmt(med_roce, "%"), style_td), Paragraph(_fmt(med_de, "", 2), style_td), Paragraph(_fmt(med_rev, "%"), style_td), Paragraph(_fmt(med_pe, "", 1), style_td)]
    ]
    med_tbl = Table(med_kpis, colWidths=[108]*5)
    med_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_blue),
        ('BACKGROUND', (0, 1), (-1, 1), c_card),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(med_tbl)
    story.append(Spacer(1, 16))

    # 3. Member Companies Directory (8 metrics per company)
    story.append(Paragraph("Member Companies Financial Directory", style_h2))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceAfter=8))

    tbl_headers = ["Company", "Ticker", "ROE (%)", "ROCE (%)", "D/E", "Rev CAGR", "P/E", "Market Cap"]
    rows = [[Paragraph(f"<b>{h}</b>", style_th) for h in tbl_headers]]

    for _, c_row in df_sector.sort_values("company_name").iterrows():
        r_name = c_row.get("company_name", c_row["company_id"])
        r_tick = c_row.get("ticker", c_row["company_id"])
        r_roe = _fmt(c_row.get(roe_col), "", 1)
        r_roce = _fmt(c_row.get("roce"), "", 1)
        r_de = _fmt(c_row.get("debt_to_equity"), "", 2)
        r_rev = _fmt(c_row.get(rev_col), "", 1)
        r_pe = _fmt(c_row.get("pe_ratio"), "", 1)
        r_mcap = _fmt(c_row.get("market_cap"), "", 0)

        rows.append([
            Paragraph(f"<b>{r_name}</b>", style_td_l),
            Paragraph(f"<code>{r_tick}</code>", style_td),
            Paragraph(r_roe, style_td),
            Paragraph(r_roce, style_td),
            Paragraph(r_de, style_td),
            Paragraph(r_rev, style_td),
            Paragraph(r_pe, style_td),
            Paragraph(r_mcap, style_td)
        ])

    comp_tbl = Table(rows, colWidths=[110, 65, 55, 55, 45, 60, 50, 100])
    comp_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_card]),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(comp_tbl)

    doc.build(story)
    return True


def run_batch_sector_reports(db_path: str = DB_PATH, output_dir: str = SECTOR_DIR) -> int:
    """
    Generates 11 sector PDF reports saved in reports/sector/<clean_sector_name>_report.pdf.
    """
    logger.info("Generating Sector PDF Reports...")
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return 0

    with get_db_connection(db_path) as conn:
        df_latest = pd.read_sql_query("""
            SELECT fr.*, c.company_name, c.ticker, s.sector_name, mc.market_cap
            FROM financial_ratios fr
            JOIN companies c ON fr.company_id = c.company_id
            LEFT JOIN sectors s ON c.sector_id = s.sector_id
            LEFT JOIN market_cap mc ON fr.company_id = mc.company_id AND CAST(mc.date AS INTEGER) = fr.year
            WHERE fr.year = (SELECT MAX(year) FROM financial_ratios fr2 WHERE fr2.company_id = fr.company_id)
        """, conn)

    if df_latest.empty:
        logger.warning("No data found for sector reports.")
        return 0

    generated_cnt = 0
    for sector_name, df_sec in df_latest.groupby("sector_name"):
        if not sector_name or pd.isna(sector_name):
            continue
        clean_name = str(sector_name).replace("/", "_").replace("&", "and").replace(" ", "_")
        pdf_path = os.path.join(output_dir, f"{clean_name}_report.pdf")
        success = generate_sector_pdf(str(sector_name), df_sec, pdf_path)
        if success:
            generated_cnt += 1

    logger.info(f"Generated {generated_cnt} sector PDF reports in {output_dir}.")
    return generated_cnt


if __name__ == "__main__":
    cnt = run_batch_sector_reports()
    print(f"Generated {cnt} Sector PDFs.")
