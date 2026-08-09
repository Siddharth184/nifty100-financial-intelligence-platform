import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cursor = conn.cursor()

tables = ["profitandloss", "balancesheet", "cashflow", "financial_ratios"]
for t in tables:
    cols = [r[1] for r in cursor.execute(f"PRAGMA table_info({t})").fetchall()]
    print(f"Table {t} columns: {cols}")

print("\nChecking latest year counts in financial_ratios:")
max_yr_count = cursor.execute("""
    SELECT COUNT(*) FROM financial_ratios fr
    JOIN (SELECT company_id, MAX(year) AS max_yr FROM financial_ratios GROUP BY company_id) m
    ON fr.company_id = m.company_id AND fr.year = m.max_yr
""").fetchone()[0]
print(f"Latest year per company row count: {max_yr_count}")

conn.close()
