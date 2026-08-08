import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cursor = conn.cursor()

companies = cursor.execute(
    "SELECT COUNT(DISTINCT company_id) FROM financial_ratios"
).fetchone()[0]

company_years = cursor.execute(
    "SELECT COUNT(*) FROM (SELECT DISTINCT company_id, year FROM financial_ratios)"
).fetchone()[0]

pnl_company_years = cursor.execute(
    "SELECT COUNT(*) FROM (SELECT DISTINCT company_id, year FROM profitandloss)"
).fetchone()[0]

missing = cursor.execute("""
    SELECT company_id, year
    FROM profitandloss
    EXCEPT
    SELECT company_id, year
    FROM financial_ratios
""").fetchall()

print("Distinct Companies in Ratios :", companies)
print("Distinct Company-Year in Ratios :", company_years)
print("Distinct P&L Company-Year :", pnl_company_years)
print("P&L records missing from Ratios :", len(missing))
print("Missing records :", missing)

print("\nP&L Year-wise counts:")
rows = cursor.execute("""
    SELECT year, COUNT(DISTINCT company_id)
    FROM profitandloss
    GROUP BY year
    ORDER BY year
""").fetchall()
extra = cursor.execute("""
    SELECT company_id, year
    FROM financial_ratios

    EXCEPT

    SELECT company_id, year
    FROM profitandloss
""").fetchall()

print("\nRatio records NOT present in P&L:", len(extra))
print("Extra records:", extra)

for year, count in rows:
    print(f"{year}: {count}")

conn.close()
