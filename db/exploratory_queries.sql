-- ============================================================
-- Nifty100 Financial Intelligence Platform
-- Exploratory SQL Queries — Sprint 1 Day 7
-- ============================================================
-- These queries validate that the SQLite database makes
-- business sense after the full ETL pipeline load.
-- Run them against db/nifty100.db using any SQLite client.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- QUERY 1: Total companies by sector
-- Purpose: Confirms sector distribution is reasonable.
--          Nifty100 should be dominated by Financials, IT, etc.
-- ============================================================
SELECT
    s.sector_name,
    COUNT(c.company_id) AS company_count
FROM companies c
LEFT JOIN sectors s ON c.sector_id = s.sector_id
GROUP BY s.sector_name
ORDER BY company_count DESC;

-- ============================================================
-- QUERY 2: Top 10 companies by total sales (latest year)
-- Purpose: Spot-check that large-cap names (Reliance, TCS,
--          HDFC Bank) appear near the top.
-- ============================================================
SELECT
    c.company_name,
    p.year,
    p.sales
FROM profitandloss p
JOIN companies c ON p.company_id = c.company_id
WHERE p.year = (SELECT MAX(year) FROM profitandloss)
ORDER BY p.sales DESC
LIMIT 10;

-- ============================================================
-- QUERY 3: Average Net Profit by year (trend check)
-- Purpose: Year-over-year averages should show a general
--          upward trend for Nifty100 companies.
-- ============================================================
SELECT
    year,
    ROUND(AVG(net_profit), 2) AS avg_net_profit,
    COUNT(*) AS companies_reporting
FROM profitandloss
GROUP BY year
ORDER BY year;

-- ============================================================
-- QUERY 4: Companies with negative operating cash flow
-- Purpose: These exist in reality (capital-intensive firms).
--          Their presence validates the data is real, not
--          artificially cleaned.
-- ============================================================
SELECT
    c.company_name,
    cf.year,
    cf.operating_cash_flow
FROM cashflow cf
JOIN companies c ON cf.company_id = c.company_id
WHERE cf.operating_cash_flow < 0
ORDER BY cf.operating_cash_flow ASC
LIMIT 10;

-- ============================================================
-- QUERY 5: Balance Sheet equation verification
-- Purpose: Assets should approximately equal Liabilities + Equity.
--          Flags rows where the variance exceeds 1%.
-- ============================================================
SELECT
    c.company_name,
    bs.year,
    bs.total_assets,
    bs.total_liabilities + bs.total_equity AS calculated_assets,
    ROUND(ABS(bs.total_assets - (bs.total_liabilities + bs.total_equity))
          / NULLIF(bs.total_assets, 0) * 100, 2) AS variance_pct
FROM balancesheet bs
JOIN companies c ON bs.company_id = c.company_id
WHERE variance_pct > 1.0
ORDER BY variance_pct DESC
LIMIT 10;

-- ============================================================
-- QUERY 6: Companies with most financial years of data
-- Purpose: Confirms data coverage depth. Well-established
--          companies should have 10+ years.
-- ============================================================
SELECT
    c.company_name,
    COUNT(DISTINCT p.year) AS years_of_data
FROM companies c
JOIN profitandloss p ON c.company_id = p.company_id
GROUP BY c.company_name
ORDER BY years_of_data DESC
LIMIT 10;

-- ============================================================
-- QUERY 7: Stock price date range
-- Purpose: Verifies we have recent market data and identifies
--          the overall time span of stock price history.
-- ============================================================
SELECT
    MIN(date) AS earliest_date,
    MAX(date) AS latest_date,
    COUNT(DISTINCT company_id) AS companies_with_prices,
    COUNT(*) AS total_price_records
FROM stock_prices;

-- ============================================================
-- QUERY 8: Market cap extremes (largest and smallest)
-- Purpose: Reliance/TCS should be at the top. Any company
--          with market_cap = 0 is suspicious.
-- ============================================================
SELECT
    c.company_name,
    mc.date,
    mc.market_cap
FROM market_cap mc
JOIN companies c ON mc.company_id = c.company_id
WHERE mc.date = (SELECT MAX(date) FROM market_cap)
ORDER BY mc.market_cap DESC
LIMIT 5;

-- ============================================================
-- QUERY 9: Financial ratio sanity check (PE ratio bounds)
-- Purpose: PE ratios below 0 or above 200 are unusual and
--          warrant investigation.
-- ============================================================
SELECT
    c.company_name,
    fr.year,
    fr.pe_ratio,
    fr.pb_ratio,
    fr.debt_to_equity
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.company_id
WHERE fr.pe_ratio < 0 OR fr.pe_ratio > 200
ORDER BY fr.pe_ratio DESC;

-- ============================================================
-- QUERY 10: Cross-table join validation
-- Purpose: Every company_id in profitandloss MUST exist in
--          companies. If this returns rows, we have orphans.
-- ============================================================
SELECT
    p.company_id,
    p.year,
    p.sales
FROM profitandloss p
LEFT JOIN companies c ON p.company_id = c.company_id
WHERE c.company_id IS NULL;

-- ============================================================
-- QUERY 11: Row counts for all tables (reconciliation)
-- Purpose: Quick summary of how much data is in each table.
-- ============================================================
SELECT 'sectors' AS table_name, COUNT(*) AS row_count FROM sectors
UNION ALL
SELECT 'companies', COUNT(*) FROM companies
UNION ALL
SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL
SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL
SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL
SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL
SELECT 'peer_groups', COUNT(*) FROM peer_groups
UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL
SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL
SELECT 'financial_ratios', COUNT(*) FROM financial_ratios;

-- ============================================================
-- QUERY 12: EPS vs Net Profit sign consistency
-- Purpose: If Net Profit is positive, EPS must also be positive.
--          Opposite signs indicate a data quality issue.
-- ============================================================
SELECT
    c.company_name,
    p.year,
    p.net_profit,
    p.eps
FROM profitandloss p
JOIN companies c ON p.company_id = c.company_id
WHERE (p.net_profit > 0 AND p.eps < 0)
   OR (p.net_profit < 0 AND p.eps > 0);
