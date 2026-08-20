-- 10 Tables for Sprint 1

CREATE TABLE IF NOT EXISTS companies (
    id VARCHAR PRIMARY KEY,
    company_logo TEXT,
    company_name VARCHAR NOT NULL,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value NUMERIC,
    book_value NUMERIC,
    roce_percentage NUMERIC,
    roe_percentage NUMERIC
);

CREATE TABLE IF NOT EXISTS profitandloss (
    id INTEGER,
    company_id VARCHAR NOT NULL,
    year VARCHAR NOT NULL,
    sales NUMERIC NOT NULL,
    expenses NUMERIC NOT NULL,
    operating_profit NUMERIC,
    opm_percentage NUMERIC,
    other_income NUMERIC,
    interest NUMERIC,
    depreciation NUMERIC,
    profit_before_tax NUMERIC,
    tax_percentage NUMERIC,
    net_profit NUMERIC,
    eps NUMERIC,
    dividend_payout NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS balancesheet (
    id INTEGER,
    company_id VARCHAR NOT NULL,
    year VARCHAR NOT NULL,
    equity_capital NUMERIC NOT NULL,
    reserves NUMERIC,
    borrowings NUMERIC,
    other_liabilities NUMERIC,
    total_liabilities NUMERIC NOT NULL,
    fixed_assets NUMERIC,
    cwip NUMERIC,
    investments NUMERIC,
    other_asset NUMERIC,
    total_assets NUMERIC NOT NULL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS cashflow (
    id INTEGER,
    company_id VARCHAR NOT NULL,
    year VARCHAR NOT NULL,
    operating_activity NUMERIC,
    investing_activity NUMERIC,
    financing_activity NUMERIC,
    net_cash_flow NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER,
    company_id VARCHAR NOT NULL PRIMARY KEY,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id VARCHAR NOT NULL,
    year INTEGER NOT NULL,
    annual_report TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id),
    UNIQUE (company_id, year)
);

CREATE TABLE IF NOT EXISTS prosandcons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id VARCHAR NOT NULL,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER,
    company_id VARCHAR NOT NULL PRIMARY KEY,
    broad_sector VARCHAR NOT NULL,
    sub_sector VARCHAR NOT NULL,
    index_weight_pct NUMERIC,
    market_cap_category VARCHAR,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER,
    company_id VARCHAR NOT NULL,
    date VARCHAR NOT NULL,
    open_price NUMERIC,
    high_price NUMERIC,
    low_price NUMERIC,
    close_price NUMERIC,
    volume INTEGER,
    adjusted_close NUMERIC,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS market_cap (
    id INTEGER,
    company_id VARCHAR NOT NULL,
    year INTEGER NOT NULL,
    market_cap_crore NUMERIC,
    enterprise_value_crore NUMERIC,
    pe_ratio NUMERIC,
    pb_ratio NUMERIC,
    ev_ebitda NUMERIC,
    dividend_yield_pct NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
