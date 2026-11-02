# Sprint 2 Retrospective - Financial Ratio Engine

## Sprint Objective
Build a production-quality Financial Ratio Engine to calculate 50+ KPIs for every valid company-year combination using the SQLite data foundation. Handle all required financial edge cases natively, perform cross-checks, and securely populate the `financial_ratios` table.

## Execution Results

### D08 Result: Profitability Ratios
- **PASS**: Computed NPM, OPM, ROE, ROCE. Handled zero-sales and negative-equity edge cases successfully (returning `None`). Executed strict cross-checks between calculated OPM and raw `opm_percentage`, logging any deviation >1% (432 cases logged).

### D09 Result: Leverage & Efficiency
- **PASS**: Calculated D/E, ICR, Asset Turnover. Bank/NBFC D/E carve-outs implemented smoothly via sector joins. Safely handled "debt-free" edge cases for ICR and non-financial D/E > 5 flagging.

### D10 Result: CAGR Engine
- **PASS**: Calculated 3Y, 5Y, and 10Y CAGRs for Revenue, PAT, and EPS. Identified and flagged `TURNAROUND` (290 cases), `DECLINE_TO_LOSS` (250 cases), `BOTH_NEGATIVE` (70 cases), and `ZERO_BASE` (50 cases). Avoided calculating invalid fractional powers on negative bases.

### D11 Result: Cash Flow KPIs
- **PASS**: Calculated FCF, CFO Quality, CapEx Intensity, and FCF Conversion. Deterministically mapped the CFO, CFI, and CFF sign combinations to the 8 required capital allocation patterns.

### D12 Result: Database Population
- **PASS**: Successfully persisted 1070 computed KPI rows directly to the `financial_ratios` SQLite table using robust transactional integrity. No duplicate combinations or anomalous inserts.

### D13 Result: Bank/NBFC ROCE
- **PASS**: Isolated Financial sector companies dynamically. Cross-checked calculated ROCE against `roce_percentage` in `companies.xlsx` and generated `output/sector_roce_notes.csv` logging 434 anomalies where the textbook logic diverges from the raw source report.

### D14 Result: QA and Testing
- **PASS**: 21/21 pytest tests passed. The end-to-end integration test successfully built the database, checked schema, and verified idempotency. Generated the `ratio_edge_cases.log` machine-audit output.

---

## Metrics & Coverage

- **Companies Processed**: 92
- **Company-Year Combinations**: 1070
- **KPI Coverage**: 100% of available historical periods in the database.
- **Capital Allocation Rows**: 1070

### Edge Cases Audited (1804 Total)
- `ROCE_ANOMALY`: 434
- `OPM_MISMATCH`: 432
- `TURNAROUND`: 290
- `DECLINE_TO_LOSS`: 250
- `DEBT_FREE`: 224
- `BOTH_NEGATIVE`: 70
- `ZERO_BASE`: 50
- `HIGH_DE`: 36
- `INSUFFICIENT`: 12
- `ZERO_PAT`: 2
- `ZERO_SALES`: 2
- `ZERO_ASSETS`: 2

- **Test Results**: 21 passed / 0 failed.
- **Manual Validation Results**: PASS (Differences ≤ ±2% on verified non-edge cases for TCS, HDFCBANK, BAJFINANCE, RELIANCE).
- **Runtime**: ~3.80s for the entire batch ratio generation.

---

## Known Issues
- Differences between our mathematically rigid ROCE/OPM formulas and the raw scraped text data (e.g. `opm_percentage` and `roce_percentage` fields in the Excel files). Rather than silently substituting, both the calculated metrics and the discrepancies were logged for upstream analyst review. 

## Specification Ambiguities
- The project documentation stated "capital_allocation.csv" needs to be outputted, but the database schema did not specify a `capital_allocation` table. We produced `output/capital_allocation.csv` cleanly alongside the database outputs as instructed.
- D/E and ROCE treatment for Financials: While calculating these via normal textbook metrics is problematic for banks, the engine successfully computed the mathematically exact formulas and let the business logic / anomalies log flag the divergences rather than skipping calculation entirely.

## Decisions Taken
- Idempotency was guaranteed by explicitly issuing `DELETE FROM financial_ratios;` at the beginning of the transaction.
- Opted to merge tables (`profitandloss`, `balancesheet`, `cashflow`, `sectors`) in memory via Pandas for rapid vectorized execution prior to inserting them into SQLite, keeping the calculation runtime under 5 seconds for the entire decade of market data.

## Sprint 3 Readiness
- **YES**. The foundation and KPI pipeline is verified, complete, and the database is ready for the Screener, Scoring Model, and Sector Analytics modules.
