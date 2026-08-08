"""
Financial Sector Carve-Out & Edge Case Logging Module — Sprint 2 Day 13.

Categorizes and logs ratio edge cases into output/ratio_edge_cases.log:
- [DATA_SOURCE_ISSUE]
- [FORMULA_DIFFERENCE]
- [VERSION_DIFFERENCE]
"""

import os
import sqlite3
import pandas as pd
from typing import List, Dict, Any
from src.utils.logger import get_logger
from src.db.connection import get_db_connection

logger = get_logger(__name__)

DB_PATH = "db/nifty100.db"
LOG_PATH = "output/ratio_edge_cases.log"

def analyze_sector_edge_cases(db_path: str = DB_PATH, log_path: str = LOG_PATH) -> bool:
    """Audits database records for financial sector carve-outs and logs edge cases."""
    logger.info("Starting Financial Sector Carve-Out and Edge Case Audit...")

    if not os.path.exists(db_path):
        logger.error(f"Database file not found at {db_path}")
        return False

    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    log_entries = []

    with get_db_connection(db_path) as conn:
        df = pd.read_sql_query("""
            SELECT 
                fr.*, 
                c.company_name, 
                s.sector_name 
            FROM financial_ratios fr
            JOIN companies c ON fr.company_id = c.company_id
            LEFT JOIN sectors s ON c.sector_id = s.sector_id
        """, conn)

        for _, row in df.iterrows():
            cid = row["company_id"]
            year = row["year"]
            cname = row["company_name"]
            is_fin = bool(row.get("is_financial_sector", 0))

            # 1. Financial Sector Carve-Out Verification
            if is_fin:
                if row.get("high_leverage_flag") == 1:
                    log_entries.append(f"[FORMULA_DIFFERENCE] Company {cname} ({cid}) FY{year}: Financial sector firm flagged for high leverage - suppressed in calculations.")
                if row.get("roce") is not None:
                    log_entries.append(f"[FORMULA_DIFFERENCE] Company {cname} ({cid}) FY{year}: Non-null ROCE ({row['roce']}) calculated for financial firm - suppressed.")

            # 2. Data Source Issues
            roe = row.get("roe")
            if roe is None:
                log_entries.append(f"[DATA_SOURCE_ISSUE] Company {cname} ({cid}) FY{year}: ROE is Null (Zero/Negative equity or missing net profit).")

            npm = row.get("npm")
            if npm is None:
                log_entries.append(f"[DATA_SOURCE_ISSUE] Company {cname} ({cid}) FY{year}: NPM is Null (Zero sales or missing data).")

            # 3. Version / Variance Differences
            cagr_sales_3yr = row.get("cagr_sales_3yr")
            if cagr_sales_3yr is None:
                log_entries.append(f"[VERSION_DIFFERENCE] Company {cname} ({cid}) FY{year}: 3Y Sales CAGR unavailable (Insufficient history or negative base).")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_entries))

    logger.info(f"Edge case audit complete. Logged {len(log_entries)} audit findings to {log_path}")
    print(f"\n[SUCCESS] Financial sector carve-out audit completed cleanly! Log saved to: {log_path}")
    return True

def main():
    analyze_sector_edge_cases()

if __name__ == "__main__":
    main()
