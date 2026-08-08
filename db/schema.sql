PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sectors (
    sector_id TEXT PRIMARY KEY,
    sector_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS companies (
    company_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    ticker TEXT UNIQUE NOT NULL,
    sector_id TEXT,
    FOREIGN KEY (sector_id) REFERENCES sectors (sector_id)
);

CREATE TABLE IF NOT EXISTS profitandloss (
    company_id TEXT,
    year INTEGER,
    sales REAL CHECK(sales >= 0),
    operating_profit REAL,
    net_profit REAL,
    eps REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies (company_id)
);

CREATE TABLE IF NOT EXISTS balancesheet (
    company_id TEXT,
    year INTEGER,
    total_assets REAL,
    total_liabilities REAL,
    total_equity REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies (company_id)
);

CREATE TABLE IF NOT EXISTS cashflow (
    company_id TEXT,
    year INTEGER,
    operating_cash_flow REAL,
    investing_cash_flow REAL,
    financing_cash_flow REAL,
    net_cash_flow REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies (company_id)
);

CREATE TABLE IF NOT EXISTS analysis (
    company_id TEXT,
    year INTEGER,
    revenue_growth REAL,
    profit_margin REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies (company_id)
);

CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    company_id TEXT,
    year INTEGER,
    doc_url TEXT,
    FOREIGN KEY (company_id) REFERENCES companies (company_id)
);

CREATE TABLE IF NOT EXISTS prosandcons (
    pc_id TEXT PRIMARY KEY,
    company_id TEXT,
    year INTEGER,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies (company_id)
);

CREATE TABLE IF NOT EXISTS peer_groups (
    group_id TEXT PRIMARY KEY,
    company_id TEXT,
    peer_company_id TEXT,
    FOREIGN KEY (company_id) REFERENCES companies (company_id),
    FOREIGN KEY (peer_company_id) REFERENCES companies (company_id)
);

CREATE TABLE IF NOT EXISTS stock_prices (
    company_id TEXT,
    date TEXT,
    close_price REAL,
    volume INTEGER,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies (company_id)
);

CREATE TABLE IF NOT EXISTS market_cap (
    company_id TEXT,
    date TEXT,
    market_cap REAL,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies (company_id)
);

CREATE TABLE IF NOT EXISTS financial_ratios (
    company_id TEXT,
    year INTEGER,
    pe_ratio REAL,
    pb_ratio REAL,
    debt_to_equity REAL,
    npm REAL,
    opm REAL,
    roe REAL,
    roce REAL,
    roa REAL,
    interest_coverage REAL,
    net_debt REAL,
    asset_turnover REAL,
    high_leverage_flag INTEGER,
    debt_free_label INTEGER,
    icr_warning INTEGER,
    icr_label TEXT,
    free_cash_flow REAL,
    cfo_quality REAL,
    capex_intensity REAL,
    fcf_conversion REAL,
    cagr_sales_3yr REAL,
    cagr_sales_5yr REAL,
    cagr_pat_3yr REAL,
    cagr_pat_5yr REAL,
    cagr_eps_3yr REAL,
    cagr_eps_5yr REAL,
    is_financial_sector INTEGER,
    capital_allocation_strategy TEXT,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,
    revenue_cagr_5yr REAL,
    pat_cagr_5yr REAL,
    eps_cagr_5yr REAL,
    composite_quality_score REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies (company_id)
);

CREATE INDEX IF NOT EXISTS idx_pnl_year ON profitandloss(year);
CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies(sector_id);
