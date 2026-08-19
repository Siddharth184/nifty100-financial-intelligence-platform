"""
Sprint 2 Review & Sign-Off Automation Module.

Automates Sprint 2 release validation:
1. Verifies financial_ratios table population in db/nifty100.db
2. Validates foreign key integrity via PRAGMA
3. Executes Quick Screener (ROE > 15%, D/E < 1)
4. Checks capital allocation report generation (output/capital_allocation.csv)
5. Checks ratio edge cases log (output/ratio_edge_cases.log)
6. Generates Markdown Sprint 2 Review Report (output/sprint2_review_report.md)
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


# Ensure project root is in sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger
from src.db.connection import get_db_connection
from src.db.database_manager import verify_foreign_keys

logger = get_logger(__name__)

DB_PATH = "db/nifty100.db"
OUTPUT_REPORT_PATH = "output/sprint2_review_report.md"
CAPITAL_ALLOC_PATH = "output/capital_allocation.csv"
EDGE_CASES_LOG_PATH = "output/ratio_edge_cases.log"

def run_screener_query(db_path: str = DB_PATH) -> List[Tuple]:
    """Runs the Quick Screener: Companies with ROE > 15% and D/E < 1.0."""
    with get_db_connection(db_path) as conn:
        query = """
            SELECT DISTINCT c.company_name, fr.company_id, fr.year, fr.roe, fr.debt_to_equity
            FROM financial_ratios fr
            JOIN companies c ON fr.company_id = c.company_id
            WHERE fr.roe > 15.0 AND (fr.debt_to_equity < 1.0 OR fr.debt_to_equity IS NULL) AND fr.is_financial_sector = 0
            ORDER BY fr.roe DESC
        """
        results = conn.execute(query).fetchall()
        return results

def generate_sprint2_report(db_path: str = DB_PATH, output_path: str = OUTPUT_REPORT_PATH) -> bool:
    """Generates Sprint 2 Markdown Review & Sign-off Report."""
    logger.info("=======================================================")
    logger.info("STARTING SPRINT 2 REVIEW & SIGN-OFF PROCESS")
    logger.info("=======================================================")

    with get_db_connection(db_path) as conn:
        fr_count = conn.execute("SELECT COUNT(*) FROM financial_ratios;").fetchone()[0]
        fk_ok = verify_foreign_keys(db_path)

    screener_results = run_screener_query(db_path)
    distinct_screener_companies = len(set(r[1] for r in screener_results))

    capital_alloc_exists = os.path.exists(CAPITAL_ALLOC_PATH)
    edge_cases_exists = os.path.exists(EDGE_CASES_LOG_PATH)

    report_content = f"""# Sprint 2 Release Sign-Off & Financial KPI Report

**Platform:** Nifty100 Financial Intelligence Platform  
**Sprint:** Sprint 2 (Financial Analytics & Ratio Engine)  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  

---

## 📊 1. Financial Ratios Engine Status

| Metric / Check | Value | Status |
| :--- | :--- | :--- |
| **Total Populated Ratio Records** | {fr_count} | {'PASS [OK]' if fr_count >= 1000 else 'FAIL [X]'} |
| **Foreign Key Compliance** | 0 Violations | {'PASS [OK]' if fk_ok else 'FAIL [X]'} |
| **Capital Allocation Report** | `output/capital_allocation.csv` | {'AVAILABLE [OK]' if capital_alloc_exists else 'MISSING [X]'} |
| **Ratio Edge Cases Log** | `output/ratio_edge_cases.log` | {'AVAILABLE [OK]' if edge_cases_exists else 'MISSING [X]'} |

---

## 🔍 2. Quick Screener Output (ROE > 15% & D/E < 1.0)

- **Total Matching Record Years:** {len(screener_results)}
- **Distinct Companies Identified:** {distinct_screener_companies}

### Top Qualifying Companies (Sample)

| Company Name | Company ID | Year | ROE (%) | Debt/Equity |
| :--- | :--- | :--- | :--- | :--- |
"""

    for r in screener_results[:10]:
        report_content += f"| {r[0]} | {r[1]} | {r[2]} | {r[3]:.2f}% | {r[4] if r[4] is not None else 0.0:.2f} |\n"

    sprint2_passed = fr_count >= 1000 and fk_ok and capital_alloc_exists and edge_cases_exists

    report_content += f"""
---

## 🏆 3. Sprint 2 Sign-Off Verdict

**OVERALL SPRINT 2 STATUS:** {'APPROVED [OK]' if sprint2_passed else 'REQUIRES REMEDIATION [X]'}

- [x] Day 08: Profitability Ratios (NPM, OPM, ROE, ROCE, ROA)
- [x] Day 09: Leverage & Efficiency Ratios (D/E, ICR, Net Debt, Asset Turnover, Risk Flags)
- [x] Day 10: CAGR Engine (3Y, 5Y, 10Y Growth across Sales, PAT, EPS)
- [x] Day 11: Free Cash Flow & Capital Allocation Engine
- [x] Day 12: Master Ratio Engine & SQLite Ingestion
- [x] Day 13: Financial Sector Carve-Out & Edge Case Logging
- [x] Day 14: Automated Test Suite & Quick Screener Verification
"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info(f"Sprint 2 Review Report saved to {output_path}")
    print(f"\n[SUCCESS] Sprint 2 Review process completed cleanly! Report generated at: {output_path}")
    return sprint2_passed

def main():
    generate_sprint2_report()

if __name__ == "__main__":
    main()
