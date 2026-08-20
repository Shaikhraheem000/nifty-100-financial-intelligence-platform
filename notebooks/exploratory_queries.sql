-- 1. Table row counts
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap;

-- 2. Company count
SELECT COUNT(DISTINCT id) AS company_count FROM companies;

-- 3. Critical null counts (example: sales in P&L)
SELECT COUNT(*) AS null_sales_count FROM profitandloss WHERE sales IS NULL;

-- 4. Duplicate company-year detection
SELECT company_id, year, COUNT(*) AS cnt 
FROM profitandloss 
GROUP BY company_id, year 
HAVING COUNT(*) > 1;

-- 5. Minimum/maximum year
SELECT MIN(year) AS min_year, MAX(year) AS max_year FROM profitandloss;

-- 6. Year coverage by company
SELECT company_id, COUNT(year) AS year_count 
FROM profitandloss 
GROUP BY company_id;

-- 7. Sector distribution
SELECT broad_sector, COUNT(*) AS company_count 
FROM sectors 
GROUP BY broad_sector;

-- 8. Foreign-key integrity
PRAGMA foreign_key_check;

-- 9. Source-vs-database reconciliation
-- (Checks the number of companies against expected 92)
SELECT 
    (SELECT COUNT(*) FROM companies) AS db_companies,
    92 AS expected_companies,
    CASE WHEN (SELECT COUNT(*) FROM companies) = 92 THEN 'PASS' ELSE 'FAIL' END AS reconciliation_status;

-- 10. Missing/partial financial records
SELECT c.id, COUNT(p.year) AS pl_years, COUNT(b.year) AS bs_years, COUNT(cf.year) AS cf_years
FROM companies c
LEFT JOIN profitandloss p ON c.id = p.company_id
LEFT JOIN balancesheet b ON c.id = b.company_id
LEFT JOIN cashflow cf ON c.id = cf.company_id
GROUP BY c.id
HAVING COUNT(p.year) < 5 OR COUNT(b.year) < 5 OR COUNT(cf.year) < 5;
